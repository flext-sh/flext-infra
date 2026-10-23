"""Binding-aware reference rewrites for automatic class nesting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, ImportItem
from libcst.metadata import (
    Assignment,
    CodePosition,
    CodeRange,
    ImportAssignment,
    MetadataWrapper,
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesQualifiedNames,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverNestingModuleAliases,
    FlextInfraUtilitiesSemanticNestingTypes,
)


class FlextInfraUtilitiesSemanticCutoverNestingReferences(
    FlextInfraUtilitiesSemanticCutoverNestingModuleAliases,
):
    """Rewrite imports and usages of classes moved below a module owner."""

    class _NestingTransformer(cst.CSTTransformer):
        """Rewrite one module's imports and references to the nested owners."""

        METADATA_DEPENDENCIES = (
            ParentNodeProvider,
            ScopeProvider,
            PositionProvider,
        )

        def __init__(
            self,
            *,
            module_bindings: t.Pair[
                t.MappingKV[str, t.StrMapping],
                t.MappingKV[str, p.Infra.RopeResource],
            ],
            definitions: t.StrMapping,
            native: t.Pair[p.Infra.RopeProject, p.Infra.RopeFile],
            inventory: t.Pair[str, t.MappingKV[Path, str]],
            resolvers: t.Triple[
                Callable[..., str],
                Callable[[cst.BaseStatement], str | None],
                Callable[..., t.Pair[str, str]],
            ],
        ) -> None:
            source, sources = inventory
            bindings_by_module, providers_by_module = module_bindings
            self.imported_module, self.member_name, self.import_route = resolvers
            self.bindings_by_module = bindings_by_module
            self.definitions = definitions
            self.sources = sources
            self.project, self.resource = native
            self.original = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                self.project,
                self.resource,
            )
            self.module_name = self.original.get_name()
            self.is_package_init = Path(self.resource.real_path).name == c.Infra.INIT_PY
            if source != self.original.source_code:
                msg = "nesting reference proof requires the immutable original source"
                raise ValueError(msg)
            self.line_offsets = [0]
            for line in source.splitlines(keepends=True):
                self.line_offsets.append(self.line_offsets[-1] + len(line))
            self.quoted: t.MutableMappingKV[
                t.Pair[int, int], m.Infra.SourceRewrite
            ] = {}
            self.elected_source = source
            self.identities: list[
                t.Triple[p.Infra.RopePyName, p.Infra.RopeSemanticModule, str]
            ] = []
            for module, bindings in bindings_by_module.items():
                provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                    FlextInfraUtilitiesRopeCore.resolve_pymodule(
                        self.project,
                        providers_by_module[module],
                    ),
                )
                self.identities.extend(
                    (provider.get_attribute(name), provider, f"{owner}.{name}")
                    for name, owner in bindings.items()
                )
            self.future_annotations = False
            self.wildcard_names: set[str] = set()
            self.retired_imports: set[str] = set()

        def _destination(
            self, module: str, prefix: str, scope: p.Infra.RopeScope
        ) -> str:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            root, separator, suffix = prefix.partition(".")
            if module == self.original.get_name():
                selected = prefix
            else:
                elected_module = runtime.build_string_module(
                    self.project,
                    self.elected_source,
                    resource=self.resource,
                )
                self.elected_source, selected = runtime.import_binding(
                    self.project,
                    elected_module,
                    module,
                    root,
                )
                if separator:
                    selected = f"{selected}.{suffix}"
            current = runtime.build_string_module(
                self.project,
                self.elected_source,
                resource=self.resource,
            )
            selected_root = selected.partition(".")[0]
            previous = runtime.expression_name(self.original.get_scope(), selected_root)
            elected_binding = runtime.expression_name(
                current.get_scope(), selected_root
            )
            if (
                module != self.original.get_name()
                and previous is not None
                and not runtime.same_name(previous, elected_binding)
            ):
                msg = f"occupied native nesting destination: {selected}"
                raise ValueError(msg)
            return FlextInfraUtilitiesSemanticNestingTypes.checked_type_reference(
                scope,
                selected,
            )

        def _replacement(
            self,
            scope: p.Infra.RopeScope,
            expression: str,
            offset: int,
        ) -> str | None:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            root = expression.partition(".")[0]
            actual = runtime.expression_name(scope, expression)
            matches = [
                (origin, bound)
                for identity, origin, bound in self.identities
                if runtime.same_name(identity, actual)
            ]
            root_binding = runtime.expression_name(scope, root)
            if not matches and not isinstance(root_binding, p.Infra.RopeAssignedName):
                return None
            chain = FlextInfraUtilitiesCodemodBindingChain
            proof = chain.FlextInfraUtilitiesCodemodBindingChain
            declarations = proof.single_reaching_declarations(
                self.original,
                scope,
                root,
            )
            self._reject_ambiguous_alias(expression, declarations)
            if not matches:
                return None
            FlextInfraUtilitiesSemanticNestingTypes.require_nesting_binding(
                (self.project, self.original, scope),
                expression,
                offset,
                self.sources,
            )
            replacements = {
                self._matched_destination(scope, expression, actual, match)
                for match in matches
            }
            if len(replacements) != 1:
                msg = (
                    "ambiguous native nesting destinations: "
                    f"{expression}: {sorted(replacements)}"
                )
                raise ValueError(msg)
            return replacements.pop()

        def _reject_ambiguous_alias(
            self,
            expression: str,
            declarations: t.SequenceOf[t.Pair[m.Infra.LogicalStatement, int]],
        ) -> None:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            if len(declarations) > 1:
                for row, _offset in declarations:
                    if row.category not in {
                        c.Infra.StatementCategory.IMPORT,
                        c.Infra.StatementCategory.FROM_IMPORT,
                    }:
                        continue
                    imported = runtime.build_string_module(
                        self.project,
                        row.text.strip(),
                        resource=self.resource,
                    )
                    candidate = runtime.expression_name(
                        imported.get_scope(), expression
                    )
                    if any(
                        runtime.same_name(identity, candidate)
                        for identity, _origin, _bound in self.identities
                    ):
                        msg = (
                            "ambiguous or reassigned native "
                            f"nesting alias: {expression}"
                        )
                        raise ValueError(msg)

        def _matched_destination(
            self,
            scope: p.Infra.RopeScope,
            expression: str,
            actual: p.Infra.RopePyName | None,
            match: t.Pair[p.Infra.RopeSemanticModule, str],
        ) -> str:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            origin, bound = match
            owner, member = bound.split(".", maxsplit=1)
            receiver, separator, _name = expression.rpartition(".")
            provider = origin
            if separator:
                receiver_name = runtime.expression_name(scope, receiver)
                if receiver_name is None:
                    msg = f"unresolved native nesting receiver: {expression}"
                    raise ValueError(msg)
                provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                    receiver_name.get_object(),
                )
            elif isinstance(actual, p.Infra.RopeImportedName):
                provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                    actual.imported_module.get_object(),
                )
            module, prefix = self.import_route(
                self.project,
                (provider, origin),
                owner,
                self.sources,
                consumer=self.original.get_name(),
            )
            destination = (
                f"{receiver}.{prefix}"
                if separator and module == provider.get_name()
                else self._destination(module, prefix, scope)
            )
            return f"{destination}.{member}"

        def type_reference(
            self,
            scope: p.Infra.RopeScope,
            expression: str,
        ) -> str | None:
            return self._replacement(scope, expression, len(self.original.source_code))

        def _span(self, node: cst.CSTNode) -> CodeRange:
            """Read the total position metadata through an explicit default.

            The sentinel default in libcst's ``get_metadata`` binds the return
            to the sentinel class for solvers that ignore the provider's
            element type; the explicit default restores the typed range and
            the guard keeps a missing resolution loud instead of silent.

            Returns:
                The resolved original source range.

            Raises:
                ValueError: The declared position dependency did not resolve.

            """
            span = self.get_metadata(
                PositionProvider,
                node,
                CodeRange(CodePosition(-1, -1), CodePosition(-1, -1)),
            )
            if span.start.line < 1 or span.end.line < 1:
                msg = "position metadata is declared and must resolve"
                raise ValueError(msg)
            return span

        def _quoted_literal(
            self,
            original_node: cst.BaseExpression,
            updated_node: cst.BaseExpression,
        ) -> cst.BaseExpression:
            position = self._span(original_node)
            start = self.line_offsets[position.start.line - 1] + position.start.column
            end = self.line_offsets[position.end.line - 1] + position.end.column
            edit = self.quoted.pop((start, end), None)
            return cst.parse_expression(edit.text) if edit is not None else updated_node

        @override
        def leave_SimpleString(
            self,
            original_node: cst.SimpleString,
            updated_node: cst.SimpleString,
        ) -> cst.BaseExpression:
            return self._quoted_literal(original_node, updated_node)

        @override
        def leave_ConcatenatedString(
            self,
            original_node: cst.ConcatenatedString,
            updated_node: cst.ConcatenatedString,
        ) -> cst.BaseExpression:
            return self._quoted_literal(original_node, updated_node)

        @staticmethod
        def _alias_name(asname: cst.AsName) -> str:
            """Return the bound alias identifier, rejecting impossible shapes.

            libcst types ``AsName.name`` as ``Name | Tuple | List``, but import
            aliases parsed from valid Python can only carry a ``Name``
            (``import x as (a, b)`` is a SyntaxError); Tuple/List belong to
            ``WithItem``/``ExceptHandler`` clauses only.

            Returns:
                The bound alias identifier, rejecting impossible shapes.

            Raises:
                TypeError: If unsupported import alias target.

            """
            if not isinstance(asname.name, cst.Name):
                msg = f"unsupported import alias target: {type(asname.name).__name__}"
                raise TypeError(msg)
            return asname.name.value

        def _import_module(self, node: cst.ImportFrom) -> str:
            return self.imported_module(
                node,
                module_name=self.module_name,
                is_package_init=self.is_package_init,
            )

        def _import_owner(self, node: cst.ImportFrom, name: str) -> str | None:
            """Admit an import only through its original native declaration.

            Returns:
                The original owner name, or ``None`` when the import has no
                provenance match.

            Raises:
                ValueError: When the import is a star import, has no
                    imported-name provenance, or is ambiguous.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            imported = runtime.build_string_module(
                self.project,
                cst.Module([]).code_for_node(node),
                resource=self.resource,
            )
            match node.names:
                case cst.ImportStar():
                    msg = "star import binding requires its native reference occurrence"
                    raise ValueError(msg)
                case _:
                    pass
            local = next(
                self._alias_name(alias.asname) if alias.asname else name
                for alias in node.names
                if FlextInfraUtilitiesQualifiedNames.dotted_name(alias.name) == name
            )
            actual = imported.get_scope().get_names().get(local)
            matches = [
                (origin, bound)
                for identity, origin, bound in self.identities
                if runtime.same_name(identity, actual)
            ]
            if not matches:
                return None
            match actual:
                case p.Infra.RopeImportedName():
                    provider = (
                        FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                            actual.imported_module.get_object(),
                        )
                    )
                case _:
                    msg = (
                        f"native nesting import has no imported-name provenance: {name}"
                    )
                    raise ValueError(msg)
            if len(matches) != 1:
                msg = f"ambiguous native nesting import: {provider.get_name()}.{name}"
                raise ValueError(msg)
            origin, bound = matches[0]
            owner, _member = bound.split(".", maxsplit=1)
            module, prefix = self.import_route(
                self.project,
                (provider, origin),
                owner,
                self.sources,
                consumer=self.original.get_name(),
            )
            self._destination(module, prefix, self.original.get_scope())
            return owner

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> None:

            if (
                isinstance(node.module, cst.Name)
                and node.module.value == "__future__"
                and not isinstance(node.names, cst.ImportStar)
                and any(
                    isinstance(alias.name, cst.Name)
                    and alias.name.value == "annotations"
                    for alias in node.names
                )
            ):
                self.future_annotations = True
            bindings = self.bindings_by_module.get(self._import_module(node), {})
            if not bindings:
                return
            if isinstance(node.names, cst.ImportStar):
                self.wildcard_names.update(bindings)

        def _resolves_bare_after_nesting(self, node: cst.CSTNode) -> bool:
            """Report whether a moved class stays reachable by its bare name here.

            References are rewritten before the structural move, so the current
            tree cannot answer this; the plan can. A nested class suite looks
            names up in the module globals, and the owner name is not bound
            until that class statement finishes, so the planner leaves both
            ends of an immediate suite reference at module level. A method body
            does not see the owner scope either, so there the qualified form is
            the one that resolves when the method later runs. A class header
            belongs to the suite around the class, so only a class body decides
            the name; a nested model's decorator in the owner body keeps the
            bare name of a member that moved above it. An annotation
            inside a class that is itself being nested does not resolve as a
            bare name: the undefined-name gate rejects it, including the
            class's own annotations. An annotation directly on the owner still
            sees those siblings. Walking outward, a function body therefore
            means qualify, an annotation inside a moved class means qualify,
            and any other reference that lands in the owner body keeps the
            bare name. Lazy alias values see their immediate class namespace;
            aliases inside a moved child qualify references to the outer owner.

            Returns:
                The resulting ``bool``.

            """
            child: cst.CSTNode = node
            in_annotation = False
            current: cst.CSTNode | None = self.get_metadata(
                ParentNodeProvider,
                node,
                None,
            )
            while current is not None:
                if isinstance(current, cst.Annotation | cst.TypeAlias):
                    in_annotation = True
                elif isinstance(current, cst.FunctionDef | cst.Lambda):
                    # Decorators and defaults run in the enclosing scope; only
                    # the body is a function scope. Annotations are tracked
                    # separately because a nested class does not bind its name
                    # for the undefined-name gate.
                    if child is current.body or (
                        in_annotation and self.future_annotations
                    ):
                        return False
                elif isinstance(
                    current,
                    cst.ListComp | cst.SetComp | cst.DictComp | cst.GeneratorExp,
                ):
                    return False
                elif isinstance(current, cst.ClassDef) and child is current.body:
                    name = current.name.value
                    if in_annotation and name in self.definitions:
                        return False
                    return name in self.definitions or name in set(
                        self.definitions.values(),
                    )
                elif isinstance(current, cst.Module):
                    # A moved module binding executes in the owner body.
                    return (
                        isinstance(child, cst.BaseStatement)
                        and self.member_name(child) in self.definitions
                    )
                child = current
                current = self.get_metadata(ParentNodeProvider, current, None)
            return False

        def _single_binding(
            self,
            original_node: cst.CSTNode,
        ) -> str | None:
            """Authorize one reference in the immutable original native scope.

            Returns:
                The binding root identifier, or ``None`` when the reference
                resolves to a type parameter or a non-binding shape.

            """
            if not isinstance(original_node, cst.BaseExpression):
                return None
            root = original_node
            while isinstance(root, cst.Attribute):
                root = root.value
            if self._type_parameter_root(root):
                return None
            current = self.get_metadata(ParentNodeProvider, original_node, None)
            while isinstance(current, cst.Attribute | cst.ImportAlias | cst.AsName):
                current = self.get_metadata(ParentNodeProvider, current, None)
            if isinstance(current, cst.Import | cst.ImportFrom):
                return None
            expression = FlextInfraUtilitiesQualifiedNames.dotted_name(original_node)
            if expression is None:
                return None
            position = self._span(original_node).start
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            offset = self.line_offsets[position.line - 1] + position.column
            scope = runtime.scope_at(
                self.original,
                offset,
            )
            actual = runtime.expression_name(scope, expression)
            self._validate_wildcard_binding(original_node, root, expression, actual)
            return self._replacement(scope, expression, offset)

        def _validate_wildcard_binding(
            self,
            original_node: cst.CSTNode,
            root: cst.BaseExpression,
            expression: str,
            actual: p.Infra.RopePyName | None,
        ) -> None:
            if actual is None and expression in self.wildcard_names:
                lexical = self.get_metadata(ScopeProvider, original_node, None)
                if lexical is None or not lexical[expression]:
                    msg = f"unresolved native wildcard nesting reference: {expression}"
                    raise ValueError(msg)
            if actual is None and isinstance(root, cst.Name):
                lexical = self.get_metadata(ScopeProvider, root, None)
                if (
                    lexical is not None
                    and any(
                        isinstance(binding, ImportAssignment)
                        for binding in lexical[root.value]
                    )
                    and expression in self.wildcard_names
                ):
                    msg = f"unresolved native nesting import reference: {expression}"
                    raise ValueError(msg)

        def _type_parameter_root(self, root: cst.CSTNode) -> bool:
            if not isinstance(root, cst.Name):
                return False
            scope = self.get_metadata(ScopeProvider, root, None)
            # Native assignments distinguish type parameters from module aliases.
            return scope is not None and any(
                isinstance(binding, Assignment)
                and isinstance(
                    binding.node, cst.TypeVar | cst.TypeVarTuple | cst.ParamSpec
                )
                for binding in scope[root.value]
            )

        @override
        def leave_Name(
            self,
            original_node: cst.Name,
            updated_node: cst.Name,
        ) -> cst.BaseExpression:

            parent = self.get_metadata(ParentNodeProvider, original_node)
            if FlextInfraUtilitiesQualifiedNames.rebinds_name_in_place(
                parent,
                original_node,
            ):
                return updated_node
            if (
                isinstance(
                    parent,
                    cst.ClassDef
                    | cst.FunctionDef
                    | cst.TypeAlias
                    | cst.TypeVar
                    | cst.TypeVarTuple
                    | cst.ParamSpec,
                )
                and parent.name is original_node
            ) or (
                isinstance(parent, cst.AssignTarget | cst.AnnAssign)
                and parent.target is original_node
            ):
                return updated_node
            if original_node.value in self.definitions and (
                self._resolves_bare_after_nesting(original_node)
            ):
                return updated_node
            bound = self._single_binding(original_node)
            return cst.parse_expression(bound) if bound is not None else updated_node

        @override
        def leave_Attribute(
            self,
            original_node: cst.Attribute,
            updated_node: cst.Attribute,
        ) -> cst.BaseExpression:
            bound = self._single_binding(original_node)
            if bound is None:
                return updated_node
            return cst.parse_expression(bound)

        @override
        def leave_ImportFrom(
            self,
            original_node: cst.ImportFrom,
            updated_node: cst.ImportFrom,
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:

            if isinstance(updated_node.names, cst.ImportStar):
                return updated_node
            aliases: list[cst.ImportAlias] = []
            seen: set[t.Pair[str, str]] = set()
            for imported in updated_node.names:
                name = (
                    FlextInfraUtilitiesQualifiedNames.dotted_name(imported.name) or ""
                )
                owner = self._import_owner(original_node, name)
                if owner is not None:
                    self.retired_imports.add(
                        self._alias_name(imported.asname) if imported.asname else name,
                    )
                    continue
                rewritten = imported
                identity = (
                    FlextInfraUtilitiesQualifiedNames.dotted_name(rewritten.name) or "",
                    self._alias_name(rewritten.asname) if rewritten.asname else "",
                )
                if identity not in seen:
                    seen.add(identity)
                    aliases.append(rewritten)
            if not aliases:
                return cst.RemoveFromParent()
            return updated_node.with_changes(
                names=FlextInfraUtilitiesQualifiedNames.normalized_import_aliases(
                    aliases,
                    parenthesized=bool(updated_node.lpar),
                ),
            )

        @override
        def leave_Assign(
            self,
            original_node: cst.Assign,
            updated_node: cst.Assign,
        ) -> cst.BaseSmallStatement:

            del original_node
            return FlextInfraUtilitiesQualifiedNames.filter_exports(
                updated_node,
                self.definitions.keys() | self.retired_imports,
            )

        @override
        def leave_AnnAssign(
            self,
            original_node: cst.AnnAssign,
            updated_node: cst.AnnAssign,
        ) -> cst.BaseSmallStatement:

            del original_node
            return FlextInfraUtilitiesQualifiedNames.filter_exports(
                updated_node,
                self.definitions.keys() | self.retired_imports,
            )

    @staticmethod
    def _assignment_targets(
        statement: cst.BaseSmallStatement,
    ) -> t.VariadicTuple[cst.BaseAssignTargetExpression]:
        """Return the targets one assignment statement binds.

        Returns:
            The bound targets, or an empty tuple for other statements.

        """
        targets: t.SequenceOf[cst.BaseAssignTargetExpression] = ()
        if isinstance(statement, cst.AnnAssign):
            targets = [statement.target]
        elif isinstance(statement, cst.Assign):
            targets = [item.target for item in statement.targets]
        return tuple(targets)

    @classmethod
    def _member_name(cls, node: cst.BaseStatement) -> str | None:
        """Return the name one module-level member statement defines.

        Returns:
            The class, function or single-target binding name, else ``None``.

        """
        if isinstance(node, cst.ClassDef | cst.FunctionDef):
            return node.name.value
        if not isinstance(node, cst.SimpleStatementLine) or len(node.body) != 1:
            return None
        statement = node.body[0]
        if isinstance(statement, cst.TypeAlias):
            return statement.name.value
        targets = cls._assignment_targets(statement)
        if (
            len(targets) != 1
            or not isinstance(targets[0], cst.Name)
            or (isinstance(statement, cst.AnnAssign) and statement.value is None)
        ):
            return None
        return targets[0].value

    @classmethod
    def _rewrite_class_nesting_references(
        cls,
        source: str,
        *,
        native: t.Pair[p.Infra.RopeProject, p.Infra.RopeFile],
        bindings: t.Pair[
            t.MappingKV[str, t.StrMapping],
            t.MappingKV[str, p.Infra.RopeResource],
        ],
        definitions: t.StrMapping,
        sources: t.MappingKV[Path, str],
    ) -> str:
        """Return binding-proven import and usage rewrites without effects.

        Returns:
            Binding-proven import and usage rewrites without effects.

        Raises:
            ValueError: When a native nesting quote range is left unmatched.

        """
        transformer = cls._NestingTransformer(
            module_bindings=bindings,
            definitions=definitions,
            native=native,
            inventory=(source, sources),
            resolvers=(
                cls._imported_module,
                cls._member_name,
                cls._nesting_import_route,
            ),
        )
        edits = FlextInfraUtilitiesSemanticNestingTypes.quoted_type_edits(
            native[0],
            native[1],
            source,
            transformer.type_reference,
        )
        transformer.quoted.update(((edit.start, edit.end), edit) for edit in edits)
        updated = MetadataWrapper(cst.parse_module(source)).visit(transformer)
        if transformer.quoted:
            msg = f"unmatched native nesting quote ranges: {sorted(transformer.quoted)}"
            raise ValueError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        original = runtime.module_imports_for_pymodule(native[0], transformer.original)
        elected = runtime.module_imports_for_pymodule(
            native[0],
            runtime.build_string_module(
                native[0],
                transformer.elected_source,
                resource=native[1],
            ),
        )
        insertions: list[ImportItem] = []
        for statement in elected.imports:
            info = statement.import_info
            previous = [
                old.import_info
                for old in original.imports
                if type(old.import_info) is type(info)
                and (
                    not isinstance(info, p.Infra.RopeFromImport)
                    or (
                        isinstance(old.import_info, p.Infra.RopeFromImport)
                        and old.import_info.module_name == info.module_name
                        and old.import_info.level == info.level
                    )
                )
            ]
            added = [
                pair
                for pair in info.names_and_aliases
                if not any(pair in old.names_and_aliases for old in previous)
            ]
            if added:
                insertions.extend(
                    ImportItem(
                        module_name=info.module_name,
                        obj_name=name,
                        alias=alias,
                        relative=info.level,
                    )
                    if isinstance(info, p.Infra.RopeFromImport)
                    else ImportItem(module_name=name, alias=alias)
                    for name, alias in added
                )
        if not insertions:
            return updated.code
        return (
            AddImportsVisitor(CodemodContext(), imports=insertions)
            .transform_module(updated)
            .code
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNestingReferences"]
