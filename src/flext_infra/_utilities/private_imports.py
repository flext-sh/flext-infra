"""Semantic private-import cutover planning."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m

from .private_import_cst import FlextInfraUtilitiesPrivateImportCst
from .private_import_facades import FlextInfraUtilitiesPrivateImportFacades
from .private_import_validation import FlextInfraUtilitiesPrivateImportValidation

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesPrivateImports:
    """Plan cycle-free local imports and uniquely public cross-owner cutovers."""

    @staticmethod
    def _same_owner_relative_module(
        file_path: Path, *, package: str, private_module: str
    ) -> str | None:
        """Derive the minimal relative module for a same-owner source path."""
        package_parts = tuple(package.split("."))
        target_parts = tuple(private_module.split("."))
        candidates: set[str] = set()
        path_parts = file_path.resolve().parts
        source_candidates = [
            path_parts[index + 1 :]
            for index, part in enumerate(path_parts)
            if part == c.Infra.DEFAULT_SRC_DIR
        ]
        # Repo-rooted trees (tests) import from the checkout root, so the
        # package path itself anchors the module without a src segment.
        rooted_parts = path_parts[-(len(package_parts) + 1) :]
        if (
            len(rooted_parts) == len(package_parts) + 1
            and tuple(rooted_parts[:-1]) == package_parts
        ):
            source_candidates.append(rooted_parts)
        for source_parts in source_candidates:
            if (
                len(source_parts) <= len(package_parts)
                or tuple(source_parts[: len(package_parts)]) != package_parts
            ):
                continue
            is_package_module = source_parts[-1] in {c.Infra.INIT_PY, c.Infra.INIT_PYI}
            module_parts = (
                source_parts[:-1]
                if is_package_module
                else (*source_parts[:-1], Path(source_parts[-1]).stem)
            )
            current_package = module_parts if is_package_module else module_parts[:-1]
            common = 0
            for current_part, target_part in zip(
                current_package, target_parts, strict=False
            ):
                if current_part != target_part:
                    break
                common += 1
            level = len(current_package) - common + 1
            suffix = ".".join(target_parts[common:])
            candidates.add(f"{'.' * level}{suffix}")
        if len(candidates) > 1:
            msg = f"ambiguous source owner for private import in {file_path}"
            raise ValueError(msg)
        return next(iter(candidates), None)

    @staticmethod
    def _runtime_public_aliases(
        tree: ast.Module,
        *,
        removals: t.MappingKV[str, set[str]],
        obsolete_imports: t.MappingKV[str, set[str]],
        replacements: t.StrMapping,
        public_imports: t.StrMapping,
    ) -> frozenset[str]:
        """Return facades required outside a ``TYPE_CHECKING`` boundary."""
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }

        def is_type_only(node: ast.AST) -> bool:
            parent = parents.get(node)
            while parent is not None:
                if (
                    isinstance(parent, ast.If)
                    and isinstance(parent.test, ast.Name)
                    and parent.test.id == "TYPE_CHECKING"
                ):
                    return True
                parent = parents.get(parent)
            return False

        runtime_aliases: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            aliases: set[str] = set()
            for imported in node.names:
                qualified = f"{node.module}.{imported.name}"
                if imported.name in removals.get(node.module, set()):
                    reference = replacements.get(qualified)
                    if reference is not None:
                        aliases.add(reference.split(".", 1)[0])
                elif imported.name in obsolete_imports.get(node.module, set()):
                    aliases.add(imported.asname or imported.name)
                elif (
                    imported.name in public_imports
                    and public_imports[imported.name] == node.module
                    and imported.asname is None
                ):
                    aliases.add(imported.name)
            if not is_type_only(node):
                runtime_aliases.update(aliases)
        return frozenset(runtime_aliases)

    @classmethod
    def plan_private_import_cutover(
        cls,
        *,
        root: Path,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModScanFinding],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Plan owner-aware relative and binding-aware public import rewrites."""
        facades = FlextInfraUtilitiesPrivateImportFacades.discover(sources)
        specs: dict[Path, list[tuple[str, str, str, str, str]]] = {}
        for finding in findings:
            parsed = ast.parse(finding.text)
            statement = parsed.body[0] if len(parsed.body) == 1 else None
            if not isinstance(statement, ast.ImportFrom) or statement.level:
                continue
            private_module = statement.module or ""
            package = FlextInfraUtilitiesPrivateImportFacades.private_owner(
                private_module
            )
            if package is None:
                continue
            file_path = (
                finding.file if finding.file.is_absolute() else root / finding.file
            ).resolve()
            relative_module = cls._same_owner_relative_module(
                file_path, package=package, private_module=private_module
            )
            for imported in statement.names:
                if imported.name == "*" and relative_module is None:
                    msg = f"ambiguous private star import in {finding.file}"
                    raise ValueError(msg)
                qualified = f"{private_module}.{imported.name}"
                target_reference = relative_module
                if target_reference is None:
                    target_reference = (
                        FlextInfraUtilitiesPrivateImportFacades.public_reference(
                            owners=facades.get(package, ()),
                            package=package,
                            qualified=qualified,
                        )
                    )
                if target_reference is None:
                    msg = (
                        f"no public facade exposes cross-owner private import "
                        f"{qualified} in {file_path}"
                    )
                    raise ValueError(msg)
                specs.setdefault(file_path, []).append((
                    private_module,
                    imported.name,
                    qualified,
                    package,
                    target_reference,
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
            relative_imports: dict[str, str] = {}
            relative_symbols: dict[str, set[str]] = {}
            removals: dict[str, set[str]] = {}
            obsolete_imports: dict[str, set[str]] = {}
            replacements: dict[str, str] = {}
            public_imports: dict[str, str] = {}
            for private_module, symbol, qualified, package, reference in file_specs:
                if reference.startswith("."):
                    previous_relative = relative_imports.get(private_module)
                    if previous_relative not in {None, reference}:
                        msg = (
                            f"ambiguous relative import for {private_module} "
                            f"in {file_path}"
                        )
                        raise ValueError(msg)
                    relative_imports[private_module] = reference
                    relative_symbols.setdefault(private_module, set()).add(symbol)
                    continue
                facade_alias = reference.split(".", 1)[0]
                previous_package = public_imports.get(facade_alias)
                if previous_package is not None and previous_package != package:
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
                public_imports[facade_alias] = package
            for facade_alias, package in public_imports.items():
                public_root_name = (
                    FlextInfraUtilitiesPrivateImportFacades.public_root_name(
                        owners=facades.get(package, ()), facade_alias=facade_alias
                    )
                )
                if public_root_name is not None:
                    for node in ast.walk(tree):
                        if (
                            not isinstance(node, ast.ImportFrom)
                            or node.module != package
                        ):
                            continue
                        for imported in node.names:
                            if (
                                imported.name == public_root_name
                                and imported.asname == facade_alias
                            ):
                                obsolete_imports.setdefault(package, set()).add(
                                    public_root_name
                                )
                                replacements[f"{package}.{public_root_name}"] = (
                                    facade_alias
                                )
            all_removals = {
                module: frozenset(
                    removals.get(module, set()) | obsolete_imports.get(module, set())
                )
                for module in removals.keys() | obsolete_imports.keys()
            }
            for facade_alias, package in public_imports.items():
                FlextInfraUtilitiesPrivateImportFacades.require_unshadowed_alias(
                    tree, package, facade_alias, file_path, all_removals
                )
            runtime_public_imports = cls._runtime_public_aliases(
                tree,
                removals=removals,
                obsolete_imports=obsolete_imports,
                replacements=replacements,
                public_imports=public_imports,
            )
            rewritten = (
                FlextInfraUtilitiesPrivateImportCst.rewrite_private_import_source(
                    source,
                    relative_imports=relative_imports,
                    removals={key: frozenset(value) for key, value in removals.items()},
                    obsolete_imports={
                        key: frozenset(value) for key, value in obsolete_imports.items()
                    },
                    replacements=replacements,
                    public_imports=public_imports,
                    runtime_public_imports=runtime_public_imports,
                )
            )
            FlextInfraUtilitiesPrivateImportValidation.require_zero_private_import_residue(
                rewritten,
                file_path=file_path,
                relative_imports=relative_imports,
                relative_symbols=relative_symbols,
                removals={
                    module: removals.get(module, set())
                    | obsolete_imports.get(module, set())
                    for module in removals.keys() | obsolete_imports.keys()
                },
                replacements=replacements,
                public_imports=public_imports,
            )
            if rewritten != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=file_path,
                        original_source=source,
                        updated_source=rewritten,
                        changes=(
                            *(
                                f"relativized {absolute} to {relative}"
                                for absolute, relative in sorted(
                                    relative_imports.items()
                                )
                            ),
                            *(
                                f"rewired {private} to {public}"
                                for private, public in sorted(replacements.items())
                            ),
                        ),
                    )
                )
        return tuple(edits)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImports"]
