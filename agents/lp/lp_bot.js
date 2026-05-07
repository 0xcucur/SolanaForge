/**
 * Meteora DLMM LP Bot — Autonomous Liquidity Provider
 * Strategy: spot, medium range, top-fee pools
 * Capital: ~$25 per position, auto-manage positions
 * 
 * Usage:
 *   node lp_bot.js screen              — Find best pools
 *   node lp_bot.js deploy <pool>       — Open position
 *   node lp_bot.js status              — Show open positions
 *   node lp_bot.js close <pool>        — Close position + withdraw
 *   node lp_bot.js claim <pool>        — Claim fees
 *   node lp_bot.js auto                — Full auto: screen → deploy → manage
 */

const DLMM = require("@meteora-ag/dlmm");
const { Connection, Keypair, PublicKey, LAMPORTS_PER_SOL, TransactionMessage, VersionedTransaction } = require("@solana/web3.js");
const bs58 = require("bs58").default;
const fs = require("fs");
const path = require("path");

// ─── CONFIG ───
    const HELIUS_RPC = process.env.HELIUS_RPC || "https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY";
const WALLET_PATH = process.env.WALLET_PATH || path.join(process.env.HOME, ".hermes/wallets/wallets.json");
const STATE_PATH = path.join(__dirname, "state.json");
const AGENT_MERIDIAN_KEY = process.env.AGENT_MERIDIAN_KEY || "YOUR_AGENT_MERIDIAN_KEY";

// Strategy parameters (learned from top LPers)
const STRATEGY = {
  strategy: "spot",
  rangeStyle: "medium",
  // Pool screening filters
  minTvl: 20_000,           // Minimum $20K TVL
  maxTvl: 500_000,          // Maximum $500K TVL  
  minVolume: 10_000,        // Minimum $10K 24h volume
  minHolders: 2_000,        // Minimum 2K holders
  maxMcap: 25_000_000,      // Max $25M market cap
  minFeeTvlRatio: 5,        // Min 5% fee/TVL ratio
  // Position parameters
  positionSizeUsd: 20,      // $20 per position
  gasReserveLamports: 0.05 * LAMPORTS_PER_SOL, // Keep 0.05 SOL for gas
  binsBelow: 25,            // Bins below active (medium range)
  binsAbove: 25,            // Bins above active (medium range)
  // Management
  oorCloseMinutes: 120,     // Close if out-of-range > 2 hours
  minClaimFeeUsd: 0.50,     // Claim fees when > $0.50
  maxPositions: 2,          // Max open positions
  stopLossPct: -20,         // Close if PnL < -20%
};

// ─── WALLET ───
function loadWallet() {
  const data = JSON.parse(fs.readFileSync(WALLET_PATH, "utf8"));
  const sol = data.solana;
  if (!sol) throw new Error("No Solana wallet found in wallets.json");
  const secret = bs58.decode(sol.private_key_b58);
  return Keypair.fromSecretKey(secret);
}

// ─── STATE ───
function loadState() {
  if (!fs.existsSync(STATE_PATH)) return { positions: [], history: [], stats: {} };
  return JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
}

