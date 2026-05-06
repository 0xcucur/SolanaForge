# 🎨 Mint Agent — SolanaForge

Automated NFT minting across multiple EVM chains with gas optimization and dry-run safety.

## Features

- **Multi-chain**: ETH, Base, MegaETH, Tempo
- **Auto-gas**: Dynamic gas estimation with 1.2x safety multiplier
- **Dry-run**: Simulate transactions without spending gas
- **Probe mode**: Check contract readiness before mint
- **Batch mint**: Mint multiple tokens in sequence
- **Real-time alerts**: Notifications via assistant when mint conditions are met

## Supported Contracts

| Type | Description | Detection |
|------|-------------|-----------|
| ERC721 | Standard NFT | `safeMint`, `mint`, `publicMint` |
| ERC1155 | Multi-token | `mint`, `mintBatch` |
| Custom | Project-specific | ABI parsing + heuristic |

## Usage

```bash
# Dry run (safe)
python mint_bot.py --chain base --contract 0x... --dry-run

# Live mint
python mint_bot.py --chain base --contract 0x... --amount 1

# Probe contract
python mint_bot.py --chain eth --contract 0x... --probe

# Check gas prices
python mint_bot.py --chain eth --gas-report
```

## FCFS Strategy

1. **Pre-mint**: Probe contract, estimate gas, prepare tx
2. **Monitor**: Watch for mint open (block timestamp, event log)
3. **Execute**: Broadcast tx with priority fee bump
4. **Verify**: Confirm receipt, check token balance

## Multi-chain Support

```python
CHAINS = {
    "eth":     {"rpc": "https://eth.llamarpc.com", "chain_id": 1},
    "base":    {"rpc": "https://base.llamarpc.com", "chain_id": 8453},
    "mega":    {"rpc": "https://carrot.megaeth.com/rpc", "chain_id": 6342},
    "tempo":   {"rpc": "https://rpc.testnet.tempodex.xyz", "chain_id": 7777777},
}
```
