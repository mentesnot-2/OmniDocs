"""
Post-generation safety: redact patterns that look like secrets or PII from model output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Email-like addresses (conservative).
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+\b"
)
# OpenAI-style API keys
_OPENAI_SK_RE = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
# AWS access key id (classic AKIA prefix)
_AWS_AKIA_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
# GitHub classic PAT
_GITHUB_PAT_RE = re.compile(r"\bghp_[A-Za-z0-9]{36,}\b")
# Slack bot token
_SLACK_TOKEN_RE = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+\b")


@dataclass
class OutputPolicyResult:
    """Text after policy passes plus labels for any redaction kinds applied."""

    text: str
    redaction_kinds: list[str] = field(default_factory=list)


def apply_output_policy(text: str) -> OutputPolicyResult:
    """
    Redact sensitive-looking substrings from user-visible model output.
    Returns a new string; does not mutate the input.
    """
    if not text:
        return OutputPolicyResult(text="")

    out = text
    kinds: list[str] = []

    def _sub(pattern: re.Pattern[str], label: str, replacement: str) -> None:
        nonlocal out
        if pattern.search(out):
            kinds.append(label)
            out = pattern.sub(replacement, out)

    _sub(_OPENAI_SK_RE, "openai_key", "[REDACTED]")
    _sub(_AWS_AKIA_RE, "aws_access_key_id", "[REDACTED]")
    _sub(_GITHUB_PAT_RE, "github_token", "[REDACTED]")
    _sub(_SLACK_TOKEN_RE, "slack_token", "[REDACTED]")
    _sub(_EMAIL_RE, "email", "[REDACTED]")

    return OutputPolicyResult(text=out, redaction_kinds=kinds)
