# -*- coding: utf-8 -*-
"""Probe: /panel/preview/ must serve the right bundle for each theme; installation snippet mapping too."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client

c = Client(SERVER_NAME="127.0.0.1")
user = User.objects.filter(is_superuser=True).first()
c.force_login(user)
print("logged in as:", user.username)

themes = ["classic", "onyx", "linen", "clay", "atomic", "fluen",
          "glassmo", "md3", "minimal", "neu", "skuermo", "bogus"]
for t in themes:
    r = c.get("/panel/preview/", {"theme": t})
    body = r.content.decode("utf-8")
    m = re.search(r'src="([^"]*widget[^"]*)"', body)
    src = m.group(1).split("/static/")[-1] if m else "NO-SCRIPT"
    print(f"{t:<9} {r.status_code}  {src}")

# Customizer page renders the 11-choice select + cards container
r = c.get("/panel/customizer/")
body = r.content.decode("utf-8")
print("customizer:", r.status_code,
      "select:", 'name="widget_theme"' in body,
      "cards:", 'id="theme-cards"' in body,
      "iframe-theme:", 'data-theme=' in body)

# Installation snippet reflects configured theme
from chat.models import WidgetConfig
cfg = WidgetConfig.objects.first()
cfg.widget_theme = "glassmo"
cfg.save(update_fields=["widget_theme"])
r = c.get("/panel/installation/")
body = r.content.decode("utf-8")
m = re.search(r'/static/widget/(widget[^\s"\']+)', body)
print("installation snippet file:", m.group(1) if m else "NOT-FOUND")

cfg.widget_theme = "classic"
cfg.save(update_fields=["widget_theme"])
r = c.get("/panel/installation/")
m = re.search(r'/static/widget/(widget[^\s"\']+)', r.content.decode("utf-8"))
print("back-to-classic snippet file:", m.group(1) if m else "NOT-FOUND")

# Themed demo page: /demo/ → /api/demo/ must serve the configured bundle
for t in ["glassmo", "md3", "classic"]:
    cfg.widget_theme = t
    cfg.save(update_fields=["widget_theme"])
    r = c.get("/demo/", follow=True)
    body = r.content.decode("utf-8")
    m = re.search(r'/static/widget/(widget[^\s"\']+)', body)
    print(f"demo theme={t:<8} status={r.status_code} file={m.group(1) if m else 'NOT-FOUND'}")

cfg.widget_theme = "classic"
cfg.save(update_fields=["widget_theme"])
