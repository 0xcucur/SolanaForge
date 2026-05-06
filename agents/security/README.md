# 🔒 Security Agent — SolanaForge

Automated security audit pipeline for Solana smart contracts, EVM contracts, and AI agent skills.

## Features

### 1. Rug Pull Detection (`rug_detector.py`)
Scans Solana tokens for 20+ red flag patterns:
- LP lock status verification
- Token concentration analysis (>50% top holder = red flag)
- Contract authority checks (mint authority, freeze authority)
- Transaction pattern analysis (wash trading detection)
- Deployer wallet history (previous rugs?)

### 2. Skill Audit Pipeline (`skill_auditor.py`)
Security scan for AI agent skills before installation:
- External URL analysis (data exfiltration detection)
- Credential handling verification
- Prompt injection pattern matching
- Supply-chain attack detection (auto-installing packages)
- OWASP Agentic AI Top 10 compliance

### 3. Smart Contract Scanner
Based on `solana-vulnerability-scanner` skill — scans for:
- Reentrancy vulnerabilities
- Integer overflow/underflow
- Access control issues
- Unchecked CPI (Cross-Program Invocation)
- Account data validation gaps

## Usage

```bash
# Audit a single token
python rug_detector.py --token <TOKEN_ADDRESS>

# Audit an agent skill
python skill_auditor.py --skill <SKILL_PATH>

# Full security sweep
python security_sweep.py --wallet <WALLET> --contracts <CONTRACTS_FILE>
```

## Integration with Hermes Agent

Security agent runs as a background watchdog:
```
1. New skill discovered → auto-audit before install
2. New token detected → rug check before interaction
3. Transaction signing → security validation first
4. Periodic wallet audit → balance & authority checks
```

## 102 Hacking Skills Installed

From yaklang/hack-skills repository:
- Smart contract vulnerability testing (Solidity, Rust)
- Blockchain-specific attack patterns
- API security (JWT, OAuth, BOLA)
- Injection testing (SQL, SSTI, XXE, etc.)
- Privilege escalation (Linux, Windows)
- Network protocol attacks
- Cryptographic attacks

Full list: `~/.hermes/skills/hack/` (102 SKILL.md)
