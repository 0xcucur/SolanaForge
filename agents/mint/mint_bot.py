#!/usr/bin/env python3
"""
EVM Multi-Chain FCFS Mint Bot
Supports: ETH, Base, MegaETH, Tempo, and any EVM-compatible chain
Mode: Full auto — monitor → detect → mint → notify

Usage:
    python3 mint_bot.py --config config.json
    python3 mint_bot.py --chain base --contract 0x... --mint-fn mint --value 0.01
    python3 mint_bot.py --dry-run --chain eth --contract 0x... --mint-fn mint --value 0.05
"""

import json
import time
import argparse
import sys
import os
import datetime
import signal
from pathlib import Path

from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account import Account

# ═══════════════════════════════════════════════════════════════
# CHAIN CONFIGS
# ═══════════════════════════════════════════════════════════════
CHAINS = {
    "eth": {
        "name": "Ethereum",
        "rpc": "https://ethereum-rpc.publicnode.com",
        "chain_id": 1,
        "explorer": "https://etherscan.io/tx/",
        "priority_fee_gwei": 3,
        "max_fee_multiplier": 1.5,
    },
    "base": {
        "name": "Base",
        "rpc": "https://base-rpc.publicnode.com",
        "chain_id": 8453,
        "explorer": "https://basescan.org/tx/",
        "priority_fee_gwei": 1,
        "max_fee_multiplier": 1.3,
    },
    "mega": {
        "name": "MegaETH",
        "rpc": "https://rpc.megaeth.com",
        "chain_id": 6342,
        "explorer": "https://megaeth.com/tx/",
        "priority_fee_gwei": 1,
        "max_fee_multiplier": 1.5,
    },
    "tempo": {
        "name": "Tempo",
        "rpc": "https://rpc.tempo.build",
        "chain_id": 9837,
        "explorer": "https://tempo.exchange/tx/",
        "priority_fee_gwei": 1,
        "max_fee_multiplier": 1.5,
    },
    "sepolia": {
        "name": "Sepolia Testnet",
        "rpc": "https://ethereum-sepolia-rpc.publicnode.com",
        "chain_id": 11155111,
        "explorer": "https://sepolia.etherscan.io/tx/",
        "priority_fee_gwei": 1,
        "max_fee_multiplier": 1.2,
    },
}

# ═══════════════════════════════════════════════════════════════
# COMMON MINT FUNCTION SIGNATURES
# ═══════════════════════════════════════════════════════════════
MINT_SIGNATURES = {
    "mint":             "0xa0712d68",  # mint(uint264) — most common
    "mint(uint256)":    "0x1249c58b",  # mint(uint256)
    "safeMint":         "0xd204c45e",  # safeMint(address)
    "publicMint":       "0x2b68b116",  # publicMint(uint256)
    "mintPublic":       "0x5b7e3f2a",  # mintPublic(uint256)
    "claim":            "0x8b9e4f93",  # claim(address,uint256,uint256,bytes32[])
    "freeMint":         "0x9d5e5b4d",  # freeMint(uint256)
}

# ERC-721 standard ABI fragments
ERC721_ABI = [
    # mint functions (common variants)
    {
        "inputs": [{"name": "quantity", "type": "uint256"}],
        "name": "mint",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "quantity", "type": "uint256"}],
        "name": "publicMint",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "quantity", "type": "uint256"}],
        "name": "mintPublic",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "quantity", "type": "uint256"},
            {"name": "maxQuantity", "type": "uint256"},
            {"name": "proof", "type": "bytes32[]"}
        ],
        "name": "claim",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "quantity", "type": "uint256"}],
        "name": "freeMint",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "safeMint",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    # view functions
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "maxSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "price",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isActive",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "saleActive",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
]


