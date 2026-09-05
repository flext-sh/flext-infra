"""Semantic private-import cutover planning."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra._utilities.private_import_cst import (
    FlextInfraUtilitiesPrivateImportCst,
)
from flext_infra._utilities.private_import_facades import (
    FlextInfraUtilitiesPrivateImportFacades,
)
from flext_infra._utilities.private_import_validation import (
    FlextInfraUtilitiesPrivateImportValidation,
)
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesPrivateImports:
    """Plan cutovers whose public facade reference is uniquely derivable."""

    @classmethod
    def plan_private_import_cutover(
        cls,
        *,
        root: Path,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModScanFinding],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Plan binding-aware rewrites for uniquely public private imports."""
        specs: dict[Path, list[tuple[str, str, str, str, str]]] = {}
        for finding in findings:
            parsed = ast.parse(finding.text)
            statement = parsed.body[0] if len(parsed.body) == 1 else None
            if not isinstance(statement, ast.ImportFrom) or statement.level:
                continue
            private_module = statement.module or ""
            layer = FlextInfraUtilitiesPrivateImportFacades.private_layer(
                private_module
            )
            if layer is None:
                continue
            package, facade_file, facade_alias = layer
            for imported in statement.names:
                if imported.name == "*":
                    msg = f"ambiguous private star import in {finding.file}"
                    raise ValueError(msg)
                qualified = f"{private_module}.{imported.name}"
                public_reference = (
                    FlextInfraUtilitiesPrivateImportFacades.public_reference(
                        sources=sources,
                        package=package,
                        facade_file=facade_file,
                        facade_alias=facade_alias,
                        qualified=qualified,
                    )
                )
                if public_reference is None:
                    continue
                file_path = (
                    finding.file
                    if finding.file.is_absolute()
                    else root / finding.file
                ).resolve()
                specs.setdefault(file_path, []).append((
                    private_module,
                    imported.name,
                    qualified,
                    package,
                    public_reference,
                ))

        edits: list[m.Infra.SemanticMigrationEdit] = []
        for file_path, file_specs in sorted(specs.items()):
            source = sources.get(file_path)
            if source is None:
                msg = f"private import source missing from inventory: {file_path}"
                raise ValueError(msg)
            if source.startswith("# AUTO-GENERATED FILE"):
                continue
            tree = ast.parse(source, filename=str(file_path))
            removals: dict[str, set[str]] = {}
            replacements: dict[str, str] = {}
            public_imports: dict[str, str] = {}
            for private_module, symbol, qualified, package, reference in file_specs:
                facade_alias = reference.split(".", 1)[0]
                FlextInfraUtilitiesPrivateImportFacades.require_unshadowed_alias(
                    tree, package, facade_alias, file_path
                )
                previous_package = next(
                    (
                        owner
                        for owner, alias in public_imports.items()
                        if alias == facade_alias and owner != package
                    ),
                    None,
                )
                if previous_package is not None:
                    msg = (
                        f"ambiguous facade alias {facade_alias} in {file_path}: "
                        f"{previous_package}, {package}"
                    )
                    raise ValueError(msg)
                previous_reference = replacements.get(qualified)
                if previous_reference not in {None, reference}:
                    msg = f"ambiguous public reference for {qualified} in {file_path}"
                    raise ValueError(msg)
                removals.setdefault(private_module, set()).add(symbol)
                replacements[qualified] = reference
                public_imports[package] = facade_alias
            rewritten = FlextInfraUtilitiesPrivateImportCst.rewrite_private_import_source(
                source,
                removals={key: frozenset(value) for key, value in removals.items()},
                replacements=replacements,
                public_imports=public_imports,
            )
            FlextInfraUtilitiesPrivateImportValidation.require_zero_private_import_residue(
                rewritten,
                file_path=file_path,
                removals=removals,
                replacements=replacements,
                public_imports=public_imports,
            )
            if rewritten != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=file_path,
                        original_source=source,
                        updated_source=rewritten,
                        changes=tuple(
                            f"rewired {private} to {public}"
                            for private, public in sorted(replacements.items())
                        ),
                    )
                )
        return tuple(edits)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImports"]

