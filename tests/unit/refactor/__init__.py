# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.refactor package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_infra_refactor_census_preview_cache import (
        TestsFlextInfraRefactorCensusPreview,
    )
    from .test_infra_refactor_cli_models_workflow import (
        TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow,
    )
    from .test_infra_refactor_namespace_moves import (
        TestsFlextInfraRefactorInfraRefactorNamespaceMoves,
    )
    from .test_infra_refactor_project_classifier import (
        TestsFlextInfraRefactorInfraRefactorProjectClassifier,
    )
    from .test_main_cli import TestsFlextInfraRefactorMainCli
    from .test_signature_propagation import TestsFlextInfraRefactorSignaturePropagation
__all__: tuple[str, ...] = (
    "TestsFlextInfraRefactorCensusPreview",
    "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
    "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
    "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
    "TestsFlextInfraRefactorMainCli",
    "TestsFlextInfraRefactorSignaturePropagation",
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
            ".test_infra_refactor_census_preview_cache": (
                "TestsFlextInfraRefactorCensusPreview",
            ),
            ".test_infra_refactor_cli_models_workflow": (
                "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
            ),
            ".test_infra_refactor_namespace_moves": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
            ),
            ".test_infra_refactor_project_classifier": (
                "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
            ),
            ".test_main_cli": ("TestsFlextInfraRefactorMainCli",),
            ".test_signature_propagation": (
                "TestsFlextInfraRefactorSignaturePropagation",
            ),
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
