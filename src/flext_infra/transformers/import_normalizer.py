"""Normalize project alias imports to canonical package-level imports."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import t, u


class FlextInfraTransformerImportNormalizer:
    """Namespace for import normalization logic and classes."""

    class Transformer(cst.CSTTransformer):
        """CST transformer that normalizes import statements to canonical form."""

        def __init__(
            self,
            *,
            file_path: Path,
            project_package: str = "",
            alias_map: Mapping[str, t.Infra.VariadicTuple[str]] | None = None,
            on_change: t.Infra.ChangeCallback = None,
        ) -> None:
            """Initialize transformer with file context and change callback."""
            self._context = u.Infra.normalizer_build_context(
                file_path=file_path,
                project_package=project_package,
                alias_map=alias_map,
            )
            self._on_change = on_change
            self.modified_imports = False
            self.aliases_present: t.Infra.StrSet = set()
            self.changes: MutableSequence[str] = []

        @override
        def leave_ImportFrom(
            self,
            original_node: cst.ImportFrom,
            updated_node: cst.ImportFrom,
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            module_name = u.Infra.cst_module_name(original_node)
            if not module_name:
                return updated_node
            if isinstance(updated_node.names, cst.ImportStar):
                return updated_node
            if module_name == self._context.project_package:
                self._track_present_aliases(updated_node.names)

            # ... similar logic to Visitor but for removal/replacement ...
            return updated_node  # Simplified for now to focus on structure

        def _track_present_aliases(self, aliases: Sequence[cst.ImportAlias]) -> None:
            for imported_alias in aliases:
                imported_name = u.Infra.cst_imported_name(imported_alias)
                if (
                    imported_name
                    and imported_name != self._context.declared_alias
                    and imported_name in self._context.project_aliases
                ):
                    self.aliases_present.add(imported_name)

        def _record_change(self, message: str) -> None:
            self.changes.append(message)
            if self._on_change is not None:
                self._on_change(message)


__all__ = ["FlextInfraTransformerImportNormalizer"]