class MintBot:
    def __init__(self, config: dict, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.chain = CHAINS[config["chain"]]
        self.w3 = Web3(Web3.HTTPProvider(
            self.chain["rpc"],
            request_kwargs={"timeout": 10}
        ))
        
        if not self.w3.is_connected():
            print(f"[FATAL] Cannot connect to {self.chain['name']} RPC: {self.chain['rpc']}")
            sys.exit(1)
        
        # Load wallet
        self.account = Account.from_key(config["private_key"])
        self.address = self.account.address
        
        # Contract
        self.contract_addr = Web3.to_checksum_address(config["contract"])
        self.contract = self.w3.eth.contract(
            address=self.contract_addr,
            abi=ERC721_ABI
        )
        
        # Mint config
        self.mint_fn = config.get("mint_fn", "mint")
        self.quantity = config.get("quantity", 1)
        self.value_eth = config.get("value", 0)
        self.value_wei = Web3.to_wei(self.value_eth, "ether")
        self.max_gas_price = Web3.to_wei(config.get("max_gas_price_gwei", 100), "gwei")
        self.gas_limit_override = config.get("gas_limit", None)
        
        # Timing
        self.poll_interval = config.get("poll_interval_sec", 0.5)
        self.max_retries = config.get("max_retries", 10)
        self.retry_delay = config.get("retry_delay_sec", 0.3)
        
        # State
        self.minted = False
        self.tx_hash = None
        self.running = True

    def log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        chain_tag = self.chain["name"]
        print(f"[{ts}] [{chain_tag}] {msg}")

    def check_balance(self) -> int:
        balance = self.w3.eth.get_balance(self.address)
        self.log(f"Balance: {Web3.from_wei(balance, 'ether')} ETH")
        return balance

    def probe_contract(self):
        """Try to read contract state before minting"""
        self.log(f"Contract: {self.contract_addr}")
        
        # Check if contract exists
        try:
            code = self.w3.eth.get_code(self.contract_addr)
            if len(code) == 0:
                self.log(f"  ⚠️  No contract deployed at this address")
                return
        except Exception:
            self.log(f"  ⚠️  Cannot check contract code")
            return
        
        # Try common view functions with explicit timeout
        for fn_name in ["totalSupply", "maxSupply", "price", "paused", "isActive", "saleActive"]:
            try:
                result = getattr(self.contract.functions, fn_name)().call()
                self.log(f"  {fn_name}() = {result}")
            except ContractLogicError:
                pass
            except Exception:
                pass
        
        # Check if mint function exists
        try:
            fn_obj = getattr(self.contract.functions, self.mint_fn)
            self.log(f"  ✓ Function '{self.mint_fn}' found")
        except AttributeError:
            self.log(f"  ✗ Function '{self.mint_fn}' NOT found — will try raw calldata")

    def build_mint_tx(self) -> dict:
        """Build the mint transaction"""
        nonce = self.w3.eth.get_transaction_count(self.address, 'pending')
        
        # Get gas parameters
        try:
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerFee', self.w3.eth.gas_price)
        except Exception:
            base_fee = self.w3.eth.gas_price
        
        priority_fee = Web3.to_wei(self.chain["priority_fee_gwei"], "gwei")
        max_fee = int(base_fee * self.chain["max_fee_multiplier"]) + priority_fee
        
        # Cap at max_gas_price
        max_fee = min(max_fee, self.max_gas_price)
        
        tx = {
            "from": self.address,
            "chainId": self.chain["chain_id"],
            "nonce": nonce,
            "maxPriorityFeePerGas": priority_fee,
            "maxFeePerGas": max_fee,
            "type": 2,  # EIP-1559
        }
        
        # Build function call
        try:
            fn_obj = getattr(self.contract.functions, self.mint_fn)
            if self.quantity > 0:
                fn_call = fn_obj(self.quantity)
            else:
                fn_call = fn_obj()
            tx_data = fn_call.build_transaction(tx)
            tx.update(tx_data)
        except AttributeError:
            # Fallback: raw calldata
            self.log(f"Using raw calldata for {self.mint_fn}")
            sig = MINT_SIGNATURES.get(self.mint_fn, self.mint_fn)
            if self.quantity > 0:
                qty_hex = hex(self.quantity)[2:].zfill(64)
                tx["data"] = sig + qty_hex
            else:
                tx["data"] = sig
            tx["to"] = self.contract_addr
        
        # Value
        if self.value_wei > 0:
            tx["value"] = self.value_wei
        
        # Gas estimation
        if self.gas_limit_override:
            tx["gas"] = self.gas_limit_override
        else:
            try:
                gas_estimate = self.w3.eth.estimate_gas(tx)
                tx["gas"] = int(gas_estimate * 1.3)  # 30% buffer
                self.log(f"Gas estimated: {gas_estimate} → using {tx['gas']}")
            except Exception as e:
                tx["gas"] = 300000  # fallback
                self.log(f"Gas estimation failed ({e}), using 300000")
        
        return tx

    def send_mint(self) -> str:
        """Sign and send the mint transaction"""
        tx = self.build_mint_tx()
        
        self.log(f"Signing tx...")
        signed = self.w3.eth.account.sign_transaction(tx, self.config["private_key"])
        
        self.log(f"Sending tx (nonce={tx['nonce']})...")
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    def wait_for_receipt(self, tx_hash: str, timeout: int = 120) -> dict:
        """Wait for transaction receipt"""
        self.log(f"Waiting for confirmation...")
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return receipt
        except Exception as e:
            self.log(f"Timeout waiting for receipt: {e}")
            return None

    def check_mint_status(self) -> bool:
        """Check if mint is available (not paused, active, etc.)"""
        try:
            code = self.w3.eth.get_code(self.contract_addr)
            if len(code) == 0:
                self.log(f"⚠️  No contract at {self.contract_addr}")
                return False
        except Exception:
            return False

        try:
            paused = self.contract.functions.paused().call()
            if paused:
                self.log(f"⏸️  Contract is PAUSED")
                return False
        except Exception:
            pass
        
        try:
            active = self.contract.functions.isActive().call()
            if active:
                return True
        except Exception:
            pass
        
        try:
            active = self.contract.functions.saleActive().call()
            if active:
                return True
        except Exception:
            pass
        
        # If we can't determine, assume it's active
        return True

    def monitor_and_mint(self):
        """Main loop: monitor for mint availability, then execute"""
        self.log("=" * 50)
        self.log(f"🚀 EVM MINT BOT STARTED")
        self.log(f"   Chain    : {self.chain['name']}")
        self.log(f"   Contract : {self.contract_addr}")
        self.log(f"   Function : {self.mint_fn}(qty={self.quantity})")
        self.log(f"   Value    : {self.value_eth} ETH")
        self.log(f"   Wallet   : {self.address}")
        self.log(f"   Mode     : {'DRY-RUN' if self.dry_run else 'LIVE'}")
        self.log("=" * 50)
        
        # Pre-flight checks
        balance = self.check_balance()
        if not self.dry_run and balance < self.value_wei:
            self.log(f"⚠️  WARNING: Balance ({Web3.from_wei(balance, 'ether')} ETH) < mint value ({self.value_eth} ETH)")
        
        self.probe_contract()
        
        # Dry-run: build TX and exit
        if self.dry_run:
            self.log(f"🏗️  [DRY-RUN] Building TX...")
            try:
                tx = self.build_mint_tx()
                self.log(f"[DRY-RUN] TX built successfully:")
                self.log(f"  To: {tx.get('to', self.contract_addr)}")
                self.log(f"  Value: {Web3.from_wei(tx.get('value', 0), 'ether')} ETH")
                self.log(f"  Gas: {tx.get('gas', 'N/A')}")
                self.log(f"  MaxFee: {Web3.from_wei(tx.get('maxFeePerGas', 0), 'gwei')} gwei")
                self.log(f"  Data: {tx.get('data', 'N/A')[:66]}...")
            except Exception as e:
                self.log(f"[DRY-RUN] TX build failed (expected if contract doesn't exist): {e}")
            return

        # Monitor loop
        attempt = 0
        self.log(f"🔍 Monitoring for mint availability (poll every {self.poll_interval}s)...")

        while self.running and not self.minted:
            try:
                # Check if mint is available
                if not self.check_mint_status():
                    time.sleep(self.poll_interval)
                    continue
                
                self.log(f"🟢 Mint appears ACTIVE! Attempting...")
                
                # LIVE MINT
                attempt += 1
                try:
                    tx_hash = self.send_mint()
                    self.log(f"📤 TX sent: {tx_hash}")
                    self.log(f"   Explorer: {self.chain['explorer']}{tx_hash}")
                    
                    receipt = self.wait_for_receipt(tx_hash)
                    
                    if receipt and receipt.get("status") == 1:
                        self.log(f"✅ MINT SUCCESSFUL!")
                        self.log(f"   Block: {receipt['blockNumber']}")
                        self.log(f"   Gas used: {receipt['gasUsed']}")
                        self.tx_hash = tx_hash
                        self.minted = True
                        break
                    elif receipt:
                        self.log(f"❌ TX reverted (status=0)")
                        if attempt < self.max_retries:
                            self.log(f"   Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay)
                    else:
                        self.log(f"⚠️  No receipt, TX may still be pending: {tx_hash}")
                        self.tx_hash = tx_hash
                        # Don't break — might need to retry with higher gas
                        
                except Exception as e:
                    self.log(f"❌ Send failed: {e}")
                    if attempt < self.max_retries:
                        self.log(f"   Retrying ({attempt}/{self.max_retries})...")
                        time.sleep(self.retry_delay)
                    else:
                        self.log(f"   Max retries reached!")
                        break
                        
            except Exception as e:
                self.log(f"⚠️  Monitor error: {e}")
                time.sleep(self.poll_interval)
        
        if self.minted:
            self.log(f"\n{'='*50}")
            self.log(f"🎉 DONE!")
            self.log(f"   TX: {self.tx_hash}")
            if self.tx_hash:
                self.log(f"   Link: {self.chain['explorer']}{self.tx_hash}")
            self.log(f"{'='*50}")
        else:
            self.log(f"\n❌ Mint not completed after {attempt} attempts")

    def stop(self):
        self.running = False


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return json.load(f)


def load_wallet_private_key() -> str:
    """Load private key from wallets.json"""
    wallet_path = Path.home() / ".hermes" / "wallets" / "wallets.json"
    if not wallet_path.exists():
        raise FileNotFoundError(f"Wallet file not found: {wallet_path}")
    with open(wallet_path) as f:
        wallets = json.load(f)
    return wallets["evm"]["private_key"]


def main():
    parser = argparse.ArgumentParser(description="EVM Multi-Chain FCFS Mint Bot")
    parser.add_argument("--config", "-c", help="Path to config JSON")
    parser.add_argument("--chain", choices=list(CHAINS.keys()), help="Chain to mint on")
    parser.add_argument("--contract", help="NFT contract address")
    parser.add_argument("--mint-fn", default="mint", help="Mint function name (default: mint)")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity to mint")
    parser.add_argument("--value", type=float, default=0, help="ETH value to send")
    parser.add_argument("--gas-limit", type=int, help="Gas limit override")
    parser.add_argument("--max-gas-gwei", type=float, default=100, help="Max gas price in gwei")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Poll interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Build TX but don't send")
    parser.add_argument("--probe-only", action="store_true", help="Only probe contract, don't mint")
    
    args = parser.parse_args()
    
    # Build config
    if args.config:
        config = load_config(args.config)
    elif args.chain and args.contract:
        config = {
            "chain": args.chain,
            "contract": args.contract,
            "mint_fn": args.mint_fn,
            "quantity": args.quantity,
            "value": args.value,
            "gas_limit": args.gas_limit,
            "max_gas_price_gwei": args.max_gas_gwei,
            "poll_interval_sec": args.poll_interval,
            "private_key": load_wallet_private_key(),
        }
    else:
        parser.error("Either --config or (--chain + --contract) required")
        return
    
    # Ensure private key
    if "private_key" not in config:
        config["private_key"] = load_wallet_private_key()
    
    # Initialize bot
    bot = MintBot(config, dry_run=args.dry_run)
    
    # Handle Ctrl+C gracefully
    def sigint_handler(sig, frame):
        bot.log("\n⏹️  Stopping...")
        bot.stop()
    signal.signal(signal.SIGINT, sigint_handler)
    
    if args.probe_only:
        bot.check_balance()
        bot.probe_contract()
    else:
        bot.monitor_and_mint()


if __name__ == "__main__":
    main()
