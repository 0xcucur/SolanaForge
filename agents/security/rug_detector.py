#!/usr/bin/env python3
"""
Rug Detector — SolanaForge Security Agent
Scans Solana tokens for rug pull indicators.

Usage:
    python rug_detector.py <TOKEN_ADDRESS>
    python rug_detector.py --batch tokens.txt
"""

import json
import sys
import requests
from dataclasses import dataclass, field
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────
HELIUS_API_KEY = ""  # Set via env or config
BIRDEYE_API_KEY = ""

RED_FLAGS = {
    "mint_authority_active":    {"weight": 25, "desc": "Mint authority not renounced — dev can mint unlimited tokens"},
    "freeze_authority_active":  {"weight": 15, "desc": "Freeze authority active — dev can freeze your tokens"},
    "top_holder_concentration": {"weight": 20, "desc": "Top holder owns >50% of supply"},
    "lp_not_locked":            {"weight": 20, "desc": "LP tokens not locked — dev can pull liquidity"},
    "low_liquidity":            {"weight": 10, "desc": "Total liquidity < $5,000 — easy to manipulate"},
    "new_token_no_history":     {"weight": 5,  "desc": "Token created < 24h ago with no trading history"},
    "deployer_has_rugged":      {"weight": 30, "desc": "Deployer wallet linked to previous rug pulls"},
    "suspicious_transfer_tax":  {"weight": 15, "desc": "Transfer tax > 5% detected"},
    "honeypot_pattern":         {"weight": 30, "desc": "Sell function restricted or disabled"},
    "copy_paste_metadata":      {"weight": 10, "desc": "Token metadata matches known rug templates"},
}

@dataclass
class ScanResult:
    token: str
    score: int = 0          # 0-100, higher = more suspicious
    flags: list = field(default_factory=list)
    safe: bool = True
    details: dict = field(default_factory=dict)

def check_mint_authority(mint_info: dict, result: ScanResult):
    """Check if mint authority is renounced."""
    if mint_info.get("mintAuthority"):
        result.score += RED_FLAGS["mint_authority_active"]["weight"]
        result.flags.append(RED_FLAGS["mint_authority_active"]["desc"])
    if mint_info.get("freezeAuthority"):
        result.score += RED_FLAGS["freeze_authority_active"]["weight"]
        result.flags.append(RED_FLAGS["freeze_authority_active"]["desc"])

def check_holder_concentration(holders: list, result: ScanResult):
    """Check if top holders own too much supply."""
    if not holders:
        return
    total_pct = sum(h.get("pct", 0) for h in holders[:5])
    if total_pct > 70:
        result.score += RED_FLAGS["top_holder_concentration"]["weight"]
        result.flags.append(f"Top 5 holders own {total_pct:.1f}% of supply")
    elif holders[0].get("pct", 0) > 50:
        result.score += RED_FLAGS["top_holder_concentration"]["weight"]
        result.flags.append(RED_FLAGS["top_holder_concentration"]["desc"])

def check_liquidity(pool_data: dict, result: ScanResult):
    """Check liquidity depth."""
    tvl = pool_data.get("tvl", 0)
    if tvl < 5000:
        result.score += RED_FLAGS["low_liquidity"]["weight"]
        result.flags.append(f"Total liquidity: ${tvl:,.0f} (risky)")
    result.details["tvl"] = tvl

def check_lp_lock(lp_info: dict, result: ScanResult):
    """Check if LP tokens are locked."""
    if not lp_info.get("locked", False):
        result.score += RED_FLAGS["lp_not_locked"]["weight"]
        result.flags.append(RED_FLAGS["lp_not_locked"]["desc"])

def analyze(token_address: str) -> ScanResult:
    """Run full rug detection analysis."""
    result = ScanResult(token=token_address)

    print(f"\n🔍 Scanning token: {token_address}")
    print("=" * 60)

    # ── Fetch on-chain data ───────────────────────────────────────────────
    # TODO: Replace placeholders with real API calls
    # Helius RPC: getAsset for mint/freeze authority, supply
    # RugCheck API: topHolders, lpLockedPct, risk flags
    # Jupiter Ultra API: liquidity check

    mint_info = {
        "mintAuthority": None,  # Set from Helius getAsset -> token_info.mint_authority
        "freezeAuthority": None,  # Set from Helius getAsset -> token_info.freeze_authority
    }

    holders = []  # Set from RugCheck topHolders -> [{pct: float, address: str}]

    pool_data = {"tvl": 0}  # Set from Jupiter Ultra API

    lp_info = {"locked": False}  # Set from RugCheck lpLockedPct

    # ── Run all checks ────────────────────────────────────────────────────
    check_mint_authority(mint_info, result)
    check_holder_concentration(holders, result)
    check_liquidity(pool_data, result)
    check_lp_lock(lp_info, result)

    # Determine verdict
    if result.score >= 50:
        result.safe = False
        verdict = "🚨 HIGH RISK — Likely rug pull"
    elif result.score >= 25:
        verdict = "⚠️ MEDIUM RISK — Proceed with caution"
    else:
        verdict = "✅ LOW RISK — No major red flags"

    print(f"\n{verdict}")
    print(f"Risk Score: {result.score}/100")

    if result.flags:
        print("\n🚩 Red Flags:")
        for i, flag in enumerate(result.flags, 1):
            print(f"  {i}. {flag}")

    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python rug_detector.py <TOKEN_ADDRESS>")
        print("       python rug_detector.py --batch tokens.txt")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        with open(sys.argv[2]) as f:
            tokens = [line.strip() for line in f if line.strip()]
        for token in tokens:
            analyze(token)
    else:
        analyze(sys.argv[1])

if __name__ == "__main__":
    main()
