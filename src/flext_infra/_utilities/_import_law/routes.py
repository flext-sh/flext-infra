"""Absolute, root-alias and lazy-export import routes of the import law.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_infra import c, m, t
from flext_infra._utilities._import_law import FlextInfraUtilitiesImportLawAst
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverBindings,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesImportLawRoutes(
    FlextInfraUtilitiesImportLawAst,
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
    def _import_law_relative_import_edits(
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
        for node in cls._import_law_iter_imports(state.tree):
            if not isinstance(node, ast.ImportFrom) or not node.level:
                continue
            base = package_parts[: len(package_parts) - (node.level - 1)]
            target = ".".join([*base, node.module or ""]).strip(".")
            indent = cls._import_law_line_indent(lines[node.lineno - 1])
            clauses = ", ".join(cls._import_law_clause(alias) for alias in node.names)
            edits.append(
                (
                    node.lineno,
                    cls._import_law_end_line(node),
                    (f"{indent}from {target} import {clauses}",),
                ),
            )
        return edits

    # -- root aliases and lazy routes -------------------------------------------------

    @classmethod
    def _import_law_route_edits(
        cls,
        state: m.Infra.ImportLawPass,
        lines: t.StrSequence,
        *,
        sources: t.MappingKV[Path, str] | None = None,
        rope_project: p.Infra.RopeProject | None = None,
        member_resolver: p.Infra.RopeSourceMemberResolver | None = None,
    ) -> t.SequenceOf[tuple[int, int, t.StrSequence]]:
        """Rewrite each ``from`` import onto its canonical lazy source.

        Returns:
            The resulting ``t.SequenceOf[tuple[int, int, t.StrSequence]]``.

        """
        return cls._import_law_native_route_edits(
            state,
            lines,
            sources=sources,
            native=(rope_project, member_resolver),
        )

    @classmethod
    def _import_law_native_route_edits(
        cls,
        state: m.Infra.ImportLawPass,
        lines: t.StrSequence,
        *,
        sources: t.MappingKV[Path, str] | None,
        native: t.Pair[
            p.Infra.RopeProject | None, p.Infra.RopeSourceMemberResolver | None
        ],
    ) -> t.SequenceOf[tuple[int, int, t.StrSequence]]:
        """Route aliases only when the declared native bindings are identical.

        Returns:
            Import edits with one provider per lexical facade binding.

        Raises:
            ValueError: If the caller did not supply its captured source project.

        """
        edits: t.MutableSequenceOf[tuple[int, int, t.StrSequence]] = []
        bindings: dict[tuple[int, str], tuple[str, str]] = {}
        rope_project, members = native
        if rope_project is None:
            message = "import routes require the captured source project"
            raise ValueError(message)
        project = rope_project

        def resolve(module: str, name: str) -> p.Infra.RopePyName | None:
            return cls.resolve_declared_binding(
                project,
                module,
                name,
                state.scope.project_root,
                sources or {},
            )

        def inherited(
            imported: t.Pair[str, ast.alias],
            root: str,
            original: p.Infra.RopePyName,
            local: p.Infra.RopePyName,
        ) -> bool:
            return cls._import_law_inherited_facade(
                state,
                imported,
                (root, original, local),
                (rope_project, members),
                sources,
            )

        # A runtime provider wins over an identical typing-only declaration.
        imports = sorted(
            cls._import_law_iter_imports(state.tree),
            key=lambda node: cls._import_law_inside_type_checking(node, state.parents),
        )
        for node in imports:
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
                    routed.setdefault(node.module, []).append(
                        cls._import_law_clause(alias)
                    )
                    continue
                root = cls._import_law_native_root_alias_source(
                    state, (node.module, alias), resolve, inherited
                )
                if cls._import_law_duplicate_alias(
                    state, (node, alias), bindings, resolve
                ):
                    continue
                routed.setdefault(
                    root
                    or cls.lazy_source(
                        state.scope, node.module, alias.name, sources=sources
                    )
                    or node.module,
                    [],
                ).append(
                    alias.asname or alias.name
                    if root is not None
                    else cls._import_law_clause(alias)
                )
            if list(routed) == [node.module] and routed[node.module] == [
                cls._import_law_clause(alias) for alias in node.names
            ]:
                continue
            indent = cls._import_law_line_indent(lines[node.lineno - 1])
            edits.append(
                (
                    node.lineno,
                    cls._import_law_end_line(node),
                    tuple(
                        f"{indent}from {module} import {', '.join(clauses)}"
                        for module, clauses in routed.items()
                    )
                    or (
                        (f"{indent}pass",)
                        if isinstance(parent := state.parents.get(id(node)), ast.If)
                        and parent.body == [node]
                        else ()
                    ),
                ),
            )
        return edits

    @classmethod
    def _import_law_inherited_facade(
        cls,
        state: m.Infra.ImportLawPass,
        imported: t.Pair[str, ast.alias],
        route: t.Triple[str, p.Infra.RopePyName, p.Infra.RopePyName],
        native: t.Pair[
            p.Infra.RopeProject | None, p.Infra.RopeSourceMemberResolver | None
        ],
        sources: t.MappingKV[Path, str] | None,
    ) -> bool:
        """Prove the local facade inherits the consumed upstream declarations.

        Returns:
            Whether native ancestry and member bindings permit the local route.

        Raises:
            ValueError: If ancestry has no source context or changes a member.

        """
        root, original, local = route
        rope_project, members = native
        if rope_project is None:
            msg = "import ancestry requires the resolved source project"
            raise ValueError(msg)
        if not (
            FlextInfraUtilitiesRopeRuntime.py_class(original.get_object())
            and FlextInfraUtilitiesRopeRuntime.py_class(local.get_object())
        ):
            return False
        module, alias = imported
        if members is None:
            captured: dict[str, t.Pair[Path, str]] = {}
            for path, text in (sources or {}).items():
                resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
                    rope_project, path
                )
                if resource is None:
                    continue
                provider = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    rope_project, resource
                )
                captured[provider.get_name()] = path, text
            members = FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver(
                rope_project, sources=captured
            )
        source = m.Infra.SourceClassReference(
            target=module,
            attributes=(alias.name,),
            qualified_base=f"{module}.{alias.name}",
        )
        target = m.Infra.SourceClassReference(
            target=root,
            attributes=(alias.asname or alias.name,),
            qualified_base=f"{root}.{alias.asname or alias.name}",
        )
        if source.qualified_base not in members.class_reaches((target,), (source,))[0]:
            return False
        paths = cls._import_law_consumed_facade_paths(state, alias.asname or alias.name)
        if paths is None:
            return False
        return cls._import_law_matching_members(state, paths, (source, target), members)

    @classmethod
    def _import_law_matching_members(
        cls,
        state: m.Infra.ImportLawPass,
        paths: t.SequenceOf[t.StrTuple],
        references: t.Pair[m.Infra.SourceClassReference, m.Infra.SourceClassReference],
        members: p.Infra.RopeSourceMemberResolver,
    ) -> bool:
        """Prove that every consumed member retains its native declaration.

        Returns:
            Whether every consumed member retains its binding.

        Raises:
            ValueError: If a local facade changes a consumed member.

        """
        source, target = references
        for path in paths:
            for index in range(1, len(path) + 1):
                prefix = path[:index]
                suffix = ".".join(prefix)
                before = members(f"{source.qualified_base}.{suffix}")
                after = members(f"{target.qualified_base}.{suffix}")
                if FlextInfraUtilitiesRopeRuntime.same_name(before, after):
                    # The same declared receiver proves every remaining
                    # attribute too, including attributes of enum instances.
                    break
                if (
                    index < len(path)
                    and FlextInfraUtilitiesRopeRuntime.py_class(before.get_object())
                    and FlextInfraUtilitiesRopeRuntime.py_class(after.get_object())
                ):
                    base = m.Infra.SourceClassReference(
                        target=source.target,
                        attributes=(*source.attributes, *prefix),
                        qualified_base=f"{source.qualified_base}.{suffix}",
                    )
                    child = m.Infra.SourceClassReference(
                        target=target.target,
                        attributes=(*target.attributes, *prefix),
                        qualified_base=f"{target.qualified_base}.{suffix}",
                    )
                    if (
                        base.qualified_base
                        in members.class_reaches((child,), (base,))[0]
                    ):
                        continue
                msg = (
                    f"{state.scope.file_path}: local facade changes consumed "
                    f"member {target.qualified_base}.{suffix}"
                )
                raise ValueError(msg)
        return True

    @classmethod
    def _import_law_native_root_alias_source(
        cls,
        state: m.Infra.ImportLawPass,
        imported: t.Pair[str, ast.alias],
        resolve: Callable[[str, str], p.Infra.RopePyName | None],
        inherited: Callable[
            [t.Pair[str, ast.alias], str, p.Infra.RopePyName, p.Infra.RopePyName],
            bool,
        ],
    ) -> str | None:
        """Prove that the role-eligible public route preserves native identity.

        Returns:
            The own public namespace, or no identity-preserving route.

        """
        module, alias = imported
        root = cls._import_law_root_alias_source(state, module, alias)
        if root is None:
            return None
        original = resolve(module, alias.name)
        local = resolve(root, alias.asname or alias.name)
        if original is None or local is None:
            return None
        return (
            root
            if FlextInfraUtilitiesRopeRuntime.same_name(original, local)
            or inherited(imported, root, original, local)
            else None
        )

    @classmethod
    def _import_law_consumed_facade_paths(
        cls, state: m.Infra.ImportLawPass, bound: str
    ) -> t.VariadicTuple[t.StrTuple] | None:
        """Read complete attribute paths reached through the module import.

        Direct class-value reads retain their original identity. Lexically
        shadowed arguments and locals never participate in the import rewrite.

        Returns:
            Consumed member paths, or no identity-preserving class-value route.

        """
        bindings, globals_ = cls._import_law_root_alias_lexical_bindings(state)
        paths: set[t.StrTuple] = set()
        for node in ast.walk(state.tree):
            if not (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == bound
            ):
                continue
            owner = cls._import_law_enclosing_scope(node, state.parents)
            visible = True
            while owner is not None:
                if bound in globals_.get(id(owner), ()):
                    break
                if bound in bindings.get(id(owner), ()):
                    visible = False
                    break
                owner = cls._import_law_enclosing_scope(owner, state.parents)
                while isinstance(owner, ast.ClassDef):
                    owner = cls._import_law_enclosing_scope(owner, state.parents)
            if not visible:
                continue
            current: ast.expr = node
            path: list[str] = []
            parent = state.parents.get(id(current))
            while isinstance(parent, ast.Attribute) and parent.value is current:
                path.append(parent.attr)
                current = parent
                parent = state.parents.get(id(current))
            if not path:
                return None
            paths.add(tuple(path))
        return tuple(sorted(paths))

    @classmethod
    def _import_law_duplicate_alias(
        cls,
        state: m.Infra.ImportLawPass,
        imported: t.Pair[ast.ImportFrom, ast.alias],
        bindings: t.MutableMappingKV[t.Pair[int, str], t.Pair[str, str]],
        resolve: Callable[[str, str], p.Infra.RopePyName | None],
    ) -> bool:
        """Reject competing native identities before eliminating a duplicate.

        Returns:
            Whether the alias already has the same native lexical provider.

        Raises:
            ValueError: If one facade binding names different or unknown objects.

        """
        node, alias = imported
        bound = alias.asname or alias.name
        if bound not in c.Infra.ALIAS_NAMES | c.Infra.IMPORT_LAW_ROOT_SINGLETONS:
            return False
        key = id(cls._import_law_enclosing_scope(node, state.parents)), bound
        current = node.module or "", alias.name
        previous = bindings.get(key)
        if previous is None:
            bindings[key] = current
            return False
        binding = resolve(*current)
        if binding is None or not FlextInfraUtilitiesRopeRuntime.same_name(
            binding, resolve(*previous)
        ):
            msg = (
                f"{state.scope.file_path}: ambiguous facade binding {bound}: "
                f"{previous} and {current}"
            )
            raise ValueError(msg)
        return True

    @classmethod
    def _import_law_root_alias_binding_edits(
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
                        if not isinstance(statement, c.Infra.AST_IMPORT_TYPES)
                    ],
                    type_ignores=[],
                ),
            ),
        )
        edits: t.MutableSequenceOf[tuple[int, int, t.StrSequence]] = []
        for node in cls._import_law_iter_imports(state.tree):
            if (
                not isinstance(node, ast.ImportFrom)
                or node.level
                or node.module != scope.namespace
                or cls._import_law_enclosing_scope(node, state.parents) is not None
            ):
                continue
            kept = [
                alias
                for alias in node.names
                if (alias.asname or alias.name) not in defined
            ]
            if len(kept) == len(node.names):
                continue
            indent = cls._import_law_line_indent(lines[node.lineno - 1])
            clauses = ", ".join(cls._import_law_clause(alias) for alias in kept)
            edits.append(
                (
                    node.lineno,
                    cls._import_law_end_line(node),
                    (f"{indent}from {scope.namespace} import {clauses}",)
                    if kept
                    else (
                        (f"{indent}pass",)
                        if isinstance(parent := state.parents.get(id(node)), ast.If)
                        and parent.body == [node]
                        else ()
                    ),
                ),
            )
        missing = (
            ()
            if scope.direct_imports
            else tuple(sorted(cls._import_law_unbound_root_aliases(state)))
        )
        if missing:
            anchor = cls._import_law_import_anchor(state.tree)
            edits.append(
                (
                    anchor + 1,
                    anchor,
                    (f"from {scope.namespace} import {', '.join(missing)}",),
                ),
            )
        return edits

    @classmethod
    def _import_law_unbound_root_aliases(
        cls, state: m.Infra.ImportLawPass
    ) -> frozenset[str]:
        """Return root aliases whose reads resolve beyond their lexical scope.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If a loaded alias requires a forbidden reverse import.

        """
        scope = state.scope
        bindings = cls._import_law_root_alias_lexical_bindings(state)
        loaded = {
            node.id
            for node in ast.walk(state.tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and cls._import_law_root_alias_read_is_unbound(node, state, bindings)
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
                (
                    provider == scope.namespace
                    or provider.startswith(f"{scope.namespace}.")
                )
                and cls.module_import_layer(provider, namespace=scope.namespace)
                > scope.layer
                and cls._import_law_runtime_uses(state, name)
            ):
                msg = (
                    f"{scope.file_path}: unbound runtime alias {name} requires "
                    "a forbidden reverse namespace import"
                )
                raise ValueError(msg)
        return missing

    @classmethod
    def _import_law_root_alias_lexical_bindings(
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
            owner = cls._import_law_enclosing_scope(node, state.parents) or state.tree
            if isinstance(node, ast.Global):
                globals_.setdefault(id(owner), set()).update(node.names)
            elif not isinstance(node, ast.Nonlocal):
                bound.setdefault(id(owner), set()).update(
                    FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(node)
                )
        return bound, globals_

    @classmethod
    def _import_law_root_alias_read_is_unbound(
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
        owner = cls._import_law_enclosing_scope(node, state.parents)
        while owner is not None:
            if node.id in globals_.get(id(owner), ()):
                break
            if node.id in bound.get(id(owner), ()):
                break
            owner = cls._import_law_enclosing_scope(owner, state.parents)
            # Class dictionaries do not enclose methods.
            while isinstance(owner, ast.ClassDef):
                owner = cls._import_law_enclosing_scope(owner, state.parents)
        else:
            return node.id not in bound.get(id(state.tree), ())
        return node.id in globals_.get(id(owner), ()) and node.id not in bound.get(
            id(state.tree), ()
        )

    @staticmethod
    def _import_law_import_anchor(tree: ast.Module) -> int:
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
            if not is_docstring and not isinstance(statement, c.Infra.AST_IMPORT_TYPES):
                break
            anchor = statement.end_lineno or statement.lineno
        return anchor

    @staticmethod
    def _import_law_root_alias_source(
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
        if (
            bound in scope.own_exports
            or bound == scope.family_letter
            or bound in scope.facade_dependencies
            or any(
                isinstance(reference, ast.Name) and reference.id == bound
                for declaration in state.tree.body
                if isinstance(declaration, c.Infra.AST_DEFINITION_TYPES)
                for parameter in declaration.type_params
                if isinstance(parameter, ast.TypeVar) and parameter.bound is not None
                for reference in ast.walk(parameter.bound)
            )
        ):
            # Retain a declaration's own role, provider and type-parameter inputs.
            return None
        return scope.namespace


__all__: list[str] = ["FlextInfraUtilitiesImportLawRoutes"]
