# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.detectors package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import test_cyclic_import_detector as test_cyclic_import_detector
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_deferred_self_reference_ast import (
        TestsFlextInfraDeferredSelfReferenceDetector,
    )
    from .test_internal_import_detector import TestsFlextInfraInternalImportDetector
    from .test_loose_object_detector import TestsFlextInfraLooseObjectDetector
    from .test_loose_object_detector_characterization import (
        TestsFlextInfraLooseObjectCharacterization,
    )
    from .test_loose_test_function_detector import (
        TestsFlextInfraLooseTestFunctionDetector,
    )
    from .test_pattern_smell_detector import TestsFlextInfraPatternSmellDetector
__all__: tuple[str, ...] = (
    "TestsFlextInfraDeferredSelfReferenceDetector",
    "TestsFlextInfraInternalImportDetector",
    "TestsFlextInfraLooseObjectCharacterization",
    "TestsFlextInfraLooseObjectDetector",
    "TestsFlextInfraLooseTestFunctionDetector",
    "TestsFlextInfraPatternSmellDetector",
    "c",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "t",
    "td",
    "test_cyclic_import_detector",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_cyclic_import_detector": ("test_cyclic_import_detector",),
            ".test_deferred_self_reference_ast": (
                "TestsFlextInfraDeferredSelfReferenceDetector",
            ),
            ".test_internal_import_detector": (
                "TestsFlextInfraInternalImportDetector",
            ),
            ".test_loose_object_detector": ("TestsFlextInfraLooseObjectDetector",),
            ".test_loose_object_detector_characterization": (
                "TestsFlextInfraLooseObjectCharacterization",
            ),
            ".test_loose_test_function_detector": (
                "TestsFlextInfraLooseTestFunctionDetector",
            ),
            ".test_pattern_smell_detector": ("TestsFlextInfraPatternSmellDetector",),
            "flext_tests": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "u",
                "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
