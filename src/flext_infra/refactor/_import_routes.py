"""Absolute, root-alias and lazy-export import routes of the import law.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping

from flext_infra import c, m, t, u
from flext_infra.refactor import FlextInfraImportNormalizationAstMixin


class FlextInfraImportNormalizationRoutesMixin(
    FlextInfraImportNormalizationAstMixin,
):
    """Route every import to its canonical source module.

    Relative imports become absolute; a root alias (facade letter,
    operational letter, ``config``/``settings`` or a name the namespace root
    re-exports unchanged) binds through the importing module's own namespace
    root; a concrete object binds through the nearest package ``__init__``
    that publishes it lazily.
    """

    # -- relative -> absolute --------------------------------------------------------

    @classmethod
    def _relative_import_edits(
        cls,
        state: m.Infra.ImportLawPass,
        lines: t.StrSequence,
    ) -> t.SequenceOf[tuple[int, int, t.StrSequence]]:
        """Rewrite relative imports into their absolute form.

        Returns:
            The resulting ``t.SequenceOf[tuple[int, int, t.StrSequence]]``.

        """
        parts = state.scope.module.split(".")
        package_parts = (
            parts if state.scope.file_path.name == c.Infra.INIT_PY else parts[:-1]
        )
        edits: t.MutableSequenceOf[tuple[int, int, t.StrSequence]] = []
        for node in cls._iter_imports(state.tree):
            if not isinstance(node, ast.ImportFrom) or not node.level:
                continue
            base = package_parts[: len(package_parts) - (node.level - 1)]
            target = ".".join([*base, node.module or ""]).strip(".")
            indent = cls._line_indent(lines[node.lineno - 1])
            clauses = ", ".join(cls._clause(alias) for alias in node.names)
            edits.append(
                (
                    node.lineno,
                    cls._end_line(node),
                    (f"{indent}from {target} import {clauses}",),
                ),
            )
        return edits

    # -- root aliases and lazy routes -------------------------------------------------

    @classmethod
    def _route_edits(
        cls,
        state: m.Infra.ImportLawPass,
        lines: t.StrSequence,
    ) -> t.SequenceOf[tuple[int, int, t.StrSequence]]:
        """Rewrite each ``from`` import onto its canonical lazy source.

        Returns:
            The resulting ``t.SequenceOf[tuple[int, int, t.StrSequence]]``.

        """
        if state.scope.direct_imports:
            return ()
        edits: t.MutableSequenceOf[tuple[int, int, t.StrSequence]] = []
        for node in cls._iter_imports(state.tree):
            if not isinstance(node, ast.ImportFrom) or node.level or not node.module:
                continue
            routed: MutableMapping[str, list[str]] = {}
            for alias in node.names:
                root = cls._root_alias_source(state, node.module, alias)
                if root is not None:
                    # The root publishes the alias under its bound name, so the
                    # long class spelling (``TestsFooConstants as c``) collapses
                    # to the published letter.
                    routed.setdefault(root, []).append(alias.asname or alias.name)
                    continue
                source = cls._lazy_source(state.scope, node.module, alias.name)
                routed.setdefault(source or node.module, []).append(
                    cls._clause(alias),
                )
            if list(routed) == [node.module]:
                continue
            indent = cls._line_indent(lines[node.lineno - 1])
            edits.append(
                (
                    node.lineno,
                    cls._end_line(node),
                    tuple(
                        f"{indent}from {module} import {', '.join(clauses)}"
                        for module, clauses in routed.items()
                    ),
                ),
            )
        return edits

    @classmethod
    def _root_alias_binding_edits(
        cls,
        state: m.Infra.ImportLawPass,
        lines: t.StrSequence,
    ) -> t.SequenceOf[tuple[int, int, t.StrSequence]]:
        """Bind root aliases a module reads but never binds; drop self-imports.

        A facade letter or root singleton the module reads, binds nowhere and
        its namespace root publishes is imported from that root; an alias the
        module imports from its own root while also defining it at module level
        is dropped, because the module owns it.

        Returns:
            The resulting ``t.SequenceOf[tuple[int, int, t.StrSequence]]``.

        """
        if state.scope.direct_imports:
            return ()
        scope = state.scope
        defined = frozenset(
            cls._module_bindings(
                ast.Module(
                    body=[
                        statement
                        for statement in state.tree.body
                        if not isinstance(statement, ast.Import | ast.ImportFrom)
                    ],
                    type_ignores=[],
                ),
            ),
        )
        edits: t.MutableSequenceOf[tuple[int, int, t.StrSequence]] = []
        for node in state.tree.body:
            if (
                not isinstance(node, ast.ImportFrom)
                or node.level
                or node.module != scope.namespace
            ):
                continue
            kept = [
                alias
                for alias in node.names
                if (alias.asname or alias.name) not in defined
            ]
            if len(kept) == len(node.names):
                continue
            indent = cls._line_indent(lines[node.lineno - 1])
            clauses = ", ".join(cls._clause(alias) for alias in kept)
            edits.append(
                (
                    node.lineno,
                    cls._end_line(node),
                    (f"{indent}from {scope.namespace} import {clauses}",)
                    if kept
                    else (),
                ),
            )
        missing = sorted(cls._unbound_root_aliases(state))
        if missing:
            anchor = cls._import_anchor(state.tree)
            edits.append(
                (
                    anchor + 1,
                    anchor,
                    (f"from {scope.namespace} import {', '.join(missing)}",),
                ),
            )
        return edits

    @staticmethod
    def _unbound_root_aliases(state: m.Infra.ImportLawPass) -> frozenset[str]:
        """Return root aliases read at module scope or below but bound nowhere.

        Returns:
            The resulting ``frozenset[str]``.

        """
        scope = state.scope
        loaded: set[str] = set()
        bound: set[str] = set(state.bindings)
        for node in ast.walk(state.tree):
            match node:
                case ast.Name(id=name, ctx=ast.Load()):
                    loaded.add(name)
                case ast.Name(id=name):
                    bound.add(name)
                case ast.arg(arg=name):
                    bound.add(name)
                case (
                    ast.FunctionDef(name=name)
                    | ast.AsyncFunctionDef(name=name)
                    | ast.ClassDef(name=name)
                ):
                    bound.add(name)
                case ast.Import(names=aliases) | ast.ImportFrom(names=aliases):
                    bound.update(
                        alias.asname or alias.name.partition(".")[0]
                        for alias in aliases
                    )
                case _:
                    pass
        aliases = c.Infra.ALIAS_NAMES | c.Infra.IMPORT_LAW_ROOT_SINGLETONS
        return frozenset(
            name
            for name in loaded - bound
            if name in aliases
            and name in state.root_exports
            and name not in scope.own_exports
            and name != scope.family_letter
            and name not in scope.facade_dependencies
        )

    @staticmethod
    def _import_anchor(tree: ast.Module) -> int:
        """Return the line after which a new module-level import belongs.

        Returns:
            The last line of the leading docstring and import block.

        """
        anchor = 0
        for index, statement in enumerate(tree.body):
            is_docstring = (
                index == 0
                and isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
            if not is_docstring and not isinstance(
                statement,
                ast.Import | ast.ImportFrom,
            ):
                break
            anchor = statement.end_lineno or statement.lineno
        return anchor

    @staticmethod
    def _root_alias_source(
        state: m.Infra.ImportLawPass,
        module: str,
        alias: ast.alias,
    ) -> str | None:
        """Return the namespace root when one binding is a root alias.

        Facade declarations and their runtime dependencies retain external
        providers instead of importing the facade they are constructing.

        Returns:
            The namespace root, or ``None`` when the binding is no root alias.

        """
        scope = state.scope
        bound = alias.asname or alias.name
        published = state.root_exports.get(bound)
        if module == scope.namespace or published is None:
            return None
        aliases = c.Infra.ALIAS_NAMES | c.Infra.IMPORT_LAW_ROOT_SINGLETONS
        if bound not in aliases and published != module:
            return None
        if (
            bound in scope.own_exports
            or bound == scope.family_letter
            or bound in scope.facade_dependencies
        ):
            return None
        if (
            scope.family_letter is not None
            and bound in c.Infra.ALIAS_NAMES
            and not module.startswith(f"{scope.namespace}.")
        ):
            # Declaration families must retain an external facade's provider.
            # Routing its base models/utilities back through self creates a cycle.
            return None
        return scope.namespace

    @staticmethod
    def _lazy_source(
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
    ) -> str | None:
        """Return the nearest package that lazily publishes one leaf object.

        Returns:
            The publishing parent package, or ``None`` when the import already
            binds through a package or no parent publishes the name.

        """
        package, _, leaf = module.rpartition(".")
        if not package or module == scope.module:
            return None
        package_dir = u.Infra.import_package_dir(scope.project_root, package)
        if package_dir is None or (package_dir / leaf).is_dir():
            return None
        if u.Infra.import_lazy_exports(package_dir, package).get(name) != module:
            return None
        return package


__all__: list[str] = ["FlextInfraImportNormalizationRoutesMixin"]
