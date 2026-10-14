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
from typing import TypeAliasType, get_args, override

from flext_cli import cli

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra.codegen import (
    FlextInfraCodegenProtocolModelAnnotations,
    FlextInfraCodegenProtocolModelRender,
)
from flext_infra.workspace.rope import FlextInfraRopeWorkspace


class FlextInfraCodegenProtocolModels(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Assemble the member's generated ``p`` layer from validated models."""

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Assemble generated protocol modules for the member repository.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        modules: dict[str, str] = {}
        with FlextInfraRopeWorkspace.open_workspace(self.repository_root) as workspace:
            targets = self._targets(workspace)
            if not targets:
                return r[t.Cli.ResultValue].fail("no declared model facade in project")
            for target in targets:
                resolved = self._resolve_models(workspace, target)
                if resolved.failure:
                    return r[t.Cli.ResultValue].from_failure(resolved)
                if resolved.value:
                    modules.update(
                        FlextInfraCodegenProtocolModelRender.render_member_modules(
                            resolved.value,
                            target,
                        ),
                    )
        return self._settle(self.repository_root, modules, dry=self.effective_dry_run)

    @classmethod
    def _targets(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> t.SequenceOf[p.Infra.ProtocolModelTarget]:
        """Derive facade roots and namespaces from exported Rope identities."""
        targets: list[p.Infra.ProtocolModelTarget] = []
        families = u.Infra.facade_families()
        for entry in workspace.modules():
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"indexed module unavailable: {entry.file_path}"
                raise ValueError(msg)
            owner = u.Infra.published_facade_owner(workspace.rope_project, resource)
            if owner is None or owner[0] != "m":
                continue
            aliases: dict[str, str] = {}
            for sibling in workspace.modules():
                if sibling.package_dir == entry.package_dir:
                    sibling_resource = workspace.resource(sibling.file_path)
                    if sibling_resource is None:
                        msg = f"indexed module unavailable: {sibling.file_path}"
                        raise ValueError(msg)
                    sibling_owner = u.Infra.published_facade_owner(
                        workspace.rope_project,
                        sibling_resource,
                    )
                    if sibling_owner is not None:
                        aliases[sibling_owner[0]] = (
                            f"{sibling.module_name}.{sibling_owner[1]}"
                        )
            facade = getattr(import_module(entry.module_name), owner[1])
            namespaces = (
                "",
                *u.Infra.resolve_class_nested_classes(
                    workspace.rope_project,
                    resource,
                    owner[1],
                ),
            )
            for namespace in namespaces:
                if namespace and (
                    cls._model_leaves(getattr(facade, namespace))
                    or not getattr(facade, namespace).__module__.startswith(
                        f"{entry.package_name}.",
                    )
                ):
                    continue
                targets.append(
                    FlextInfraCodegenProtocolModelAnnotations.ProtocolModelTarget(
                        package_name=entry.package_name,
                        protocol_directory=(
                            entry.package_dir / f"_{families['p'].module}"
                        ).relative_to(workspace.repository_root),
                        facade_container=owner[1].removesuffix(families["m"].suffix),
                        package_module_prefix=f"{entry.package_name}.",
                        protocol_ref_prefix=f"p.{namespace}" if namespace else "p",
                        models_facade_name="m",
                        facade_probes=tuple(sorted(aliases.items())),
                    ),
                )
        return tuple(targets)

    @classmethod
    def _resolve_models(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        target: p.Infra.ProtocolModelTarget,
    ) -> p.Result[t.SequenceOf[p.Infra.ProtocolModel]]:
        """Resolve every referenced protocol name against the models facade.

        Returns:
            The resulting ``p.Result[t.SequenceOf[p.Infra.ProtocolModel]]``.

        """
        referenced = cls._referenced_names(workspace, target)
        manual = cls._manual_protocol_names(workspace, target)
        wanted = sorted(
            name for name in referenced if name.partition(".")[0] not in manual
        )
        if not wanted:
            return r[t.SequenceOf[p.Infra.ProtocolModel]].ok(())
        owner_path = dict(target.facade_probes)["m"]
        module_name, _, owner_name = owner_path.rpartition(".")
        container = getattr(import_module(module_name), owner_name)
        for namespace in target.protocol_ref_prefix.split(".")[1:]:
            container = getattr(container, namespace)
        models: list[p.Infra.ProtocolModel] = []
        for name in wanted:
            candidate = container
            for component in name.split("."):
                candidate = getattr(candidate, component, None)
            if candidate is None:
                return r[t.SequenceOf[p.Infra.ProtocolModel]].fail(
                    f"referenced protocol {target.protocol_ref_prefix}.{name} "
                    f"resolves to no model on {target.facade_container}Models",
                )
            models.extend(cls._model_leaves(candidate))
        return r[t.SequenceOf[p.Infra.ProtocolModel]].ok(tuple(models))

    @classmethod
    def _model_leaves(
        cls,
        candidate: p.AttributeProbe,
    ) -> t.VariadicTuple[p.Infra.ProtocolModel]:
        """Expand discriminated-union aliases into their leaf models.

        Returns:
            The resulting ``t.VariadicTuple[p.Infra.ProtocolModel]``.

        """
        if isinstance(candidate, TypeAliasType):
            value = candidate.__value__
            if isinstance(value, UnionType):
                return tuple(
                    leaf
                    for leaf in get_args(value)
                    if isinstance(leaf, type) and issubclass(leaf, m.BaseModel)
                )
            candidate = value
        if isinstance(candidate, type) and issubclass(candidate, m.BaseModel):
            return (candidate,)
        return ()

    @classmethod
    def _referenced_names(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        target: p.Infra.ProtocolModelTarget,
    ) -> set[str]:
        """Read actual imported protocol primaries from every indexed Python root."""
        found: set[str] = set()
        owner = dict(target.facade_probes).get("p")
        if owner is None:
            msg = f"no declared protocols facade for {target.package_name}"
            raise ValueError(msg)
        module_name, _, class_name = owner.rpartition(".")
        protocol_entry = next(
            item for item in workspace.modules() if item.module_name == module_name
        )
        protocol_resource = workspace.resource(protocol_entry.file_path)
        if protocol_resource is None:
            msg = f"indexed facade unavailable: {protocol_entry.file_path}"
            raise ValueError(msg)
        binding = u.Infra.resolve_pymodule(
            workspace.rope_project, protocol_resource
        ).get_attribute(class_name)
        references = FlextInfraUtilitiesSemanticFamilyTypeReferences
        namespace = target.protocol_ref_prefix.partition(".")[2]
        for entry in workspace.modules():
            if entry.file_path.is_relative_to(
                workspace.repository_root / target.protocol_directory
            ):
                continue
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"indexed module unavailable: {entry.file_path}"
                raise ValueError(msg)
            module = u.Infra.resolve_pymodule(workspace.rope_project, resource)
            source = module.source_code
            primaries = (
                (source[begin:end], u.Infra.scope_at(module, begin))
                for begin, end in references.reference_regions(source)
            )
            quoted = (
                (rendered[begin:end], scope)
                for node, scope, _line in references.scoped_quoted_type_nodes(
                    source,
                    workspace.rope_project,
                    module,
                )
                for rendered in (ast.unparse(node),)
                for begin, end in references.reference_regions(rendered)
            )
            for primary, scope in chain(primaries, quoted):
                name, separator, tail = primary.partition(".")
                if not separator or not u.Infra.same_name(binding, scope.lookup(name)):
                    continue
                if namespace:
                    tail = (
                        tail.removeprefix(f"{namespace}.")
                        if tail.startswith(f"{namespace}.")
                        else ""
                    )
                if tail:
                    found.add(tail)
        return found

    @classmethod
    def _manual_protocol_names(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        target: p.Infra.ProtocolModelTarget,
    ) -> set[str]:
        """Honor existing protocol members through their resolved inheritance."""
        owner = dict(target.facade_probes).get("p")
        if owner is None:
            return set()
        module_name, _, class_name = owner.rpartition(".")
        module = next(
            item for item in workspace.modules() if item.module_name == module_name
        )
        resource = workspace.resource(module.file_path)
        if resource is None:
            msg = f"indexed facade unavailable: {module.file_path}"
            raise ValueError(msg)
        facade = (
            u.Infra
            .resolve_pymodule(workspace.rope_project, resource)
            .get_attribute(class_name)
            .get_object()
        )
        for namespace in target.protocol_ref_prefix.split(".")[1:]:
            member = facade.get_attributes().get(namespace)
            if member is None:
                return set()
            facade = member.get_object()
        return {
            name
            for name, member in facade.get_attributes().items()
            if (declaring_module := member.get_object().get_module()) is not None
            and (declaring_resource := declaring_module.get_resource()) is not None
            and not declaring_resource.read().startswith(c.Infra.AUTOGEN_HEADERS)
        }

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
        changed: list[str] = []
        for relative, content in sorted(modules.items()):
            destination = root / relative
            if (
                destination.is_file()
                and destination.read_text(encoding="utf-8") == content
            ):
                continue
            changed.append(relative)
            if not dry:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
        if changed and dry:
            return r[t.Cli.ResultValue].fail(
                f"{len(changed)} generated protocol module(s) drifted: "
                f"{', '.join(changed)}",
            )
        verb = "checked" if dry else "assembled"
        cli.display_text(
            f"protocol-models: {verb} {len(modules)} module(s), {len(changed)} updated",
        )
        return r[t.Cli.ResultValue].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenProtocolModels"]
