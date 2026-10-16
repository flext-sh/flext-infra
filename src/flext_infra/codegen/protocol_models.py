"""Assemble member structural protocols from validated models on demand.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
        package_dir, facades, runtime_facades = cls._facade_inventory(
            project, workspace
        )
        if package_dir is None or not {"m", "p"}.issubset(facades):
            return r[t.MappingKV[Path, str]].fail(
                f"project has no declared model/protocol facade: {project.package_name}"
            )
        directory = (
            package_dir / u.Infra.facade_families()["p"].directory
        ).relative_to(workspace.repository_root)
        models: dict[str, p.ModelType] = {}
        declarations: dict[str, p.Infra.RopePyName] = {}
        aliases: dict[str, tuple[str, ...]] = {}
        base = (
            workspace.rope_project
            .get_module("pydantic")
            .get_attribute("BaseModel")
            .get_object()
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
        package_dir: Path | None = None
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
            package_dir = entry.package_dir
        return package_dir, facades, runtime_facades

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

        Raises:
            ValueError: If an indexed module is unavailable.

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
