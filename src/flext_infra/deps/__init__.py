# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.deps.__unit__ import (
    CHILD_MODULE_PATHS as _CHILD_MODULE_PATHS,
    EXCLUDED_LAZY_NAMES as _EXCLUDED_LAZY_NAMES,
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.deps import phases as phases
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionService as FlextInfraDependencyDetectionService,
    )
    from flext_infra.deps.detection_analysis import (
        FlextInfraDependencyDetectionAnalysis as FlextInfraDependencyDetectionAnalysis,
    )
    from flext_infra.deps.detector import (
        FlextInfraRuntimeDevDependencyDetector as FlextInfraRuntimeDevDependencyDetector,
    )
    from flext_infra.deps.detector_runtime import (
        FlextInfraDependencyDetectorRuntime as FlextInfraDependencyDetectorRuntime,
    )
    from flext_infra.deps.extra_paths import (
        FlextInfraExtraPathsManager as FlextInfraExtraPathsManager,
    )
    from flext_infra.deps.fix_pyrefly_config import (
        FlextInfraConfigFixer as FlextInfraConfigFixer,
    )
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService as FlextInfraInternalDependencySyncService,
    )
    from flext_infra.deps.modernizer import (
        FlextInfraPyprojectModernizer as FlextInfraPyprojectModernizer,
    )
    from flext_infra.deps.phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps.phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps.phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps.phases.ensure_mypy import (
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps.phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pytest import (
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps.phases.ensure_ruff import (
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps.phases.inject_comments import (
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )
    from flext_infra.deps.toml_phase import (
        FlextInfraTomlPhaseService as FlextInfraTomlPhaseService,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = merge_lazy_imports(
    _CHILD_MODULE_PATHS,
    build_lazy_import_map(
        _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
    ),
    exclude_names=_EXCLUDED_LAZY_NAMES,
    module_name=__name__,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
