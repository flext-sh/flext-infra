# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "main_cli_tests": "tests.unit.github.main_cli_tests",
    "main_dispatch_tests": "tests.unit.github.main_dispatch_tests",
    "main_integration_tests": "tests.unit.github.main_integration_tests",
    "main_tests": "tests.unit.github.main_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
