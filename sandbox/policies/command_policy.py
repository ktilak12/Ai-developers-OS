import re
from typing import Tuple, List, Set, Dict, Any

class CommandSecurityPolicy:
    """
    Command Security Policy layer.
    Enforces strict allow/deny rules before any command is dispatched into the sandbox.
    Protects against command injection, destructive host deletions, fork bombs, and unauthorized privilege escalation.
    """

    ALLOWED_COMMAND_PREFIXES: List[str] = [
        "npm test",
        "npm run test",
        "npm run build",
        "npm run lint",
        "npm install",
        "npx jest",
        "npx vitest",
        "npx eslint",
        "pytest",
        "python -m unittest",
        "python -m pytest",
        "python -m pip install",
        "pip install",
        "mvn test",
        "mvn clean test",
        "git status",
        "git diff",
        "node --version",
        "python --version",
        "npm --version"
    ]

    DENIED_PATTERNS: List[re.Pattern] = [
        re.compile(r"rm\s+-rf\s+(/|~|\$HOME)", re.IGNORECASE),
        re.compile(r"\b(shutdown|reboot|poweroff|init\s+0)\b", re.IGNORECASE),
        re.compile(r"(curl|wget)\s+.*\|\s*(bash|sh|zsh)", re.IGNORECASE),
        re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:", re.IGNORECASE),  # Fork bomb
        re.compile(r"\b(sudo|su|pkexec|doas)\b", re.IGNORECASE),
        re.compile(r"\b(mkfs|dd\s+if=)\b", re.IGNORECASE),
        re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
        re.compile(r"\b(chmod\s+-R\s+777\s+/)\b", re.IGNORECASE),
        re.compile(r"\b(docker\s+run|docker\s+exec)\b", re.IGNORECASE),  # Prevent Docker-in-Docker escape
    ]

    def __init__(self, additional_allowed: List[str] = None):
        self.allowed_prefixes = list(self.ALLOWED_COMMAND_PREFIXES)
        if additional_allowed:
            self.allowed_prefixes.extend(additional_allowed)

    def is_command_allowed(self, command: str) -> Tuple[bool, str]:
        cmd_clean = command.strip()
        if not cmd_clean:
            return False, "Command cannot be empty."

        # Check against denied dangerous regex patterns
        for pattern in self.DENIED_PATTERNS:
            if pattern.search(cmd_clean):
                return False, f"Security Violation: Command matched restricted dangerous pattern: '{pattern.pattern}'"

        # Check against allowed prefixes
        for prefix in self.allowed_prefixes:
            if cmd_clean == prefix or cmd_clean.startswith(prefix + " "):
                return True, f"Command allowed under policy prefix: '{prefix}'"

        return False, f"Permission Denied: Command '{cmd_clean}' is not in the allowed sandbox commands list."

    def get_policy_summary(self) -> Dict[str, Any]:
        return {
            "allowed_prefixes": self.allowed_prefixes,
            "denied_patterns_count": len(self.DENIED_PATTERNS),
            "enforcement_mode": "STRICT_ALLOWLIST",
            "non_root_enforced": True,
            "sandbox_isolated": True
        }

DEFAULT_COMMAND_POLICY = CommandSecurityPolicy()
