"""Small Rope-driven text patch helpers for governed module aliases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, p
from flext_infra._utilities._rope._analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._rope._analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)


class FlextInfraUtilitiesRopeModulePatch:
    """String-level patch helpers driven by Rope-discovered module rules."""

    @staticmethod
    def runtime_alias_bindings(
        source: str,
        *,
        alias: str,
    ) -> tuple[ast.Assign | ast.AnnAssign, ...]:
        """Return only direct module bindings for the declared alias.

        Returns:
            Only direct module bindings for the declared alias.

        """
        return tuple(
            node
            for node in ast.parse(source).body
            if isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
            and any(
                isinstance(target, ast.Name) and target.id == alias
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        )

    @staticmethod
    def _unique_class_binding_root(
        bindings: MutableSequence[ast.Assign | ast.AnnAssign],
    ) -> ast.expr | None:
        """Return the root expression of one unambiguous module binding.

        Returns:
            The root expression below attribute access, or ``None`` when the
            name has no single binding carrying a value.

        """
        if len(bindings) != 1 or bindings[0].value is None:
            return None
        root: ast.expr = bindings[0].value
        while isinstance(root, ast.Attribute):
            root = root.value
        return root

    @staticmethod
    def facade_letter_names_at(
        project: p.Infra.RopeProject,
        path: Path,
    ) -> frozenset[str]:
        """Return the exported lower-case names bound directly to a class.

        A facade letter (ADR-015 R1a, ADR-018 p.1) is a published alias whose
        single module binding names a class the module declares or imports,
        e.g. ``c = FlextCliConstants`` or ``tm = FlextTestsUtilitiesMatchers.X``.
        Singleton instances (``cli = FlextCli.fetch_global()``), functions
        (``main``), and attributes of instances (``lazy.attribute``) stay in
        the namespace root that declares them and are never inherited.

        Returns:
            The exported lower-case names bound directly to a class.

        Raises:
            TypeError: If the native module exposes no module syntax tree.

        """
        module = project.get_pymodule(
            FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path),
            force_errors=True,
        )
        if not FlextInfraUtilitiesRopeRuntime.source_module(module):
            message = f"Facade export metadata has no native source module: {path}"
            raise TypeError(message)
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            message = f"facade source carries no module syntax tree: {path}"
            raise TypeError(message)
        class_names = {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        } | {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        # One parse serves every export: indexing the direct module bindings by
        # name once keeps this linear in the module size.
        bindings_by_name: MutableMapping[
            str,
            MutableSequence[ast.Assign | ast.AnnAssign],
        ] = {}
        for node in tree.body:
            if not isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for bound in {
                target.id for target in targets if isinstance(target, ast.Name)
            }:
                bindings_by_name.setdefault(bound, []).append(node)
        letters: set[str] = set()
        for (
            name
        ) in FlextInfraUtilitiesRopeAnalysisSourceScan.module_assignment_strings_source(
            module,
            c.Infra.DUNDER_ALL,
        ):
            if not name.islower() or name.startswith("_"):
                continue
            root = FlextInfraUtilitiesRopeModulePatch._unique_class_binding_root(
                bindings_by_name.get(name, []),
            )
            if isinstance(root, ast.Name) and root.id in class_names:
                letters.add(name)
        return frozenset(letters)

    @staticmethod
    def absolute_import_sources_source(source: str, *, name: str) -> Sequence[str]:
        """Return the top-level packages an absolute ``from X import`` binds name from.

        Returns:
            The top-level packages an absolute ``from X import`` binds name from.

        """
        return tuple(
            dict.fromkeys(
                node.module.split(".", 1)[0]
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module is not None
                and any((alias.asname or alias.name) == name for alias in node.names)
            ),
        )

    @classmethod
    def remove_runtime_alias_export(
        cls, source_module: p.Infra.RopeSourceModule, *, alias: str
    ) -> str:
        """Return source with one published alias letter removed from ``__all__``.

        The owner of a declared-but-unbound letter is the declaration itself:
        removing the letter repairs the published surface without inventing a
        runtime binding the module never wrote.

        Returns:
            Source with one published alias letter removed from ``__all__``.

        """
        source = source_module.source_code
        exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
            source_module
        )
        if alias not in exports:
            return source
        return cls.rewrite_all_declaration(
            source,
            names=[name for name in exports if name != alias],
        )

    @staticmethod
    def rewrite_all_declaration(source: str, *, names: list[str]) -> str:
        """Publish exactly ``names`` through the canonical ``__all__`` rewrite.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If ambiguous __all__ declarations during facade repair; or if
                facade repair requires an explicit literal __all__ declaration; or if
                __all__ declaration has no complete source span; or if __all__
                declaration shares a source line with another statement.

        """
        declarations = [
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        ]
        if len(declarations) > 1:
            message = "ambiguous __all__ declarations during facade repair"
            raise ValueError(message)
        rendered = f"__all__: list[str] = {names!r}\n"
        if not declarations:
            return source.rstrip() + "\n\n" + rendered
        declaration = declarations[0]
        if (
            isinstance(declaration, ast.AugAssign)
            or not isinstance(declaration.value, c.Infra.AST_SEQUENCE_DISPLAY_TYPES)
            or not all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in declaration.value.elts
            )
            or (isinstance(declaration, ast.Assign) and len(declaration.targets) != 1)
        ):
            message = "facade repair requires an explicit literal __all__ declaration"
            raise ValueError(message)
        lines = source.splitlines(keepends=True)
        if declaration.end_lineno is None or declaration.end_col_offset is None:
            message = "__all__ declaration has no complete source span"
            raise ValueError(message)
        if lines[declaration.lineno - 1][: declaration.col_offset].strip() or (
            (
                trailing := lines[declaration.end_lineno - 1][
                    declaration.end_col_offset :
                ].strip()
            )
            and not trailing.startswith("#")
        ):
            message = "__all__ declaration shares a source line with another statement"
            raise ValueError(message)
        lines[declaration.lineno - 1 : declaration.end_lineno] = [rendered]
        return "".join(lines)

    @staticmethod
    def ensure_from_import(source: str, *, module: str, name: str) -> str:
        """Insert one top-level from-import after the module header when absent.

        The module header is the leading docstring and import block; the
        from-import joins its end. A binding already present at module scope
        leaves the source untouched.

        Returns:
            Source with ``from <module> import <name>`` present at module scope.

        """
        for statement in ast.parse(source).body:
            if (
                isinstance(statement, ast.ImportFrom)
                and statement.level == 0
                and statement.module == module
                and any(alias.name == name for alias in statement.names)
            ):
                return source
        lines = source.splitlines(keepends=True)
        header_end = 0
        for statement in ast.parse(source).body:
            is_docstring = (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
            if not is_docstring and not isinstance(
                statement, ast.Import | ast.ImportFrom
            ):
                break
            header_end = statement.end_lineno or statement.lineno
        lines.insert(header_end, f"from {module} import {name}\n")
        return "".join(lines)


__all__: list[str] = ["FlextInfraUtilitiesRopeModulePatch"]
