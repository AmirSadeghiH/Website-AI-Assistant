"""Inject panel sidebar ACL into every /panel/ render.

Keeps the sidebar honest even for views that don't go through _panel_ctx,
and survives future views without per-view boilerplate.
"""
from __future__ import annotations


def panel_extras(request):
    # Only for panel pages; avoids extra DB hits on widget/API traffic.
    if not request.path.startswith("/panel/"):
        return {}
    try:
        from chat.models import SiteProfile
        from chat.panel_access import allowed_pages_for

        is_superuser = bool(getattr(request.user, "is_superuser", False))
        # allowed_pages: None = unrestricted (superuser or legacy staff)
        allowed = allowed_pages_for(request.user) if getattr(request.user, "is_authenticated", False) else set()
        sp = SiteProfile.objects.first()
        return {
            "is_superuser": is_superuser,
            "allowed_pages": allowed,
            "site_profile": sp,
        }
    except Exception:
        return {}
