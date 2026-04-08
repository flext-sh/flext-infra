# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.refactor.test_rope_semantic as _tests_refactor_test_rope_semantic

    test_rope_semantic = _tests_refactor_test_rope_semantic
    import tests.refactor.test_rope_stubs as _tests_refactor_test_rope_stubs

    test_rope_stubs = _tests_refactor_test_rope_stubs
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "test_rope_semantic": "tests.refactor.test_rope_semantic",
    "test_rope_stubs": "tests.refactor.test_rope_stubs",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "d",
    "e",
    "h",
    "r",
    "s",
    "test_rope_semantic",
    "test_rope_stubs",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
