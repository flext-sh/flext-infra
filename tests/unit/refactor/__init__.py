# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_apply_renames_cli import TestsFlextInfraApplyRenamesCli
    from .test_declarative_enforcement import (
        TestsFlextInfraRefactorDeclarativeEnforcement,
        TestsFlextInfraRefactorDeclarativeEnforcementInCensus,
    )
    from .test_infra_refactor_class_and_propagation import (
        TestsFlextInfraRefactorInfraRefactorClassAndPropagation,
    )
    from .test_infra_refactor_class_placement import (
        TestsFlextInfraRefactorInfraRefactorClassPlacement,
    )
    from .test_infra_refactor_cli_models_workflow import (
        TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow,
    )
    from .test_infra_refactor_import_modernizer import (
        TestsFlextInfraRefactorInfraRefactorImportModernizer,
    )
    from .test_infra_refactor_legacy_and_annotations import (
        TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations,
    )
    from .test_infra_refactor_migrate_to_class_mro import (
        TestsFlextInfraRefactorInfraRefactorMigrateToClassMro,
    )
    from .test_infra_refactor_mro_completeness import (
        TestsFlextInfraRefactorInfraRefactorMroCompleteness,
    )
    from .test_infra_refactor_mro_shape import (
        TestsFlextInfraRefactorInfraRefactorMroShape,
    )
    from .test_infra_refactor_namespace_aliases import (
        TestsFlextInfraRefactorInfraRefactorNamespaceAliases,
    )
    from .test_infra_refactor_namespace_enforcer import (
        TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer,
    )
    from .test_infra_refactor_namespace_moves import (
        TestsFlextInfraRefactorInfraRefactorNamespaceMoves,
    )
    from .test_infra_refactor_pattern_corrections import (
        TestsFlextInfraRefactorInfraRefactorPatternCorrections,
    )
    from .test_infra_refactor_policy_family_rules import (
        TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules,
    )
    from .test_infra_refactor_project_classifier import (
        TestsFlextInfraRefactorInfraRefactorProjectClassifier,
    )
    from .test_infra_refactor_safety import (
        RefactorSafetyStub,
        TestsFlextInfraRefactorInfraRefactorSafety,
    )
    from .test_infra_refactor_service import TestsFlextInfraRefactorInfraRefactorService
    from .test_infra_refactor_typing_unifier import (
        FlextInfraRefactorTypingUnificationRule,
        TestsFlextInfraRefactorInfraRefactorTypingUnifier,
    )
    from .test_main_cli import TestsFlextInfraRefactorMainCli
__all__: tuple[str, ...] = (
    "FlextInfraRefactorTypingUnificationRule",
    "RefactorSafetyStub",
    "TestsFlextInfraApplyRenamesCli",
    "TestsFlextInfraRefactorDeclarativeEnforcement",
    "TestsFlextInfraRefactorDeclarativeEnforcementInCensus",
    "TestsFlextInfraRefactorInfraRefactorClassAndPropagation",
    "TestsFlextInfraRefactorInfraRefactorClassPlacement",
    "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
    "TestsFlextInfraRefactorInfraRefactorImportModernizer",
    "TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations",
    "TestsFlextInfraRefactorInfraRefactorMigrateToClassMro",
    "TestsFlextInfraRefactorInfraRefactorMroCompleteness",
    "TestsFlextInfraRefactorInfraRefactorMroShape",
    "TestsFlextInfraRefactorInfraRefactorNamespaceAliases",
    "TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer",
    "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
    "TestsFlextInfraRefactorInfraRefactorPatternCorrections",
    "TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules",
    "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
    "TestsFlextInfraRefactorInfraRefactorSafety",
    "TestsFlextInfraRefactorInfraRefactorService",
    "TestsFlextInfraRefactorInfraRefactorTypingUnifier",
    "TestsFlextInfraRefactorMainCli",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_apply_renames_cli": ("TestsFlextInfraApplyRenamesCli",),
            ".test_declarative_enforcement": (
                "TestsFlextInfraRefactorDeclarativeEnforcement",
                "TestsFlextInfraRefactorDeclarativeEnforcementInCensus",
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
            ".test_infra_refactor_mro_shape": (
                "TestsFlextInfraRefactorInfraRefactorMroShape",
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
                "RefactorSafetyStub",
                "TestsFlextInfraRefactorInfraRefactorSafety",
            ),
            ".test_infra_refactor_service": (
                "TestsFlextInfraRefactorInfraRefactorService",
            ),
            ".test_infra_refactor_typing_unifier": (
                "FlextInfraRefactorTypingUnificationRule",
                "TestsFlextInfraRefactorInfraRefactorTypingUnifier",
            ),
            ".test_main_cli": ("TestsFlextInfraRefactorMainCli",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