function saveState(state) {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

// ─── POOL SCREENING ───
async function fetchPoolsFromMeteora() {
  const url = "https://pool-discovery-api.datapi.meteora.ag/pools?page_size=50&timeframe=24h&category=trending";
  const res = await fetch(url);
  const data = await res.json();
  return data.data || [];
}

async function fetchTopLPers(poolAddress) {
  const url = `https://api.agentmeridian.xyz/api/top-lp/${poolAddress}`;
  const res = await fetch(url, { headers: { "x-api-key": AGENT_MERIDIAN_KEY } });
  const data = await res.json();
  return data;
}

function filterPools(pools) {
  return pools.filter((p) => {
    const tvl = p.active_tvl || 0;
    const vol = p.volume || 0;
    const holders = p.token_x?.holders || 0;
    const mcap = p.token_x?.market_cap || 0;
    const feeTvlRatio = p.fee_tvl_ratio || 0;
    const isVerified = p.token_x?.is_verified;
    const hasFreeze = p.token_x?.has_freeze_authority;
    const hasMint = p.token_x?.has_mint_authority;

    return (
      tvl >= STRATEGY.minTvl &&
      tvl <= STRATEGY.maxTvl &&
      vol >= STRATEGY.minVolume &&
      holders >= STRATEGY.minHolders &&
      mcap <= STRATEGY.maxMcap &&
      feeTvlRatio >= STRATEGY.minFeeTvlRatio &&
      !hasFreeze &&
      !hasMint &&
      (p.pool_type === "DLMM" || p.name?.includes("-"))
    );
  });
}

function scorePool(pool, lperData) {
  const feeTvlRatio = pool.fee_tvl_ratio || 0;
  const tvl = pool.active_tvl || 0;
  const vol = pool.volume || 0;
  const holders = pool.token_x?.holders || 0;
  const topLpers = lperData.topLpers || [];

  // Score components
  const feeScore = Math.min(feeTvlRatio / 20, 1) * 30; // Max 30 points
  const tvlScore = tvl > 50_000 ? 20 : tvl / 50_000 * 20; // Max 20 points
  const volScore = Math.min(vol / 100_000, 1) * 15; // Max 15 points
  const holderScore = Math.min(holders / 10_000, 1) * 10; // Max 10 points
  const lperCountScore = Math.min(topLpers.length / 10, 1) * 15; // Max 15 points

  // Top LPer PnL average
  const pnlValues = topLpers.map((l) => l.pnlPerInflowPct || 0).filter((v) => v > 0);
  const avgPnl = pnlValues.length > 0 ? pnlValues.reduce((a, b) => a + b, 0) / pnlValues.length : 0;
  const pnlScore = Math.min(avgPnl / 50, 1) * 10; // Max 10 points

  return feeScore + tvlScore + volScore + holderScore + lperCountScore + pnlScore;
}

async function screenPools() {
  console.log("🔍 Fetching pools from Meteora...");
  const pools = await fetchPoolsFromMeteora();
  console.log(`  Found ${pools.length} pools, filtering...`);

  const filtered = filterPools(pools);
  console.log(`  ${filtered.length} pools pass filters`);

  // Fetch top LPers for each (limit to top 10 to save API calls)
  const scored = [];
  for (const pool of filtered.slice(0, 10)) {
    try {
      const lperData = await fetchTopLPers(pool.pool_address);
      const score = scorePool(pool, lperData);
      scored.push({
        ...pool,
        score,
        topLpers: lperData.topLpers || [],
        suggestedStyle: null,
      });
    } catch (e) {
      // skip
    }
  }

  scored.sort((a, b) => b.score - a.score);
  return scored;
}

// ─── POSITION MANAGEMENT ───
async function deployPosition(connection, wallet, poolAddress, poolInfo) {
  console.log(`\n🚀 Deploying position on ${poolInfo.name || poolAddress}`);

  const dlmm = await DLMM.create(connection, new PublicKey(poolAddress));
  const activeBin = await dlmm.getActiveBin();
  console.log(`  Active bin: ${activeBin.binId}, Price: ${activeBin.price}`);

  // Calculate SOL amount from USD target
  const solPrice = await fetchSolPrice();
  const solAmount = STRATEGY.positionSizeUsd / solPrice;
  const lamports = Math.floor(solAmount * LAMPORTS_PER_SOL);

  console.log(`  Position size: $${STRATEGY.positionSizeUsd} (${solAmount.toFixed(4)} SOL)`);
  console.log(`  Range: ${STRATEGY.binsBelow} below + ${STRATEGY.binsAbove} above active bin`);

  // Create position with strategy
  const maxBinId = activeBin.binId + STRATEGY.binsAbove;
  const minBinId = activeBin.binId - STRATEGY.binsBelow;

  try {
    // Use initializePositionAndAddLiquidityByStrategy
    const { transaction, position } = await dlmm.initializePositionAndAddLiquidityByStrategy({
      positionPubKey: Keypair.generate().publicKey,
      lbPairPubKey: new PublicKey(poolAddress),
      userPubKey: wallet.publicKey,
      totalXAmount: BigInt(0), // Single-side SOL (quote side)
      totalYAmount: BigInt(lamports),
      strategy: {
        maxBinId: activeBin.binId + STRATEGY.binsAbove,
        minBinId: activeBin.binId - STRATEGY.binsBelow,
        strategyType: STRATEGY.strategy === "spot" ? DLMM.StrategyType.SpotBalanced : DLMM.StrategyType.BidAskBalanced,
      },
    });

    // Sign and send
    const latestBlockhash = await connection.getLatestBlockhash();
    transaction.recentBlockhash = latestBlockhash.blockhash;
    transaction.feePayer = wallet.publicKey;
    transaction.sign(wallet);

    const txId = await connection.sendTransaction(transaction, { skipPreflight: false });
    console.log(`  ✅ TX: https://solscan.io/tx/${txId}`);

    // Save position
    const state = loadState();
    state.positions.push({
      pool: poolAddress,
      name: poolInfo.name,
      positionPubkey: position.publicKey.toString(),
      openTime: Date.now(),
      openPrice: activeBin.price,
      activeBinId: activeBin.binId,
      amountLamports: lamports,
      amountUsd: STRATEGY.positionSizeUsd,
      txId,
    });
    saveState(state);

    return { success: true, txId };
  } catch (e) {
    console.error(`  ❌ Deploy failed: ${e.message}`);
    return { success: false, error: e.message };
  }
}

async function closePosition(connection, wallet, poolAddress, positionPubkey) {
  console.log(`\n📤 Closing position ${positionPubkey}`);

  try {
    const dlmm = await DLMM.create(connection, new PublicKey(poolAddress));

    // Remove all liquidity
    const position = await dlmm.getPosition(new PublicKey(positionPubkey));
    const binArrays = await dlmm.getBinArrays();

    const removeTx = await dlmm.removeLiquidity({
      position: new PublicKey(positionPubkey),
      user: wallet.publicKey,
      fromBinId: position.lowerBinId,
      toBinId: position.upperBinId,
      binArraysCredit: binArrays.map((ba) => ba.publicKey),
    });

    // Close the position account
    const closeTx = await dlmm.closePositionIfEmpty({
      position: new PublicKey(positionPubkey),
      user: wallet.publicKey,
    });

    // Send remove liquidity
    const latestBlockhash = await connection.getLatestBlockhash();
    const removeMsg = new TransactionMessage({
      payerKey: wallet.publicKey,
      recentBlockhash: latestBlockhash.blockhash,
      instructions: removeTx.instructions || removeTx,
    }).compileToV0Message();

    const removeVtx = new VersionedTransaction(removeMsg);
    removeVtx.sign([wallet]);
    const removeSig = await connection.sendTransaction(removeVtx);
    console.log(`  Remove liquidity TX: https://solscan.io/tx/${removeSig}`);

    // Send close
    if (closeTx) {
      const closeMsg = new TransactionMessage({
        payerKey: wallet.publicKey,
        recentBlockhash: (await connection.getLatestBlockhash()).blockhash,
        instructions: closeTx.instructions || closeTx,
      }).compileToV0Message();

      const closeVtx = new VersionedTransaction(closeMsg);
      closeVtx.sign([wallet]);
      const closeSig = await connection.sendTransaction(closeVtx);
      console.log(`  Close position TX: https://solscan.io/tx/${closeSig}`);
    }

    // Update state
    const state = loadState();
    state.positions = state.positions.filter((p) => p.positionPubkey !== positionPubkey);
    saveState(state);

    console.log("  ✅ Position closed");
    return { success: true };
  } catch (e) {
    console.error(`  ❌ Close failed: ${e.message}`);
    return { success: false, error: e.message };
  }
}

async function claimFees(connection, wallet, poolAddress, positionPubkey) {
  console.log(`\n💰 Claiming fees from ${positionPubkey}`);
  try {
    const dlmm = await DLMM.create(connection, new PublicKey(poolAddress));
    const claimTx = await dlmm.claimFees({
      position: new PublicKey(positionPubkey),
      user: wallet.publicKey,
    });

    const latestBlockhash = await connection.getLatestBlockhash();
    const msg = new TransactionMessage({
      payerKey: wallet.publicKey,
      recentBlockhash: latestBlockhash.blockhash,
      instructions: claimTx.instructions || claimTx,
    }).compileToV0Message();

    const vtx = new VersionedTransaction(msg);
    vtx.sign([wallet]);
    const sig = await connection.sendTransaction(vtx);
    console.log(`  ✅ Claim TX: https://solscan.io/tx/${sig}`);
    return { success: true, txId: sig };
  } catch (e) {
    console.error(`  ❌ Claim failed: ${e.message}`);
    return { success: false, error: e.message };
  }
}

async function showStatus(connection, wallet) {
  const state = loadState();
  console.log("\n📊 LP Bot Status");
  console.log("=".repeat(50));

  if (state.positions.length === 0) {
    console.log("  No open positions");
    return;
  }

  const solPrice = await fetchSolPrice();

  for (const pos of state.positions) {
    try {
      const dlmm = await DLMM.create(connection, new PublicKey(pos.pool));
      const activeBin = await dlmm.getActiveBin();
      const userPositions = await dlmm.getPositionsByUserAndLbPair(wallet.publicKey);

      // Find our position
      const ourPos = userPositions.userPositions?.find(
        (p) => p.publicKey.toString() === pos.positionPubkey
      );

      const isActive = ourPos
        ? activeBin.binId >= ourPos.lowerBinId && activeBin.binId <= ourPos.upperBinId
        : false;

      const holdHours = (Date.now() - pos.openTime) / (1000 * 60 * 60);
      const priceChange = ((activeBin.price - pos.openPrice) / pos.openPrice) * 100;

      console.log(`\n  Pool: ${pos.name || pos.pool}`);
      console.log(`  Position: ${pos.positionPubkey.slice(0, 12)}...`);
      console.log(`  Value: ~$${pos.amountUsd} | SOL: ${(pos.amountLamports / LAMPORTS_PER_SOL).toFixed(4)}`);
      console.log(`  Active Bin: ${activeBin.binId} | In Range: ${isActive ? "✅" : "❌"}`);
      console.log(`  Price Change: ${priceChange >= 0 ? "+" : ""}${priceChange.toFixed(2)}%`);
      console.log(`  Hold: ${holdHours.toFixed(1)}h`);
      if (ourPos) {
        console.log(`  Range: bin ${ourPos.lowerBinId} → ${ourPos.upperBinId}`);
      }
    } catch (e) {
      console.log(`\n  Pool: ${pos.name || pos.pool} — Error: ${e.message}`);
    }
  }
}

// ─── HELPERS ───
async function fetchSolPrice() {
  try {
    const res = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd");
    const data = await res.json();
    return data.solana?.usd || 150;
  } catch {
    return 150; // fallback
  }
}

// ─── MAIN ───
async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || "help";

  const wallet = loadWallet();
  const connection = new Connection(HELIUS_RPC, { commitment: "confirmed" });

  console.log(`Wallet: ${wallet.publicKey}`);
  const balance = await connection.getBalance(wallet.publicKey);
  console.log(`Balance: ${(balance / LAMPORTS_PER_SOL).toFixed(4)} SOL\n`);

  switch (command) {
    case "screen": {
      const pools = await screenPools();
      console.log("\n🏆 Top Pools:");
      for (const p of pools.slice(0, 5)) {
        console.log(`\n  ${p.name} — Score: ${p.score.toFixed(1)}`);
        console.log(`    TVL: $${(p.active_tvl || 0).toLocaleString()} | Vol: $${(p.volume || 0).toLocaleString()}`);
        console.log(`    Fee/TVL: ${(p.fee_tvl_ratio || 0).toFixed(1)}% | Holders: ${p.token_x?.holders}`);
        console.log(`    MCap: $${(p.token_x?.market_cap || 0).toLocaleString()} | Price: $${p.token_x?.price}`);
      }
      break;
    }

    case "deploy": {
      const poolAddr = args[1];
      if (!poolAddr) {
        console.error("Usage: node lp_bot.js deploy <pool_address>");
        process.exit(1);
      }

      // Check existing positions
      const state = loadState();
      if (state.positions.length >= STRATEGY.maxPositions) {
        console.error(`Max positions (${STRATEGY.maxPositions}) reached. Close one first.`);
        process.exit(1);
      }

      // Fetch pool info for context
      const pools = await fetchPoolsFromMeteora();
      const poolInfo = pools.find((p) => p.pool_address === poolAddr) || { name: "Unknown" };

      await deployPosition(connection, wallet, poolAddr, poolInfo);
      break;
    }

    case "close": {
      const poolAddr = args[1];
      const posKey = args[2];
      if (!poolAddr) {
        console.error("Usage: node lp_bot.js close <pool_address> [position_pubkey]");
        process.exit(1);
      }

      if (posKey) {
        await closePosition(connection, wallet, poolAddr, posKey);
      } else {
        // Find position from state
        const state = loadState();
        const pos = state.positions.find((p) => p.pool === poolAddr);
        if (!pos) {
          console.error("No open position found for this pool");
          process.exit(1);
        }
        await closePosition(connection, wallet, poolAddr, pos.positionPubkey);
      }
      break;
    }

    case "claim": {
      const poolAddr = args[1];
      const posKey = args[2];
      if (!poolAddr) {
        console.error("Usage: node lp_bot.js claim <pool_address> [position_pubkey]");
        process.exit(1);
      }
      const state = loadState();
      const pos = posKey
        ? { positionPubkey: posKey }
        : state.positions.find((p) => p.pool === poolAddr);
      if (!pos) {
        console.error("No open position found");
        process.exit(1);
      }
      await claimFees(connection, wallet, poolAddr, pos.positionPubkey);
      break;
    }

    case "status": {
      await showStatus(connection, wallet);
      break;
    }

    case "auto": {
      console.log("🤖 Auto mode: screening + deploying best pool");
      const state = loadState();
      if (state.positions.length >= STRATEGY.maxPositions) {
        console.log(`Already at max positions (${STRATEGY.maxPositions}), running management loop...`);

        // ── Management loop: check each open position ──
        for (const pos of state.positions) {
          try {
            const dlmm = await DLMM.create(connection, new PublicKey(pos.pool));
            const activeBin = await dlmm.getActiveBin();
            const userPositions = await dlmm.getPositionsByUserAndLbPair(wallet.publicKey);
            const ourPos = userPositions.userPositions?.find(
              (p) => p.publicKey.toString() === pos.positionPubkey
            );

            if (!ourPos) {
              console.log(`  ⚠️ Position ${pos.positionPubkey.slice(0, 12)}… not found on-chain, skipping`);
              continue;
            }

            const isActive = activeBin.binId >= ourPos.lowerBinId && activeBin.binId <= ourPos.upperBinId;
            const outOfRangeMinutes = isActive ? 0 : (Date.now() - pos.openTime) / (1000 * 60);
            const holdHours = (Date.now() - pos.openTime) / (1000 * 60 * 60);

            console.log(`\n  Pool: ${pos.name || pos.pool}`);
            console.log(`    Active bin: ${activeBin.binId} | In range: ${isActive ? "✅" : "❌"}`);
            console.log(`    Hold: ${holdHours.toFixed(1)}h | OOR: ${outOfRangeMinutes.toFixed(0)}min`);

            // Close if out-of-range too long
            if (!isActive && outOfRangeMinutes > STRATEGY.oorCloseMinutes) {
              console.log(`    → Out of range > ${STRATEGY.oorCloseMinutes}min, closing position...`);
              await closePosition(connection, wallet, pos.pool, pos.positionPubkey);
              continue;
            }

            // Check stop-loss
            const solPrice = await fetchSolPrice();
            const currentValueUsd = pos.amountUsd; // approximate
            // TODO: calculate real PnL from on-chain data
            const priceChangePct = ((activeBin.price - pos.openPrice) / pos.openPrice) * 100;
            if (priceChangePct <= STRATEGY.stopLossPct) {
              console.log(`    → Price dropped ${priceChangePct.toFixed(1)}% (stop-loss: ${STRATEGY.stopLossPct}%), closing...`);
              await closePosition(connection, wallet, pos.pool, pos.positionPubkey);
              continue;
            }

            // Claim fees if above threshold
            if (isActive) {
              console.log(`    → Position in range, checking fees...`);
              // TODO: check accumulated fees and claim if > STRATEGY.minClaimFeeUsd
              console.log(`    → Fee claim check (TODO: integrate fee data)`);
            }
          } catch (e) {
            console.log(`  ❌ Error managing ${pos.pool}: ${e.message}`);
          }
        }
      } else {
        const pools = await screenPools();
        if (pools.length === 0) {
          console.log("No suitable pools found");
          break;
        }
        const best = pools[0];
        console.log(`\nBest pool: ${best.name} (score: ${best.score.toFixed(1)})`);
        await deployPosition(connection, wallet, best.pool_address, best);
      }
      break;
    }

    default:
      console.log(`
Meteora DLMM LP Bot
Commands:
  screen              Find best pools (auto-ranked)
  deploy <pool>       Open LP position
  status              Show open positions
  close <pool>        Close position + withdraw
  claim <pool>        Claim LP fees
  auto                Full auto: screen → deploy
      `);
  }
}

main().catch(console.error);
