# -*- coding: utf-8 -*-
"""Extract prodcheck release-gate items relevant to this project.

Keeps items whose stack is "any" or "django" (plus the generic AI/core areas),
groups them by checklist -> section, and writes a reviewable BLOCKERS.md with
one line per item for the verification pass.
"""
import json
import os
import sys
from collections import OrderedDict

SRC = os.path.join(os.environ.get("TEMP", "."), "prodcheck.json")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BLOCKERS.md")

with open(SRC, encoding="utf-8") as fh:
    data = json.load(fh)

print("total items:", data["counts"]["total"])
print("release_gate items:", data["counts"]["release_gate"])

kept = [it for it in data["items"] if it.get("release_gate") and it.get("stack") in ("any", "django", "python")]
print("kept (release_gate & stack in any/django/python):", len(kept))

groups = OrderedDict()
for it in kept:
    key = (it["domain"], it["checklist"], it["section"])
    groups.setdefault(key, []).append(it)

lines = []
lines.append("# BLOCKERS — prodcheck release gate (Django/any)")
lines.append("")
lines.append(f"Kept {len(kept)} of {data['counts']['release_gate']} release-gate items "
             f"(stack filter: any + django). Each item needs: file:line + quote, or UNKNOWN.")
lines.append("")
for (domain, checklist, section), items in groups.items():
    lines.append(f"## {checklist} — {section}  [{domain}]")
    lines.append("")
    for it in items:
        lines.append(f"- [ ] ({it['id']}) {it['text']}")
    lines.append("")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("wrote", OUT, "with", sum(1 for l in lines if l.startswith('- [ ]')), "checkbox items")

# Also print the section summary so the human can pick the review order
print("\n== Sections ==")
for (domain, checklist, section), items in groups.items():
    print(f"{len(items):>3}  {checklist} — {section}")
