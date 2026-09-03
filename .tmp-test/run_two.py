"""Call the two failing test methods directly to see raw tracebacks."""
import os
import sys
import traceback

sys.path.insert(0, r"D:\ai-support-platform")
os.chdir(r"D:\ai-support-platform")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DEBUG", "True")

import django

django.setup()

from chat.tests import SupportAdminTests

out = open(r"D:\ai-support-platform\.tmp-test\detail2.txt", "w", encoding="utf-8")

for method in (
    "test_sniff_file_type_matches_content_not_extension",
    "test_retriever_raises_clear_error_on_dimension_mismatch",
):
    instance = SupportAdminTests(method)
    try:
        getattr(instance, method)()
        out.write(f"{method}: PASSED\n\n")
    except Exception:
        out.write(f"{method}: RAISED\n")
        traceback.print_exc(file=out)
        out.write("\n")

out.close()
