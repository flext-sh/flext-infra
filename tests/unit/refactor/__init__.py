# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.unit.refactor.test_infra_refactor_census_preview_cache import (
        TestsFlextInfraRefactorCensusPreviewCache as TestsFlextInfraRefactorCensusPreviewCache,
    )
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
        TestsFlextInfraRefactorInfraRefactorClassAndPropagation as TestsFlextInfraRefactorInfraRefactorClassAndPropagation,
    )
    from tests.unit.refactor.test_infra_refactor_class_placement import (
        TestsFlextInfraRefactorInfraRefactorClassPlacement as TestsFlextInfraRefactorInfraRefactorClassPlacement,
    )
    from tests.unit.refactor.test_infra_refactor_cli_models_workflow import (
        TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow as TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow,
    )
    from tests.unit.refactor.test_infra_refactor_engine import (
        TestsFlextInfraRefactorInfraRefactorEngine as TestsFlextInfraRefactorInfraRefactorEngine,
    )
    from tests.unit.refactor.test_infra_refactor_import_modernizer import (
        TestsFlextInfraRefactorInfraRefactorImportModernizer as TestsFlextInfraRefactorInfraRefactorImportModernizer,
    )
    from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import (
        TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations as TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations,
    )
    from tests.unit.refactor.test_infra_refactor_migrate_to_class_mro import (
        TestsFlextInfraRefactorInfraRefactorMigrateToClassMro as TestsFlextInfraRefactorInfraRefactorMigrateToClassMro,
    )
    from tests.unit.refactor.test_infra_refactor_mro_completeness import (
        TestsFlextInfraRefactorInfraRefactorMroCompleteness as TestsFlextInfraRefactorInfraRefactorMroCompleteness,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_aliases import (
        TestsFlextInfraRefactorInfraRefactorNamespaceAliases as TestsFlextInfraRefactorInfraRefactorNamespaceAliases,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_enforcer import (
        TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer as TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_moves import (
        TestsFlextInfraRefactorInfraRefactorNamespaceMoves as TestsFlextInfraRefactorInfraRefactorNamespaceMoves,
    )
    from tests.unit.refactor.test_infra_refactor_pattern_corrections import (
        TestsFlextInfraRefactorInfraRefactorPatternCorrections as TestsFlextInfraRefactorInfraRefactorPatternCorrections,
    )
    from tests.unit.refactor.test_infra_refactor_policy_family_rules import (
        TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules as TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules,
    )
    from tests.unit.refactor.test_infra_refactor_project_classifier import (
        TestsFlextInfraRefactorInfraRefactorProjectClassifier as TestsFlextInfraRefactorInfraRefactorProjectClassifier,
    )
    from tests.unit.refactor.test_infra_refactor_safety import (
        EngineSafetyStub as EngineSafetyStub,
        TestsFlextInfraRefactorInfraRefactorSafety as TestsFlextInfraRefactorInfraRefactorSafety,
    )
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        FlextInfraRefactorTypingUnificationRule as FlextInfraRefactorTypingUnificationRule,
        TestsFlextInfraRefactorInfraRefactorTypingUnifier as TestsFlextInfraRefactorInfraRefactorTypingUnifier,
    )
    from tests.unit.refactor.test_main_cli import (
        TestsFlextInfraRefactorMainCli as TestsFlextInfraRefactorMainCli,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_refactor_census_preview_cache": (
            "TestsFlextInfraRefactorCensusPreviewCache",
        ),
        ".test_infra_refactor_class_and_propagation": (
            "TestsFlextInfraRefactorInfraRefactorClassAndPropagation",
        ),
        ".test_infra_refactor_class_placement": (
            "TestsFlextInfraRefactorInfraRefactorClassPlacement",
        ),
        ".test_infra_refactor_cli_models_workflow": (
            "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
        ),
        ".test_infra_refactor_engine": ("TestsFlextInfraRefactorInfraRefactorEngine",),
        ".test_infra_refactor_import_modernizer": (
            "TestsFlextInfraRefactorInfraRefactorImportModernizer",
        ),
        ".test_infra_refactor_legacy_and_annotations": (
            "TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations",
        ),
        ".test_infra_refactor_migrate_to_class_mro": (
            "TestsFlextInfraRefactorInfraRefactorMigrateToClassMro",
        ),
        ".test_infra_refactor_mro_completeness": (
            "TestsFlextInfraRefactorInfraRefactorMroCompleteness",
        ),
        ".test_infra_refactor_mro_import_rewriter": (
            "test_infra_refactor_mro_import_rewriter",
        ),
        ".test_infra_refactor_namespace_aliases": (
            "TestsFlextInfraRefactorInfraRefactorNamespaceAliases",
        ),
        ".test_infra_refactor_namespace_enforcer": (
            "TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer",
        ),
        ".test_infra_refactor_namespace_moves": (
            "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
        ),
        ".test_infra_refactor_pattern_corrections": (
            "TestsFlextInfraRefactorInfraRefactorPatternCorrections",
        ),
        ".test_infra_refactor_policy_family_rules": (
            "TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules",
        ),
        ".test_infra_refactor_project_classifier": (
            "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
        ),
        ".test_infra_refactor_safety": (
            "EngineSafetyStub",
            "TestsFlextInfraRefactorInfraRefactorSafety",
        ),
        ".test_infra_refactor_typing_unifier": (
            "FlextInfraRefactorTypingUnificationRule",
            "TestsFlextInfraRefactorInfraRefactorTypingUnifier",
        ),
        ".test_main_cli": ("TestsFlextInfraRefactorMainCli",),
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
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
