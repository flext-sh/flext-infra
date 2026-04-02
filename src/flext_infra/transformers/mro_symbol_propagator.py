"""Symbol propagation transformer for MRO-migrated imports — rope-based."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import override

from flext_infra import FlextInfraUtilitiesRope, t
from flext_infra.transformers._base import FlextInfraRopeTransformer


class FlextInfraRefactorMROSymbolPropagator(FlextInfraRopeTransformer):
    """Rewrite imports and references after symbols move into facade namespaces.

    For each module_move entry, rewrites ``from old_module import Symbol``
    to ``from old_module import Facade`` and qualifies bare references
    as ``Facade.NestedPath``.
    """

    def __init__(
        self,
        *,
        module_moves: Mapping[str, t.Infra.Pair[str, t.StrMapping]],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with module move configuration."""
        super().__init__(on_change=on_change)
        self._module_moves = module_moves

    def rewrite_source(self, source: str) -> tuple[str, Sequence[str]]:
        """Rewrite one source string using the configured MRO move map."""
        self.changes.clear()
        rewritten_source = source
        for module_name, (facade_alias, symbol_paths) in self._module_moves.items():
            rewritten_source = self._rewrite_from_imports(
                rewritten_source,
                module_name=module_name,
                facade_alias=facade_alias,
                symbol_paths=symbol_paths,
            )
            rewritten_source = self._qualify_bare_references(
                rewritten_source,
                facade_alias=facade_alias,
                symbol_paths=symbol_paths,
            )
        return (rewritten_source, list(self.changes))

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply import and reference rewrites. Returns (new_source, changes)."""
        source = FlextInfraUtilitiesRope.read_source(resource)
        rewritten_source, changes = self.rewrite_source(source)
        if rewritten_source != source and changes:
            FlextInfraUtilitiesRope.write_source(
                rope_project,
                resource,
                rewritten_source,
                description="mro symbol propagator",
            )
        return (rewritten_source, changes)

    def _rewrite_from_imports(
        self,
        source: str,
        *,
        module_name: str,
        facade_alias: str,
        symbol_paths: t.StrMapping,
    ) -> str:
        """Rewrite ``from module import OldSymbol`` to ``from module import Facade``."""
        for old_symbol, target_path in symbol_paths.items():
            # Match: from module_name import old_symbol (possibly with alias)
            pattern = re.compile(
                rf"(from\s+{re.escape(module_name)}\s+import\s+)"
                rf"(\b{re.escape(old_symbol)}\b)",
            )
            new_source = pattern.sub(rf"\1{facade_alias}", source)
            if new_source != source:
                self._record_change(
                    f"Rewired import: {module_name}.{old_symbol} -> {facade_alias}.{target_path}",
                )
                source = new_source
        return source

    def _qualify_bare_references(
        self,
        source: str,
        *,
        facade_alias: str,
        symbol_paths: t.StrMapping,
    ) -> str:
        """Replace bare symbol references with qualified facade paths."""
        for old_symbol, target_path in symbol_paths.items():
            # Skip definition sites (class X, def X, X =, X:)
            ref_pattern = re.compile(
                rf"(?<!class\s)(?<!def\s)(?<!\.)(?<!import\s)"
                rf"\b{re.escape(old_symbol)}\b"
                rf"(?!\s*[=:](?!=))"
                rf"(?!\s*\()",
            )
            qualified = f"{facade_alias}.{target_path}"
            new_source = ref_pattern.sub(qualified, source)
            if new_source != source:
                self._record_change(
                    f"Qualified reference: {old_symbol} -> {qualified}",
                )
                source = new_source
        return source


__all__ = ["FlextInfraRefactorMROSymbolPropagator"]
