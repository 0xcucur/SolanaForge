# 🛠️ SolanaForge — Autonomous AI Agent Framework for Solana DeFi

> A multi-agent AI system that automates NFT minting, liquidity pool management, on-chain intelligence gathering, and security auditing on Solana and EVM chains — powered by Hermes Agent.

## 🎯 The Problem

Solana DeFi moves fast. Manual operations mean missed mints, unoptimized LP positions, and blind spots in market intelligence. Traders and developers need:
- **Automated NFT minting** during FCFS drops (seconds matter)
- **Smart LP management** that learns from top performers
- **Real-time on-chain intelligence** from DEXes, social media, and whale wallets
- **Security-first approach** with automated vulnerability scanning

## 🏗️ Core Logic Flow

### Multi-Agent Architecture

```
┌─────────────────────────────────────────────────┐
│              SolanaForge Orchestrator            │
│         (Hermes Agent — Task Delegation)         │
├──────────┬──────────┬──────────┬────────────────┤
│ 🎨 Mint  │ 💧 LP    │ 📊 Intel │ 🔒 Security  │
│  Agent   │  Agent   │  Agent   │   Agent       │
├──────────┼──────────┼──────────┼────────────────┤
│ FCFS NFT │ Meteora  │ Birdeye  │ Rug Pull     │
│ Auto-Mint│ DLMM LP  │ Dune     │ Detection    │
│ Multi-   │ Smart    │ Helius   │ Contract     │
│ Chain    │ Strategy │ X/Twitter│ Audit        │
└──────────┴──────────┴──────────┴────────────────┘
```

### Agent Capabilities

**1. Mint Agent** — NFT minting automation
- Multi-chain support: ETH, Base, MegaETH, Tempo
- Auto-gas estimation with dynamic pricing
- Dry-run mode for safe testing
- Gas probe for contract readiness verification
- Real-time notifications via assistant

**2. LP Agent** — Liquidity Pool management
- Meteora DLMM integration on Solana
- AI-driven strategy learning from 100+ top LPers
- Auto-deploy, fee claim, position rebalancing
- Risk management: stop-loss, take-profit, OOR alerts
- Pool screening with fee/TVL scoring algorithm

**3. Intel Agent** — On-chain intelligence
- DEX trade tracking (Raydium, Jupiter, Orca)
- Whale wallet monitoring and pattern recognition
- Social sentiment analysis from X/Twitter
- Helius RPC integration for Solana data
- Birdeye API for real-time token metrics

**4. Security Agent** — Automated security audit
- Rug pull detection with 20+ red flag patterns
- Smart contract vulnerability scanning (Solana + EVM)
- Supply-chain attack detection for agent skills
- Wallet security verification
- Multi-agent audit workflow with human review

### Reasoning Flow (Example: LP Position)

```
1. POOL DISCOVERY
   → Screen 100+ DLMM pools via Meteora API
   → Score: fee/TVL ratio, volume, liquidity depth
   → Filter: pools with >$10K TVL, >7% fee/TVL

2. STRATEGY LEARNING
   → Query Agent Meridian API for top 100 LPers per pool
   → Analyze: strategy type (spot/bid-ask), bin range, hold time
   → Calculate: win rate, avg PnL, sharpe ratio per strategy

3. POSITION SIZING
   → Apply Kelly Criterion for optimal allocation
   → Risk-adjust: max 20% per position, reserve gas budget
   → Set alerts: OOR >2hr, PnL drop >15%

4. EXECUTION
   → Deploy via @meteora-ag/dlmm SDK
   → Monitor via WebSocket for real-time updates
   → Auto-claim when accumulated fees > threshold

5. CONTINUOUS OPTIMIZATION
   → Re-screen pools every 6 hours
   → Adjust strategy based on market conditions
   → Log all decisions for future learning
```

## 📊 Impact & Usage

### Token Consumption
- **~500K tokens/day** across 4 agents
- 282 specialized skills loaded on demand
- Multi-model routing via Manifest (cost optimization)
- RTK integration for 60-90% token savings on terminal output

### Real Workflows Executed
1. **NFT Mint Bot**: Built, tested, deployed on 4 EVM chains
2. **LP Strategy Research**: Analyzed 100+ top LPers via Meridian API
3. **Pool Screening**: Scored 10 DLMM pools in real-time
4. **Security Audit**: Scanned 8 ClawHub skills, caught 1 dangerous & 3 caution-rated
5. **Wallet Generation**: Created Solana + EVM wallets with proper key management

### Metrics
- **282 agent skills** installed and organized
- **4 autonomous agents** running parallel workflows
- **6 Solana protocols** integrated (Raydium, Jupiter, Orca, Meteora, Helius, Birdeye)
- **4 EVM chains** supported (ETH, Base, MegaETH, Tempo)
- **100+ wallet patterns** analyzed for LP strategy

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Hermes Agent (multi-agent orchestration) |
| AI Model Routing | Manifest API (70+ models) |
| Solana SDK | @solana/web3.js, @meteora-ag/dlmm |
| EVM SDK | web3.py (multi-chain) |
| Token Optimization | RTK (Rust Token Killer) |
| Intelligence | Birdeye, Helius, Dune Analytics |
| Scheduling | Cron jobs with context chaining |
| Security | OWASP Agentic AI patterns, skill audit pipeline |

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/SolanaForge.git
cd SolanaForge

# Install dependencies
npm install
pip install -r requirements.txt

# Configure
cp config/config.example.json config/config.json
# Edit config.json with your RPC endpoints and API keys

# Run agents
hermes run agents/mint     # NFT mint agent
hermes run agents/lp       # LP management agent
hermes run agents/intel    # Intelligence agent
hermes run agents/security # Security audit agent
```

## 📁 Project Structure

```
SolanaForge/
├── agents/
│   ├── mint/           # NFT minting automation
│   │   ├── mint_bot.py        # EVM multi-chain mint bot
│   │   └── README.md
│   ├── lp/             # Liquidity pool management
│   │   ├── lp_bot.js          # Meteora DLMM LP bot
│   │   ├── study.sh           # Pool analysis script
│   │   └── README.md
│   ├── intel/          # On-chain intelligence
│   │   ├── pool_screener.js   # DLMM pool screening
│   │   ├── whale_tracker.js   # Whale wallet monitoring
│   │   └── README.md
│   └── security/       # Security audit
│       ├── rug_detector.py    # Rug pull detection
│       ├── skill_auditor.py   # Agent skill security audit
│       └── README.md
├── skills/             # 282 specialized agent skills
│   ├── solana/         # 177 Solana ecosystem skills
│   ├── hack/           # 102 security/hacking skills
│   └── meta/           # Meta-skills (self-improvement)
├── scripts/            # Utility scripts
├── config/             # Configuration templates
├── docs/               # Documentation
│   ├── ARCHITECTURE.md
│   ├── AGENTS.md
│   └── SKILLS.md
└── README.md
```

## 🔐 Security Model

- **Private keys**: Never committed, stored in `~/.hermes/wallets/` with 600 permissions
- **API keys**: Environment variables only, never in code
- **Skill auditing**: Every skill scanned before installation
- **Dry-run mode**: All agents support `--dry-run` for safe testing
- **Human-in-the-loop**: Critical actions (live mint, large LP positions) require confirmation

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ using Hermes Agent — the autonomous AI agent framework.*
