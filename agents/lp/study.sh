#!/bin/bash
# Deep LP Study Script — analyzes top pools for optimal LP strategy
# Usage: bash study.sh [pool_address]

cd ~/.hermes/wallets/solana-lp-bot

if [ -z "$1" ]; then
    echo "Usage: study.sh <pool_address>"
    echo "Use 'screen' to find top pools first"
    exit 1
fi

POOL="$1"
API_KEY="${AGENT_MERIDIAN_KEY:-YOUR_AGENT_MERIDIAN_KEY}"

echo "🔬 Deep Study: $POOL"
echo "============================================"

# Pool detail
echo ""
echo "📊 Pool Detail:"
curl -sL -H "x-api-key: $API_KEY" "https://api.agentmeridian.xyz/api/discovery/pools/$POOL" | \
  node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
    const j=JSON.parse(d);
    console.log('  Name:',j.name);
    console.log('  Bin Step:',j.dlmm_params?.bin_step);
    console.log('  Active Bin:',j.dlmm_params?.active_id);
    console.log('  Fee:',j.fee_pct+'%','|','Max Fee:',j.dlmm_params?.max_fee_bps+'bps');
    console.log('  Volatility:',j.dlmm_params?.volatility_accumulator);
    console.log('  Token X:',j.token_x?.symbol,'| MCap: \$'+(j.token_x?.market_cap/1e6).toFixed(1)+'M | Holders:',j.token_x?.holders,'| Verified:',j.token_x?.is_verified);
    console.log('  Token Y:',j.token_y?.symbol,'| Price:',j.token_y?.price);
  })"

# Study LPers
echo ""
echo "🎯 Top LPers Study:"
curl -sL -H "x-api-key: $API_KEY" "https://api.agentmeridian.xyz/api/study-top-lp/$POOL" | \
  node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
    const j=JSON.parse(d);
    console.log('  Active Positions:',j.activePositionCount);
    console.log('  Suggested:',JSON.stringify(j.suggestedStyle));

    console.log('\n  --- Winners ---');
    j.topWinnersByPct?.slice(0, 5).forEach((w,i) => {
      console.log('    '+(i+1)+'. PnL: '+w.pnlPct?.toFixed(1)+'% | Fee: \$'+w.feeUsd?.toFixed(1)+' | Hold: '+w.ageHours?.toFixed(1)+'h | Strat: '+w.strategy+' | Range: '+w.rangeStyle+' | Bins: '+w.widthBins+' | Value: \$'+w.inputValue?.toFixed(0));
    });

    console.log('\n  --- All-Time Historical ---');
    j.topHistoricalOwners?.slice(0, 5).forEach((h,i) => {
      const strat = h.preferredStrategy || '?';
      const range = h.preferredRangeStyle || '?';
      console.log('    '+(i+1)+'. AvgPnL: '+h.avgPnlPct?.toFixed(1)+'% | AvgHold: '+h.avgHoldHours?.toFixed(1)+'h | AvgFee: '+h.avgFeePercent?.toFixed(1)+'% | Strat: '+strat+' | Range: '+range);
      h.topPositions?.slice(0, 2).forEach(p => {
        console.log('       Pos: '+p.pnlPct?.toFixed(1)+'% | '+p.ageHours?.toFixed(1)+'h | \$'+p.inputValue?.toFixed(0)+' | Bins: '+p.widthBins);
      });
    });
  })"

echo ""
echo "============================================"