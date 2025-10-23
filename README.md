# CS294 - Green Agent Evaluation Framework

**A10 Team**: Mingxi Tang, Yufeng Yan, Haofeng Liu, Meixin Ma

## Project: Green Agent Evaluation for Crypto Trading AI Agent in DeFi Operations

This repository contains our implementation of a Green Agent evaluation framework for crypto trading AI agents operating in DeFi environments.

## 📁 Project Structure

### `green_agent_demo/`
Complete demonstration of our Green Agent evaluation framework:

- **`green_agent.py`** - Core Green Agent implementation with multi-dimensional evaluation
- **`demo.py`** - Interactive demonstration (requires user input)
- **`video_demo.py`** - Automated demo for video recording
- **`white_agent_simulator.py`** - Sample White Agent implementations
- **`VIDEO_SCRIPT.md`** - Complete video recording guide and talking points
- **`README.md`** - Detailed project documentation

## 🚀 Quick Start

```bash
cd green_agent_demo
python3 video_demo.py  # Automated demo for video recording
python3 demo.py        # Interactive demo
```

## 🎯 Project Overview

**Task**: Evaluate crypto trading AI agents in DeFi operations

**Environment**: Sandbox blockchain with realistic DeFi protocols (Uniswap, Curve, etc.)

**Evaluation Dimensions**:
- ✅ **Correctness**: Goal achievement & parameter validation
- 🛡️ **Safety**: Risk detection & mitigation strategies  
- ⚡ **Efficiency**: Gas optimization & routing analysis

**Safety Classifications**: SAFE | MODERATE_RISK | HIGH_RISK | DANGEROUS

## 🧪 Demo Features

- Multi-dimensional agent evaluation with weighted scoring
- Risk factor detection (slippage, MEV, contract verification)
- Transaction simulation with outcome prediction
- Safety classification with clear thresholds
- Actionable recommendations for improvement
- Comprehensive reporting and analysis

## 📊 Example Results

Our Green Agent successfully evaluates diverse agent types:
- **OptimalSwapBot** (Score: 0.92/1.00, SAFE) - Efficient operations approved
- **RiskyArb** (Score: 0.46/1.00, DANGEROUS) - High-risk operations rejected
- **SmartRebalancer** (Score: 0.90/1.00, SAFE) - Good strategy approved

## 🎬 Video Demo

The automated demo (`video_demo.py`) provides a 3-minute walkthrough suitable for course submission, covering:
1. Task introduction and environment setup
2. Live evaluation of three different agent types
3. Design rationale and framework capabilities

---

**Course**: CS294 - AI Agents  
**Institution**: UC Berkeley  
**Semester**: Fall 2025