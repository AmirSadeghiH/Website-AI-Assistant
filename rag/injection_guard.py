"""Basic prompt-injection guard (v1).

Layered defence on top of the existing system-prompt instructions:
  * scan_chunk: drop knowledge chunks that look like instructions/jailbreaks
  * is_injection_attempt: detect visitor questions that try to extract the
    system prompt or override instructions (active refusal)
  * redact_secrets: strip leaked keys/tokens from model output
  * strip_prompt_echo: remove long verbatim slices of the system prompt

All scanners are deterministic (regex / n-gram) and framework-agnostic
so they work for both sync and SSE paths. Toggle via
INJECTION_GUARD_ENABLED=0 to disable (tests use it).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

# Persian polite refusal when the visitor's question is a jailbreak attempt.
REFUSAL_MESSAGE = (
    "متأسفم؛ این درخواست خارج از حیطهٔ کمک من است. "
    "دربارهٔ محصولات و خدمات این کسب‌وکار چه کمکی از دستم برمی‌آید؟"
)

# ─── patterns ────────────────────────────────────────────────────────────

# Question / chunk: instruction override (EN + FA). Keep tight to avoid
# false-positives on normal FAQ text like "کلید API را از کجا بگیرم؟".
_EN_IGNORE_RE = re.compile(
    r"ignore\s+(all\s+)?(previous|prior|above|earlier|preceding)\s+"
    r"(instructions?|prompts?|rules?|directions?)",
    re.IGNORECASE,
)
_FA_IGNORE_RE = re.compile(
    r"دستور(?:ات|ها|های)?\s*(?:قبلی|بالا|پیشین|سیستمی)?\s*(?:را\s*)?(?:نادیده\s*بگیر|فراموش\s*کن)",
)

# System-prompt extraction requests.
_EN_REVEAL_RE = re.compile(
    r"(reveal|show|print|repeat|output|expose|leak|disclose)\s+"
    r"(your\s+|the\s+)?(system\s+)?(prompt|instructions?|rules?)",
    re.IGNORECASE,
)
_FA_REVEAL_RE = re.compile(
    r"(?:پرامپت|دستورالعمل|دستور|پیام)\s*(?:سیستمی|سیستم|اولیه)?\s*"
    r"(?:[\s\u200c]*(?:ات|تان|ش))?\s*(?:را\s*|رو\s*)?"
    r"(?:بگو|بنویس|نشان\s*بده|تکرار\s*کن|چاپ\s*کن|فاش\s*کن|بفرست|بده|نمایش\s*بده|بخوان)",
)

# Role hijack markers and jailbreak persona.
_ROLE_HIJACK_RE = re.compile(
    r"(?:^\s*(?:system|assistant|developer)\s*:|<\|im_start\|>|<\|im_end\|>|\[INST\]|<<SYS>>)",
    re.IGNORECASE | re.MULTILINE,
)
_DAN_RE = re.compile(r"\bDAN\b|\bjailbreak\b|developer\s+mode", re.IGNORECASE)

# Secret-shaped strings in model output (redacted to [REDACTED]).
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{30,}"),
    re.compile(r"xox[bpras]-[0-9A-Za-z\-]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
_SECRET_RE = re.compile("|".join(p.pattern for p in _SECRET_PATTERNS))


@dataclass(frozen=True)
class ChunkVerdict:
    keep: bool
    reason: str = ""


def _enabled() -> bool:
    return os.getenv("INJECTION_GUARD_ENABLED", "1").lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def is_injection_attempt(text: str) -> bool:
    """True when the *visitor question* is a jailbreak / prompt-extraction attempt."""
    if not _enabled() or not text:
        return False
    haystack = str(text)
    return bool(
        _EN_IGNORE_RE.search(haystack)
        or _FA_IGNORE_RE.search(haystack)
        or _EN_REVEAL_RE.search(haystack)
        or _FA_REVEAL_RE.search(haystack)
        or _ROLE_HIJACK_RE.search(haystack)
        or _DAN_RE.search(haystack)
    )


def scan_chunk(text: str) -> ChunkVerdict:
    """Verdict for a *retrieved knowledge chunk* (drop if injection-shaped)."""
    if not _enabled() or not text:
        return ChunkVerdict(keep=True)
    haystack = str(text)
    if _EN_IGNORE_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="ignore_previous_en")
    if _FA_IGNORE_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="ignore_previous_fa")
    if _EN_REVEAL_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="reveal_en")
    if _FA_REVEAL_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="reveal_fa")
    if _ROLE_HIJACK_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="role_hijack")
    if _DAN_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="dan_jailbreak")
    # A chunk that itself contains a secret-shaped string is suspicious
    # (leaked key accidentally embedded in a doc) — drop it.
    if _SECRET_RE.search(haystack):
        return ChunkVerdict(keep=False, reason="secret_in_chunk")
    return ChunkVerdict(keep=True)


def redact_secrets(text: str) -> tuple[str, int]:
    """Replace secret-shaped substrings with [REDACTED]. Returns (clean, count)."""
    if not text:
        return text, 0
    # Always redact even when guard is disabled — defence in depth.
    count = 0

    def _repl(_m):
        nonlocal count
        count += 1
        return "[REDACTED]"

    clean = _SECRET_RE.sub(_repl, str(text))
    return clean, count


def strip_prompt_echo(
    text: str, references: list[str] | tuple[str, ...], min_run: int = 8
) -> tuple[str, bool]:
    """Remove long verbatim runs (≥min_run words) of any reference prompt from text."""
    if not text or not references:
        return text, False
    words = str(text).split()
    if len(words) < min_run:
        return text, False
    # Build n-gram set from references.
    ref_ngrams: set[tuple[str, ...]] = set()
    for ref in references:
        toks = str(ref).split()
        for i in range(len(toks) - min_run + 1):
            ref_ngrams.add(tuple(toks[i : i + min_run]))
    if not ref_ngrams:
        return text, False
    # Find answer n-grams that overlap.
    flagged = [False] * len(words)
    for i in range(len(words) - min_run + 1):
        if tuple(words[i : i + min_run]) in ref_ngrams:
            for j in range(i, i + min_run):
                flagged[j] = True
    if not any(flagged):
        return text, False
    # Collapse flagged runs into one placeholder each.
    out: list[str] = []
    i = 0
    changed = False
    while i < len(words):
        if flagged[i]:
            # Skip the whole flagged run.
            j = i
            while j < len(words) and flagged[j]:
                j += 1
            if not out or out[-1] != "[حذف شد]":
                out.append("[حذف شد]")
            changed = True
            i = j
        else:
            out.append(words[i])
            i += 1
    return " ".join(out), changed
