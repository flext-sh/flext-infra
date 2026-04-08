# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "test_rope_semantic": "tests.refactor.test_rope_semantic",
    "test_rope_stubs": "tests.refactor.test_rope_stubs",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
