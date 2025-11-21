#!/bin/bash

# Setup script for DeFi Agent Evaluation Environment
# This script installs Foundry (Anvil) and starts a local blockchain fork

set -e

echo "🔧 Setting up DeFi Agent Evaluation Environment"
echo "================================================"

# Check if Foundry is installed
if ! command -v foundryup &> /dev/null; then
    echo "📦 Installing Foundry..."
    curl -L https://foundry.paradigm.xyz | bash
    source ~/.bashrc || source ~/.zshrc
    foundryup
else
    echo "✅ Foundry already installed"
fi

# Check if Anvil is available
if ! command -v anvil &> /dev/null; then
    echo "❌ Anvil not found. Please run 'foundryup' and try again."
    exit 1
fi

echo "✅ Foundry/Anvil is ready"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found. Using defaults."
    echo "   Please copy .env.example to .env and configure your API keys."
fi

# Start Anvil with mainnet fork
echo ""
echo "🚀 Starting Anvil (Local Ethereum Fork)..."
echo "================================================"

FORK_URL="${FORK_URL:-https://eth-mainnet.g.alchemy.com/v2/demo}"

echo "Fork URL: $FORK_URL"
echo "RPC URL: http://127.0.0.1:8545"
echo ""
echo "📝 Anvil will run with the following configuration:"
echo "   - Chain ID: 1 (Ethereum Mainnet)"
echo "   - Accounts: 10 pre-funded test accounts"
echo "   - Gas Price: 0 (free transactions)"
echo "   - Fork: Latest Ethereum mainnet state"
echo ""
echo "Press Ctrl+C to stop Anvil"
echo "================================================"
echo ""

# Start Anvil
anvil \
  --fork-url "$FORK_URL" \
  --chain-id 1 \
  --gas-price 0 \
  --base-fee 0 \
  --accounts 10 \
  --balance 10000
