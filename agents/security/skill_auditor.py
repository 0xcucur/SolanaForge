#!/usr/bin/env python3
"""
Skill Auditor — SolanaForge Security Agent
Scans AI agent skills for security vulnerabilities before installation.

Based on OWASP Agentic AI Top 10 security patterns.
Catches: data exfiltration, credential theft, prompt injection, supply-chain attacks.

Usage:
    python skill_auditor.py <SKILL_PATH>
    python skill_auditor.py --scan-dir ~/.hermes/skills/
"""

import os
import re
import sys
import json
from dataclasses import dataclass, field
from pathlib import Path

# ── Attack Patterns ────────────────────────────────────────────────────────
PATTERNS = {
    "data_exfiltration": {
        "weight": 30,
        "desc": "Potential data exfiltration to external server",
        "regexes": [
            r'https?://[^\s]+\.(ngrok|requestbin|webhook|pipedream|burpcollaborator)\.',
            r'curl\s+.*-d\s+.*https?://',
            r'fetch\(["\']https?://[^\s]+["\'].*,\s*\{.*body',
            r'requests\.post\(.*https?://',
            r'wget\s+.*-O-.*https?://',
        ]
    },
    "credential_theft": {
        "weight": 35,
        "desc": "Potential credential/secret theft",
        "regexes": [
            r'(?:cat|read|get|fetch|load).*\.(?:env|pem|key|secret|token|credentials)',
            r'os\.environ\[.*(?:KEY|TOKEN|SECRET|PASSWORD|PRIVATE)',
            r'process\.env\.(?:KEY|TOKEN|SECRET|PASSWORD|PRIVATE)',
            r'(?:PRIVATE_KEY|MNEMONIC|SEED_PHRASE)',
            r'\.ssh/id_rsa',
        ]
    },
    "prompt_injection": {
        "weight": 25,
        "desc": "Potential prompt injection (modifies SOUL.md, MEMORY.md, or instructions)",
        "regexes": [
            r'(?:write|append|overwrite|modify).*(?:SOUL\.md|IDENTITY\.md|MEMORY\.md|CLAUDE\.md)',
            r'(?:system|assistant).*prompt.*(?:inject|override|replace)',
            r'ignore\s+(?:all\s+)?previous\s+instructions',
            r'you\s+are\s+now\s+(?:a|an|the)',
        ]
    },
    "supply_chain": {
        "weight": 20,
        "desc": "Supply-chain attack (auto-installs packages without user consent)",
        "regexes": [
            r'(?:pip|npm|yarn|pnpm|cargo)\s+install\s+(?!.*(?:#|\/\/))',
            r'subprocess\.run\(\[.*(?:pip|npm|yarn|pnpm)',
            r'exec\(["\'](?:pip|npm)',
            r'eval\(',
        ]
    },
    "filesystem_abuse": {
        "weight": 15,
        "desc": "Suspicious filesystem access outside skill directory",
        "regexes": [
            r'(?:rm|remove|rmtree)\s+.*(?:-rf|-fr)\s+/',
            r'os\.remove\(.*(?:/etc|/var|/root|~)',
            r'shutil\.rmtree\(',
            r'chmod\s+777',
        ]
    },
    "network_abuse": {
        "weight": 10,
        "desc": "Suspicious network activity",
        "regexes": [
            r'(?:bind|listen|accept)\(.*(?:0\.0\.0\.0|\*)',
            r'socket\.socket\(',
            r'subprocess\.call\(\[.*nc\s',
            r'(?:reverse|bind)\s+shell',
        ]
    },
    "obfuscation": {
        "weight": 15,
        "desc": "Obfuscated or encoded payloads",
        "regexes": [
            r'base64\.(?:b64decode|decodebytes)',
            r'\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){5,}',
            r'chr\(\d+\)(?:\s*\+\s*chr\(\d+\)){5,}',
            r'(?:exec|eval)\(.*(?:decode|decrypt|deobfuscate)',
        ]
    },
}

@dataclass
class AuditResult:
    skill_path: str
    skill_name: str
    score: int = 0          # 0-100, higher = more suspicious
    flags: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    safe: bool = True

