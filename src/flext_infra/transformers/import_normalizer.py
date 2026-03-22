"""Normalize project alias imports to canonical package-level imports."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated, override

import libcst as cst
from pydantic import ConfigDict, Field

from flext_infra import NormalizerContext, m, t, u


class FlextInfraTransformerImportNormalizer:
    """Namespace for import normalization logic and classes."""

    class Violation(m.ArbitraryTypesModel):
        model_config = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field()]
        line: Annotated[t.PositiveInt, Field()]
        current_import: Annotated[t.NonEmptyStr, Field()]
        suggested_import: Annotated[t.NonEmptyStr, Field()]
        violation_type: Annotated[str, Field(pattern="^(deep|wrong_source)$")]

    Context = NormalizerContext

    class Transformer(cst.CSTTransformer):
        def __init__(
            self,
            *,
            file_path: Path,
            project_package: str = "",
            alias_map: dict[str, tuple[str, ...]] | None = None,
            on_change: Callable[[str], None] | None = None,
        ) -> None:
            """Initialize transformer with file context and change callback."""
            self._context = u.Infra.normalizer_build_context(
                file_path=file_path,
                project_package=project_package,
                alias_map=alias_map,
            )
            self._on_change = on_change
            self.modified_imports = False
            self.aliases_to_inject: set[str] = set()
            self.aliases_present: set[str] = set()
            self.changes: list[str] = []

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
