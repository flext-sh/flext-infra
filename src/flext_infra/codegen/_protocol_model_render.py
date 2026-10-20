"""Render structural protocol classes for the generated ``p`` layer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
from textwrap import dedent, indent

from flext_infra import c, config, p, t, u
from flext_infra.codegen import FlextInfraCodegenProtocolModelAnnotations


class FlextInfraCodegenProtocolModelRender(FlextInfraCodegenProtocolModelAnnotations):
    """Render structural protocols and their generated-file modules."""

    def render_member_modules(
        self,
        models: t.MappingKV[str, p.Infra.RopePyName],
        protocol_directory: Path,
        aliases: t.MappingKV[str, str],
    ) -> t.MappingKV[Path, str]:
        """Render source-bound declarations and their composing owner modules.

        Returns:
            The resulting ``t.MappingKV[Path, str]``.

        Raises:
            ValueError: If model declaration has no native scope; or if protocol
                declaration exceeds configured LOC cap.

        """
        self.references = {
            name: (
                f"{self.project.class_stem}"
                f"{name.rpartition('.')[0].replace('.', '')}"
                f"ProtocolsGeneratedModels.{name.rpartition('.')[2]}"
            )
            for name in models
        }
        graph: dict[str, set[str]] = {}
        for name, model in sorted(models.items()):
            declaration = self.declarations[name].get_object()
            scope = declaration.get_scope()
            if scope is None:
                msg = f"model declaration has no native scope: {name}"
                raise ValueError(msg)
            self.dependencies.clear()
            self.render_protocol(name.rpartition(".")[2], model, scope)
            graph[name] = self.dependencies.intersection(models)
        components = {
            min(component): tuple(sorted(component))
            for component in u.Infra.strongly_connected_components(graph)
        }
        component_for = {
            name: key for key, names in components.items() for name in names
        }
        ordered = u.Infra.dependency_order(
            tuple(sorted(components)),
            dependencies=lambda key: tuple(
                sorted({
                    component_for[dependency]
                    for name in components[key]
                    for dependency in graph[name]
                    if component_for[dependency] != key
                })
            ),
            normalize=lambda name: name,
        )
        modules: t.MutableMappingKV[Path, str] = {}
        grouped: dict[str, list[str]] = defaultdict(list)
        for key in ordered:
            for name in components[key]:
                grouped[name.rpartition(".")[0]].append(name)
        for name in aliases:
            grouped.setdefault(name.rpartition(".")[0], [])
        for namespace, names in grouped.items():
            self._render_namespace(
                protocol_directory, (namespace, names), models, aliases, modules
            )
        for path, content in modules.items():
            if len(content.splitlines()) > config.Infra.codegen.loc_cap.max_lines:
                msg = f"protocol module exceeds configured LOC cap: {path}"
                raise ValueError(msg)
        return modules

    def _render_namespace(
        self,
        directory: Path,
        group: tuple[str, list[str]],
        models: t.MappingKV[str, p.Infra.RopePyName],
        aliases: t.MappingKV[str, str],
        modules: t.MutableMappingKV[Path, str],
    ) -> None:
        """Render budgeted parts and the composing owner for one namespace.

        Raises:
            ValueError: If a single declaration exceeds the configured LOC cap.

        """
        namespace, names = group
        parts: list[tuple[str, str]] = []
        token = namespace.replace(".", "_").lower()
        stem = f"generated_models_{token}" if token else "generated_models"
        members: list[str] = []
        chunk = ""
        for name in names:
            self.owner = (
                f"{self.project.class_stem}ProtocolsGeneratedPart{len(modules) + 1:02d}"
            )
            body = self._render_chunk((*members, name), models)
            header = self._module_header(self.project, self.imports)
            if chunk and (
                header.count("\n") + body.count("\n") + 4
                > config.Infra.codegen.loc_cap.max_lines
            ):
                previous = self._render_chunk(tuple(members), models)
                self._append_part(
                    modules,
                    parts,
                    directory / stem,
                    previous,
                    self._module_header(self.project, self.imports),
                )
                members = []
                self.owner = (
                    f"{self.project.class_stem}"
                    f"ProtocolsGeneratedPart{len(modules) + 1:02d}"
                )
                body = self._render_chunk((name,), models)
                header = self._module_header(self.project, self.imports)
            if (
                header.count("\n") + body.count("\n") + 4
                > config.Infra.codegen.loc_cap.max_lines
            ):
                msg = f"protocol declaration exceeds configured LOC cap: {namespace}"
                raise ValueError(msg)
            members.append(name)
            chunk = body
        if chunk:
            self._append_part(
                modules,
                parts,
                directory / stem,
                chunk,
                self._module_header(self.project, self.imports),
            )
        modules[directory / f"{stem}.py"] = self._render_aggregate(
            namespace, parts, aliases
        )

    def _render_aggregate(
        self,
        namespace: str,
        parts: list[tuple[str, str]],
        aliases: t.MappingKV[str, str],
    ) -> str:
        """Compose generated parts and native aliases without changing their order.

        Returns:
            The complete aggregate owner module.

        Raises:
            ValueError: If an alias has no authenticated source declaration.

        """
        aggregate = (
            f"{self.project.class_stem}{namespace.replace('.', '')}"
            "ProtocolsGeneratedModels"
        )
        self.owner = aggregate
        self.local_members = frozenset()
        self.imports.clear()
        for _module, owner in parts:
            statement = f"from {self.protocol_package} import {owner}"
            self.imports[statement] = statement
        bases = ", ".join(owner for _module, owner in parts)
        alias_lines: list[str] = []
        for name in aliases:
            if name.rpartition(".")[0] != namespace:
                continue
            binding = u.Infra.qualified_name(
                self.workspace.rope_project,
                f"m.{name}",
                module_name=self.project.package_name,
            )
            alias = self.alias_definition(binding)
            if alias is None:
                msg = f"protocol alias has no authenticated source declaration: {name}"
                raise ValueError(msg)
            node, lexical = alias
            annotation = self.source(ast.unparse(node.value), lexical)
            alias_lines.append(f"    type {name.rpartition('.')[2]} = {annotation}")
        return (
            self._module_header(self.project, self.imports, structural=False) + "\n"
            f"class {aggregate}({bases}):\n"
            '    """Compose the generated structural declarations."""\n'
            + "\n".join(alias_lines)
            + f'\n\n__all__: list[str] = ["{aggregate}"]\n'
        )

    def _render_chunk(
        self, names: t.StrSequence, models: t.MappingKV[str, p.Infra.RopePyName]
    ) -> str:
        """Recompute exact imports and local references for a budgeted owner.

        Returns:
            The concatenated structural declarations for this owner.

        Raises:
            ValueError: If a model lacks its authenticated native source scope.

        """
        self.local_members = frozenset(names)
        self.imports.clear()
        bodies: list[str] = []
        for name in names:
            scope = models[name].get_object().get_scope()
            if scope is None:
                msg = f"model has no native source scope: {name}"
                raise ValueError(msg)
            bodies.append(
                self.render_protocol(name.rpartition(".")[2], models[name], scope)
            )
        return "".join(bodies)

    def render_protocol(
        self,
        name: str,
        model: p.Infra.RopePyName,
        scope: p.Infra.RopeScope,
    ) -> str:
        """Preserve field mutability and the model's authored method signatures.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If model declaration has no source module.

        """
        lines = self._field_lines(model)
        module = scope.pyobject.get_module()
        if not u.Infra.source_module(module):
            msg = f"model declaration has no source module: {name}"
            raise ValueError(msg)
        for method in self._source_methods(model):
            lines.extend(self._render_method(name, method))
        if not lines:
            lines.append("    pass")
        return (
            "\n".join((
                "@runtime_checkable",
                f"class {name}(p.Model, Protocol):",
                '    """Structural contract generated from a validated model."""',
                "",
                *lines,
            ))
            + "\n\n"
        )

    def _source_methods(
        self, model: p.Infra.RopePyName
    ) -> tuple[p.Infra.RopeScope, ...]:
        """Elect authored methods using the existing ancestor override order.

        Returns:
            Every elected native method scope in source order.

        """
        methods: dict[str, list[p.Infra.RopeScope]] = {}
        for ancestor in reversed(self.source_lineage(model)):
            owner = ancestor.get_module()
            resource = owner.get_resource() if owner is not None else None
            if resource is None or not Path(resource.real_path).is_relative_to(
                self.workspace.repository_root
            ):
                continue
            lexical = ancestor.get_scope()
            if lexical is None:
                continue
            declared: dict[str, list[p.Infra.RopeScope]] = {}
            for method in lexical.get_scopes():
                if method.get_kind() == c.Infra.RopeScopeKind.FUNCTION:
                    declared.setdefault(method.pyobject.get_name(), []).append(method)
            methods.update(declared)
        return tuple(item for group in methods.values() for item in group)

    def _render_method(self, name: str, method: p.Infra.RopeScope) -> list[str]:
        """Render one elected method without altering its structural contract.

        Returns:
            The method decorators and signature, or no lines for private methods.

        Raises:
            TypeError: If the native method or its decorators lack proof.

        """
        method_name = method.pyobject.get_name()
        if (
            method.get_kind() != c.Infra.RopeScopeKind.FUNCTION
            or method_name.startswith(("_", "model_"))
        ):
            return []
        definition = method.pyobject
        if not isinstance(definition, p.Infra.RopeSourceDefinition):
            msg = f"public method has no authenticated declaration: {method_name}"
            raise TypeError(msg)
        node = definition.get_ast()
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            msg = f"public method has no native callable AST: {method_name}"
            raise TypeError(msg)
        module = definition.get_module()
        lexical = method.parent
        if not u.Infra.source_module(module) or lexical is None:
            msg = f"method has no authenticated lexical module: {method_name}"
            raise TypeError(msg)
        if any(
            self.is_type(
                decorator.func if isinstance(decorator, ast.Call) else decorator,
                lexical,
                self.project.upstream,
                f"u.{validator}",
            )
            for decorator in node.decorator_list
            for validator in ("field_validator", "model_validator")
        ):
            return []
        signature = self._method_signature(name, method, node, module)
        lines: list[str] = []
        for decorator in node.decorator_list:
            if self.is_type(
                decorator.func if isinstance(decorator, ast.Call) else decorator,
                lexical,
                self.project.upstream,
                "u.computed_field",
            ):
                continue
            if any(
                self.is_type(decorator, lexical, "builtins", descriptor)
                for descriptor in ("property", "classmethod", "staticmethod")
            ) or (isinstance(decorator, ast.Attribute) and decorator.attr == "setter"):
                lines.append(f"    @{ast.unparse(decorator)}")
            else:
                msg = (
                    "public method decorator has no structural proof: "
                    f"{name}.{method_name}"
                )
                raise TypeError(msg)
        self.record_imports(signature, method)
        lines.append(indent(f"{signature}: ...", "    "))
        return lines

    def _method_signature(
        self,
        name: str,
        method: p.Infra.RopeScope,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module: p.Infra.RopeSourceModule,
    ) -> str:
        """Rebind only native annotation regions in the authored signature.

        Returns:
            The unchanged signature structure with authenticated annotations.

        Raises:
            TypeError: If the method has an untyped or missing return signature.

        """
        method_name = method.pyobject.get_name()
        lexical = method.parent
        if lexical is None:
            msg = f"method has no authenticated lexical module: {method_name}"
            raise TypeError(msg)
        statements = u.Infra.logical_statements(module.source_code)
        annotation_regions = u.Infra.annotation_regions(module.source_code, module)
        self._validate_method_signature(f"{name}.{method_name}", node, lexical)
        statement = next(item for item in statements if item.line == method.get_start())
        signature = module.source_code[statement.start_offset : statement.end_offset]
        _first, last = u.Infra.expression_segments(signature, 0, len(signature), ":")[0]
        signature = signature[:last]
        header_end = statement.start_offset + last
        for begin, end, _line in reversed(annotation_regions):
            stop = min(end, header_end)
            if statement.start_offset <= begin < stop <= header_end:
                signature = (
                    signature[: begin - statement.start_offset]
                    + self.source(
                        module.source_code[begin:stop],
                        method,
                        self._method_type_parameters(node),
                    )
                    + signature[stop - statement.start_offset :]
                )
        signature = dedent(signature).strip()
        if "->" not in signature:
            msg = f"public method {name}.{method_name} lacks a return annotation"
            raise TypeError(msg)
        return signature

    @staticmethod
    def _method_type_parameters(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> dict[str, ast.expr]:
        """Bind native PEP 695 parameter names for signature annotation rebinding.

        Returns:
            Native name expressions for every declared type parameter.

        Raises:
            TypeError: If a parameter is not a native Python type declaration.

        """
        parameters: dict[str, ast.expr] = {}
        for parameter in node.type_params:
            if not isinstance(
                parameter, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple
            ):
                msg = "public method has no native type parameter declaration"
                raise TypeError(msg)
            parameters[parameter.name] = ast.Name(id=parameter.name, ctx=ast.Load())
        return parameters

    def _validate_method_signature(
        self,
        name: str,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lexical: p.Infra.RopeScope,
    ) -> None:
        """Require authored annotations for every non-receiver parameter.

        Raises:
            TypeError: If a public signature is not completely typed.

        """
        arguments = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            *((node.args.vararg,) if node.args.vararg is not None else ()),
            *((node.args.kwarg,) if node.args.kwarg is not None else ()),
        )
        positional = (*node.args.posonlyargs, *node.args.args)
        receiver = (
            positional[0]
            if positional
            and not any(
                self.is_type(decorator, lexical, "builtins", "staticmethod")
                for decorator in node.decorator_list
            )
            else None
        )
        if node.returns is None or any(
            argument.annotation is None
            and not (argument is receiver and argument.arg in {"self", "cls"})
            for argument in arguments
        ):
            msg = f"public method {name} has an untyped signature"
            raise TypeError(msg)

    def _field_lines(self, model: p.Infra.RopePyName) -> list[str]:
        lines: list[str] = []
        fields, frozen = self.source_fields(model)
        for field_name, (annotation, lexical, field_frozen) in fields.items():
            rendered = self.source(ast.unparse(annotation), lexical)
            if frozen or field_frozen:
                lines.extend((
                    "    @property",
                    f"    def {field_name}(self) -> {rendered}: ...",
                ))
            else:
                lines.append(f"    {field_name}: {rendered}")
        return lines

    def source_lineage(
        self, binding: p.Infra.RopePyName
    ) -> tuple[p.Infra.RopePyObject, ...]:
        """Reuse the canonical C3 merger over authenticated native class owners.

        Returns:
            The authenticated owners in canonical C3 order.

        """
        owners: dict[str, p.Infra.RopePyObject] = {}

        def lineage(
            value: p.Infra.RopePyObject, visiting: frozenset[str]
        ) -> tuple[str, ...]:
            identity = self.identity(value)
            if identity in visiting:
                msg = f"cyclic native model ancestry: {identity}"
                raise ValueError(msg)
            owners[identity] = value
            object_type = u.Infra.qualified_name(
                self.workspace.rope_project, "object", module_name="builtins"
            ).get_object()
            bases = tuple(
                base for base in u.Infra.direct_bases(value) if base != object_type
            )
            return (
                identity,
                *u.Infra.merge_class_lineages(
                    (
                        *(lineage(base, visiting | {identity}) for base in bases),
                        tuple(self.identity(base) for base in bases),
                    ),
                    message=f"inconsistent native model ancestry: {identity}",
                ),
            )

        return tuple(
            owners[identity] for identity in lineage(binding.get_object(), frozenset())
        )

    def source_fields(
        self, binding: p.Infra.RopePyName
    ) -> tuple[dict[str, tuple[ast.expr, p.Infra.RopeScope, bool]], bool]:
        """Project native inherited fields in the canonical C3 source order.

        Returns:
            Inherited fields with their lexical scopes and effective frozen policy.

        Raises:
            TypeError: If an ancestor lacks an authenticated native class.

        """
        fields: dict[str, tuple[ast.expr, p.Infra.RopeScope, bool]] = {}
        frozen = False
        for owner in reversed(self.source_lineage(binding)):
            identity = self.identity(owner)
            if not isinstance(owner, p.Infra.RopeSourceDefinition):
                continue
            node, lexical = owner.get_ast(), owner.get_scope()
            if not isinstance(node, ast.ClassDef) or lexical is None:
                msg = f"model ancestor has no native class declaration: {identity}"
                raise TypeError(msg)
            keyword_policy = self._keyword_frozen_policy(node, identity)
            for statement in node.body:
                if not isinstance(statement, ast.Assign | ast.AnnAssign):
                    continue
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                if any(
                    isinstance(target, ast.Name) and target.id == "model_config"
                    for target in targets
                ):
                    frozen = self._model_config_policy(
                        statement.value, lexical, identity, frozen=frozen
                    )
                    continue
                if not isinstance(statement, ast.AnnAssign) or not isinstance(
                    statement.target, ast.Name
                ):
                    continue
                self._source_field(statement, lexical, identity, fields)
            if keyword_policy is not None:
                frozen = keyword_policy
        return fields, frozen

    @staticmethod
    def _native_boolean(value: ast.expr, message: str) -> bool:
        """Authenticate a literal boolean without evaluating authored code.

        Returns:
            The native boolean literal.

        Raises:
            TypeError: If the expression is not a literal boolean.

        """
        if not isinstance(value, ast.Constant) or not isinstance(value.value, bool):
            raise TypeError(message)
        return value.value

    @classmethod
    def _keyword_frozen_policy(cls, node: ast.ClassDef, identity: str) -> bool | None:
        """Read the class-header frozen policy in authored keyword order.

        Returns:
            The explicit policy, or None when no keyword owns it.

        Raises:
            TypeError: If expanded keywords have no native closed proof.

        """
        policy: bool | None = None
        for keyword in node.keywords:
            if keyword.arg is None:
                msg = (
                    "model keyword configuration has no native closed proof: "
                    f"{identity}"
                )
                raise TypeError(msg)
            if keyword.arg == "frozen":
                policy = cls._native_boolean(
                    keyword.value,
                    "model keyword frozen policy has no native boolean proof: "
                    f"{identity}",
                )
        return policy

    def _model_config_policy(
        self,
        value: ast.expr | None,
        lexical: p.Infra.RopeScope,
        identity: str,
        *,
        frozen: bool,
    ) -> bool:
        """Read literal model configuration without changing inherited defaults.

        Returns:
            The effective frozen policy after the authored configuration.

        Raises:
            TypeError: If configuration lacks native literal or owner proof.

        """
        if isinstance(value, ast.Name | ast.Attribute):
            binding = u.Infra.resolve_symbol(lexical, value)
            if binding is not None and u.Infra.assigned_name(binding):
                module, _line = u.Infra.definition_location(binding)
                if len(binding.assignments) == 1 and u.Infra.source_module(module):
                    declaration = binding.assignments[0].ast_node
                    if not isinstance(declaration, ast.expr):
                        msg = (
                            f"model configuration has no source expression: {identity}"
                        )
                        raise TypeError(msg)
                    return self._model_config_policy(
                        declaration,
                        u.Infra.scope_at(
                            module,
                            u.Infra.source_offset(module.source_code, declaration),
                        ),
                        identity,
                        frozen=frozen,
                    )
        if not isinstance(value, ast.Call | ast.Dict):
            msg = f"model configuration has no native literal proof: {identity}"
            raise TypeError(msg)
        if isinstance(value, ast.Call) and not (
            self.is_type(value.func, lexical, "pydantic", "ConfigDict")
            or self.is_type(value.func, lexical, self.project.upstream, "m.ConfigDict")
            or self.is_type(value.func, lexical, "builtins", "dict")
        ):
            msg = f"model configuration has no canonical source owner: {identity}"
            raise TypeError(msg)
        options = (
            [(item.arg, item.value) for item in value.keywords]
            if isinstance(value, ast.Call)
            else [
                (key.value if isinstance(key, ast.Constant) else None, item)
                for key, item in zip(value.keys, value.values, strict=True)
            ]
        )
        for key, option in options:
            if key is None:
                msg = (
                    "expanded model configuration has no native closed proof: "
                    f"{identity}"
                )
                raise TypeError(msg)
            if key == "frozen":
                frozen = self._native_boolean(
                    option,
                    f"model frozen policy has no native boolean proof: {identity}",
                )
        return frozen

    def _source_field(
        self,
        statement: ast.AnnAssign,
        lexical: p.Infra.RopeScope,
        identity: str,
        fields: dict[str, tuple[ast.expr, p.Infra.RopeScope, bool]],
    ) -> None:
        """Apply one public annotated declaration to the inherited field map."""
        if not isinstance(statement.target, ast.Name):
            return
        name = statement.target.id
        if name.startswith("_"):
            return
        annotation = statement.annotation
        if isinstance(annotation, ast.Subscript) and self.is_type(
            annotation.value, lexical, "typing", "ClassVar"
        ):
            fields.pop(name, None)
            return
        field_frozen = False
        if isinstance(annotation, ast.Subscript) and self.is_type(
            annotation.value, lexical, "typing", "Final"
        ):
            if statement.value is not None:
                fields.pop(name, None)
                return
            field_frozen = True
            annotation = annotation.slice
        metadata = [statement.value] if statement.value is not None else []
        if (
            isinstance(annotation, ast.Subscript)
            and self.is_type(annotation.value, lexical, "typing", "Annotated")
            and isinstance(annotation.slice, ast.Tuple)
        ):
            metadata = [*annotation.slice.elts[1:], *metadata]
        fields[name] = (
            annotation,
            lexical,
            self._field_metadata_frozen(
                metadata, lexical, f"{identity}.{name}", frozen=field_frozen
            ),
        )

    def _field_metadata_frozen(
        self,
        metadata: list[ast.expr],
        lexical: p.Infra.RopeScope,
        identity: str,
        *,
        frozen: bool,
    ) -> bool:
        """Apply the authored Pydantic Field metadata in source order.

        Returns:
            The effective frozen policy for this field.

        """
        for value in metadata:
            if isinstance(value, ast.Call) and self.is_type(
                value.func, lexical, "pydantic", "Field"
            ):
                for option in value.keywords:
                    if option.arg == "frozen":
                        frozen = self._native_boolean(
                            option.value,
                            "field frozen policy has no native boolean proof: "
                            f"{identity}",
                        )
        return frozen

    def _append_part(
        self,
        modules: t.MutableMappingKV[Path, str],
        parts: list[tuple[str, str]],
        target: Path,
        body: str,
        header: str,
    ) -> None:
        """Append one budgeted part using the existing generated-module boundary."""
        index = len(parts) + 1
        module = f"{target.name}_{index:02d}"
        owner = f"{self.project.class_stem}ProtocolsGeneratedPart{len(modules) + 1:02d}"
        modules[target.with_name(f"{module}.py")] = (
            f"{header}class {owner}:\n{indent(body, '    ')}\n"
            f'__all__: list[str] = ["{owner}"]\n'
        )
        parts.append((module, owner))

    @staticmethod
    def _module_header(
        project: p.Infra.ProjectSpec,
        imports: t.MappingKV[str, str],
        *,
        structural: bool = True,
    ) -> str:
        """Use upstream protocol bases and the elected same-family owner imports.

        Returns:
            The resulting ``str``.

        """
        upstream = project.upstream
        statements = set(imports.values())
        if structural:
            statements.update((
                "from typing import Protocol, runtime_checkable",
                f"from {upstream} import p",
            ))
        return (
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            "from __future__ import annotations\n\n"
            + "\n".join(sorted(statements))
            + "\n\n"
        )


__all__: list[str] = ["FlextInfraCodegenProtocolModelRender"]
