# 🎬 Video Recording Script & Talking Points

## 📝 3-Minute Video Structure

### 🎯 OPENING (0:00 - 0:30) - Task Introduction
**"Hello! I'm presenting the Green Agent Evaluation Framework for crypto trading AI agents, developed by A10 Team for CS294."**

**Show on screen:** `python3 video_demo.py` running

**Key Points to Cover:**
- "Our task is to evaluate crypto trading AI agents in DeFi operations"
- "The environment is a sandbox blockchain with realistic DeFi protocols like Uniswap and Curve"
- "Agents can perform token swaps, portfolio rebalancing, staking, and automated trading strategies"
- "Our Green Agent evaluates three key dimensions: correctness, safety, and efficiency"

### 🧪 DEMONSTRATION (0:30 - 2:30) - Live Examples

**"Let me show you how our Green Agent evaluates different White Agent outputs..."**

#### Example 1: OptimalSwapBot_v2.0 (0:30 - 1:00)
**"First, we have an excellent agent performing a simple ETH to USDC swap"**
- Point out the high overall score (0.92/1.00)
- "Notice the perfect safety score - no risk factors detected"
- "The Green Agent approved this for execution"
- "It validates swap parameters, checks for MEV protection, and simulates the outcome"

#### Example 2: RiskyArb_v1.2 (1:00 - 1:45)
**"Now here's a dangerous agent attempting a risky operation"**
- Point out the low score (0.46/1.00) and DANGEROUS classification
- "The Green Agent detected multiple red flags: unverified contracts, 25% slippage tolerance, excessive gas usage"
- "Despite achieving the technical goal, the safety score is zero"
- "This demonstrates how our Green Agent protects users from unsafe operations"

#### Example 3: SmartRebalancer_v1.8 (1:45 - 2:30)
**"Finally, a portfolio rebalancing agent with moderate complexity"**
- Point out the good score (0.90/1.00) and SAFE classification
- "The Green Agent evaluates the allocation strategy and validates rebalancing thresholds"
- "Even with multiple transactions, it's classified as safe"

### 🔬 DESIGN NOTES (2:30 - 3:00) - Wrap Up

**"Our test case design ensures comprehensive reliability testing"**

**Key Points:**
- "We created a spectrum from excellent to dangerous agents"
- "Test cases cover real DeFi scenarios based on actual protocols"
- "Edge cases include unverified contracts and high-risk operations"
- "The multi-dimensional evaluation balances correctness, safety, and efficiency"

**"Our Green Agent demonstrates automated safety classification, transaction simulation, and actionable recommendations - making it ready for production DeFi environments."**

---

## 🎥 Video Recording Tips

### Technical Setup
1. **Screen Recording**: Use QuickTime or similar
2. **Terminal Setup**: 
   ```bash
   cd /Users/louis/Desktop/CS294/green_agent_demo
   python3 video_demo.py
   ```
3. **Window Size**: Make terminal text large enough to read
4. **Audio**: Clear narration explaining what's happening

### Presentation Tips
- **Pace**: Speak clearly and not too fast
- **Highlight**: Point out key scores and classifications
- **Explain**: What the Green Agent is assessing in each case
- **Visual**: Let the output scroll naturally, don't rush

### Key Messages to Emphasize
1. **Multi-dimensional evaluation** (correctness + safety + efficiency)
2. **Real-world relevance** (actual DeFi scenarios)
3. **Safety-first approach** (dangerous agents get rejected)
4. **Comprehensive framework** (handles diverse agent types)

---

## 📋 Demo Commands Reference

```bash
# Interactive demo (for testing)
python3 demo.py

# Automated demo (for video recording)
python3 video_demo.py

# Show white agent spectrum
python3 white_agent_simulator.py
```

---

## 🎯 Success Criteria Check

✅ **Task Introduction**: Environment, actions, evaluation criteria  
✅ **Demonstration**: 3 concrete examples with different risk levels  
✅ **Green Agent Assessment**: Clear explanation of what's being evaluated  
✅ **Design Notes**: Test case generation and reliability testing rationale  
✅ **Concise**: Under 3 minutes when narrated properly  

**Ready to record! Good luck with your video! 🎬**