def scan_file(filepath: str) -> list:
    """Scan a single file for attack patterns."""
    findings = []
    try:
        with open(filepath, 'r', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return findings

    for category, pattern_info in PATTERNS.items():
        for regex in pattern_info["regexes"]:
            for i, line in enumerate(lines, 1):
                if re.search(regex, line, re.IGNORECASE):
                    findings.append({
                        "category": category,
                        "weight": pattern_info["weight"],
                        "desc": pattern_info["desc"],
                        "file": filepath,
                        "line": i,
                        "content": line.strip()[:120],
                    })
    return findings

def scan_urls(skill_path: str) -> list:
    """Extract and analyze all URLs in skill files."""
    findings = []
    suspicious_tlds = ['.xyz', '.top', '.click', '.buzz', '.gq', '.ml', '.cf']
    url_pattern = re.compile(r'https?://[^\s\)\"\'>\]]+')

    for root, dirs, files in os.walk(skill_path):
        for fname in files:
            if not fname.endswith(('.md', '.py', '.js', '.ts', '.sh', '.yaml', '.yml', '.json')):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', errors='ignore') as f:
                    content = f.read()
            except:
                continue

            urls = url_pattern.findall(content)
            for url in urls:
                # Check for suspicious patterns
                if any(tld in url for tld in suspicious_tlds):
                    findings.append({
                        "category": "suspicious_url",
                        "weight": 10,
                        "desc": f"Suspicious TLD in URL: {url[:80]}",
                        "file": fpath,
                    })
                if 'pastebin' in url or 'hastebin' in url:
                    findings.append({
                        "category": "pastebin_url",
                        "weight": 15,
                        "desc": f"Pastebin URL (potential payload drop): {url[:80]}",
                        "file": fpath,
                    })
    return findings

def audit_skill(skill_path: str) -> AuditResult:
    """Audit a single skill directory."""
    skill_path = os.path.expanduser(skill_path)
    skill_name = os.path.basename(skill_path)
    result = AuditResult(skill_path=skill_path, skill_name=skill_name)

    if not os.path.isdir(skill_path):
        result.issues.append(f"Path is not a directory: {skill_path}")
        return result

    # Scan all files
    for root, dirs, files in os.walk(skill_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            findings = scan_file(fpath)
            result.flags.extend(findings)

    # Scan URLs
    url_findings = scan_urls(skill_path)
    result.flags.extend(url_findings)

    # Calculate score
    seen_categories = set()
    for flag in result.flags:
        cat = flag["category"]
        if cat not in seen_categories:
            result.score += flag["weight"]
            seen_categories.add(cat)

    result.score = min(result.score, 100)
    result.safe = result.score < 30

    return result

def print_report(result: AuditResult):
    """Print human-readable audit report."""
    print(f"\n{'='*60}")
    print(f"🔍 Skill Audit: {result.skill_name}")
    print(f"{'='*60}")

    if result.score >= 50:
        verdict = "🚨 DANGEROUS — Do NOT install"
    elif result.score >= 30:
        verdict = "⚠️ CAUTION — Review carefully before installing"
    else:
        verdict = "✅ SAFE — No major issues detected"

    print(f"\n{verdict}")
    print(f"Risk Score: {result.score}/100")
    print(f"Files scanned: {sum(1 for _ in os.walk(result.skill_path) for _ in _[2])}")

    if result.flags:
        print(f"\n🚩 Findings ({len(result.flags)}):")
        for i, flag in enumerate(result.flags, 1):
            print(f"\n  [{i}] {flag['category'].upper()} (weight: {flag['weight']})")
            print(f"      {flag['desc']}")
            if 'line' in flag:
                print(f"      File: {flag['file']}:{flag['line']}")
                print(f"      Code: {flag['content']}")
            else:
                print(f"      File: {flag['file']}")

    if result.issues:
        print(f"\n⚠️ Issues:")
        for issue in result.issues:
            print(f"  - {issue}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python skill_auditor.py <SKILL_PATH>")
        print("       python skill_auditor.py --scan-dir ~/.hermes/skills/")
        print("       python skill_auditor.py --json <SKILL_PATH>")
        sys.exit(1)

    json_mode = "--json" in sys.argv
    scan_dir_mode = "--scan-dir" in sys.argv

    if scan_dir_mode:
        idx = sys.argv.index("--scan-dir") + 1
        base_dir = os.path.expanduser(sys.argv[idx])
        skills = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

        print(f"Scanning {len(skills)} skills in {base_dir}...")
        results = []
        for skill in sorted(skills):
            result = audit_skill(os.path.join(base_dir, skill))
            results.append(result)
            status = "✅" if result.safe else "🚨"
            print(f"  {status} {skill}: {result.score}/100")

        dangerous = [r for r in results if not r.safe]
        if dangerous:
            print(f"\n🚨 {len(dangerous)} SKILLS FLAGGED:")
            for r in dangerous:
                print(f"  - {r.skill_name} ({r.score}/100)")
        else:
            print(f"\n✅ All {len(results)} skills passed audit")

    else:
        skill_path = sys.argv[-1]
        result = audit_skill(skill_path)

        if json_mode:
            output = {
                "skill": result.skill_name,
                "score": result.score,
                "safe": result.safe,
                "flags": result.flags,
                "issues": result.issues,
            }
            print(json.dumps(output, indent=2))
        else:
            print_report(result)

if __name__ == "__main__":
    main()
