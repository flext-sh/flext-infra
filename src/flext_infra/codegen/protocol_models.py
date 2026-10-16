"""Assemble member structural protocols from validated models on demand.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from importlib import import_module
from itertools import chain
from pathlib import Path
from types import UnionType
from typing import TypeAliasType, Union, get_args, get_origin, override

from flext_infra import FlextInfra, FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenProtocolModelRender


class FlextInfraCodegenProtocolModels(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Assemble the member's generated ``p`` layer from validated models."""

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Use the canonical self conformance transaction for publication.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        outcome = FlextInfra(repository_root=self.repository_root).codegen_conform(
            m.Infra.CodegenConformRequest(
                root=self.repository_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=(
                    c.Infra.CodegenConformMode.CHECK
                    if self.effective_dry_run
                    else c.Infra.CodegenConformMode.APPLY
                ),
            )
        )
        if outcome.failure:
            return r[t.Cli.ResultValue].from_failure(outcome)
        return r[t.Cli.ResultValue].ok(value=True)

    @classmethod
    def render_modules(
        cls,
        project: p.Infra.ProjectSpec,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[t.MappingKV[Path, str]]:
        """Plan the elected project's protocol sources without writing files.

        Returns:
            The resulting ``p.Result[t.MappingKV[Path, str]]``.

        """
        _package_dir, facades, runtime_facades = cls._facade_inventory(
            project, workspace
        )
        if not name:
            return r[
                FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget
            ].fail(f"pyproject manifest declares no project name: {manifest}")
        package = name.replace("-", "_")
        container = "".join(part.capitalize() for part in package.split("_"))
        layout = u.Infra.layout(root)
        if layout is None:
            return r[
                FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget
            ].fail(f"member package layout is unresolved: {root}")
        owner = u.Infra.facade_module_path(layout.package_dir, "m")
        if owner is None:
            return r[
                FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget
            ].fail(f"member models facade is unresolved: {root}")
        declarations = tuple(
            node
            for node in ast.parse(owner.read_text(encoding="utf-8")).body
            if isinstance(node, ast.ClassDef)
        )
        if len(declarations) != 1:
            return r[
                FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget
            ].fail(f"member models facade is ambiguous: {owner}")
        namespaces = tuple(
            node.name for node in declarations[0].body if isinstance(node, ast.ClassDef)
        )
        if len(namespaces) > 1:
            return r[
                FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget
            ].fail(f"member models namespace is ambiguous: {owner}")
        suffix = f".{namespaces[0]}" if namespaces else ""
        return r[FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget].ok(
            FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget(
                package_name=package,
                facade_container=container,
                package_module_prefix=f"{package}.",
                protocol_ref_prefix=f"p{suffix}",
                models_facade_name=f"m{suffix}",
                facade_probes=(
                    ("m", f"{package}.models.{declarations[0].name}{suffix}"),
                    ("p", f"{package}.protocols.{container}Protocols{suffix}"),
                    ("c", f"{package}.constants.{container}Constants{suffix}"),
                    ("t", f"{package}.typings.{container}Types{suffix}"),
                ),
            ),
        )
        for name in sorted(cls._referenced_names(workspace, facades["p"], directory)):
            manual = cls._member(facades["p"], name)
            if manual is not None:
                module = manual.get_object().get_module()
                resource = module.get_resource() if module is not None else None
                if resource is not None and not u.Infra.require_file_resource(
                    resource, name
                ).read().startswith(c.Infra.AUTOGEN_HEADERS):
                    continue
            if cls._member(facades["m"], name) is None:
                return r[t.MappingKV[Path, str]].fail(
                    f"referenced protocol p.{name} resolves to no declared model"
                )
            candidate = runtime_facades["m"]
            for component in name.split("."):
                candidate = getattr(candidate, component)
            resolved = cls._model_routes(workspace, base, name, candidate)
            if resolved.failure:
                return r[t.MappingKV[Path, str]].from_failure(resolved)
            for route, model, binding in resolved.value:
                models[route] = model
                declarations[route] = binding
            if isinstance(candidate, TypeAliasType):
                aliases[name] = tuple(
                    route for route, _model, _binding in resolved.value
                )
        return r[t.MappingKV[Path, str]].ok(
            FlextInfraCodegenProtocolModelRender(
                project,
                workspace,
                runtime_facades,
                declarations,
            ).render_member_modules(
                models,
                directory,
                aliases,
            )
        )

    @staticmethod
    def _facade_inventory(
        project: p.Infra.ProjectSpec, workspace: p.Infra.RopeWorkspaceDsl
    ) -> tuple[
        Path | None,
        t.DictKV[str, p.Infra.RopePyName],
        t.DictKV[str, p.ModuleOwned],
    ]:
        facades: dict[str, p.Infra.RopePyName] = {}
        runtime_facades: dict[str, p.ModuleOwned] = {}
        for entry in workspace.modules():
            if entry.package_name != project.package_name:
                continue
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"indexed module unavailable: {entry.file_path}"
                raise ValueError(msg)
            owner = u.Infra.published_facade_owner(workspace.rope_project, resource)
            if owner is None:
                continue
            facades[owner[0]] = u.Infra.resolve_pymodule(
                workspace.rope_project, resource
            ).get_attribute(owner[1])
            runtime_facades[owner[0]] = getattr(
                import_module(entry.module_name), owner[1]
            )
        for namespace in target.models_facade_name.split(".")[1:]:
            container = getattr(container, namespace, None)
            if container is None:
                return r[t.SequenceOf[type[m.BaseModel]]].fail(
                    f"models facade declares no namespace {namespace}",
                )
        models: list[type[m.BaseModel]] = []
        for name in wanted:
            candidate = getattr(container, name, None)
            if candidate is None:
                return r[t.SequenceOf[type[m.BaseModel]]].fail(
                    f"referenced protocol {target.protocol_ref_prefix}.{name} "
                    f"resolves to no model on {target.facade_container}Models",
                )
            models.extend(cls._model_leaves(candidate))
        return r[t.SequenceOf[type[m.BaseModel]]].ok(tuple(models))

    @classmethod
    def _model_routes(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        base: p.Infra.RopePyObject,
        name: str,
        candidate: p.ModuleOwned,
    ) -> p.Result[t.VariadicTuple[t.Triple[str, p.ModelType, p.Infra.RopePyName]]]:
        result_type = r[t.VariadicTuple[t.Triple[str, p.ModelType, p.Infra.RopePyName]]]
        routes: list[t.Triple[str, p.ModelType, p.Infra.RopePyName]] = []
        value = (
            candidate.__value__ if isinstance(candidate, TypeAliasType) else candidate
        )
        leaves = (
            get_args(value) if get_origin(value) in {UnionType, Union} else (value,)
        )
        for leaf in leaves:
            if not isinstance(leaf, type) or not u.model_type(leaf):
                return result_type.fail(
                    f"referenced protocol p.{name} is not a model declaration"
                )
            module = workspace.rope_project.get_module(leaf.__module__)
            first, separator, tail = leaf.__qualname__.partition(".")
            binding = module.get_attribute(first)
            if separator:
                binding = cls._member(binding, tail)
            if binding is None or base not in u.Infra.class_ancestry(
                binding.get_object()
            ):
                return result_type.fail(
                    f"referenced protocol p.{name} is not a model declaration"
                )
            prefix, separator, _last = name.rpartition(".")
            route = (
                (f"{prefix}.{leaf.__name__}" if separator else leaf.__name__)
                if isinstance(candidate, TypeAliasType)
                else name
            )
            routes.append((route, leaf, binding))
        return result_type.ok(tuple(routes))

    @staticmethod
    def _member(
        binding: p.Infra.RopePyName,
        name: str,
    ) -> p.Infra.RopePyName | None:
        """Follow the exact declared route, including inherited nested namespaces.

        Returns:
            The resulting ``p.Infra.RopePyName | None``.

        """
        for component in name.split("."):
            child = binding.get_object().get_attributes().get(component)
            if child is None:
                return None
            binding = child
        return binding

    @classmethod
    def _referenced_names(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        binding: p.Infra.RopePyName,
        directory: Path,
    ) -> set[str]:
        """Read actual imported protocol primaries from every indexed Python root.

        Returns:
            The resulting ``set[str]``.

        """
        found: set[str] = set()
        protocols = root / "src" / target.package_name / "_protocols"
        for path in sorted(protocols.rglob("*.py")):
            if path.name.startswith("generated_models"):
                continue
            pending = list(ast.parse(path.read_text(encoding="utf-8")).body)
            while pending:
                node = pending.pop()
                if isinstance(node, ast.ClassDef):
                    found.add(node.name)
                    pending.extend(node.body)
                elif isinstance(node, ast.If):
                    pending.extend((*node.body, *node.orelse))
                elif isinstance(node, ast.TypeAlias):
                    found.add(node.name.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(
                    node.target, ast.Name
                ):
                    found.add(node.target.id)
                elif isinstance(node, ast.Assign):
                    found.update(
                        target.id
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    )
        return found

    @classmethod
    def _settle(
        cls,
        root: Path,
        modules: t.MappingKV[str, str],
        *,
        dry: bool,
    ) -> p.Result[t.Cli.ResultValue]:
        """Compare or write generated modules under the member protocols dir.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        found: set[str] = set()
        for entry in workspace.modules():
            if entry.file_path.is_relative_to(workspace.repository_root / directory):
                continue
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"indexed module unavailable: {entry.file_path}"
                raise ValueError(msg)
            module = u.Infra.resolve_pymodule(workspace.rope_project, resource)
            source = module.source_code
            primaries = (
                (source[begin:end], u.Infra.scope_at(module, begin))
                for begin, end in u.Infra.reference_regions(source)
            )
            quoted = (
                (expression[begin:end], scope)
                for expression, scope, _line in u.Infra.scoped_quoted_type_references(
                    source,
                    workspace.rope_project,
                    module,
                )
                for begin, end in u.Infra.reference_regions(expression)
            )
            for primary, scope in chain(primaries, quoted):
                name, separator, tail = primary.partition(".")
                if not separator or not u.Infra.same_name(
                    binding, u.Infra.expression_name(scope, name)
                ):
                    continue
                if tail:
                    found.add(tail)
        return found


__all__: list[str] = ["FlextInfraCodegenProtocolModels"]
