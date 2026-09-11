"""Plan limits, message-unit math and cycle arithmetic.

Single source of truth for plan names, monthly limits, input-size presets
and helpers. Imported by models, views, panel and middleware.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

# ── Plan limits (monthly, hard-coded per product decision) ──────────────
PLAN_LIMITS: dict[str, int] = {
    "simple": 2500,
    "plus":   7500,
    "pro":    20000,
}

PLAN_LABELS: dict[str, str] = {
    "simple": "هم پاسخ",
    "plus":   "هم پاسخ پلاس",
    "pro":    "هم پاسخ پرو",
}

PLAN_DURATION_CHOICES: list[tuple[int, str]] = [
    (1,  "۱ ماهه"),
    (3,  "۳ ماهه"),
    (12, "۱ ساله"),
]

# ── Input-size presets ──────────────────────────────────────────────────
# Admin-facing labels → chars-per-message-unit.
# "محتویات داخل جعبهٔ محصول x چیا هستش؟" ≈ 40 chars → always 1 unit.
INPUT_SIZE_CHOICES: list[tuple[str, str]] = [
    ("very_low",  "خیلی کم"),
    ("low",       "کم"),
    ("medium",    "متوسط"),
    ("high",      "زیاد"),
    ("very_high", "خیلی زیاد"),
]

_INPUT_SIZE_MAP: dict[str, int] = {
    "very_low":  150,
    "low":       300,
    "medium":    600,
    "high":      1200,
    "very_high": 2400,
}


def chars_per_unit(size_class: str = "medium") -> int:
    return _INPUT_SIZE_MAP.get(size_class, 600)


def compute_units(text: str, size_class: str = "medium") -> int:
    """How many message-units does *text* consume?

    A typical short question is ≤ 150 chars ⇒ always 1 unit regardless of
    size_class. A 1800-char message at medium (600 chars/unit) ⇒ 3 units.
    """
    n = chars_per_unit(size_class)
    return max(1, math.ceil(len(text or "") / n))


# ── Calendar-month arithmetic (no dateutil dependency) ──────────────────

def add_months(dt: datetime, months: int) -> datetime:
    """Return *dt* shifted forward by *months* calendar months.

    Preserves the time-of-day and clamps day-of-month to the target
    month's last day (31 Mar → 30 Apr).  timezone-aware safe.
    """
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    # clamp day
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(dt.day, max_day)
    return dt.replace(year=year, month=month, day=day)


def get_monthly_window(anchor: datetime, now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """Return (cycle_start, cycle_end) for the monthly window that contains *now*.

    Windows are calendar-month slices starting from *anchor*'s day-of-month.
    For example, anchor = Jan 15, now = Feb 20  →  (Feb 15, Mar 14).
    """
    now = now or timezone.now()
    # If anchor is in the future (plan not yet active), return a dummy window
    if now < anchor:
        return anchor, anchor
    # Count how many full months have elapsed since anchor
    months_elapsed = (now.year - anchor.year) * 12 + (now.month - anchor.month)
    cycle_start = add_months(anchor, months_elapsed)
    # If now < cycle_start (edge case: day-of-month shifted), back up one
    if now < cycle_start:
        months_elapsed -= 1
        cycle_start = add_months(anchor, months_elapsed)
    cycle_end = add_months(cycle_start, 1)
    return cycle_start, cycle_end


# ── Usage helpers ───────────────────────────────────────────────────────

def monthly_usage(cycle_start: datetime, cycle_end: datetime) -> int:
    """Sum of Message.units for user messages in [cycle_start, cycle_end)."""
    from chat.models import Message
    from django.db.models import Sum
    agg = Message.objects.filter(
        role="user",
        created_at__gte=cycle_start,
        created_at__lt=cycle_end,
    ).aggregate(total=Sum("units"))
    return int(agg["total"] or 0)


def quota_info(plan: str, period_start, now=None) -> dict:
    """Return usage dict: used, limit, remaining, pct, cycle_start, cycle_end, exceeded.

    Returns zeros when plan is unknown or period_start is None.
    """
    now = now or timezone.now()
    limit = PLAN_LIMITS.get(plan, 0)
    if not period_start or not limit:
        return {"used": 0, "limit": limit, "remaining": limit, "pct": 0,
                "cycle_start": None, "cycle_end": None, "exceeded": False}
    cs, ce = get_monthly_window(period_start, now)
    used = monthly_usage(cs, ce)
    remaining = max(0, limit - used)
    pct = round(100 * used / limit) if limit else 0
    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "pct": pct,
        "cycle_start": cs,
        "cycle_end": ce,
        "exceeded": used >= limit,
    }


# ── Expiry enforcement ──────────────────────────────────────────────────
# When the subscription period ends and the superuser has not renewed:
#   1. widget public key is rotated (old install snippet dies)
#   2. allowed origins are stashed + cleared (widget API / CORS reject)
#   3. SiteProfile.suspended = True (staff panel shows the lock screen)
# Renewal reverses 2 (restores origins), rotates the key again (fresh
# snippet) and reactivates the period.

_PLAN_STATE_CACHE_KEY = "plan:expired-flag"
_PLAN_STATE_TTL = 10


def ensure_plan_state() -> None:
    """Lazily enforce expiry. Cheap: 10s-cached flag + one write on transition."""
    from django.core.cache import cache
    try:
        from .models import SiteProfile
        sp = SiteProfile.objects.first()
        if sp is None:
            return
        expired = sp.is_expired and not sp.suspended
        if not expired:
            return
        from .models import ProviderSettings
        provider = ProviderSettings.objects.first()
        if provider is not None:
            # Stash origins once (never overwrite a previous stash with empty)
            if not sp.suspended_origins and provider.widget_allowed_origins.strip():
                sp.suspended_origins = provider.widget_allowed_origins
            provider.widget_allowed_origins = ""
            import uuid
            provider.widget_public_key = uuid.uuid4().hex
            provider.save(update_fields=("widget_public_key", "widget_allowed_origins", "updated_at"))
        sp.suspended = True
        sp.save(update_fields=("suspended", "suspended_origins", "updated_at"))
        cache.delete("ai-support:widget-config")
        cache.delete("ai-support:installation")
        cache.delete(_PLAN_STATE_CACHE_KEY)
    except Exception:
        pass


def plan_is_expired() -> bool:
    """10s-cached check used on every widget API request / panel request."""
    from django.core.cache import cache
    val = cache.get(_PLAN_STATE_CACHE_KEY)
    if val is not None:
        return bool(val)
    try:
        from .models import SiteProfile
        sp = SiteProfile.objects.first()
        val = bool(sp and sp.is_expired)
    except Exception:
        val = False
    cache.set(_PLAN_STATE_CACHE_KEY, val, timeout=_PLAN_STATE_TTL)
    return bool(val)


def invalidate_plan_state_cache() -> None:
    from django.core.cache import cache
    cache.delete(_PLAN_STATE_CACHE_KEY)

