# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.refactor.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator as FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import (
        FlextInfraRefactorCensus as FlextInfraRefactorCensus,
    )
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer as FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.classvar_constant_autofix import (
        FlextInfraRefactorClassvarConstantAutofix as FlextInfraRefactorClassvarConstantAutofix,
    )
    from flext_infra.refactor.declarative_enforcement import (
        FlextInfraRefactorDeclarativeEnforcement as FlextInfraRefactorDeclarativeEnforcement,
    )
    from flext_infra.refactor.file_executor import (
        FlextInfraClassNestingPostCheckGate as FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor as FlextInfraRefactorFileExecutor,
    )
    from flext_infra.refactor.legacy_text_ops import (
        FlextInfraRefactorLegacyTextOps as FlextInfraRefactorLegacyTextOps,
    )
    from flext_infra.refactor.loader import (
        FlextInfraRefactorRuleLoader as FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO as FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.modernize_orchestrator import (
        FlextInfraModernizeOrchestrator as FlextInfraModernizeOrchestrator,
    )
    from flext_infra.refactor.mro_import_rewriter import (
        FlextInfraRefactorMROImportRewriter as FlextInfraRefactorMROImportRewriter,
    )
    from flext_infra.refactor.mro_migration_validator import (
        FlextInfraRefactorMROMigrationValidator as FlextInfraRefactorMROMigrationValidator,
    )
    from flext_infra.refactor.mro_resolver import (
        FlextInfraRefactorMROResolver as FlextInfraRefactorMROResolver,
    )
    from flext_infra.refactor.namespace_enforcer import (
        FlextInfraNamespaceEnforcer as FlextInfraNamespaceEnforcer,
    )
    from flext_infra.refactor.namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin as FlextInfraNamespaceEnforcerPhasesMixin,
    )
    from flext_infra.refactor.orchestrator import (
        FlextInfraRefactorOrchestrator as FlextInfraRefactorOrchestrator,
    )
    from flext_infra.refactor.project_classifier import (
        FlextInfraProjectClassifier as FlextInfraProjectClassifier,
    )
    from flext_infra.refactor.safety import (
        FlextInfraRefactorSafetyManager as FlextInfraRefactorSafetyManager,
    )
    from flext_infra.refactor.scanner import (
        FlextInfraRefactorLooseClassScanner as FlextInfraRefactorLooseClassScanner,
    )
    from flext_infra.refactor.service import (
        FlextInfraRefactorService as FlextInfraRefactorService,
    )
    from flext_infra.refactor.text_executor import (
        FlextInfraRefactorTextExecutor as FlextInfraRefactorTextExecutor,
    )
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer as FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.refactor.wrapper_root_namespace import (
        FlextInfraWrapperRootNamespaceRefactor as FlextInfraWrapperRootNamespaceRefactor,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
