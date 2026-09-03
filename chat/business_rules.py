"""Business Rules engine (feature: Business Rules).

Evaluated on every chat turn. Pure Python, no DB write, no LLM call.
Rules are "if trigger then suggest link/text or nudge handoff" — the
value prop the operator asked for: a non-technical site manager can
say "if pricing → suggest /pricing" and it actually fires.

Kept intentionally small; the widget decides rendering (chip vs bar).
"""

import re

from django.core.cache import cache

from .intents import detect_intent

_CACHE_KEY = "ai-support:business-rules:v1"
_CACHE_TTL = 30

# Very coarse negative-sentiment detector (Persian + English). This is not
# a model — it is a keyword gate that is cheap and predictable; the LLM
# still produces the answer, we just nudge the UI.
_NEGATIVE_PATTERNS = tuple(
    re.compile(p) for p in (
        r"عصبانی",
        r"ناراضی",
        r"افتضاح",
        r"خیلی بد",
        r"مسخره",
        r"شکایت",
        r"بی.?فایده",
        r"اهانت",
        r"تهدید",
        r"\bangry\b",
        r"\bterrible\b",
        r"\bawful\b",
        r"\bcomplain",
        r"\brefund\b.*\bangry",
    )
)


def _is_negative(text):
    s = (text or "").lower()
    for pat in _NEGATIVE_PATTERNS:
        if pat.search(s):
            return True
    # Heuristic: many exclamation/question marks
    if s.count("!") + s.count("!") >= 4:
        return True
    if text and len(text) <= 60 and ("!!" in text or "؟؟" in text):
        return True
    return False


def get_active_rules():
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached
    from .models import BusinessRule

    rules = list(BusinessRule.objects.filter(enabled=True).order_by("priority", "-updated_at"))
    cache.set(_CACHE_KEY, rules, timeout=_CACHE_TTL)
    return rules


def invalidate_rules_cache():
    cache.delete(_CACHE_KEY)


def evaluate_rules(*, message, intent=None, used_fallback=False, confidence=None):
    """Return a list of matched rule actions for this turn.

    Each action is a dict: {rule_id, name, action_type, payload, label}.
    At most 2 actions are returned (priority order); the caller attaches
    them to the response as ``rule_actions``.
    """
    text = (message or "").strip()
    if not text:
        return []
    # Detect intent lazily if not provided
    if intent is None:
        try:
            intent = detect_intent(text)
        except Exception:
            intent = "general"

    normalized = text.replace("ي", "ی").replace("ك", "ک").lower()
    rules = get_active_rules()
    matched = []

    for rule in rules:
        tt = rule.trigger_type
        tv = (rule.trigger_value or "").strip()
        fire = False

        if tt == "intent":
            fire = (tv == intent) if tv else False
        elif tt == "keyword":
            if tv:
                needle = tv.replace("ي", "ی").replace("ك", "ک").lower().strip()
                fire = needle in normalized
        elif tt == "sentiment_negative":
            fire = _is_negative(text)
        elif tt == "fallback":
            fire = bool(used_fallback)
        else:
            continue

        if fire:
            matched.append(
                {
                    "rule_id": rule.pk,
                    "name": rule.name,
                    "action_type": rule.action_type,
                    "payload": rule.action_payload or "",
                    "label": rule.action_label or rule.name,
                }
            )
            if len(matched) >= 2:
                break

    return matched
