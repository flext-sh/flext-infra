# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.gates package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.gates.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.gates.abstraction_boundary import (
        FlextInfraAbstractionBoundaryGate as FlextInfraAbstractionBoundaryGate,
    )
    from flext_infra.gates.bandit import FlextInfraBanditGate as FlextInfraBanditGate
    from flext_infra.gates.base_gate import FlextInfraGate as FlextInfraGate
    from flext_infra.gates.canonical_alias import (
        FlextInfraCanonicalAliasGate as FlextInfraCanonicalAliasGate,
    )
    from flext_infra.gates.loc_cap import FlextInfraLocCapGate as FlextInfraLocCapGate
    from flext_infra.gates.markdown import (
        FlextInfraMarkdownGate as FlextInfraMarkdownGate,
    )
    from flext_infra.gates.mypy import FlextInfraMypyGate as FlextInfraMypyGate
    from flext_infra.gates.namespace import (
        FlextInfraNamespaceGate as FlextInfraNamespaceGate,
    )
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate as FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate as FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import (
        FlextInfraRuffFormatGate as FlextInfraRuffFormatGate,
    )
    from flext_infra.gates.ruff_lint import (
        FlextInfraRuffLintGate as FlextInfraRuffLintGate,
    )
    from flext_infra.gates.runtime_census import (
        FlextInfraRuntimeCensusGate as FlextInfraRuntimeCensusGate,
    )
    from flext_infra.gates.silent_failure import (
        FlextInfraSilentFailureGate as FlextInfraSilentFailureGate,
    )
    from flext_infra.gates.smells import FlextInfraSmellsGate as FlextInfraSmellsGate
    from flext_infra.gates.tier_whitelist import (
        FlextInfraTierWhitelistGate as FlextInfraTierWhitelistGate,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
