"""Render structural protocol classes for the generated ``p`` layer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from textwrap import dedent, indent

from flext_infra import c, config, p, t, u
from flext_infra.codegen import FlextInfraCodegenProtocolModelAnnotations


class FlextInfraCodegenProtocolModelRender(FlextInfraCodegenProtocolModelAnnotations):
    """Render structural protocols and their generated-file modules."""

    @classmethod
    def render_member_modules(
        cls,
        models: t.MappingKV[str, p.ModelType],
        project: p.Infra.ProjectSpec,
        workspace: p.Infra.RopeWorkspaceDsl,
        facades: t.MappingKV[str, p.ModuleOwned],
        declarations: t.MappingKV[str, p.Infra.RopePyName],
        protocol_directory: Path,
        aliases: t.MappingKV[str, t.StrSequence],
    ) -> t.MappingKV[Path, str]:
        """Render source-bound declarations and their composing owner modules.

        Returns:
            The resulting ``t.MappingKV[Path, str]``.

        Raises:
            ValueError: If model declaration has no native scope; or if protocol
                declaration exceeds configured LOC cap.

        """
        renderer = cls(project, workspace, facades, declarations)
        grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for name, model in sorted(models.items()):
            declaration = declarations[name].get_object()
            scope = declaration.get_scope()
            if scope is None:
                msg = f"model declaration has no native scope: {name}"
                raise ValueError(msg)
            body = renderer._render_protocol(name.rpartition(".")[2], model, scope)
            grouped[name.rpartition(".")[0]].append((model.__module__, body))
        modules: dict[Path, str] = {}
        for namespace, bodies in grouped.items():
            parts: list[tuple[str, str]] = []
            token = namespace.replace(".", "_").lower()
            stem = f"generated_models_{token}" if token else "generated_models"
            chunk = ""
            for _owner, body in bodies:
                header = cls._module_header(project, renderer.imports)
                if chunk and (
                    header.count("\n") + chunk.count("\n") + body.count("\n") + 1
                    > config.Infra.codegen.loc_cap.max_lines
                ):
                    renderer._append_part(
                        modules, parts, protocol_directory, stem, chunk, header
                    )
                    chunk = ""
                if (
                    header.count("\n") + body.count("\n") + 1
                    > config.Infra.codegen.loc_cap.max_lines
                ):
                    msg = (
                        f"protocol declaration exceeds configured LOC cap: {namespace}"
                    )
                    raise ValueError(msg)
                chunk += body
            if chunk:
                renderer._append_part(
                    modules,
                    parts,
                    protocol_directory,
                    stem,
                    chunk,
                    cls._module_header(project, renderer.imports),
                )
            aggregate = f"{project.class_stem}{namespace.replace('.', '')}ProtocolsGeneratedModels"
            imports = "\n".join(
                f"from .{module} import {owner}" for module, owner in parts
            )
            bases = ", ".join(owner for _module, owner in parts)
            alias_lines = [
                f"    type {name.rpartition('.')[2]} = "
                + " | ".join(f"_public.p.{route}" for route in routes)
                for name, routes in aliases.items()
                if name.rpartition(".")[0] == namespace
            ]
            modules[protocol_directory / f"{stem}.py"] = (
                f"{cls._module_header(project, {})}{imports}\n\n"
                f"class {aggregate}({bases}):\n"
                '    """Compose the generated structural declarations."""\n'
                + "\n".join(alias_lines)
                + f'\n\n__all__: list[str] = ["{aggregate}"]\n'
            )
        return modules

    def _render_protocol(
        self,
        name: str,
        model: p.ModelType,
        scope: p.Infra.RopeScope,
    ) -> str:
        """Preserve field mutability and the model's authored method signatures.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If field; or if public method.
            ValueError: If model declaration has no source module.

        """
        lines = [
            "@runtime_checkable",
            f"class {name}(Protocol):",
            '    """Structural contract generated from a validated model."""',
            "",
        ]
        for field_name, field in model.model_fields.items():
            if field.annotation is None:
                msg = f"field {field_name!r} has no annotation"
                raise TypeError(msg)
            rendered = self.render(field.annotation, scope)
            if model.model_config.get("frozen", False) is True or field.frozen is True:
                lines.extend((
                    "    @property",
                    f"    def {field_name}(self) -> {rendered}: ...",
                ))
            else:
                lines.append(f"    {field_name}: {rendered}")
        module = scope.pyobject.get_module()
        if module is None:
            msg = f"model declaration has no source module: {name}"
            raise ValueError(msg)
        statements = u.Infra.logical_statements(module.source_code)
        annotation_regions = u.Infra.annotation_regions(module.source_code, module)
        for method in scope.get_scopes():
            method_name = method.pyobject.get_name()
            if (
                method.get_kind() != c.Infra.RopeScopeKind.FUNCTION
                or method_name.startswith(("_", "model_"))
            ):
                continue
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
                        + self.source(module.source_code[begin:stop], scope)
                        + signature[stop - statement.start_offset :]
                    )
            signature = dedent(signature)
            signature = signature.strip()
            if "->" not in signature:
                msg = f"public method {name}.{method_name} lacks a return annotation"
                raise TypeError(msg)
            descriptor = vars(model).get(method_name)
            if type(descriptor) is property:
                setter = any(
                    item.text.strip() == f"@{method_name}.setter"
                    for item in statements
                    if method.get_region()[0] <= item.start_offset
                    and item.line < method.get_start()
                )
                lines.append(
                    f"    @{method_name}.setter" if setter else "    @property"
                )
            elif type(descriptor) in {classmethod, staticmethod}:
                lines.append(f"    @{type(descriptor).__name__}")
            self.record_imports(signature, scope)
            lines.append(indent(f"{signature}: ...", "    "))
        if len(lines) == 4:
            lines.append("    pass")
        return "\n".join(lines) + "\n\n"

    def _append_part(
        self,
        modules: t.MutableMappingKV[Path, str],
        parts: list[tuple[str, str]],
        directory: Path,
        stem: str,
        body: str,
        header: str,
    ) -> None:
        """Append one budgeted part using the existing generated-module boundary."""
        index = len(parts) + 1
        module = f"{stem}_{index:02d}"
        owner = f"{self.project.class_stem}ProtocolsGeneratedPart{len(modules) + 1:02d}"
        modules[directory / f"{module}.py"] = (
            f"{header}class {owner}:\n{indent(body, '    ')}\n__all__: list[str] = []\n"
        )
        parts.append((module, owner))

    @staticmethod
    def _module_header(
        project: p.Infra.ProjectSpec,
        imports: t.MappingKV[str, str],
    ) -> str:
        """Import the package object without eagerly reading its composing facade.

        Returns:
            The resulting ``str``.

        """
        return (
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            "from __future__ import annotations\n\n"
            "from typing import Protocol, runtime_checkable\n"
            f"import {project.package_name} as _public\n"
            + "\n".join(sorted(imports.values()))
            + "\n\n"
        )


__all__: list[str] = ["FlextInfraCodegenProtocolModelRender"]
