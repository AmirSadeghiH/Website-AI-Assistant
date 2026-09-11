"""Central panel page ACL for admin users created from «اتاق فرمان».

- Superusers bypass every check.
- Staff without a StaffPermission row keeps legacy behavior (full access)
  so existing deployments do not lock anyone out on upgrade.
- Staff with a row is restricted to the page keys stored in allowed_pages.

Page keys canonical list — must match StaffPermission.PAGE_CHOICES
and be used as the first arg to panel_access_required().
"""
from __future__ import annotations

from functools import wraps

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

PANEL_PAGES: tuple[str, ...] = (
    "dashboard",
    "conversations",
    "unanswered",
    "leads",
    "handoff",
    "knowledge",
    "customizer",
    "installation",
    "ai_settings",
    "business_rules",
    "guard_settings",
    "wizard",
)

PANEL_PAGE_LABELS: dict[str, str] = {
    "dashboard": "داشبورد",
    "conversations": "مکالمات",
    "unanswered": "سؤالات بی‌پاسخ",
    "leads": "سرنخ‌ها",
    "handoff": "درخواست‌های پشتیبانی",
    "knowledge": "پایگاه دانش",
    "customizer": "شخصی‌سازی ویجت",
    "installation": "نصب ویجت",
    "ai_settings": "تنظیمات هوش مصنوعی",
    "business_rules": "قوانین کسب‌وکار",
    "guard_settings": "محافظ محتوا",
    "wizard": "گام‌های راه‌اندازی",
    "health_summary": "سلامت سیستم",
}


def allowed_pages_for(user) -> set[str] | None:
    """None = unrestricted (superuser or legacy staff without a row)."""
    if user is None or not getattr(user, "is_active", False):
        return set()
    if getattr(user, "is_superuser", False):
        return None
    # Legacy: no StaffPermission row -> full access (safe upgrade)
    try:
        row = getattr(user, "staff_permission", None)
        if row is None:
            from chat.models import StaffPermission
            row = StaffPermission.objects.filter(user=user).first()
        if row is None:
            return None
        return set(row.allowed_pages or [])
    except Exception:
        return set()


def can_access(user, page: str) -> bool:
    allowed = allowed_pages_for(user)
    if allowed is None:
        return True
    return page in allowed


def panel_access_required(page: str):
    """Decorator: staff_member_required + page ACL. Must wrap the view function."""
    def decorator(view_func):
        @wraps(view_func)
        @staff_member_required
        def _wrapped(request, *args, **kwargs):
            if not can_access(request.user, page):
                # For HTML panel views, a Persian 403 page reads better than a bare 403.
                # For API-like panel views (JsonResponse), the caller still gets 403.
                accept = (request.headers.get("Accept") or "").lower()
                if "application/json" in accept:
                    return HttpResponseForbidden("دسترسی ندارید.")
                return render(request, "panel/forbidden.html", {
                    "page": page,
                    "label": PANEL_PAGE_LABELS.get(page, page),
                }, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def command_room_required(view_func):
    """Only superusers may open «اتاق فرمان» and its sub-pages."""
    @wraps(view_func)
    @staff_member_required
    def _wrapped(request, *args, **kwargs):
        if not getattr(request.user, "is_superuser", False):
            return render(request, "panel/forbidden.html", {
                "page": "command_room",
                "label": "اتاق فرمان",
            }, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped
