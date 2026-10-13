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

    @classmethod
    def _unbound_root_aliases(cls, state: m.Infra.ImportLawPass) -> frozenset[str]:
        """Return root aliases read at module scope or below but bound nowhere.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If a loaded alias requires a forbidden reverse import.

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
        missing = frozenset(
            name
            for name in loaded - bound
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
        ):
            # A declaration retains its own role and external facade provider.
            return None
        if any(
            isinstance(reference, ast.Name) and reference.id == bound
            for declaration in state.tree.body
            if isinstance(
                declaration,
                ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
            )
            for parameter in declaration.type_params
            if isinstance(parameter, ast.TypeVar) and parameter.bound is not None
            for reference in ast.walk(parameter.bound)
        ):
            return None
        return scope.namespace

    @classmethod
    def _lazy_source(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
    ) -> str | None:
        """Return the nearest package that lazily publishes one leaf object.

        Returns:
            The publishing parent package, or ``None`` when the import already
            binds through a package or no parent publishes the name.

        """
        package = module.rpartition(".")[0]
        directory = u.Infra.import_package_dir(scope.project_root, module)
        if directory is not None:
            return cls._declared_subpackage_source(scope, module, name)
        if not package or module == scope.module:
            return None
        if u.Infra.import_lazy_exports(scope.project_root, module) is not None:
            return None
        exports = u.Infra.import_lazy_exports(scope.project_root, package)
        if exports is None or exports.get(name) != module:
            return None
        return package

    @classmethod
    def _declared_subpackage_source(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
    ) -> str | None:
        """Discover a unique source declaration published by its own package.

        Returns:
            The declaring public package, or no declared destination.

        Raises:
            ValueError: When independent declarations publish the same name.
        """
        directory = u.Infra.import_package_dir(scope.project_root, module)
        if directory is None:
            return None
        candidates: t.MutableMappingKV[str, str] = {}
        for source_path in sorted(
            directory.rglob("*.py"),
            key=lambda path: (len(path.parts), path),
        ):
            if source_path.name == c.Infra.INIT_PY:
                continue
            source = source_path.read_text(encoding=c.DEFAULT_ENCODING)
            if name not in u.Infra.public_export_names_source(source):
                continue
            declaration = cls._module_bindings(ast.parse(source)).get(name)
            if not isinstance(
                declaration,
                ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.ImportFrom,
            ):
                continue
            relative = source_path.relative_to(directory)
            owner = ".".join((module, *relative.parent.parts))
            identity = cls._declaration_identity(
                scope,
                f"{owner}.{source_path.stem}",
                name,
                frozenset(),
            )
            candidates.setdefault(identity, owner)
        ancestors = cls._declared_ancestors(scope, tuple(candidates))
        candidates = {
            identity: owner
            for identity, owner in candidates.items()
            if identity not in ancestors
        }
        if len(candidates) > 1:
            msg = (
                f"Ambiguous declared public import {module}.{name}: "
                f"{sorted(candidates)}"
            )
            raise ValueError(msg)
        return next(iter(candidates.values()), None)

    @classmethod
    def _declared_ancestors(
        cls,
        scope: m.Infra.ImportLawScope,
        identities: t.StrTuple,
    ) -> frozenset[str]:
        """Find explicit source ancestors of the published declarations.

        Returns:
            Canonical identities extended by another declaration.
        """
        ancestors: set[str] = set()
        for identity in identities:
            provider, _, symbol = identity.rpartition(".")
            parent = u.Infra.import_package_dir(
                scope.project_root,
                provider.rpartition(".")[0],
            )
            if parent is None:
                continue
            tree = ast.parse(
                (parent / f"{provider.rpartition('.')[2]}.py").read_text(
                    encoding=c.DEFAULT_ENCODING,
                ),
            )
            declaration = cls._module_bindings(tree).get(symbol)
            if not isinstance(declaration, ast.ClassDef):
                continue
            for expression in declaration.bases:
                base = (
                    expression.value
                    if isinstance(expression, ast.Subscript)
                    else expression
                )
                if isinstance(base, ast.Attribute) and base.attr != symbol:
                    continue
                receiver = base.value if isinstance(base, ast.Attribute) else base
                if not isinstance(receiver, ast.Name):
                    continue
                bound, binding = cls._declared_binding(tree, receiver.id)
                if isinstance(binding, ast.ImportFrom) and binding.module:
                    imported = next(
                        (
                            alias
                            for alias in binding.names
                            if (alias.asname or alias.name) == bound
                        ),
                        None,
                    )
                    if imported is not None and (
                        isinstance(base, ast.Attribute) or imported.name == symbol
                    ):
                        ancestors.add(
                            cls._declaration_identity(
                                scope,
                                f"{binding.module}.{imported.name}"
                                if isinstance(base, ast.Attribute)
                                else binding.module,
                                base.attr
                                if isinstance(base, ast.Attribute)
                                else imported.name,
                                frozenset(),
                            ),
                        )
        return frozenset(ancestors)

    @classmethod
    def _declared_binding(
        cls,
        tree: ast.Module,
        name: str,
    ) -> tuple[str, ast.stmt | None]:
        """Follow module-level name aliases without executing the provider.

        Returns:
            The original bound name and its declaring statement.

        Raises:
            ValueError: When aliases form a cycle.
        """
        bindings = cls._module_bindings(tree)
        seen: set[str] = set()
        while name not in seen:
            seen.add(name)
            binding = bindings.get(name)
            if not isinstance(binding, ast.Assign | ast.AnnAssign) or not isinstance(
                binding.value,
                ast.Name,
            ):
                return name, binding
            name = binding.value.id
        msg = f"Cyclic declared binding: {name}"
        raise ValueError(msg)

    @classmethod
    def _declaration_identity(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
        seen: frozenset[str],
    ) -> str:
        """Follow explicit reexports to their source, rejecting cyclic bindings.

        Returns:
            The canonical declaration's qualified identity.

        Raises:
            ValueError: When a reexport cycles or has no declared binding.
            TypeError: When the binding is not a source declaration.
        """
        identity = f"{module}.{name}"
        if identity in seen:
            msg = f"Cyclic declared public import: {identity}"
            raise ValueError(msg)
        exports = u.Infra.import_lazy_exports(scope.project_root, module)
        if exports is not None and name in exports:
            return cls._declaration_identity(
                scope,
                exports[name],
                name,
                seen | {identity},
            )
        parent = u.Infra.import_package_dir(
            scope.project_root,
            module.rpartition(".")[0],
        )
        if parent is None:
            return identity
        path = parent / f"{module.rpartition('.')[2]}.py"
        if not path.is_file():
            msg = f"Missing declared public import: {identity}"
            raise ValueError(msg)
        binding = cls._module_bindings(
            ast.parse(path.read_text(encoding=c.DEFAULT_ENCODING)),
        ).get(name)
        if isinstance(binding, ast.ImportFrom):
            alias = next(
                alias for alias in binding.names if (alias.asname or alias.name) == name
            )
            parts = module.split(".")[:-1]
            target = (
                ".".join(
                    (*parts[: len(parts) - binding.level + 1], binding.module or ""),
                ).rstrip(".")
                if binding.level
                else binding.module
            )
            if target:
                return cls._declaration_identity(
                    scope,
                    target,
                    alias.name,
                    seen | {identity},
                )
        if not isinstance(
            binding,
            ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        ):
            msg = f"Missing declared public import: {identity}"
            raise TypeError(msg)
        return identity


__all__: list[str] = ["FlextInfraImportNormalizationRoutesMixin"]
