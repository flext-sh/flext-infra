"""Rope-backed from-import alias relocation for FlextInfraUtilitiesRopeImports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import libcst as cst

from flext_infra import m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesQualifiedNames,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesRopeImportsRelocationMixin:
    """Move selected names between absolute from-imports by Rope identity."""

    @classmethod
    def relocate_from_import_aliases(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        *,
        source_module: str,
        target_module: str,
        aliases: t.StrSequence,
    ) -> str | None:
        """Move names and their bindings between absolute imports using Rope.

        The relocated source is written to ``resource`` and returned; ``None``
        means no import changed.

        Returns:
            The resulting ``str | None``.

        """
        updated = cls.plan_from_import_aliases(
            rope_project,
            resource,
            source_module=source_module,
            target_module=target_module,
            aliases=aliases,
        )
        if updated is not None:
            resource.write(updated)
        return updated

    @classmethod
    def plan_package_root_import(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        source_module: str,
        aliases: t.StrSequence,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan an own-package import without publishing or rebinding foreign names.

        The project declaration owns the target. Rope owns import bindings and
        aliases; foreign-package findings remain unmodified residue.

        Returns:
            A typed source edit, no-op, or an explicit resource/ownership failure.

        """
        entry = rope_workspace.module(file_path)
        root = entry.project_root if entry is not None else None
        if root is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].fail(
                f"import owner has no declared project: {file_path}",
            )
        own = FlextInfraUtilitiesPyproject.project_package_name(root)
        if source_module.split(".", maxsplit=1)[0] != own:
            # Foreign-package findings stay unmodified residue.
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        resource = rope_workspace.resource(file_path)
        if resource is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].fail(
                f"import owner is not a Rope resource: {file_path}",
            )
        original = resource.read()
        updated = cls.plan_from_import_aliases(
            rope_workspace.rope_project,
            resource,
            source_module=source_module,
            target_module=own,
            aliases=aliases,
        )
        if updated is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok((
            m.Infra.SemanticMigrationEdit(
                file_path=file_path.resolve(),
                original_source=original,
                updated_source=updated,
                changes=(f"bound import to declared package {own}",),
            ),
        ))

    @classmethod
    def plan_from_import_aliases(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        *,
        source_module: str,
        target_module: str,
        aliases: t.StrSequence,
    ) -> str | None:
        """Prepare scoped imports in place without changing reference text.

        Invalid Rope or CST representations propagate their native type errors.

        Returns:
            The prepared source, or None when no selected import exists.

        Raises:
            RuntimeError: If an import identity is unresolved, unsupported, or
                conflicts with a target binding in the same lexical scope.

        """
        aliases_to_move = frozenset(aliases)
        if not aliases_to_move:
            return None
        original_source: str = resource.read()
        tree = ast.parse(original_source)
        owners = (
            (source_module, rope_project.find_module(source_module)),
            (target_module, rope_project.find_module(target_module)),
        )
        # Only physical Python newlines contribute to AST line numbers.
        lines = re.split(r"(?<=\n)|(?<=\r)(?!\n)", original_source)
        imports = cls._scoped_from_imports(
            rope_project,
            resource,
            tree,
            owners,
            cls._reject_module_alias_consumers(
                rope_project,
                resource,
                lines,
                owners[0][1],
                aliases_to_move,
            ),
        )
        if owners[0][1] is None:
            for statement, module_name, _scope in imports:
                if module_name != source_module or not any(
                    name.name in aliases_to_move for name in statement.names
                ):
                    continue
                # Repeated bindings fail before unresolved source identities.
                if len({name.asname or name.name for name in statement.names}) != len(
                    statement.names,
                ):
                    msg = (
                        "conflicting Rope imported binding: "
                        f"{resource.path}:{statement.lineno}"
                    )
                    raise RuntimeError(msg)
                msg = f"unresolved Rope source module: {source_module}"
                raise RuntimeError(msg)
        changes = [
            cls._render_import_alias_statement(
                resource,
                statement,
                lines,
                target_module,
                aliases_to_move,
            )
            for statement, module_name, _scope in imports
            if module_name == source_module
            and cls._validate_import_alias_bindings(
                resource,
                statement,
                imports,
                target_module,
                aliases_to_move,
            )
        ]
        if not changes:
            return None
        return FlextInfraUtilitiesRopeSource.rewrite_source_at_offsets(
            rope_project,
            resource,
            changes,
            apply=False,
        )

    @staticmethod
    def _ast_character_offset(
        lines: t.StrSequence,
        line: int,
        column: int | None,
    ) -> int:
        """Convert a physical AST UTF-8 byte position into a Rope character offset.

        Returns:
            The character offset in the original source snapshot.

        """
        return sum(map(len, lines[: line - 1])) + len(
            lines[line - 1].encode("utf-8")[:column].decode("utf-8"),
        )

    @classmethod
    def _reject_module_alias_consumers(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        lines: t.StrSequence,
        source_resource: t.Infra.RopeResource | None,
        aliases: frozenset[str],
    ) -> t.VariadicTuple[t.Infra.RopePyName]:
        """Reject selected exports in runtime or scoped quoted type attributes.

        Returns:
            The selected export identities for subsequent star-import validation.

        Raises:
            RuntimeError: If an attribute consumes a selected source export.

        """
        selected_names = (
            tuple(
                binding
                for name, binding in FlextInfraUtilitiesRopeCore
                .resolve_pymodule(
                    rope_project,
                    source_resource,
                )
                .get_attributes()
                .items()
                if name in aliases
            )
            if source_resource is not None
            else ()
        )
        pymodule = FlextInfraUtilitiesRopeCore.resolve_pymodule(rope_project, resource)
        protected = FlextInfraUtilitiesSemanticFamilyTypeReferences.type_payload_ranges(
            "".join(lines),
            pymodule,
        )
        source = "".join(lines)
        for (
            begin,
            end,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(source):
            expression = source[begin:end]
            if "." not in expression or any(
                start <= begin < end <= stop for start, stop in protected
            ):
                continue
            binding = FlextInfraUtilitiesRopeRuntime.expression_name(
                FlextInfraUtilitiesRopeRuntime.scope_at(pymodule, begin),
                expression,
            )
            if any(
                FlextInfraUtilitiesRopeRuntime.same_name(expected, binding)
                for expected in selected_names
            ):
                msg = (
                    f"unsupported Rope module consumer: "
                    f"{resource.path}:{pymodule.lines.get_line_number(begin)}"
                )
                raise RuntimeError(msg)
        type_sources = FlextInfraUtilitiesSemanticFamilyTypeReferences
        for expression, scope, line in type_sources.scoped_quoted_type_references(
            "".join(lines),
            rope_project,
            pymodule,
        ):
            if "." not in expression:
                continue
            binding = FlextInfraUtilitiesRopeRuntime.expression_name(scope, expression)
            if any(
                FlextInfraUtilitiesRopeRuntime.same_name(expected, binding)
                for expected in selected_names
            ):
                msg = f"unsupported Rope module consumer: {resource.path}:{line}"
                raise RuntimeError(msg)
        return selected_names

    @classmethod
    def _scoped_from_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        tree: ast.Module,
        owners: t.SequenceOf[t.Pair[str, t.Infra.RopeResource | None]],
        selected_names: t.SequenceOf[t.Infra.RopePyName],
    ) -> list[t.Triple[ast.ImportFrom, str, ast.AST]]:
        """Resolve import identities and lexical scopes before planning any edit.

        Returns:
            Resolved imports and their innermost lexical scopes.

        """
        imports: list[t.Triple[ast.ImportFrom, str, ast.AST]] = []
        scopes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        ]
        for statement in ast.walk(tree):
            if not isinstance(statement, ast.ImportFrom):
                continue
            module_name = cls._relocated_from_import_module(
                rope_project,
                resource,
                statement,
                owners,
            )
            if module_name is None:
                continue
            if any(name.name == "*" for name in statement.names):
                cls._reject_star_alias_consumer(
                    rope_project,
                    resource,
                    statement,
                    module_name,
                    selected_names,
                )
            scope = max(
                (
                    candidate
                    for candidate in scopes
                    if (candidate.lineno, candidate.col_offset)
                    < (statement.lineno, statement.col_offset)
                    and statement.lineno <= (candidate.end_lineno or candidate.lineno)
                ),
                key=lambda candidate: (candidate.lineno, candidate.col_offset),
                default=tree,
            )
            imports.append((statement, module_name, scope))
        return imports

    @staticmethod
    def _relocated_from_import_module(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        owners: t.SequenceOf[t.Pair[str, t.Infra.RopeResource | None]],
    ) -> str | None:
        """Resolve relative imports by physical Rope identity, in owner order.

        Returns:
            The absolute module name, or None for an unresolved relative import.

        """
        if not statement.level:
            return statement.module or ""
        imported_resource = rope_project.find_relative_module(
            statement.module or "",
            resource.parent,
            statement.level,
        )
        if imported_resource is None:
            return None
        module_name = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            rope_project,
            imported_resource,
        ).get_name()
        return next(
            (
                name
                for name, owner in owners
                if owner is not None and imported_resource.real_path == owner.real_path
            ),
            module_name,
        )

    @staticmethod
    def _reject_star_alias_consumer(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        module_name: str,
        selected_names: t.SequenceOf[t.Infra.RopePyName],
    ) -> None:
        """Reject star imports exposing a selected Rope identity.

        Raises:
            TypeError: If the imported module has no valid module AST.
            RuntimeError: If the star import exposes a selected source export.

        """
        imported_resource = (
            rope_project.find_relative_module(
                statement.module or "",
                resource.parent,
                statement.level,
            )
            if statement.level
            else rope_project.find_module(module_name)
        )
        if imported_resource is None:
            return
        imported = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            rope_project,
            imported_resource,
        )
        imported_tree = imported.get_ast()
        if not isinstance(imported_tree, ast.Module):
            msg = f"invalid Rope module AST: {module_name}"
            raise TypeError(msg)
        exports: t.StrSequence | None = None
        for declaration in imported_tree.body:
            if not isinstance(declaration, ast.Assign | ast.AnnAssign):
                continue
            if "__all__" in (
                FlextInfraUtilitiesRopeAnalysis.assignment_target_names(declaration)
            ):
                exports = (
                    FlextInfraUtilitiesRopeAnalysis.literal_string_sequence(
                        declaration.value,
                    )
                    if isinstance(declaration.value, ast.List | ast.Tuple | ast.Set)
                    and all(
                        isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                        for element in declaration.value.elts
                    )
                    else None
                )
        # Only a sole, unescaped literal binding proves exclusion. Any extra
        # access can mutate or publish the list through an unknown writer.
        if sum(
            isinstance(node, ast.Name) and node.id == "__all__"
            for node in ast.walk(imported_tree)
        ) != 1 or any(
            (isinstance(node, ast.Constant) and node.value == "__all__")
            or (isinstance(node, ast.Attribute) and node.attr == "__all__")
            or (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"exec", "eval", "globals", "locals", "vars"}
            )
            for node in ast.walk(imported_tree)
        ):
            exports = None
        exported_names = (
            exports
            if exports is not None
            else tuple(
                name for name in imported.get_attributes() if not name.startswith("_")
            )
        )
        if any(
            FlextInfraUtilitiesRopeRuntime.same_name(expected, binding)
            for name, binding in imported.get_attributes().items()
            if name in exported_names
            for expected in selected_names
        ):
            msg = (
                "unsupported Rope module/star consumer: "
                f"{resource.path}:{statement.lineno}"
            )
            raise RuntimeError(msg)

    @staticmethod
    def _validate_import_alias_bindings(
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        imports: t.SequenceOf[t.Triple[ast.ImportFrom, str, ast.AST]],
        target_module: str,
        aliases: frozenset[str],
    ) -> bool:
        """Reject repeated or conflicting selected bindings before rendering.

        Returns:
            Whether this statement contains any selected import.

        Raises:
            RuntimeError: If source bindings repeat or conflict.

        """
        moved = [name for name in statement.names if name.name in aliases]
        if not moved:
            return False
        if len({name.asname or name.name for name in statement.names}) != len(
            statement.names,
        ):
            msg = (
                f"conflicting Rope imported binding: {resource.path}:{statement.lineno}"
            )
            raise RuntimeError(msg)
        scope = next(
            scope for imported, _module_name, scope in imports if imported is statement
        )
        for target_statement, imported_module, target_scope in imports:
            if imported_module != target_module or target_scope is not scope:
                continue
            if any(
                existing.name == "*"
                or any(
                    (existing.asname or existing.name) == (name.asname or name.name)
                    and existing.name != name.name
                    for name in moved
                )
                for existing in target_statement.names
            ):
                msg = f"ambiguous Rope target binding: {target_module}"
                raise RuntimeError(msg)
        return True

    @classmethod
    def _render_import_alias_statement(
        cls,
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        lines: t.StrSequence,
        target_module: str,
        aliases: frozenset[str],
    ) -> t.Triple[int, int, str]:
        """Render a source range with its contiguous relocated CST alias groups.

        Returns:
            The original character range and its replacement source.

        Raises:
            RuntimeError: If a mixed import occurs in an inline suite.

        """
        start = cls._ast_character_offset(lines, statement.lineno, statement.col_offset)
        end = cls._ast_character_offset(
            lines,
            statement.end_lineno or statement.lineno,
            statement.end_col_offset,
        )
        indentation = (
            lines[statement.lineno - 1]
            .encode("utf-8")[: statement.col_offset]
            .decode("utf-8")
        )
        parsed = cst.parse_module("".join(lines)[start:end] + "\n")
        replacements = cls._relocated_import_groups(
            parsed,
            target_module,
            aliases,
            f"{resource.path}:{statement.lineno}",
        )
        if len(replacements) > 1 and indentation.strip():
            msg = (
                "unsupported Rope inline mixed import: "
                f"{resource.path}:{statement.lineno}"
            )
            raise RuntimeError(msg)
        return (
            start,
            end,
            ("\n" + indentation).join(
                parsed.code_for_node(replacement) for replacement in replacements
            ),
        )

    @staticmethod
    def _relocated_import_groups(
        parsed: cst.Module,
        target_module: str,
        aliases: frozenset[str],
        location: str,
    ) -> list[cst.ImportFrom]:
        """Preserve alias ordering and trivia while splitting selected CST groups.

        Returns:
            The contiguous selected and unselected import groups.

        Raises:
            TypeError: If CST returns an invalid import representation.

        """
        line = parsed.body[0]
        if not isinstance(line, cst.SimpleStatementLine):
            msg = f"unsupported Rope import statement: {location}"
            raise TypeError(msg)
        imported_statement = line.body[0]
        if not isinstance(imported_statement, cst.ImportFrom) or isinstance(
            imported_statement.names,
            cst.ImportStar,
        ):
            msg = f"unsupported Rope import statement: {location}"
            raise TypeError(msg)
        groups: list[t.Pair[bool, list[cst.ImportAlias]]] = []
        for alias in imported_statement.names:
            selected = parsed.code_for_node(alias.name) in aliases
            if groups and groups[-1][0] == selected:
                groups[-1][1].append(alias)
            else:
                groups.append((selected, [alias]))
        return [
            imported_statement.with_changes(
                module=cst.parse_expression(target_module)
                if selected
                else imported_statement.module,
                relative=() if selected else imported_statement.relative,
                names=FlextInfraUtilitiesQualifiedNames.normalized_import_aliases(
                    names,
                    parenthesized=imported_statement.lpar is not None,
                ),
            )
            for selected, names in groups
        ]


__all__: list[str] = ["FlextInfraUtilitiesRopeImportsRelocationMixin"]
