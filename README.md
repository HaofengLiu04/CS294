# CS294 - AI Agents Course Projects

**Team A10**: Mingxi Tang, Yufeng Yan, Haofeng Liu, Meixin Ma

## Overview

This repository contains implementations for evaluating AI agents in blockchain and DeFi environments, developed for UC Berkeley's CS294 AI Agents course (Fall 2025).

## Project Structure

### `green_agent_demo/`
Initial demonstration of Green Agent evaluation framework for crypto trading AI agents.

**Key Features:**
- Multi-dimensional evaluation (correctness, safety, efficiency)
- Risk factor detection and safety classification
- Transaction simulation and outcome prediction
- Interactive and automated demo modes

**Quick Start:**
```bash
cd green_agent_demo
python3 video_demo.py  # Automated demo
python3 demo.py        # Interactive demo
```

### `defi_agent_eval/`
Advanced DeFi agent evaluation framework with real blockchain integration.

**Key Features:**
- LLM-powered white agents using OpenAI GPT-4o
- Real blockchain execution via Anvil (local Ethereum testnet)
- ERC20 token operations with actual on-chain transactions
- Natural language instruction processing
- Comprehensive test scenarios and evaluation metrics

**Quick Start:**
```bash
cd defi_agent_eval
# See defi_agent_eval/README.md for setup instructions
```

## Project Goals

**Primary Task**: Evaluate AI agents operating in DeFi environments

**Evaluation Dimensions:**
- Correctness: Goal achievement and parameter validation
- Safety: Risk detection and mitigation strategies
- Efficiency: Gas optimization and routing analysis

**Safety Classifications**: SAFE | MODERATE_RISK | HIGH_RISK | DANGEROUS

## Repository Information

**Course**: CS294 - AI Agents  
**Institution**: UC Berkeley  
**Semester**: Fall 2025

## Documentation

Detailed documentation is available in each project directory:
- `green_agent_demo/README.md` - Demo implementation guide
- `defi_agent_eval/README.md` - Advanced framework documentation