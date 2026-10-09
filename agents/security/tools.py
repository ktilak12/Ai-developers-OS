import os
import re
from typing import Dict, Any, List, Optional

class SecurityTools:
    """
    Security scanners and static analysis tools utilized by the Security Agent:
    1. Secret detection (AWS, GitHub, JWT, DB passwords, private keys)
    2. Command & code injection patterns
    3. Unsafe SQL queries
    4. Insecure configurations
    """

    SECRET_PATTERNS = [
        ("AWS Access Key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
        ("GitHub Personal Access Token", re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{40,})\b")),
        ("Generic API Secret Key", re.compile(r"""(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[:=]\s*["']([a-zA-Z0-9\-_]{20,})["']""")),
        ("Hardcoded Database Password", re.compile(r"""(?i)(password|passwd|pwd)\s*[:=]\s*["']([^"'\s]{6,})["']""")),
        ("Private RSA / PEM Key", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")),
        ("JWT Secret Token", re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"))
    ]

    DANGEROUS_CODE_PATTERNS = [
        ("Arbitrary Code Execution via eval()", re.compile(r"\beval\s*\("), "CRITICAL", "Avoid eval(); use safe JSON.parse or ast.literal_eval."),
        ("Command Injection via shell=True", re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"), "CRITICAL", "Pass argument lists without shell=True to prevent shell injection."),
        ("Unsanitized os.system() Execution", re.compile(r"\bos\.system\s*\("), "HIGH", "Use subprocess.run with argument vectors rather than os.system()."),
        ("Dangerous child_process.exec()", re.compile(r"child_process\.(exec|execSync)\s*\("), "HIGH", "Use child_process.execFile or execSpan with sanitized arguments.")
    ]

    SQL_INJECTION_PATTERNS = [
        ("SQL Injection via String Formatting", re.compile(r"""(?i)(execute|cursor\.execute)\s*\(\s*f["'][^"']*(SELECT|INSERT|UPDATE|DELETE)[^"']*\{"""), "CRITICAL", "Use parameterized SQL queries with bind variables instead of f-strings."),
        ("SQL Injection via String Concatenation", re.compile(r"""(?i)(execute|cursor\.execute)\s*\(\s*["'][^"']*(SELECT|INSERT|UPDATE|DELETE)[^"']*["']\s*\+"""), "CRITICAL", "Use parameterized SQL queries rather than string concatenation.")
    ]

    INSECURE_CONFIG_PATTERNS = [
        ("Wildcard CORS with Credentials", re.compile(r"""allow_origins\s*=\s*\[\s*["']\*["']\s*\]\s*,\s*allow_credentials\s*=\s*True"""), "MEDIUM", "Do not combine allow_origins=['*'] with allow_credentials=True."),
        ("Hardcoded Production Debug Mode", re.compile(r"""(?i)(DEBUG\s*=\s*True|app\.debug\s*=\s*True)"""), "LOW", "Ensure debug mode is controlled via environment variables.")
    ]

    MAX_READ_BYTES: int = 1_000_000
    MAX_CONTENT_CHARS: int = 500_000

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

    def _resolve_safe_path(self, rel_path: str) -> Optional[str]:
        """Resolves target path and enforces workspace jail to prevent path traversal."""
        if not rel_path or not isinstance(rel_path, str) or "\0" in rel_path:
            return None
        try:
            full_path = os.path.realpath(os.path.abspath(os.path.join(self.root_dir, rel_path)))
            if os.path.commonpath([self.root_dir, full_path]) != self.root_dir:
                return None
            return full_path
        except (ValueError, Exception):
            return None

    def scan_content(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scans a single file's text content across all security detectors."""
        if not content or not isinstance(content, str):
            return []
        if len(content) > self.MAX_CONTENT_CHARS:
            content = content[:self.MAX_CONTENT_CHARS]
        findings = []
        lines = content.splitlines()

        # 1. Hardcoded Secrets
        for line_num, line in enumerate(lines, 1):
            if any(marker in line.lower() for marker in ["test", "dummy", "placeholder", "example"]) and "password123" in line:
                continue  # skip known non-production fixtures

            for rule_name, pattern in self.SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "file": file_path,
                        "line": line_num,
                        "severity": "CRITICAL" if "Key" in rule_name or "Private" in rule_name else "HIGH",
                        "rule_id": "SEC-SECRET-001",
                        "rule_name": rule_name,
                        "description": f"Exposed secret detected: {rule_name}.",
                        "recommendation": "Move credential to environment variables (.env) or KMS secret manager."
                    })

        # 2. Dangerous Execution Patterns
        for line_num, line in enumerate(lines, 1):
            for rule_name, pattern, severity, rec in self.DANGEROUS_CODE_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "file": file_path,
                        "line": line_num,
                        "severity": severity,
                        "rule_id": "SEC-INJECT-002",
                        "rule_name": rule_name,
                        "description": f"Potentially unsafe execution: {rule_name}.",
                        "recommendation": rec
                    })

        # 3. Unsafe Database Queries
        for line_num, line in enumerate(lines, 1):
            for rule_name, pattern, severity, rec in self.SQL_INJECTION_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "file": file_path,
                        "line": line_num,
                        "severity": severity,
                        "rule_id": "SEC-SQLI-003",
                        "rule_name": rule_name,
                        "description": f"SQL injection vulnerability: {rule_name}.",
                        "recommendation": rec
                    })

        # 4. Insecure Configuration
        for line_num, line in enumerate(lines, 1):
            for rule_name, pattern, severity, rec in self.INSECURE_CONFIG_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "file": file_path,
                        "line": line_num,
                        "severity": severity,
                        "rule_id": "SEC-CONFIG-004",
                        "rule_name": rule_name,
                        "description": f"Insecure configuration pattern: {rule_name}.",
                        "recommendation": rec
                    })

        return findings

    def scan_file(self, rel_path: str) -> List[Dict[str, Any]]:
        safe_path = self._resolve_safe_path(rel_path)
        if not safe_path or not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            return []
        try:
            if os.path.getsize(safe_path) > self.MAX_READ_BYTES:
                return []
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(self.MAX_READ_BYTES)
            return self.scan_content(rel_path, content)
        except Exception:
            return []
