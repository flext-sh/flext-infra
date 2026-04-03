"""Alias remover transformer — rope-based implementation."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import t, u


class FlextInfraRefactorAliasRemover:
    """Remove module-level ``Name = Name`` identity aliases via rope.

    Wraps :pymethod:`u.Infra.remove_module_level_aliases`
    with configurable allow-lists.
    """

    def __init__(
        self,
        allow_aliases: t.Infra.StrSet,
        allow_target_suffixes: t.Infra.VariadicTuple[str],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize alias remover with allow-list configuration."""
        self._allow_aliases = allow_aliases
        self._allow_target_suffixes = allow_target_suffixes
        self._on_change = on_change

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool = True,
    ) -> tuple[str, Sequence[str]]:
        """Apply alias removal. Returns (new_source, list of change descriptions)."""
        new_source, removed = u.Infra.remove_module_level_aliases(
            rope_project,
            resource,
            allow=self._allow_aliases,
            apply=apply,
        )
        if removed and self._on_change is not None:
            for alias in removed:
                self._on_change(f"Removed alias: {alias}")
        return new_source, removed
