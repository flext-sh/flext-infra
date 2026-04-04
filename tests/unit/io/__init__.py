# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Io package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.io.test_infra_json_io as _tests_unit_io_test_infra_json_io

    test_infra_json_io = _tests_unit_io_test_infra_json_io
    import tests.unit.io.test_infra_terminal_detection as _tests_unit_io_test_infra_terminal_detection
    from tests.unit.io.test_infra_json_io import SampleModel, TestFlextInfraJsonService

    test_infra_terminal_detection = _tests_unit_io_test_infra_terminal_detection
    from tests.unit.io.test_infra_terminal_detection import (
        TestShouldUseColor,
        TestShouldUseUnicode,
    )

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "SampleModel": "tests.unit.io.test_infra_json_io",
    "TestFlextInfraJsonService": "tests.unit.io.test_infra_json_io",
    "TestShouldUseColor": "tests.unit.io.test_infra_terminal_detection",
    "TestShouldUseUnicode": "tests.unit.io.test_infra_terminal_detection",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "test_infra_json_io": "tests.unit.io.test_infra_json_io",
    "test_infra_terminal_detection": "tests.unit.io.test_infra_terminal_detection",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "SampleModel",
    "TestFlextInfraJsonService",
    "TestShouldUseColor",
    "TestShouldUseUnicode",
    "d",
    "e",
    "h",
    "r",
    "s",
    "test_infra_json_io",
    "test_infra_terminal_detection",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
