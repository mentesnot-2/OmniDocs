"""Unit tests for RAG output policy and JSON parsing helpers."""

import json

from generation.answer_generator import (
    _parse_generation_json,
    _truncate_context,
    _neutralize_boundary_markers,
)
from generation.output_policy import apply_output_policy


def test_apply_output_policy_redacts_email_and_sk() -> None:
    raw = "Contact admin@example.com and use sk-123456789012345678901234567890 for API."
    result = apply_output_policy(raw)
    assert "@" not in result.text
    assert "sk-" not in result.text
    assert "REDACTED" in result.text
    assert "email" in result.redaction_kinds
    assert "openai_key" in result.redaction_kinds


def test_parse_generation_json_plain() -> None:
    payload = {"answer": "ok", "refused": False, "refusal_reason": ""}
    parsed = _parse_generation_json(json.dumps(payload))
    assert parsed == payload


def test_parse_generation_json_fenced() -> None:
    payload = {"answer": "x", "refused": True, "refusal_reason": "missing"}
    text = "```json\n" + json.dumps(payload) + "\n```"
    assert _parse_generation_json(text) == payload


def test_truncate_context_appends_notice() -> None:
    long = "a" * 500
    out = _truncate_context(long, max_chars=200)
    assert len(out) <= 200
    assert "truncated" in out.lower()


def test_neutralize_boundary_markers_inserts_zwsp() -> None:
    marker = "<<<SECRET>>>"
    text = f"hello {marker} bye"
    out = _neutralize_boundary_markers(text, (marker,))
    assert marker not in out
    assert "\u200b" in out
