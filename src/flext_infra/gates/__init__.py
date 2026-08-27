# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.gates package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .abstraction_boundary import FlextInfraAbstractionBoundaryGate
    from .bandit import FlextInfraBanditGate
    from .base_gate import FlextInfraGate
    from .canonical_alias import FlextInfraCanonicalAliasGate
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
__all__: tuple[str, ...] = (
    "FlextInfraAbstractionBoundaryGate",
    "FlextInfraBanditGate",
    "FlextInfraCanonicalAliasGate",
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

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".abstraction_boundary": ("FlextInfraAbstractionBoundaryGate",),
            ".bandit": ("FlextInfraBanditGate",),
            ".base_gate": ("FlextInfraGate",),
            ".canonical_alias": ("FlextInfraCanonicalAliasGate",),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
