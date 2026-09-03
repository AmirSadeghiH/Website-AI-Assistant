"""Run specific tests in-process and print full failure details.

Used because the pwsh harness mangles unittest stderr output.
"""
import io
import sys
from unittest import TextTestRunner, TextTestResult


class VerboseResult(TextTestResult):
    failures = []
    errors = []

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            sys.stdout.write(f"{flavour}: {test}\n{err}\n")


import django
import os
import sys

sys.path.insert(0, r"D:\ai-support-platform")
os.chdir(r"D:\ai-support-platform")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DEBUG", "True")
django.setup()

from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.runner import DiscoverRunner

setup_test_environment()
runner = DiscoverRunner(verbosity=0, interactive=False)
old_config = runner.setup_databases()

import unittest

from chat.tests import SupportAdminTests, ChatEndpointTests

loader = unittest.TestLoader()
names = sys.argv[1:] or [
    "chat.tests.SupportAdminTests.test_sniff_file_type_matches_content_not_extension",
    "chat.tests.SupportAdminTests.test_retriever_raises_clear_error_on_dimension_mismatch",
]
suite = loader.loadTestsFromNames(names)

result = TextTestRunner(stream=io.StringIO(), resultclass=VerboseResult).run(suite)
with open(r"D:\ai-support-platform\.tmp-test\detail.txt", "w", encoding="utf-8") as fh:
    for flavour, errors in (("ERROR", result.errors), ("FAIL", result.failures)):
        for test, err in errors:
            fh.write(f"{flavour}: {test}\n{err}\n---\n")
    fh.write(f"run={result.testsRun} failures={len(result.failures)} errors={len(result.errors)}\n")
sys.stdout.write(f"run={result.testsRun} failures={len(result.failures)} errors={len(result.errors)}\n")

runner.teardown_databases(old_config)
teardown_test_environment()
