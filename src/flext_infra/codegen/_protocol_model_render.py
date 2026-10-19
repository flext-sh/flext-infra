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
            name: f"{self.project.class_stem}{name.rpartition('.')[0].replace('.', '')}ProtocolsGeneratedModels.{name.rpartition('.')[2]}"
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
            self._render_protocol(name.rpartition(".")[2], model, scope)
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
        for namespace, names in grouped.items():
            parts: list[tuple[str, str]] = []
            token = namespace.replace(".", "_").lower()
            stem = f"generated_models_{token}" if token else "generated_models"
            members: list[str] = []
            chunk = ""
            for name in names:
                self.owner = f"{self.project.class_stem}ProtocolsGeneratedPart{len(modules) + 1:02d}"
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
                        protocol_directory / stem,
                        previous,
                        self._module_header(self.project, self.imports),
                    )
                    members = []
                    self.owner = f"{self.project.class_stem}ProtocolsGeneratedPart{len(modules) + 1:02d}"
                    body = self._render_chunk((name,), models)
                    header = self._module_header(self.project, self.imports)
                if (
                    header.count("\n") + body.count("\n") + 4
                    > config.Infra.codegen.loc_cap.max_lines
                ):
                    msg = (
                        f"protocol declaration exceeds configured LOC cap: {namespace}"
                    )
                    raise ValueError(msg)
                members.append(name)
                chunk = body
            if chunk:
                self._append_part(
                    modules,
                    parts,
                    protocol_directory / stem,
                    chunk,
                    self._module_header(self.project, self.imports),
                )
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
            modules[protocol_directory / f"{stem}.py"] = (
                self._module_header(self.project, self.imports, structural=False) + "\n"
                f"class {aggregate}({bases}):\n"
                '    """Compose the generated structural declarations."""\n'
                + "\n".join(alias_lines)
                + f'\n\n__all__: list[str] = ["{aggregate}"]\n'
            )
        for path, content in modules.items():
            if len(content.splitlines()) > config.Infra.codegen.loc_cap.max_lines:
                msg = f"protocol module exceeds configured LOC cap: {path}"
                raise ValueError(msg)
        return modules

    def _render_chunk(
        self, names: t.StrSequence, models: t.MappingKV[str, p.Infra.RopePyName]
    ) -> str:
        """Recompute exact imports and local references for a budgeted owner."""
        self.local_members = frozenset(names)
        self.imports.clear()
        bodies: list[str] = []
        for name in names:
            scope = models[name].get_object().get_scope()
            if scope is None:
                msg = f"model has no native source scope: {name}"
                raise ValueError(msg)
            bodies.append(
                self._render_protocol(name.rpartition(".")[2], models[name], scope)
            )
        return "".join(bodies)

    def _render_protocol(
        self,
        name: str,
        model: p.Infra.RopePyName,
        scope: p.Infra.RopeScope,
    ) -> str:
        """Preserve field mutability and the model's authored method signatures.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If field; or if public method.
            ValueError: If model declaration has no source module.

        """
        lines = self._field_lines(model, scope)
        module = scope.pyobject.get_module()
        if not u.Infra.source_module(module):
            msg = f"model declaration has no source module: {name}"
            raise ValueError(msg)
        methods: dict[str, list[p.Infra.RopeScope]] = {}
        for ancestor in reversed(self.source_lineage(model)):
            owner = ancestor.get_module()
            lexical = ancestor.get_scope()
            resource = owner.get_resource() if owner is not None else None
            if (
                resource is None
                or lexical is None
                or not Path(resource.real_path).is_relative_to(
                    self.workspace.repository_root
                )
            ):
                continue
            declared: dict[str, list[p.Infra.RopeScope]] = {}
            for method in lexical.get_scopes():
                if method.get_kind() == c.Infra.RopeScopeKind.FUNCTION:
                    declared.setdefault(method.pyobject.get_name(), []).append(method)
            methods.update(declared)
        for method in (item for group in methods.values() for item in group):
            method_name = method.pyobject.get_name()
            if (
                method.get_kind() != c.Infra.RopeScopeKind.FUNCTION
                or method_name.startswith(("_", "model_"))
            ):
                continue
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
            statements = u.Infra.logical_statements(module.source_code)
            annotation_regions = u.Infra.annotation_regions(module.source_code, module)
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
                msg = f"public method {name}.{method_name} has an untyped signature"
                raise TypeError(msg)
            statement = next(
                item for item in statements if item.line == method.get_start()
            )
            signature = module.source_code[
                statement.start_offset : statement.end_offset
            ]
            _first, last = u.Infra.expression_segments(
                signature, 0, len(signature), ":"
            )[0]
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
                            {
                                parameter.name: ast.Name(
                                    id=parameter.name, ctx=ast.Load()
                                )
                                for parameter in node.type_params
                            },
                        )
                        + signature[stop - statement.start_offset :]
                    )
            signature = dedent(signature)
            signature = signature.strip()
            if "->" not in signature:
                msg = f"public method {name}.{method_name} lacks a return annotation"
                raise TypeError(msg)
            for decorator in node.decorator_list:
                if any(
                    self.is_type(decorator, lexical, "builtins", descriptor)
                    for descriptor in ("property", "classmethod", "staticmethod")
                ) or (
                    isinstance(decorator, ast.Attribute) and decorator.attr == "setter"
                ):
                    lines.append(f"    @{ast.unparse(decorator)}")
                else:
                    msg = f"public method decorator has no structural proof: {name}.{method_name}"
                    raise TypeError(msg)
            self.record_imports(signature, method)
            lines.append(indent(f"{signature}: ...", "    "))
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

    def _field_lines(
        self, model: p.Infra.RopePyName, scope: p.Infra.RopeScope
    ) -> list[str]:
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
        """Reuse the canonical C3 merger over authenticated native class owners."""
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
        """Project native inherited fields in the canonical C3 source order."""
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
            keyword_policy: bool | None = None
            for keyword in node.keywords:
                if keyword.arg is None:
                    msg = f"model keyword configuration has no native closed proof: {identity}"
                    raise TypeError(msg)
                if keyword.arg == "frozen":
                    if not isinstance(keyword.value, ast.Constant) or not isinstance(
                        keyword.value.value, bool
                    ):
                        msg = f"model keyword frozen policy has no native boolean proof: {identity}"
                        raise TypeError(msg)
                    keyword_policy = keyword.value.value
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
                    value = statement.value
                    if not isinstance(value, ast.Call | ast.Dict):
                        msg = f"model configuration has no native literal proof: {identity}"
                        raise TypeError(msg)
                    if isinstance(value, ast.Call) and not (
                        self.is_type(value.func, lexical, "pydantic", "ConfigDict")
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
                            msg = f"expanded model configuration has no native closed proof: {identity}"
                            raise TypeError(msg)
                        if key == "frozen":
                            if not isinstance(option, ast.Constant) or not isinstance(
                                option.value, bool
                            ):
                                msg = f"model frozen policy has no native boolean proof: {identity}"
                                raise TypeError(msg)
                            frozen = option.value
                    continue
                if not isinstance(statement, ast.AnnAssign) or not isinstance(
                    statement.target, ast.Name
                ):
                    continue
                name = statement.target.id
                if name.startswith("_"):
                    continue
                annotation = statement.annotation
                if isinstance(annotation, ast.Subscript) and self.is_type(
                    annotation.value, lexical, "typing", "ClassVar"
                ):
                    fields.pop(name, None)
                    continue
                field_frozen = False
                if isinstance(annotation, ast.Subscript) and self.is_type(
                    annotation.value, lexical, "typing", "Final"
                ):
                    if statement.value is not None:
                        fields.pop(name, None)
                        continue
                    field_frozen = True
                    annotation = annotation.slice
                metadata = [statement.value] if statement.value is not None else []
                if (
                    isinstance(annotation, ast.Subscript)
                    and self.is_type(annotation.value, lexical, "typing", "Annotated")
                    and isinstance(annotation.slice, ast.Tuple)
                ):
                    metadata = [*annotation.slice.elts[1:], *metadata]
                for value in metadata:
                    if isinstance(value, ast.Call) and self.is_type(
                        value.func, lexical, "pydantic", "Field"
                    ):
                        for option in value.keywords:
                            if option.arg == "frozen":
                                if not isinstance(
                                    option.value, ast.Constant
                                ) or not isinstance(option.value.value, bool):
                                    msg = f"field frozen policy has no native boolean proof: {identity}.{name}"
                                    raise TypeError(msg)
                                field_frozen = option.value.value
                fields[name] = annotation, lexical, field_frozen
            if keyword_policy is not None:
                frozen = keyword_policy
        return fields, frozen

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
            f'{header}class {owner}:\n{indent(body, "    ")}\n__all__: list[str] = ["{owner}"]\n'
        )
        parts.append((module, owner))

    def _module_header(
        self,
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
        return (
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            "from __future__ import annotations\n\n"
            + (
                "from typing import Protocol, runtime_checkable\n"
                f"from {upstream} import p\n"
                if structural
                else ""
            )
            + "\n".join(sorted(imports.values()))
            + "\n\n"
        )


__all__: list[str] = ["FlextInfraCodegenProtocolModelRender"]
