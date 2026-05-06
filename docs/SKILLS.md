# 📚 Skills Registry — SolanaForge

SolanaForge ships with **282 specialized agent skills** organized by domain. Skills are loaded on-demand via `skill_view()` to minimize token consumption.

## Overview

| Category | Count | Source | Description |
|----------|-------|--------|-------------|
| Solana Ecosystem | 77 | ClawHub + GitHub | Raydium, Jupiter, Orca, Meteora, Helius, Birdeye, etc. |
| Security / Hacking | 102 | yaklang/hack-skills | Vulnerability scanning, penetration testing, exploit patterns |
| Meta / Self-Improvement | 4 | Hermes built-in | Memory, skill factory, self-improving agent |
| Other Tools | 99 | Hermes built-in | Browser, coding, productivity, research, social media |

## Solana Skills (77)

### DeFi Protocols
- **raydium** — Raydium AMM/CLMM SDK integration
- **orca** — Orca Whirlpool concentrated liquidity
- **meteora** — Meteora DLMM, vaults, farms
- **jupiter** — Jupiter aggregator swap routing
- **jupiter-swap-integration** — Deep Jupiter API integration
- **sanctum** — Sanctum liquid staking (LST)
- **kamino** — Kamino Finance lending/vaults
- **marginfi** — Marginfi lending/borrowing

### Trading & Execution
- **solana-trader** — Autonomous token trading agent
- **trading-bot-architecture** — Trading bot design patterns
- **sniper-dynamics-and-mitigation** — Sniper bot detection & defense
- **jito-bundles-and-priority-fees** — Jito MEV protection bundles
- **pump-fun-mechanics** — Pump.fun bonding curve mechanics
- **pump-analyzer-solana** — Pump.fun real-time analytics

### Intelligence & Data
- **helius** — Helius RPC, webhooks, parsed transactions
- **birdeye** — Birdeye real-time DeFi data API
- **coingecko** — CoinGecko Solana API integration
- **ct-alpha** — Crypto Twitter alpha research via X
- **whale-wallet-analysis** — Whale wallet tracking & patterns
- **wallet-analysis** — Multi-chain wallet portfolio analysis
- **rug-detection-checklist** — 20+ rug pull red flags
- **token-analysis-checklist** — Token deep-dive analysis

### Infrastructure
- **solana-kit** — Modern @solana/kit SDK
- **solana-dev** — Solana dApp development guide
- **helius-dflow** — DFlow trading integration
- **quicknode** — QuickNode RPC infrastructure
- **surfpool** — Surfpool dev environment

### Security
- **solana-vulnerability-scanner** — 6 critical vulnerability checks
- **frontend-security-basics** — Phishing & prompt injection defense
- **light-protocol** — Light Protocol ZK compression

## Security Skills (102)

From yaklang/hack-skills — covers:
- Smart contract vulnerabilities (Solidity, Rust)
- API security (JWT, OAuth, BOLA, IDOR)
- Injection attacks (SQL, SSTI, XXE, XSS, command injection)
- Privilege escalation (Linux, Windows)
- Network protocol attacks
- Cryptographic attacks (RSA, symmetric ciphers)
- Container escape
- DeFi attack patterns (flash loans, reentrancy)
- WAF bypass techniques

## Loading Skills

Skills are loaded on-demand in Hermes Agent:

```python
# Load a specific skill
skill_view(name="meteora")

# Search for relevant skills
skill_view(name="helius-jupiter")  # Combined Helius + Jupiter
```

## Installing More Skills

From ClawHub:
```bash
clawhub install <skill-name>
```

From GitHub:
```bash
# Clone and copy SKILL.md to ~/.hermes/skills/<category>/
git clone <repo-url> /tmp/skill-source
cp /tmp/skill-source/SKILL.md ~/.hermes/skills/<category>/<skill-name>/
```

## Skill Directory Structure

```
~/.hermes/skills/
├── solana/
│   ├── meteora/SKILL.md
│   ├── raydium/SKILL.md
│   ├── helius/SKILL.md
│   ├── birdeye/SKILL.md
│   └── ... (77 total)
├── hack/
│   ├── smart-contract-vulnerabilities/SKILL.md
│   ├── sqli-sql-injection/SKILL.md
│   ├── defi-attack-patterns/SKILL.md
│   └── ... (102 total)
└── meta/
    ├── elite-longterm-memory/SKILL.md
    ├── Skill Factory/SKILL.md
    └── self-improving-agent/SKILL.md
```
