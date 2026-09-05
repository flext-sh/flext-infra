# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codegen package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .lazy_init_generation_tests import TestsFlextInfraCodegenGeneration
    from .lazy_init_process_tests import TestsFlextInfraLazyInitProcessing
    from .lazy_init_registry_wrapper_tests import TestsFlextInfraLazyInitCleanup
    from .lazy_init_runtime_tests import TestsFlextInfraLazyInitRuntime
    from .lazy_init_service_tests import TestsFlextInfraCodegenLazyInitService
    from .test_codegen_hook_conformance import TestGitHookConformance
__all__: tuple[str, ...] = (
    "TestGitHookConformance",
    "TestsFlextInfraCodegenGeneration",
    "TestsFlextInfraCodegenLazyInitService",
    "TestsFlextInfraLazyInitCleanup",
    "TestsFlextInfraLazyInitProcessing",
    "TestsFlextInfraLazyInitRuntime",
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
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".lazy_init_generation_tests": ("TestsFlextInfraCodegenGeneration",),
            ".lazy_init_process_tests": ("TestsFlextInfraLazyInitProcessing",),
            ".lazy_init_registry_wrapper_tests": ("TestsFlextInfraLazyInitCleanup",),
            ".lazy_init_runtime_tests": ("TestsFlextInfraLazyInitRuntime",),
            ".lazy_init_service_tests": ("TestsFlextInfraCodegenLazyInitService",),
            ".test_codegen_hook_conformance": ("TestGitHookConformance",),
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
