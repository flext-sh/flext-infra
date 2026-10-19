"""Absolute, root-alias and lazy-export import routes of the import law.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.refactor import FlextInfraImportNormalizationAstMixin

if TYPE_CHECKING:
    from pathlib import Path


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
        *,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> t.SequenceOf[tuple[int, int, t.StrSequence]]:
        """Rewrite each ``from`` import onto its canonical lazy source.

        Returns:
            The resulting ``t.SequenceOf[tuple[int, int, t.StrSequence]]``.

        """
        edits: t.MutableSequenceOf[tuple[int, int, t.StrSequence]] = []
        for node in cls._iter_imports(state.tree):
            if not isinstance(node, ast.ImportFrom) or node.level or not node.module:
                continue
            routed: MutableMapping[str, list[str]] = {}
            for alias in node.names:
                if state.scope.direct_imports and (
                    node.module == state.scope.namespace
                    or node.module.startswith(f"{state.scope.namespace}.")
                ):
                    # The declaration relocation owner must move the dependency;
                    # lazy routing cannot make an own-namespace edge legal.
                    routed.setdefault(node.module, []).append(cls._clause(alias))
                    continue
                root = cls._root_alias_source(state, node.module, alias)
                if root is not None:
                    # The root publishes the alias under its bound name, so the
                    # long class spelling (``TestsFooConstants as c``) collapses
                    # to the published letter.
                    routed.setdefault(root, []).append(alias.asname or alias.name)
                    continue
                source = cls.lazy_source(
                    state.scope, node.module, alias.name, sources=sources
                )
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
        missing = (
            ()
            if scope.direct_imports
            else tuple(sorted(cls._unbound_root_aliases(state)))
        )
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

    @classmethod
    def _unbound_root_aliases(cls, state: m.Infra.ImportLawPass) -> frozenset[str]:
        """Return root aliases whose reads resolve beyond their lexical scope.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If a loaded alias requires a forbidden reverse import.

        """
        scope = state.scope
        bindings = cls._root_alias_lexical_bindings(state)
        loaded = {
            node.id
            for node in ast.walk(state.tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and cls._root_alias_read_is_unbound(node, state, bindings)
        }
        aliases = c.Infra.ALIAS_NAMES | c.Infra.IMPORT_LAW_ROOT_SINGLETONS
        missing = frozenset(
            name
            for name in loaded
            if name in aliases
            and name in state.root_exports
            and name not in scope.own_exports
            and name != scope.family_letter
            and name not in scope.facade_dependencies
        )
        for name in missing:
            provider = state.root_exports[name]
            if (
                provider.split(".")[0] == scope.namespace
                and u.Infra.module_import_layer(provider) > scope.layer
                and cls._runtime_uses(state.tree, name, state.parents)
            ):
                msg = (
                    f"{scope.file_path}: unbound runtime alias {name} requires "
                    "a forbidden reverse namespace import"
                )
                raise ValueError(msg)
        return missing

    @classmethod
    def _root_alias_lexical_bindings(
        cls,
        state: m.Infra.ImportLawPass,
    ) -> t.Pair[t.MappingKV[int, set[str]], t.MappingKV[int, set[str]]]:
        """Record native lexical bindings and explicit globals for each scope.

        Returns:
            The same per-scope bound and global name sets used by read resolution.

        """
        bound: dict[int, set[str]] = {}
        globals_: dict[int, set[str]] = {}
        for node in ast.walk(state.tree):
            owner = cls._enclosing_scope(node, state.parents) or state.tree
            if isinstance(node, ast.Global):
                globals_.setdefault(id(owner), set()).update(node.names)
            elif not isinstance(node, ast.Nonlocal):
                bound.setdefault(id(owner), set()).update(
                    u.Infra.bound_identifiers(node)
                )
        return bound, globals_

    @classmethod
    def _root_alias_read_is_unbound(
        cls,
        node: ast.Name,
        state: m.Infra.ImportLawPass,
        bindings: t.Pair[t.MappingKV[int, set[str]], t.MappingKV[int, set[str]]],
    ) -> bool:
        """Resolve a loaded name through lexical owners and explicit global edges.

        Returns:
            Whether this exact read reaches an unbound module-level name.

        """
        bound, globals_ = bindings
        owner = cls._enclosing_scope(node, state.parents)
        while owner is not None:
            if node.id in globals_.get(id(owner), ()):
                break
            if node.id in bound.get(id(owner), ()):
                break
            owner = cls._enclosing_scope(owner, state.parents)
            # Class dictionaries do not enclose methods.
            while isinstance(owner, ast.ClassDef):
                owner = cls._enclosing_scope(owner, state.parents)
        else:
            return node.id not in bound.get(id(state.tree), ())
        return node.id in globals_.get(id(owner), ()) and node.id not in bound.get(
            id(state.tree), ()
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
        Renamed facade letters retain their original provider and binding until
        a semantic reference cutover can remove the local alias atomically.

        Returns:
            The namespace root, or ``None`` when the binding is no root alias.

        """
        scope = state.scope
        if scope.direct_imports:
            return None
        bound = alias.asname or alias.name
        aliases = c.Infra.ALIAS_NAMES | c.Infra.IMPORT_LAW_ROOT_SINGLETONS
        if bound != alias.name and (alias.name in aliases or bound not in aliases):
            # The imported letter owns the role, not its local spelling: m as tm
            # is still models even when the root publishes tm as matchers.
            # A shared provider module also does not prove two exports identical.
            return None
        published = state.root_exports.get(bound)
        if module == scope.namespace or published is None:
            return None
        renamed_external = alias.name != bound and not published.startswith(
            f"{scope.namespace}.",
        )
        different_provider = (bound not in aliases or alias.name != bound) and (
            published != module
        )
        if renamed_external or different_provider:
            return None
        external_family = (
            scope.family_letter is not None
            and bound in c.Infra.ALIAS_NAMES
            and not module.startswith(f"{scope.namespace}.")
        )
        if (
            bound in scope.own_exports
            or bound == scope.family_letter
            or bound in scope.facade_dependencies
            or external_family
            or any(
                isinstance(reference, ast.Name) and reference.id == bound
                for declaration in state.tree.body
                if isinstance(
                    declaration,
                    ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
                )
                for parameter in declaration.type_params
                if isinstance(parameter, ast.TypeVar) and parameter.bound is not None
                for reference in ast.walk(parameter.bound)
            )
        ):
            # Retain a declaration's own role, provider and type-parameter inputs.
            return None
        return scope.namespace


__all__: list[str] = ["FlextInfraImportNormalizationRoutesMixin"]
