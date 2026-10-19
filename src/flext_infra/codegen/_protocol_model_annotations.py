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
        self.imports: dict[str, str] = {}
        self.dependencies: set[str] = set()
        self.references: dict[str, str] = {}
        self.owner = ""
        self.local_members: frozenset[str] = frozenset()
        self.protocol_package = (
            f"{project.package_name}.{u.Infra.facade_families()['p'].directory}"
        )

    @staticmethod
    def identity(value: p.Infra.RopePyObject) -> str:
        """Return the native qualified declaration identity."""
        module = value.get_module()
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
        return u.Infra.same_name(
            u.Infra.qualified_name(
                self.workspace.rope_project, name, module_name=module
            ),
            u.Infra.expression_name(scope, ast.unparse(node)),
        )

    @staticmethod
    def alias_definition(
        binding: p.Infra.RopePyName,
    ) -> tuple[ast.TypeAlias, p.Infra.RopeScope] | None:
        """Locate a PEP 695 alias in its original native module."""
        module, line = u.Infra.definition_location(binding)
        if not u.Infra.source_module(module) or line is None:
            return None
        for node in ast.walk(module.get_ast()):
            if isinstance(node, ast.TypeAlias) and node.lineno == line:
                return node, u.Infra.scope_at(
                    module, u.Infra.source_offset(module.source_code, node)
                )
        return None

    def source(
        self,
        annotation: str,
        scope: p.Infra.RopeScope,
        parameters: t.MappingKV[str, ast.expr] | None = None,
    ) -> str:
        """Expand bound aliases and reject weak types without executing source."""
        return ast.unparse(
            self._expression(
                ast.parse(annotation, mode="eval").body,
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
        visiting: tuple[str, ...],
    ) -> ast.expr:
        if isinstance(node, ast.Name) and node.id in parameters:
            return parameters[node.id]
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return self._expression(
                    ast.parse(node.value, mode="eval").body,
                    scope,
                    parameters,
                    visiting,
                )
            return node
        if isinstance(node, ast.Name | ast.Attribute | ast.Subscript):
            primary = node.value if isinstance(node, ast.Subscript) else node
            binding = u.Infra.expression_name(scope, ast.unparse(primary))
            for module, name in (("builtins", "object"), ("typing", "Any")):
                if self.is_type(primary, scope, module, name):
                    msg = f"forbidden generated protocol annotation: {module}.{name}"
                    raise TypeError(msg)
            alias = self.alias_definition(binding) if binding is not None else None
            if alias is not None:
                declaration, lexical = alias
                module = lexical.pyobject.get_module()
                if module is None:
                    msg = "type alias has no authenticated native module"
                    raise ValueError(msg)
                identity = f"{module.get_name()}:{declaration.lineno}"
                if identity in visiting:
                    msg = (
                        f"recursive alias requires a canonical public owner: {identity}"
                    )
                    raise ValueError(msg)
                arguments = (
                    node.slice.elts
                    if isinstance(node, ast.Subscript)
                    and isinstance(node.slice, ast.Tuple)
                    else [node.slice]
                    if isinstance(node, ast.Subscript)
                    else []
                )
                variadic = next(
                    (
                        index
                        for index, parameter in enumerate(declaration.type_params)
                        if isinstance(parameter, ast.TypeVarTuple)
                    ),
                    None,
                )
                if variadic is None and len(arguments) != len(declaration.type_params):
                    msg = f"type alias specialization has unmatched parameters: {identity}"
                    raise ValueError(msg)
                specialized: dict[str, ast.expr] = {}
                if variadic is None:
                    specialized = {
                        parameter.name: self._expression(
                            argument, scope, parameters, visiting
                        )
                        for parameter, argument in zip(
                            declaration.type_params, arguments, strict=True
                        )
                    }
                else:
                    trailing = len(declaration.type_params) - variadic - 1
                    if len(arguments) < len(declaration.type_params) - 1:
                        msg = f"type alias variadic specialization is incomplete: {identity}"
                        raise ValueError(msg)
                    stop = len(arguments) - trailing
                    for index, parameter in enumerate(declaration.type_params):
                        if index == variadic:
                            specialized[parameter.name] = ast.Tuple(
                                elts=[
                                    self._expression(
                                        argument, scope, parameters, visiting
                                    )
                                    for argument in arguments[index:stop]
                                ],
                                ctx=ast.Load(),
                            )
                        else:
                            argument = arguments[
                                index
                                if index < variadic
                                else stop + index - variadic - 1
                            ]
                            specialized[parameter.name] = self._expression(
                                argument, scope, parameters, visiting
                            )
                return self._expression(
                    declaration.value, lexical, specialized, (*visiting, identity)
                )
            if isinstance(node, ast.Subscript):
                if self.is_type(primary, scope, "typing", "Literal"):
                    self.record_imports(ast.unparse(primary), scope)
                    return node
                if self.is_type(primary, scope, "typing", "Annotated"):
                    if not isinstance(node.slice, ast.Tuple):
                        msg = "Annotated requires a native payload and metadata"
                        raise ValueError(msg)
                    return self._expression(
                        node.slice.elts[0], scope, parameters, visiting
                    )
                return ast.Subscript(
                    value=self._expression(primary, scope, parameters, visiting),
                    slice=self._expression(node.slice, scope, parameters, visiting),
                    ctx=ast.Load(),
                )
            if binding is None:
                msg = f"annotation has no authenticated native identity: {ast.unparse(node)}"
                raise ValueError(msg)
            for name, declaration in self.declarations.items():
                published: p.Infra.RopePyName | None = self.protocol_facade
                for member in name.split("."):
                    published = (
                        published.get_object().get_attributes().get(member)
                        if published is not None
                        else None
                    )
                if u.Infra.same_name(declaration, binding) or u.Infra.same_name(
                    published, binding
                ):
                    self.dependencies.add(name)
                    reference = self.references.get(name)
                    if reference is None:
                        if self.owner:
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
                            return ast.parse(f"p.{name}", mode="eval").body
                        return ast.Name(
                            id=declaration.get_object().get_name(), ctx=ast.Load()
                        )
                    if name in self.local_members:
                        reference = f"{self.owner}.{name.rpartition('.')[2]}"
                    elif reference.partition(".")[0] != self.owner:
                        statement = f"import {self.protocol_package}"
                        self.imports[statement] = statement
                        reference = f"{self.protocol_package}.{reference}"
                    return ast.parse(reference, mode="eval").body
            root, separator, tail = ast.unparse(node).partition(".")
            root_binding = u.Infra.expression_name(scope, root)
            if (
                separator
                and root_binding is not None
                and (
                    u.Infra.same_name(self.protocol_facade, root_binding)
                    or root_binding.get_object()
                    in u.Infra.class_ancestry(self.protocol_facade.get_object())
                )
            ):
                upstream = u.Infra.qualified_name(
                    self.workspace.rope_project, "p", module_name=self.project.upstream
                )
                selected: p.Infra.RopePyName | None = upstream
                for component in tail.split("."):
                    selected = (
                        selected.get_object().get_attributes().get(component)
                        if selected is not None
                        else None
                    )
                if u.Infra.same_name(selected, binding):
                    return ast.parse(f"p.{tail}", mode="eval").body
                if u.Infra.same_name(self.protocol_facade, root_binding):
                    return ast.parse(
                        self._declared_owner_reference(binding), mode="eval"
                    ).body
                if not u.Infra.same_name(selected, binding):
                    msg = f"annotation protocol differs from the configured parent: {ast.unparse(node)}"
                    raise ValueError(msg)
            imported_roots = self.record_imports(ast.unparse(node), scope)
            root = ast.unparse(node).partition(".")[0]
            builtin = (
                self.workspace.rope_project
                .get_module("builtins")
                .get_attributes()
                .get(root)
            )
            if root not in imported_roots and not u.Infra.same_name(builtin, binding):
                msg = f"annotation has no public imported owner: {ast.unparse(node)}"
                raise ValueError(msg)
            return node
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

    def _declared_owner_reference(self, binding: p.Infra.RopePyName) -> str:
        """Use the existing same-family barrel, never reenter this project's p."""
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
        if not u.Infra.same_name(selected, binding):
            msg = "protocol barrel changes the authenticated declaration identity"
            raise ValueError(msg)
        statement = f"import {self.protocol_package}"
        self.imports[statement] = statement
        return f"{self.protocol_package}.{'.'.join(parts)}"

    def record_imports(self, source: str, scope: p.Infra.RopeScope) -> set[str]:
        """Retain imports only from the authenticated declaring lexical module."""
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
