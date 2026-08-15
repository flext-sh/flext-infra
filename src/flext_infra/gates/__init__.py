# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.gates package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .abstraction_boundary import FlextInfraAbstractionBoundaryGate
    from .bandit import FlextInfraBanditGate
    from .base_gate import FlextInfraGate
    from .canonical_alias import FlextInfraCanonicalAliasGate
    from .codemod import FlextInfraCodemodGate
    from .deferred_self_reference import FlextInfraDeferredSelfReferenceGate
    from .layout import FlextInfraLayoutGate
    from .loc_cap import FlextInfraLocCapGate
    from .markdown import FlextInfraMarkdownGate
    from .mypy import FlextInfraMypyGate
    from .namespace import FlextInfraNamespaceGate
    from .pyrefly import FlextInfraPyreflyGate
    from .pyright import FlextInfraPyrightGate
    from .ruff_format import FlextInfraRuffFormatGate
    from .ruff_lint import FlextInfraRuffLintGate
    from .runtime_census import FlextInfraRuntimeCensusGate
    from .silent_failure import FlextInfraSilentFailureGate
    from .smells import FlextInfraSmellsGate
    from .tier_whitelist import FlextInfraTierWhitelistGate

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".abstraction_boundary": ("FlextInfraAbstractionBoundaryGate",),
    ".bandit": ("FlextInfraBanditGate",),
    ".base_gate": ("FlextInfraGate",),
    ".canonical_alias": ("FlextInfraCanonicalAliasGate",),
    ".codemod": ("FlextInfraCodemodGate",),
    ".deferred_self_reference": ("FlextInfraDeferredSelfReferenceGate",),
    ".layout": ("FlextInfraLayoutGate",),
    ".loc_cap": ("FlextInfraLocCapGate",),
    ".markdown": ("FlextInfraMarkdownGate",),
    ".mypy": ("FlextInfraMypyGate",),
    ".namespace": ("FlextInfraNamespaceGate",),
    ".pyrefly": ("FlextInfraPyreflyGate",),
    ".pyright": ("FlextInfraPyrightGate",),
    ".ruff_format": ("FlextInfraRuffFormatGate",),
    ".ruff_lint": ("FlextInfraRuffLintGate",),
    ".runtime_census": ("FlextInfraRuntimeCensusGate",),
    ".silent_failure": ("FlextInfraSilentFailureGate",),
    ".smells": ("FlextInfraSmellsGate",),
    ".tier_whitelist": ("FlextInfraTierWhitelistGate",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraAbstractionBoundaryGate",
    "FlextInfraBanditGate",
    "FlextInfraCanonicalAliasGate",
    "FlextInfraCodemodGate",
    "FlextInfraDeferredSelfReferenceGate",
    "FlextInfraGate",
    "FlextInfraLayoutGate",
    "FlextInfraLocCapGate",
    "FlextInfraMarkdownGate",
    "FlextInfraMypyGate",
    "FlextInfraNamespaceGate",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "FlextInfraRuntimeCensusGate",
    "FlextInfraSilentFailureGate",
    "FlextInfraSmellsGate",
    "FlextInfraTierWhitelistGate",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
