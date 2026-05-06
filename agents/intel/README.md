# 📊 Intelligence Agent — SolanaForge

Real-time on-chain intelligence gathering from multiple sources, aggregated into actionable insights.

## Data Sources

### Solana Native
- **Helius RPC**: Transaction parsing, webhooks, parsed accounts
- **Birdeye API**: Token prices, DEX trades, whale tracking
- **Dune Analytics**: Historical queries, custom dashboards

### Social Intelligence
- **X/Twitter**: CT alpha, whale movements, sentiment
- **Discord**: Server monitoring, alpha channels
- **Telegram**: Signal groups, bot feeds

### Market Data
- **Raydium**: AMM trades, liquidity changes
- **Jupiter**: Aggregator routing, best prices
- **Orca**: Concentrated liquidity pools
- **Meteora**: DLMM pool data, top LPer analysis

## Agents

### Pool Screener (`pool_screener.js`)
Screens 100+ DLMM pools every 6 hours:
- Score: fee/TVL ratio (7%+ = good)
- Volume trends (24h vs 7d average)
- Liquidity depth analysis
- Top LPer strategy patterns

### Whale Tracker (`whale_tracker.js`)
Monitors whale wallets in real-time:
- Detect accumulation patterns (>10x normal volume)
- Cross-reference with known market makers
- Alert on large token movements (>$50K)
- Track new token launches by whales

### Sentiment Analyzer
Processes social signals:
- CT sentiment scoring (-1 to +1)
- Token mention frequency tracking
- Whale/VC/KOL movement correlation
- Early warning on rug pulls (famous last words detection)

## Usage

```bash
# Screen pools now
node pool_screener.js

# Watch whale movements
node whale_tracker.js --watch --min-amount 50000

# Get sentiment for token
node sentiment.js --token BONK
```

## Output Format

```json
{
  "timestamp": "2025-07-07T02:30:00Z",
  "pools_screened": 107,
  "top_picks": [
    {
      "pool": "67C4rdUriP9EFbUo7CeoiFhM52Jgu9LZpe37Jk2k1tHZ",
      "name": "USDUC-SOL",
      "score": 86.3,
      "fee_tvl_ratio": 12.7,
      "strategy": "spot",
      "win_rate": 100,
      "avg_pnl": 87.0
    }
  ],
  "whale_alerts": [],
  "sentiment": {
    "overall": 0.65,
    "trending": ["BONK", "WIF", "POPCAT"]
  }
}
```
