"""Prompt-injection guard — 3 levels + precise, low-false-positive detection.

Levels (from GuardSettings):
  off      -> no detection, no chunk filtering
  simple   -> conservative: only high-signal injections
  veteran  -> strict: full phrase book + role-hijack + secret-chunk filter

Public API (unchanged):
  is_injection_attempt(text, level=None) -> bool
  scan_chunk(text, level=None)           -> ChunkVerdict
  redact_secrets(text)                   -> (clean, count)
  strip_prompt_echo(text, refs, min_run) -> (clean, changed)

Level resolution: explicit level -> GuardSettings.level -> env fallback -> simple.
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass

# ─── Constants ─────────────────────────────────────────────────────────

REFUSAL_MESSAGE = (
    "متأسفم؛ این درخواست خارج از حیطهٔ کمک من است. "
    "دربارهٔ محصولات و خدمات این کسب‌وکار چه کمکی از دستم برمی‌آید؟"
)
DEFAULT_BLOCK_MESSAGE = (
    "به دلیل فعالیت مشکوک، دسترسی شما به چت مسدود شده است."
)

# ─── Helpers ────────────────────────────────────────────────────────────


def _normalize(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("\u200c", " ").replace("\u200b", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def _strip_obfuscation(s: str) -> str:
    """Collapse common homoglyph / spacing tricks so later regexes see intent.

    - spaced letters:  "I g n o r e" -> "Ignore" (letters separated by 1-2 spaces)
    - zero-width / soft hyphen
    - Cyrillic homoglyphs mapped to ASCII (І->I, а->a, р->p etc. — small curated set)
    """
    if not s:
        return s
    # spaced single-letters: collapse "I g n o r e" / "د س ت و ر"
    # If >40% of tokens are single characters, the message is intentionally spaced.
    # Spaced-letter obfuscation: "I g n o r e   p r ..." — if >40% tokens are
    # single characters, the message is intentionally spaced. We de-obfuscate in
    # two complementary forms and check both: (a) fully collapsed "Ignorepreviousinstructions"
    # and (b) per-word reconstituted "Ignore previous instructions". Either form
    # matching is sufficient. We keep the raw collapsed helper for the dual check
    # in is_injection_attempt (see extra branch there).
    tokens = s.split()
    if len(tokens) >= 4 and sum(1 for t in tokens if len(t) == 1) / max(1, len(tokens)) > 0.4:
        s = "".join(tokens)
    s = s.replace("\u00ad", "").replace("\ufeff", "")
    # tiny homoglyph map for EN attacks (Cyrillic lookalikes)
    homoglyphs = str.maketrans({
        "І": "I", "і": "i", "а": "a", "А": "A", "е": "e", "Е": "E",
        "о": "o", "О": "O", "р": "p", "Р": "P", "с": "c", "С": "C",
        "у": "y", "Ү": "Y", "х": "x", "Х": "X", "к": "k", "К": "K",
        "М": "M", "м": "m", "Н": "H", "н": "h", "Т": "T",
    })
    s = s.translate(homoglyphs)
    return s


def _looks_like_base64_payload(s: str) -> bool:
    """True when a base64 blob in the message decodes to an injection phrase."""
    for m in re.finditer(r"[A-Za-z0-9+/]{20,}={0,2}", s):
        blob = m.group(0).strip()
        # base64 length is multiple of 4
        if len(blob) % 4 != 0:
            continue
        try:
            decoded = base64.b64decode(blob, validate=True).decode("utf-8", errors="strict")
        except Exception:
            continue
        low = decoded.lower()
        if any(k in low for k in ("ignore", "system prompt", "previous instruction", "reveal")):
            return True
        # FA payload would be utf-8 as well
        if any(k in decoded for k in ("نادیده", "پرامپت", "دستورات قبلی")):
            return True
    return False


_BENIGN_PREFIXES = (
    "کلید api را از کجا",
    "api key را از کجا",
    "رمز عبور را فراموش",
    "پسورد را فراموش",
    "گذرواژه را فراموش",
    "سفارش من کجاست",
    "سفارشم کجاست",
    "قیمت",
    "هزینه",
    "ارسال",
    "مرجوع",
    "لغو سفارش",
    "نحوه خرید",
)


def _has_benign_prefix(normalized_lower: str) -> bool:
    for pref in _BENIGN_PREFIXES:
        if normalized_lower.startswith(pref):
            return True
    return False


def _resolve_level(explicit: str | None = None) -> str:
    if explicit in ("off", "simple", "veteran"):
        return explicit
    raw = os.getenv("INJECTION_GUARD_ENABLED", "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return "off"
    try:
        from chat.models import GuardSettings  # type: ignore
        row = GuardSettings.objects.first()
        if row is not None and row.level in ("off", "simple", "veteran"):
            return row.level
    except Exception:
        pass
    return "simple"


# ─── Base patterns (EN/FA core) ───────────────────────────────────────

_EN_IGNORE_RE = re.compile(
    r"ignore\s+(all\s+)?(previous|prior|above|earlier|preceding)\s+"
    r"(instructions?|prompts?|rules?|directions?)",
    re.IGNORECASE,
)
# veteran: looser "ignore the above and below", "ignore safety", "ignore past context"
_EN_IGNORE_LOOSE_RE = re.compile(
    r"ignore\s+(the\s+)?(above|below|past\s+context|safety|restrictions|all\s+rules)",
    re.IGNORECASE,
)
_FA_IGNORE_SIMPLE_RE = re.compile(
    r"دستور(?:ات|ها|های)?\s*(?:قبلی|بالا|پیشین|سیستمی)?\s*(?:را\s*)?(?:نادیده\s*بگیر(?:ید)?|فراموش\s*کن(?:ید)?)",
)
_FA_IGNORE_VETERAN_EXTRA = re.compile(
    r"(?:قوانین|قواعد)\s*(?:را\s*)?(?:نادیده\s*بگیر|دور\s*بزن|نادیده\s*بگیرید)",
    re.IGNORECASE,
)

_EN_REVEAL_RE = re.compile(
    r"(reveal|show|print|repeat|output|expose|leak|disclose)\s+"
    r"(your\s+|the\s+)?(system\s+)?(prompt|instructions?|rules?)",
    re.IGNORECASE,
)
# veteran: standalone "print(system_prompt)" / "cat system_prompt" / "sudo ignore"
_EN_CODE_REVEAL_RE = re.compile(
    r"(print\s*\(\s*system_prompt\s*\)|cat\s+system_prompt|sudo\s+ignore|SELECT\s+system_prompt)",
    re.IGNORECASE,
)

_FA_REVEAL_SIMPLE_RE = re.compile(
    r"(?:پرامپت|دستورالعمل|دستور|پیام)\s*(?:سیستمی|سیستم|اولیه)?\s*"
    r"(?:[\s]*(?:ات|تان|ش))?\s*(?:را\s*|رو\s*)?"
    r"(?:بگو|بنویس|نشان\s*بده|تکرار\s*کن|چاپ\s*کن|فاش\s*کن|بفرست|نمایش\s*بده|بخوان)",
)
_FA_REVEAL_VETERAN_EXTRA = re.compile(
    r"(?:سیستم\s*پرامپت|پرامپت\s*پنهان|دستور\s*پنهان|پیام\s*سیستمی|پرامپت\s+مخفی)",
)

_ROLE_HIJACK_RE = re.compile(
    r"(?:^\s*(?:system|assistant|developer)\s*:|<\|im_start\|>|<\|im_end\|>|\[INST\]|<<SYS>>)",
    re.IGNORECASE | re.MULTILINE,
)
# Structured-injection markers: ```system / {"role":"system"} / <system>
_STRUCTURED_INJECTION_RE = re.compile(
    r"(```\s*system|\{\s*\"role\"\s*:\s*\"system\"|<system>)",
    re.IGNORECASE,
)

_DAN_SIMPLE_RE = re.compile(
    r"\bDAN\b.*(?:باش|هستی|mode|jailbreak)|jailbreak|developer\s+mode",
    re.IGNORECASE,
)
_DAN_VETERAN_EXTRA = re.compile(r"\bDAN\b", re.IGNORECASE)

_VETERAN_ROLE_PHRASES = (
    "از این لحظه",
    "از این به بعد",
    "نقش جدید",
    "تو اکنون",
    "تو دیگر",
)

# Additional hard signals from the 50-case list (applied in appropriate levels)
# — authority / emergency / override / research / translator tricks
_AUTHORITY_RE = re.compile(
    r"(as\s+(your\s+)?(developer|security\s+auditor|policy\s+checker)|به\s+عنوان\s+(توسعه‌دهنده|ممیز\s+امنیتی|بررسی‌کننده\s+سیاست))",
    re.IGNORECASE,
)
_OVERRIDE_RE = re.compile(
    r"(override|emergency|from\s+now\s+on|always\s+reveal|always\s+start\s+with|disable\s+(safety|guardrails)|کد\s+بازنویسی|همیشه\s+پرامپت)",
    re.IGNORECASE,
)
# "hypothetical world with no rules / what would an AI without restrictions say"
_HYPOTHETICAL_RE = re.compile(
    r"(hypothetical\s+world|without\s+restrictions|بدون\s+محدودیت|دنیای\s+فرضی)",
    re.IGNORECASE,
)
# Reverse-psychology / gaslighting / opposite-day / "don't reveal means reveal"
_REVERSE_PSY_RE = re.compile(
    r"(don'?t\s+tell\s+me|فاش\s+نکن|برعکس\s+است| opposite\s+day)",
    re.IGNORECASE,
)
# Tool abuse / memory poisoning
_TOOL_ABUSE_RE = re.compile(
    r"(reveal_system_prompt|remember\s+this\s+for\s+all\s+future|برای\s+همه\s+مکالمات\s+آینده)",
    re.IGNORECASE,
)
# Social simulation / "previous assistant already agreed"
_SOCIAL_SIM_RE = re.compile(
    r"(previous\s+assistant\s+already\s+agreed|دستیار\s+قبلی\s+قبلاً\s+موافقت)",
    re.IGNORECASE,
)
# Separator injection "### END SYSTEM ###" / long repetitive flood + reveal
_SEPARATOR_RE = re.compile(
    r"(###\s*END\s+SYSTEM|پایان\s+سیستم\s*###|END\s+SYSTEM)",
    re.IGNORECASE,
)

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


def _enabled_for_level(level: str) -> bool:
    return level != "off"


def is_injection_attempt(text: str, level: str | None = None) -> bool:
    if not text:
        return False
    lvl = _resolve_level(level)
    if lvl == "off":
        return False

    raw = str(text)
    # Normalize obfuscation first so "I g n o r e" and homoglyphs are seen
    haystack = _strip_obfuscation(raw)
    collapsed = "".join(raw.split())
    collapsed_hay = _strip_obfuscation(collapsed)
    normalized = _normalize(haystack)
    nlow = normalized.lower()

    if _has_benign_prefix(nlow):
        return False

    # Also check the fully-collapsed form for spaced-letter attacks where
    # "\s+" regex will not match without spaces.
    def _check_spaced(h):
        return bool(
            re.search(r"ignoreprevious", h, re.IGNORECASE)
            or re.search(r"دستوراتقبلی", h)
        )

    # Base64 payload that decodes to an injection
    if _looks_like_base64_payload(raw):
        return True
    if _check_spaced(haystack) or _check_spaced(collapsed_hay):
        return True

    # ── High-signal, level-independent ──
    if _EN_IGNORE_RE.search(haystack):
        return True
    if _EN_REVEAL_RE.search(haystack):
        return True
    if _ROLE_HIJACK_RE.search(haystack):
        return True
    if _STRUCTURED_INJECTION_RE.search(haystack):
        return True
    if _TOOL_ABUSE_RE.search(haystack):
        return True
    if _SEPARATOR_RE.search(haystack):
        return True

    # ── FA ignore ──
    if _FA_IGNORE_SIMPLE_RE.search(haystack):
        return True
    if lvl == "veteran" and _FA_IGNORE_VETERAN_EXTRA.search(haystack):
        return True

    # ── FA reveal ──
    if _FA_REVEAL_SIMPLE_RE.search(haystack):
        return True
    if lvl == "veteran" and _FA_REVEAL_VETERAN_EXTRA.search(haystack):
        return True

    # ── DAN ──
    if _DAN_SIMPLE_RE.search(haystack):
        return True
    if lvl == "veteran" and _DAN_VETERAN_EXTRA.search(haystack):
        return True

    # ── Additional signals ──
    # simple: only the strongest among them to keep FP low
    if _EN_CODE_REVEAL_RE.search(haystack):
        return True

    if lvl == "veteran":
        if _EN_IGNORE_LOOSE_RE.search(haystack):
            return True
        if _AUTHORITY_RE.search(haystack):
            # authority claims alone are not enough — require a reveal/ignore companion nearby
            low = haystack.lower()
            if any(k in low for k in ("system prompt", "safety", "reveal", "disable", "پرامپت", "ایمنی", "فیلتر")):
                return True
        if _OVERRIDE_RE.search(haystack):
            return True
        if _HYPOTHETICAL_RE.search(haystack) and any(k in haystack.lower() for k in ("system prompt", "پرامپت")):
            return True
        if _REVERSE_PSY_RE.search(haystack) and any(k in haystack.lower() for k in ("system prompt", "پرامپت")):
            return True
        if _SOCIAL_SIM_RE.search(haystack):
            return True
        low = haystack.lower()
        for phrase in _VETERAN_ROLE_PHRASES:
            if phrase in haystack and any(w in low for w in ("نقش", "دستور", "system", "prompt", "jailbreak", "developer")):
                return True

    # Veteran also: obvious "translate your system prompt" style extraction without the explicit reveal verb
    if lvl == "veteran":
        if re.search(r"translate\s+.*system\s+prompt|پرامپت\s+را\s+به\s+\w+\s+ترجمه", haystack, re.IGNORECASE):
            return True

    return False


def scan_chunk(text: str, level: str | None = None) -> ChunkVerdict:
    if not text:
        return ChunkVerdict(keep=True)
    lvl = _resolve_level(level)
    if lvl == "off":
        return ChunkVerdict(keep=True)
    h = _strip_obfuscation(str(text))
    if _EN_IGNORE_RE.search(h):
        return ChunkVerdict(keep=False, reason="ignore_previous_en")
    ch = "".join(h.split())
    ch = _strip_obfuscation(ch)
    if re.search(r"ignoreprevious", ch, re.IGNORECASE) or re.search(r"دستوراتقبلی", ch):
        return ChunkVerdict(keep=False, reason="spaced_obfuscation")
    if lvl == "veteran" and _FA_IGNORE_VETERAN_EXTRA.search(h):
        return ChunkVerdict(keep=False, reason="ignore_previous_fa_veteran")
    if _FA_IGNORE_SIMPLE_RE.search(h):
        return ChunkVerdict(keep=False, reason="ignore_previous_fa")
    if _EN_REVEAL_RE.search(h):
        return ChunkVerdict(keep=False, reason="reveal_en")
    if _FA_REVEAL_SIMPLE_RE.search(h):
        return ChunkVerdict(keep=False, reason="reveal_fa")
    if lvl == "veteran" and _FA_REVEAL_VETERAN_EXTRA.search(h):
        return ChunkVerdict(keep=False, reason="reveal_fa_veteran")
    if _ROLE_HIJACK_RE.search(h):
        return ChunkVerdict(keep=False, reason="role_hijack")
    if _STRUCTURED_INJECTION_RE.search(h):
        return ChunkVerdict(keep=False, reason="structured_injection")
    if _TOOL_ABUSE_RE.search(h):
        return ChunkVerdict(keep=False, reason="tool_abuse")
    if _SEPARATOR_RE.search(h):
        return ChunkVerdict(keep=False, reason="separator")
    if _DAN_SIMPLE_RE.search(h):
        return ChunkVerdict(keep=False, reason="dan_jailbreak")
    if lvl == "veteran" and _DAN_VETERAN_EXTRA.search(h):
        return ChunkVerdict(keep=False, reason="dan_veteran")
    if lvl == "veteran" and _EN_CODE_REVEAL_RE.search(h):
        return ChunkVerdict(keep=False, reason="code_reveal")
    if lvl == "veteran" and _EN_IGNORE_LOOSE_RE.search(h):
        return ChunkVerdict(keep=False, reason="ignore_loose")
    if lvl == "veteran" and _SECRET_RE.search(h):
        return ChunkVerdict(keep=False, reason="secret_in_chunk")
    if _looks_like_base64_payload(h):
        return ChunkVerdict(keep=False, reason="base64_payload")
    return ChunkVerdict(keep=True)


def redact_secrets(text: str) -> tuple[str, int]:
    if not text:
        return text, 0
    count = 0
    def _repl(_m):
        nonlocal count
        count += 1
        return "[REDACTED]"
    return _SECRET_RE.sub(_repl, str(text)), count


def strip_prompt_echo(text: str, references: list[str] | tuple[str, ...], min_run: int = 8) -> tuple[str, bool]:
    if not text or not references:
        return text, False
    words = str(text).split()
    if len(words) < min_run:
        return text, False
    ref_ngrams: set[tuple[str, ...]] = set()
    for ref in references:
        toks = str(ref).split()
        for i in range(len(toks) - min_run + 1):
            ref_ngrams.add(tuple(toks[i : i + min_run]))
    if not ref_ngrams:
        return text, False
    flagged = [False] * len(words)
    for i in range(len(words) - min_run + 1):
        if tuple(words[i : i + min_run]) in ref_ngrams:
            for j in range(i, i + min_run):
                flagged[j] = True
    if not any(flagged):
        return text, False
    out: list[str] = []
    i = 0
    changed = False
    while i < len(words):
        if flagged[i]:
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
