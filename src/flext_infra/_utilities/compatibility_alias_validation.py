"""Strict validation for semantic compatibility-alias cutovers."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from .qualified_names import FlextInfraUtilitiesQualifiedNames

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesCompatibilityAliasValidation:
    """Reject ambiguous bindings, exports, and post-cutover residue."""

    @staticmethod
    def require_static_compatibility_alias_exports(
        tree: ast.Module, file_path: Path, aliases: frozenset[str]
    ) -> None:
        """Reject dynamic export ownership before changing an alias owner."""
        if not aliases:
            return
        for node in tree.body:
            value: ast.expr | None = None
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                )
            ) or (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "__all__"
            ):
                value = node.value
            if value is not None and not (
                isinstance(value, ast.List | ast.Tuple)
                and all(
                    isinstance(element, ast.Constant) and isinstance(element.value, str)
                    for element in value.elts
                )
            ):
                msg = f"dynamic __all__ blocks alias cutover in {file_path}"
                raise ValueError(msg)

    @staticmethod
    def require_zero_compatibility_alias_residue(
        source: str,
        file_path: Path,
        *,
        qualified_aliases: t.StrMapping,
        exported_aliases: frozenset[str],
    ) -> None:
        """Require removed identities and their literal exports to disappear."""
        tree = ast.parse(source, filename=str(file_path))
        for node in tree.body:
            value: ast.expr | None = None
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                )
            ) or (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "__all__"
            ):
                value = node.value
            if isinstance(value, ast.List | ast.Tuple) and any(
                isinstance(element, ast.Constant) and element.value in exported_aliases
                for element in value.elts
            ):
                msg = f"alias export residue in {file_path}"
                raise ValueError(msg)
        residue = sorted(
            FlextInfraUtilitiesQualifiedNames.qualified_name_residue(
                source, qualified_aliases
            )
        )
        if residue:
            msg = f"qualified alias residue {residue[0]} in {file_path}"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesCompatibilityAliasValidation"]
