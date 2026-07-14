# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.refactor.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
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

    from tests.unit.refactor import (
        test_infra_refactor_mro_import_rewriter as test_infra_refactor_mro_import_rewriter,
    )
    from tests.unit.refactor.test_declarative_enforcement import (
        TestsFlextInfraRefactorDeclarativeEnforcement as TestsFlextInfraRefactorDeclarativeEnforcement,
        TestsFlextInfraRefactorDeclarativeEnforcementInCensus as TestsFlextInfraRefactorDeclarativeEnforcementInCensus,
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
    from tests.unit.refactor.test_infra_refactor_mro_shape import (
        TestsFlextInfraRefactorInfraRefactorMroShape as TestsFlextInfraRefactorInfraRefactorMroShape,
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
        RefactorSafetyStub as RefactorSafetyStub,
        TestsFlextInfraRefactorInfraRefactorSafety as TestsFlextInfraRefactorInfraRefactorSafety,
    )
    from tests.unit.refactor.test_infra_refactor_service import (
        TestsFlextInfraRefactorInfraRefactorService as TestsFlextInfraRefactorInfraRefactorService,
    )
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        FlextInfraRefactorTypingUnificationRule as FlextInfraRefactorTypingUnificationRule,
        TestsFlextInfraRefactorInfraRefactorTypingUnifier as TestsFlextInfraRefactorInfraRefactorTypingUnifier,
    )
    from tests.unit.refactor.test_main_cli import (
        TestsFlextInfraRefactorMainCli as TestsFlextInfraRefactorMainCli,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
