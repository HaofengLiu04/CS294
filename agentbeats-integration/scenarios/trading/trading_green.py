import argparse
import asyncio
import json
import logging
import os
import queue
import re
import sys
import time
from typing import Dict

import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, Part, TaskState, TextPart
from a2a.utils import new_agent_text_message

from agentbeats.green_executor import GreenAgent, GreenExecutor
from agentbeats.models import EvalRequest, EvalResult
from agentbeats.tool_provider import ToolProvider

# Make sure we can import the trading evaluator from the CS294 parent project
CS294_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFI_ROOT = os.path.join(CS294_ROOT, "defi_agent_eval")
for p in (CS294_ROOT, DEFI_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from defi_agent_eval.green_agent.trading.trading_evaluator import TradingEvaluator
from defi_agent_eval.green_agent.trading.models import TradingDecision, TradingAction


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_green")


def decision_from_response(resp: str) -> TradingDecision:
    """Parse the white agent response (expected JSON string) into TradingDecision."""
    try:
        data = json.loads(resp)
    except Exception:
        match = re.search(r"\{.*\}", resp, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception as e:
                logger.warning(f"Failed to parse decision (json extract), defaulting to hold: {e}")
                return TradingDecision(summary="hold", reasoning=str(resp), actions=[])
        else:
            logger.warning("Failed to parse decision (no JSON found), defaulting to hold")
            return TradingDecision(summary="hold", reasoning=str(resp), actions=[])

    actions = []
    for a in data.get("actions", []):
        try:
            actions.append(TradingAction(**a))
        except Exception:
            continue

    return TradingDecision(
        summary=data.get("summary", "hold"),
        reasoning=data.get("reasoning", ""),
        actions=actions,
    )


class TradingGreen(GreenAgent):
    """Green agent that wraps our TradingEvaluator and talks to white agents via A2A."""

    def __init__(self):
        self._tool_provider = ToolProvider()

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        if not request.participants:
            return False, "No participants provided"
        return True, "ok"

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        logger.info(f"Starting trading orchestration with participants: {list(req.participants.keys())}")

        progress_q: "queue.Queue[dict]" = queue.Queue()
        done_flag = False

        def progress_cb(event: dict):
            # called from evaluator thread; must be thread-safe
            try:
                progress_q.put_nowait(event)
            except Exception:
                pass

        async def progress_pumper():
            nonlocal done_flag
            last_sent = 0.0
            last_msg = ""
            while not done_flag:
                # drain queue and keep latest
                latest = None
                try:
                    while True:
                        latest = progress_q.get_nowait()
                except Exception:
                    pass
                if latest:
                    if latest.get("type") == "cycle":
                        msg = f"CYCLE {latest.get('cycle_idx')}/{latest.get('total_cycles')} @ {latest.get('timestamp')}"
                    elif latest.get("type") == "agent":
                        msg = f"{latest.get('agent')}: {latest.get('stage')} (cycle {latest.get('cycle_idx')})"
                    else:
                        msg = f"{latest.get('type')}: {latest}"

                    now = time.time()
                    if msg != last_msg and (now - last_sent) > 0.8:
                        last_msg = msg
                        last_sent = now
                        await updater.update_status(TaskState.working, new_agent_text_message(msg))
                await asyncio.sleep(0.2)

        def make_handler(role: str):
            def handler(prompt: str) -> TradingDecision:
                async def call_agent():
                    resp = await self._tool_provider.talk_to_agent(prompt, str(req.participants[role]), new_conversation=False)
                    return resp

                resp_text = asyncio.run(call_agent())
                return decision_from_response(resp_text)

            return handler

        agent_clients: Dict[str, callable] = {role: make_handler(role) for role in req.participants.keys()}

        evaluator = TradingEvaluator(
            agent_names=list(req.participants.keys()),
            agent_clients=agent_clients,
            config=req.config,
            progress_callback=progress_cb,
        )

        def run_sync():
            return evaluator.run_competition()

        try:
            pump_task = asyncio.create_task(progress_pumper())
            await updater.update_status(TaskState.working, new_agent_text_message("Trading evaluation started"))
            performance = await asyncio.to_thread(run_sync)
            await updater.update_status(TaskState.working, new_agent_text_message("Trading evaluation finished"))

            # Extract judge text and remove non-performance entries
            judge_text = ""
            if "_judge_text" in performance:
                judge_text = performance.pop("_judge_text", "")

            lines = []
            for name, perf in performance.items():
                if not hasattr(perf, "total_return_pct"):
                    continue
                lines.append(f"{name}: total_return={perf.total_return_pct:+.2f}%, sharpe={perf.sharpe_ratio:.2f}, score={perf.total_score:.3f}")
            summary_text = "\n".join(lines)

            perf_payload = {
                k: v.__dict__ for k, v in performance.items() if hasattr(v, "__dict__") and hasattr(v, "total_return_pct")
            }
            if judge_text:
                perf_payload["_judge_text"] = judge_text
            result = EvalResult(winner="", detail={"performance": perf_payload})
            await updater.add_artifact(
                parts=[
                    Part(root=TextPart(text=summary_text)),
                    Part(root=TextPart(text=json.dumps(result.detail, default=str))),
                    Part(root=TextPart(text=f"LLM_JUDGE:\n{judge_text}")),
                ],
                name="Result",
            )
        finally:
            done_flag = True
            try:
                pump_task.cancel()
            except Exception:
                pass
            self._tool_provider.reset()


def trading_green_agent_card(url: str) -> AgentCard:
    return AgentCard(
        name="trading_green",
        description="Trading green agent orchestrator",
        url=url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[],
    )


def main():
    parser = argparse.ArgumentParser(description="Run trading green agent (AgentBeats A2A).")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9109)
    parser.add_argument("--card-url", type=str, help="External URL for agent card")
    args = parser.parse_args()

    agent_url = args.card_url or f"http://{args.host}:{args.port}/"
    executor = GreenExecutor(TradingGreen())
    agent_card = trading_green_agent_card(agent_url)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()


