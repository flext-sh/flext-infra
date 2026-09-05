"""Postconditions for semantic private-import rewrites."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import libcst as cst
from libcst.metadata import MetadataWrapper, QualifiedNameProvider

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesPrivateImportValidation:
    """Reject old import residue or an incomplete public cutover."""

    @staticmethod
    def require_zero_private_import_residue(
        source: str,
        *,
        file_path: Path,
        removals: t.MappingKV[str, set[str]],
        replacements: t.StrMapping,
        public_imports: t.StrMapping,
    ) -> None:
        """Require old imports/bindings gone and public imports present."""
        tree = ast.parse(source, filename=str(file_path))
        for module, symbols in removals.items():
            if any(
                isinstance(node, ast.ImportFrom)
                and node.module == module
                and any(imported.name in symbols for imported in node.names)
                for node in ast.walk(tree)
            ):
                msg = f"private import residue from {module} in {file_path}"
                raise ValueError(msg)
        for package, alias in public_imports.items():
            if not any(
                isinstance(node, ast.ImportFrom)
                and node.module == package
                and any(
                    imported.name == alias and imported.asname is None
                    for imported in node.names
                )
                for node in tree.body
            ):
                msg = f"public facade import {package}.{alias} missing in {file_path}"
                raise ValueError(msg)
        qualified_names = MetadataWrapper(cst.parse_module(source)).resolve(
            QualifiedNameProvider
        )
        residue = {
            name.name
            for names in qualified_names.values()
            for name in names
            if name.name in replacements
        }
        if residue:
            msg = f"private binding residue {sorted(residue)} in {file_path}"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportValidation"]

