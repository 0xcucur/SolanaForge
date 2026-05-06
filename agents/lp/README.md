# 💧 LP Agent — SolanaForge

Autonomous liquidity provider on Meteora DLMM (Solana), with AI-driven strategy learned from 100+ top performing LPers.

## Features

- **Pool Screening**: Score 100+ pools by fee/TVL ratio, volume, liquidity depth
- **Strategy Learning**: Analyze top LPers via Agent Meridian API
- **Auto-Deploy**: Open positions with optimal bin range
- **Fee Claims**: Auto-claim when accumulated fees > threshold
- **Risk Management**: Stop-loss, take-profit, OOR alerts
- **Position Monitoring**: Real-time PnL tracking via WebSocket

## Commands

```bash
# Screen pools
node lp_bot.js screen

# Deploy to a pool
node lp_bot.js deploy <POOL_ADDRESS>

# Check status
node lp_bot.js status

# Close a position
node lp_bot.js close <POOL> <POSITION>

# Claim fees
node lp_bot.js claim <POOL> <POSITION>
```

## Strategy: Learned from Top LPers

Data from Agent Meridian API — 100+ top LPers analyzed across 6 DLMM pools:

| Metric | Value |
|--------|-------|
| Dominant Strategy | Spot (60%+ winners) |
| Bin Range | Medium (35-69 bins) |
| Hold Time | 2-17 days (median ~100h) |
| Sweet Spot | fee/TVL ≥7% |
| Best Pool | USDUC-SOL (87% avg PnL, 100% win rate) |
| Best Performer | 178.7% PnL, hold 560h |

## Risk Parameters

- Max position size: $20 per pool
- Gas reserve: $5 minimum
- Auto-close: OOR >2hr OR PnL drop >15%
- Auto-claim: accumulated fees >$0.50
- Max concurrent positions: 3

## Top Pools (screened 2025-07-07)

| Pool | Score | Fee/TVL | Volume 24h |
|------|-------|---------|------------|
| Goblin-SOL | 87.2 | 19.3% | $218K |
| USDUC-SOL | 86.3 | 12.7% | $16.5K |
| ASTEROID-SOL | 72.1 | 5.1% | $66K |

## Dependencies

- @meteora-ag/dlmm — Meteora DLMM SDK
- @solana/web3.js — Solana web3
- @solana/spl-token — SPL token operations
- bs58 — Base58 encoding
