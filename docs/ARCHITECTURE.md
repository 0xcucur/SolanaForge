# 🏗️ Architecture — SolanaForge

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SolanaForge Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Hermes    │    │   Manifest  │    │     RTK     │     │
│  │   Agent     │◄──►│   Router    │◄──►│  Optimizer  │     │
│  │  (Core)     │    │  (70+ LLMs) │    │ (60-90% ↓)  │     │
│  └──────┬──────┘    └─────────────┘    └─────────────┘     │
│         │                                                   │
│  ┌──────▼──────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Agent     │    │   Cron      │    │   Memory    │     │
│  │  Delegation │    │  Scheduler  │    │  (Long-term)│     │
│  │ (Parallel)  │    │ (Context    │    │ (282 skills)│     │
│  └──────┬──────┘    │  Chaining)  │    └─────────────┘     │
│         │           └─────────────┘                         │
│  ┌──────▼──────────────────────────────────────────┐       │
│  │              Agent Workforce                     │       │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │       │
│  │  │  Mint  │ │   LP   │ │ Intel  │ │Security│   │       │
│  │  │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │   │       │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘   │       │
│  └──────┼──────────┼──────────┼──────────┼─────────┘       │
│         │          │          │          │                   │
│  ┌──────▼──────────▼──────────▼──────────▼─────────┐       │
│  │              External APIs                       │       │
│  │  Helius │ Birdeye │ Meteora │ Jupiter │ Raydium │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     Blockchain Layer                        │
│  ┌──────────────────────┐  ┌────────────────────────────┐  │
│  │      Solana           │  │         EVM Chains         │  │
│  │  Raydium, Jupiter,    │  │  ETH, Base, MegaETH,      │  │
│  │  Orca, Meteora DLMM,  │  │  Tempo                    │  │
│  │  Helius RPC, Birdeye  │  │  NFT Minting, ERC20/721   │  │
│  └──────────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Agent Communication Flow

```
User Request (Telegram)
       │
       ▼
Hermes Agent (Orchestrator)
       │
       ├──► Delegate to Mint Agent (if NFT related)
       │    └──► EVM RPC → Contract → Transaction
       │
       ├──► Delegate to LP Agent (if liquidity related)
       │    └──► Meteora SDK → DLMM Pool → Position
       │
       ├──► Delegate to Intel Agent (if research related)
       │    └──► Birdeye/Helius/Dune → Analysis → Report
       │
       └──► Delegate to Security Agent (if audit related)
            └──► Scan → Analysis → Verdict
       │
       ▼
Response to User (Telegram)
```

## Multi-Agent Orchestration

SolanaForge uses Hermes Agent's `delegate_task` for parallel agent execution:

```python
# Example: Full security + LP analysis
delegate_task(
    tasks=[
        {"goal": "Screen DLMM pools and rank top 5", "toolsets": ["terminal", "web"]},
        {"goal": "Audit top 3 tokens for rug pull signs", "toolsets": ["terminal", "web"]},
        {"goal": "Analyze whale movements for SOL", "toolsets": ["web"]},
    ],
    role="orchestrator"
)
```

## Skill Registry

282 skills organized by domain:
- **solana/** (77): Raydium, Jupiter, Orca, Meteora, Helius, Birdeye, etc.
- **hack/** (102): Security auditing, vulnerability scanning, penetration testing
- **meta/** (4): Self-improvement, memory, skill factory
- **Other** (99): Browser, coding, productivity, research, etc.

Skills are loaded on-demand via `skill_view()` to minimize token consumption.

## Token Optimization

| Component | Savings | Method |
|-----------|---------|--------|
| RTK | 60-90% | Filter terminal output |
| Skill Loading | ~70% | On-demand via skill_view |
| Manifest Routing | ~50% | Auto-select cheapest model |
| Context Compression | ~40% | Session summaries |

**Estimated: 500K tokens/day → ~150K after optimization**
