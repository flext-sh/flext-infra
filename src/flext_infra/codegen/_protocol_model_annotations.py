"""Project annotations from authenticated native declarations, never imports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, p, t, u


class FlextInfraCodegenProtocolModelAnnotations:
    """Resolve aliases and specializations in their original lexical scopes."""

    def __init__(
        self,
        project: p.Infra.ProjectSpec,
        workspace: p.Infra.RopeWorkspaceDsl,
        declarations: t.MappingKV[str, p.Infra.RopePyName],
    ) -> None:
        if not workspace.rope_project.authenticated_sources:
            msg = "protocol projection requires authenticated native sources"
            raise ValueError(msg)
        self.project = project
        self.workspace = workspace
        self.declarations = declarations
        self.protocol_facade = u.Infra.qualified_name(
            workspace.rope_project, "p", module_name=project.package_name
        )
        self.imports: t.MutableMappingKV[str, str] = {}
        self.dependencies: set[str] = set()
        self.references: t.MutableMappingKV[str, str] = {}
        self.owner = ""
        self.local_members: frozenset[str] = frozenset()
        self.builtin_names = (
            u.Infra
            .build_string_module(workspace.rope_project, "")
            .get_scope()
            .get_names()
        )
        self.protocol_package = (
            f"{project.package_name}.{u.Infra.facade_families()['p'].directory}"
        )

    @staticmethod
    def identity(value: p.Infra.RopePyObject) -> str:
        """Return the native qualified declaration identity.

        Returns:
            The declaration's authenticated module and lexical class route.

        Raises:
            ValueError: The declaration has no native owner or lexical scope.

        """
        module = value.get_module()
        if not isinstance(value, p.Infra.RopeSourceDefinition):
            if module is not None and u.Infra.abstract_class(value):
                return f"{module.get_name()}.{value.get_name()}"
            msg = f"declaration has no native class identity: {value.get_name()}"
            raise ValueError(msg)
        scope = value.get_scope()
        if module is None or scope is None:
            msg = f"declaration has no native source identity: {value.get_name()}"
            raise ValueError(msg)
        names = [value.get_name()]
        while scope.parent is not None:
            scope = scope.parent
            if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
                names.append(scope.pyobject.get_name())
        return f"{module.get_name()}.{'.'.join(reversed(names))}"

    def is_type(
        self, node: ast.expr, scope: p.Infra.RopeScope, module: str, name: str
    ) -> bool:
        binding = u.Infra.expression_name(scope, ast.unparse(node))
        return binding is not None and u.Infra.same_name(
            (
                self.builtin_names[name]
                if module == "builtins"
                else u.Infra.qualified_name(
                    self.workspace.rope_project, name, module_name=module
                )
            ),
            binding,
        )

    @staticmethod
    def member(binding: p.Infra.RopePyName, name: str) -> p.Infra.RopePyName | None:
        """Follow a public route through the native attribute graph.

        Returns:
            The exact published binding, or absence of that route.

        """
        for member in name.split("."):
            resolved = binding.get_object().get_attributes().get(member)
            if resolved is None:
                return None
            binding = resolved
        return binding

    alias_definition = staticmethod(u.Infra.annotation_alias_definition)

    def source(
        self,
        annotation: str,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr] | None = None,
    ) -> str:
        """Expand bound aliases and reject weak types without executing source.

        Returns:
            The source-owned structural annotation.

        """
        return ast.unparse(
            self._expression(
                ast.parse(f"({annotation})", mode="eval").body,
                scope,
                parameters if parameters is not None else {},
                (),
            )
        )

    def _expression(
        self,
        node: ast.expr,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr],
        visiting: t.StrTuple,
    ) -> ast.expr:
        if isinstance(node, ast.Constant) or (
            isinstance(node, ast.Name) and node.id in parameters
        ):
            return self._literal(node, scope, parameters, visiting)
        if isinstance(node, ast.Name | ast.Attribute | ast.Subscript):
            return self._bound_expression(node, scope, parameters, visiting)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return ast.BinOp(
                left=self._expression(node.left, scope, parameters, visiting),
                op=ast.BitOr(),
                right=self._expression(node.right, scope, parameters, visiting),
            )
        if isinstance(node, ast.Tuple | ast.List):
            values = [
                self._expression(item, scope, parameters, visiting)
                for item in node.elts
            ]
            return (
                ast.Tuple(elts=values, ctx=ast.Load())
                if isinstance(node, ast.Tuple)
                else ast.List(elts=values, ctx=ast.Load())
            )
        if isinstance(node, ast.Starred):
            return ast.Starred(
                value=self._expression(node.value, scope, parameters, visiting),
                ctx=ast.Load(),
            )
        msg = f"unsupported native protocol annotation: {ast.unparse(node)}"
        raise TypeError(msg)

    def _literal(
        self,
        node: ast.expr,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr],
        visiting: t.StrTuple,
    ) -> ast.expr:
        if isinstance(node, ast.Name):
            return parameters[node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return self._expression(
                ast.parse(node.value, mode="eval").body, scope, parameters, visiting
            )
        return node

    def _bound_expression(
        self,
        node: ast.Name | ast.Attribute | ast.Subscript,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr],
        visiting: t.StrTuple,
    ) -> ast.expr:
        primary = node.value if isinstance(node, ast.Subscript) else node
        binding = u.Infra.expression_name(scope, ast.unparse(primary))
        for module, name in (("builtins", "object"), ("typing", "Any")):
            if self.is_type(primary, scope, module, name):
                msg = f"forbidden generated protocol annotation: {module}.{name}"
                raise TypeError(msg)
        alias = self.alias_definition(binding) if binding is not None else None
        if alias is not None:
            return self._alias_expression(node, scope, parameters, visiting, alias)
        if isinstance(node, ast.Subscript):
            return self._subscript(node, scope, parameters, visiting)
        if binding is None:
            # A future public port must have both a native facade and model owner.
            root, separator, route = ast.unparse(primary).partition(".")
            declaration = self.declarations.get(route)
            if (
                separator
                and declaration is not None
                and u.Infra.same_name(
                    self.protocol_facade, u.Infra.expression_name(scope, root)
                )
            ):
                self.dependencies.add(route)
                return self._model_reference(route, declaration)
            msg = (
                f"annotation has no authenticated native identity: {ast.unparse(node)}"
            )
            raise ValueError(msg)
        return self._name_expression(node, scope, binding)

    def _subscript(
        self,
        node: ast.Subscript,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr],
        visiting: t.StrTuple,
    ) -> ast.expr:
        if self.is_type(node.value, scope, "typing", "Literal"):
            self.record_imports(ast.unparse(node.value), scope)
            return node
        if self.is_type(node.value, scope, "typing", "Annotated"):
            if not isinstance(node.slice, ast.Tuple):
                msg = "Annotated requires a native payload and metadata"
                raise ValueError(msg)
            return self._expression(node.slice.elts[0], scope, parameters, visiting)
        return ast.Subscript(
            value=self._expression(node.value, scope, parameters, visiting),
            slice=self._expression(node.slice, scope, parameters, visiting),
            ctx=ast.Load(),
        )

    def _alias_expression(
        self,
        node: ast.expr,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr],
        visiting: t.StrTuple,
        alias: t.Pair[ast.TypeAlias, p.Infra.RopeScope],
    ) -> ast.expr:
        declaration, lexical = alias
        module = lexical.pyobject.get_module()
        if module is None:
            msg = "type alias has no authenticated native module"
            raise ValueError(msg)
        identity = f"{module.get_name()}:{declaration.lineno}"
        if identity in visiting:
            msg = f"recursive alias requires a canonical public owner: {identity}"
            raise ValueError(msg)
        arguments = (
            node.slice.elts
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Tuple)
            else [node.slice]
            if isinstance(node, ast.Subscript)
            else []
        )
        specialized = self._specialize_alias(
            (declaration, identity), arguments, scope, parameters, visiting
        )
        return self._expression(
            declaration.value, lexical, specialized, (*visiting, identity)
        )

    def _specialize_alias(
        self,
        alias: t.Pair[ast.TypeAlias, str],
        arguments: t.SequenceOf[ast.expr],
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr],
        visiting: t.StrTuple,
    ) -> t.MappingKV[str, ast.expr]:
        declaration, identity = alias
        variadic = next(
            (
                index
                for index, parameter in enumerate(declaration.type_params)
                if isinstance(parameter, ast.TypeVarTuple)
            ),
            None,
        )
        if variadic is None:
            if len(arguments) != len(declaration.type_params):
                msg = f"type alias specialization has unmatched parameters: {identity}"
                raise ValueError(msg)
            return {
                self._type_parameter_name(parameter): self._expression(
                    argument, scope, parameters, visiting
                )
                for parameter, argument in zip(
                    declaration.type_params, arguments, strict=True
                )
            }
        if len(arguments) < len(declaration.type_params) - 1:
            msg = f"type alias variadic specialization is incomplete: {identity}"
            raise ValueError(msg)
        specialized: t.MutableMappingKV[str, ast.expr] = {}
        stop = len(arguments) - (len(declaration.type_params) - variadic - 1)
        for index, parameter in enumerate(declaration.type_params):
            if index == variadic:
                specialized[self._type_parameter_name(parameter)] = ast.Tuple(
                    elts=[
                        self._expression(argument, scope, parameters, visiting)
                        for argument in arguments[index:stop]
                    ],
                    ctx=ast.Load(),
                )
            else:
                argument = arguments[
                    index if index < variadic else stop + index - variadic - 1
                ]
                specialized[self._type_parameter_name(parameter)] = self._expression(
                    argument, scope, parameters, visiting
                )
        return specialized

    @staticmethod
    def _type_parameter_name(parameter: ast.type_param) -> str:
        if not isinstance(parameter, ast.TypeVar | ast.TypeVarTuple | ast.ParamSpec):
            msg = "native annotation has an unsupported type parameter declaration"
            raise TypeError(msg)
        return parameter.name

    def _name_expression(
        self,
        node: ast.Name | ast.Attribute,
        scope: p.Infra.RopeScope,
        binding: p.Infra.RopePyName,
    ) -> ast.expr:
        for name, declaration in self.declarations.items():
            published = self.member(self.protocol_facade, name)
            if declaration.get_object() is binding.get_object() or (
                published is not None and published.get_object() is binding.get_object()
            ):
                self.dependencies.add(name)
                return self._model_reference(name, declaration)
        protocol = self._protocol_reference(node, scope, binding)
        if protocol is not None:
            return protocol
        if self._local_protocol(binding):
            return ast.parse(self._declared_owner_reference(binding), mode="eval").body
        imported_roots = self.record_imports(ast.unparse(node), scope)
        root = ast.unparse(node).partition(".")[0]
        builtin = self.builtin_names.get(root)
        if root not in imported_roots and (
            builtin is None or not u.Infra.same_name(builtin, binding)
        ):
            msg = f"annotation has no public imported owner: {ast.unparse(node)}"
            raise ValueError(msg)
        return node

    def _local_protocol(self, binding: p.Infra.RopePyName) -> bool:
        value = binding.get_object()
        owner = value.get_module()
        resource = owner.get_resource() if owner is not None else None
        layout = u.Infra.layout(
            self.workspace.repository_root, rope_project=self.workspace.rope_project
        )
        return (
            layout is not None
            and resource is not None
            and Path(resource.real_path).is_relative_to(
                layout.package_dir / u.Infra.facade_families()["p"].directory
            )
            and u.Infra.qualified_name(
                self.workspace.rope_project, "Protocol", module_name="typing"
            ).get_object()
            in u.Infra.class_ancestry(value)
        )

    def _model_reference(self, name: str, declaration: p.Infra.RopePyName) -> ast.expr:
        reference = self.references.get(name)
        if reference is None:
            if not self.owner:
                return ast.Name(id=declaration.get_object().get_name(), ctx=ast.Load())
            parent = u.Infra.qualified_name(
                self.workspace.rope_project,
                f"p.{name}",
                module_name=self.project.upstream,
            )
            published = u.Infra.qualified_name(
                self.workspace.rope_project,
                f"p.{name}",
                module_name=self.project.package_name,
            )
            if not u.Infra.same_name(parent, published):
                msg = f"model dependency has no elected protocol receiver: {name}"
                raise ValueError(msg)
            statement = f"from {self.project.upstream} import p"
            self.imports[statement] = statement
            return ast.parse(f"p.{name}", mode="eval").body
        if name in self.local_members:
            reference = f"{self.owner}.{name.rpartition('.')[2]}"
        elif reference.partition(".")[0] != self.owner:
            statement = f"import {self.protocol_package}"
            self.imports[statement] = statement
            reference = f"{self.protocol_package}.{reference}"
        return ast.parse(reference, mode="eval").body

    def _protocol_reference(
        self, node: ast.expr, scope: p.Infra.RopeScope, binding: p.Infra.RopePyName
    ) -> ast.expr | None:
        root, separator, tail = ast.unparse(node).partition(".")
        root_binding = u.Infra.expression_name(scope, root)
        if (
            not separator
            or root_binding is None
            or not (
                u.Infra.same_name(self.protocol_facade, root_binding)
                or root_binding.get_object()
                in u.Infra.class_ancestry(self.protocol_facade.get_object())
            )
        ):
            return None
        upstream = u.Infra.qualified_name(
            self.workspace.rope_project, "p", module_name=self.project.upstream
        )
        selected = self.member(upstream, tail)
        if selected is not None and u.Infra.same_name(selected, binding):
            statement = f"from {self.project.upstream} import p"
            self.imports[statement] = statement
            return ast.parse(f"p.{tail}", mode="eval").body
        if u.Infra.same_name(self.protocol_facade, root_binding):
            return ast.parse(self._declared_owner_reference(binding), mode="eval").body
        msg = (
            "annotation protocol differs from the configured parent: "
            f"{ast.unparse(node)}"
        )
        raise ValueError(msg)

    def _declared_owner_reference(self, binding: p.Infra.RopePyName) -> str:
        """Use the existing same-family barrel, never reenter this project's p.

        Returns:
            The source-owned public barrel reference.

        Raises:
            ValueError: The barrel is absent or changes the declaration identity.

        """
        value = binding.get_object()
        module, scope = value.get_module(), value.get_scope()
        resource = module.get_resource() if module is not None else None
        layout = u.Infra.layout(
            self.workspace.repository_root, rope_project=self.workspace.rope_project
        )
        if (
            layout is None
            or scope is None
            or resource is None
            or not Path(resource.real_path).is_relative_to(
                layout.package_dir / u.Infra.facade_families()["p"].directory
            )
        ):
            msg = "protocol reference has no declared same-family source owner"
            raise ValueError(msg)
        parts = [value.get_name()]
        while scope.parent is not None:
            scope = scope.parent
            if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
                parts.append(scope.pyobject.get_name())
        parts.reverse()
        barrel = u.Infra.qualified_name(
            self.workspace.rope_project,
            parts[0],
            module_name=self.protocol_package,
        )
        selected = barrel
        for member in parts[1:]:
            child = selected.get_object().get_attributes().get(member)
            if child is None:
                msg = f"protocol barrel member is unresolved: {'.'.join(parts)}"
                raise ValueError(msg)
            selected = child
        if selected.get_object() is not value:
            selected_value = selected.get_object()
            selected_module = selected_value.get_module()
            selected_module_name = (
                selected_module.get_name() if selected_module is not None else None
            )
            msg = (
                "protocol barrel changes the authenticated declaration identity: "
                f"reference={self.protocol_package}.{'.'.join(parts)}; "
                f"expected_source={resource.real_path}; "
                f"selected_kind={type(selected_value).__name__}; "
                f"selected_module={selected_module_name}"
            )
            raise ValueError(msg)
        statement = f"import {self.protocol_package}"
        self.imports[statement] = statement
        return f"{self.protocol_package}.{'.'.join(parts)}"

    def record_imports(self, source: str, scope: p.Infra.RopeScope) -> set[str]:
        """Retain imports only from the authenticated declaring lexical module.

        Returns:
            The lexical names whose actual import statements were retained.

        Raises:
            ValueError: The annotation lacks an authenticated source owner.

        """
        module = scope.pyobject.get_module()
        if not u.Infra.source_module(module):
            msg = "protocol annotation has no declaring source module"
            raise ValueError(msg)
        roots = {
            source[begin:end].partition(".")[0]
            for begin, end in u.Infra.reference_regions(source)
        }
        protocol = u.Infra.expression_name(module.get_scope(), "p")
        upstream_protocol = protocol is not None and (
            u.Infra.same_name(protocol, self.protocol_facade)
            or protocol.get_object()
            in u.Infra.class_ancestry(self.protocol_facade.get_object())
        )
        imported_roots: set[str] = set()
        for information in u.Infra.native_import_infos(
            self.workspace.rope_project, module
        ):
            aliases = tuple(
                (name, alias)
                for name, alias in information.names_and_aliases
                if (alias or name.partition(".")[0]) in roots
                and not (upstream_protocol and (alias or name.partition(".")[0]) == "p")
            )
            if aliases:
                imported_roots.update(
                    alias or name.partition(".")[0] for name, alias in aliases
                )
                resource = module.get_resource()
                if resource is None:
                    msg = "annotation import has no authenticated source resource"
                    raise ValueError(msg)
                imported = (
                    u.Infra.from_import(
                        u.Infra.resolve_import_module(
                            current_package=u.Infra.package_name_for_module(
                                module.get_name(), resource
                            ),
                            module_name=information.module_name,
                            level=information.level,
                        ),
                        0,
                        aliases,
                    )
                    if isinstance(information, p.Infra.RopeFromImport)
                    else u.Infra.normal_import(aliases)
                )
                statement = imported.get_import_statement()
                self.imports[statement] = statement
        return imported_roots


__all__: list[str] = ["FlextInfraCodegenProtocolModelAnnotations"]
