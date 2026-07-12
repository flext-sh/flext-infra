# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps.phases package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.deps.phases.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
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

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
