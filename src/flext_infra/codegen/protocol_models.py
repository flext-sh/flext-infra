"""Project model contracts from the authenticated source graph.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from itertools import chain
from pathlib import Path

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenProtocolModelRender


class FlextInfraCodegenProtocolModels(FlextInfraServiceBase):
    """Select source model identities and publish through ordinary conformance."""

    def execute(self) -> p.Result[p.Infra.CodegenResult]:
        """Execute the canonical planner, transaction and publication owner."""
        from flext_infra import FlextInfra

        return FlextInfra(repository_root=self.repository_root).codegen_conform(
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

    @classmethod
    def render_modules(
        cls, project: p.Infra.ProjectSpec, workspace: p.Infra.RopeWorkspaceDsl
    ) -> p.Result[t.Pair[t.MappingKV[Path, str], t.MappingKV[str, str]]]:
        """Select native Pydantic descendants and close their source annotations."""
        result_type = r[t.Pair[t.MappingKV[Path, str], t.MappingKV[str, str]]]
        if not workspace.rope_project.authenticated_sources:
            return result_type.fail(
                "protocol projection requires authenticated native sources"
            )
        package_dir, facades = cls._facade_inventory(project, workspace)
        if package_dir is None or not {"m", "p"}.issubset(facades):
            return result_type.ok(({}, {}))
        base = u.Infra.qualified_name(
            workspace.rope_project, "BaseModel", module_name="pydantic"
        ).get_object()
        inventory: dict[str, p.Infra.RopePyName] = {}
        pending = [("", facades["m"])]
        visited: set[str] = set()
        while pending:
            prefix, namespace = pending.pop()
            value = namespace.get_object()
            if not u.Infra.py_class(value):
                continue
            identity = FlextInfraCodegenProtocolModelRender.identity(value)
            if identity in visited:
                continue
            visited.add(identity)
            for name, binding in sorted(value.get_attributes().items()):
                if name.startswith("_"):
                    continue
                route = f"{prefix}{name}"
                child = binding.get_object()
                if base in u.Infra.class_ancestry(child):
                    existing = inventory.get(route)
                    if existing is not None and not u.Infra.same_name(
                        existing, binding
                    ):
                        return result_type.fail(
                            f"model facade route has competing native identities: {route}"
                        )
                    inventory[route] = binding
                elif u.Infra.py_class(child):
                    pending.append((f"{route}.", binding))
        renderer = FlextInfraCodegenProtocolModelRender(project, workspace, inventory)
        directory = (
            package_dir / u.Infra.facade_families()["p"].directory
        ).relative_to(workspace.repository_root)
        models: dict[str, p.Infra.RopePyName] = {}
        aliases: dict[str, str] = {}

        def external_port(route: str) -> bool:
            binding = cls._member(facades["p"], route)
            owner = binding.get_object().get_module() if binding is not None else None
            resource = owner.get_resource() if owner is not None else None
            return resource is not None and not Path(resource.real_path).is_relative_to(
                package_dir
            )

        for name in sorted(cls._referenced_names(workspace, facades["p"], directory)):
            if external_port(name):
                continue
            manual = cls._member(facades["p"], name)
            candidate = cls._member(facades["m"], name)
            if candidate is None:
                if manual is not None:
                    definition = manual.get_object()
                    owner = definition.get_module()
                    if isinstance(
                        definition, p.Infra.RopeSourceDefinition
                    ) and u.Infra.source_module(owner):
                        node = definition.get_ast()
                        if (
                            isinstance(node, ast.ClassDef)
                            and node.end_lineno is not None
                        ):
                            for begin, end, line in u.Infra.annotation_regions(
                                owner.source_code, owner
                            ):
                                if node.lineno <= line <= node.end_lineno:
                                    renderer.source(
                                        owner.source_code[begin:end],
                                        u.Infra.scope_at(owner, begin),
                                    )
                    continue
                return result_type.fail(
                    f"referenced protocol p.{name} resolves to no declared model"
                )
            if name in inventory:
                models[name] = inventory[name]
                continue
            alias = renderer.alias_definition(candidate)
            if alias is None:
                return result_type.fail(
                    f"referenced protocol p.{name} is not a model declaration"
                )
            node, scope = alias
            if node.type_params:
                return result_type.fail(
                    f"protocol union requires an explicit specialization: {name}"
                )
            before = set(renderer.dependencies)
            renderer.dependencies.clear()
            aliases[name] = renderer.source(ast.unparse(node.value), scope)
            routes = tuple(sorted(renderer.dependencies))
            renderer.dependencies.update(before)
            if not routes:
                return result_type.fail(
                    f"protocol alias has no source model dependencies: {name}"
                )
            models.update(
                (route, inventory[route])
                for route in routes
                if not external_port(route)
            )
        models.update(
            (route, inventory[route])
            for route in renderer.dependencies
            if not external_port(route)
        )
        renderer.imports.clear()
        # The same source renderer validates annotations and discovers every model
        # dependency, including specialized aliases and authored method signatures.
        visited_models: set[str] = set()
        while pending_models := sorted(set(models) - visited_models):
            for name in pending_models:
                binding = models[name]
                scope = binding.get_object().get_scope()
                if scope is None:
                    return result_type.fail(
                        f"model has no authenticated declaration scope: {name}"
                    )
                renderer._render_protocol(name.rpartition(".")[2], binding, scope)
                visited_models.add(name)
            models.update(
                (route, inventory[route])
                for route in renderer.dependencies
                if not external_port(route)
            )
        members: dict[str, p.Infra.RopePyName] = {}
        for route, binding in models.items():
            member = route.rpartition(".")[2]
            previous = members.setdefault(member, binding)
            if not u.Infra.same_name(previous, binding):
                return result_type.fail(
                    f"competing generated protocol member identities: {member}"
                )
        return result_type.ok((
            renderer.render_member_modules(models, directory, aliases),
            {
                route: renderer.identity(binding.get_object())
                for route, binding in models.items()
            },
        ))

    @classmethod
    def plan_transfers(
        cls,
        project: p.Infra.ProjectSpec,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
        captured: p.Infra.CodemodSourceEpoch,
        model_identities: t.MappingKV[str, str],
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Derive native ownership transfers to the staged generated receivers."""
        package, facades = cls._facade_inventory(project, workspace)
        if package is None or "p" not in facades:
            return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(())
        rules: list[m.Infra.RopeContractRule] = []
        annotation_rules: list[m.Infra.RopeContractRule] = []
        for entry in workspace.modules():
            if (
                entry.file_path.parent
                != package / u.Infra.facade_families()["p"].directory
            ):
                continue
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"staged protocol receiver is unavailable: {entry.file_path}"
                raise ValueError(msg)
            module = u.Infra.resolve_pymodule(workspace.rope_project, resource)
            if not module.source_code.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            tree = module.get_ast()
            if not isinstance(tree, ast.Module):
                msg = "staged receiver has no native module AST"
                raise TypeError(msg)
            for wrapper in tree.body:
                if not isinstance(wrapper, ast.ClassDef):
                    continue
                for declaration in wrapper.body:
                    if not isinstance(declaration, ast.ClassDef):
                        continue
                    generated = u.Infra.expression_name(
                        module.get_scope(), f"{wrapper.name}.{declaration.name}"
                    )
                    if generated is None:
                        msg = "generated protocol has no staged native binding"
                        raise ValueError(msg)
                    # The composing owner identifies the public namespace from the
                    # model's published native route, not the generated file name.
                    receiver_identity = FlextInfraCodegenProtocolModelRender.identity(
                        generated.get_object()
                    )
                    for route, model_identity in model_identities.items():
                        if route.rpartition(".")[2] != declaration.name:
                            continue
                        previous = cls._member(facades["p"], route)
                        model = cls._member(facades["m"], route)
                        if (
                            model is None
                            or FlextInfraCodegenProtocolModelRender.identity(
                                model.get_object()
                            )
                            != model_identity
                        ):
                            msg = f"staged model identity changed during projection: {route}"
                            raise ValueError(msg)
                        receiver = f"_projected_model_{len(annotation_rules)}"
                        goal = f"{receiver}.{declaration.name}"
                        annotation_rules.append(
                            m.Infra.RopeContractRule(
                                id=f"project-model-annotation-{len(annotation_rules)}",
                                pattern=f"${receiver}",
                                goal=goal,
                                arguments={"receiver": f"name={model_identity}"},
                                imports={
                                    receiver: f"from {entry.module_name} import {wrapper.name} as {receiver}"
                                },
                                bindings={goal: receiver_identity},
                                families=("p",),
                            )
                        )
                        if previous is None:
                            continue
                        if u.Infra.same_name(previous, model):
                            # A leaked concrete-model alias is not a protocol
                            # declaration and must never retire the schema owner.
                            continue
                        owner = previous.get_object().get_module()
                        owned_resource = (
                            owner.get_resource() if owner is not None else None
                        )
                        if owned_resource is None or not Path(
                            owned_resource.real_path
                        ).is_relative_to(
                            package / u.Infra.facade_families()["p"].directory
                        ):
                            continue
                        if owned_resource.read().startswith(c.Infra.AUTOGEN_HEADERS):
                            continue
                        protocol_base = u.Infra.qualified_name(
                            workspace.rope_project, "Protocol", module_name="typing"
                        ).get_object()
                        if protocol_base not in u.Infra.class_ancestry(
                            previous.get_object()
                        ):
                            msg = f"authored projection has no native protocol ancestry: {route}"
                            raise ValueError(msg)
                        unexpected = {
                            name
                            for name in previous.get_object().get_attributes()
                            if not name.startswith("_")
                            and name not in model.get_object().get_attributes()
                        }
                        if unexpected:
                            msg = f"operational port cannot be retired as model data: {route}: {sorted(unexpected)}"
                            raise ValueError(msg)
                        identity = FlextInfraCodegenProtocolModelRender.identity(
                            previous.get_object()
                        )
                        module_name = owner.get_name()
                        expression = identity.removeprefix(f"{module_name}.")
                        goal = f"_projected_{len(rules)}.{declaration.name}"
                        rules.append(
                            m.Infra.RopeContractRule(
                                id=f"project-model-port-{len(rules)}",
                                pattern=f"${receiver}",
                                goal=goal,
                                arguments={"receiver": f"name={identity}"},
                                imports={
                                    goal.partition(".")[
                                        0
                                    ]: f"from {entry.module_name} import {wrapper.name} as {goal.partition('.')[0]}"
                                },
                                bindings={goal: receiver_identity},
                                ownership_transfer=(module_name, expression),
                            )
                        )
        transferred = u.Infra.plan_contract_rules(
            workspace, sources, rules, captured=captured
        )
        if transferred.failure:
            return transferred
        updated = dict(sources)
        for edit in transferred.value:
            updated[edit.file_path] = edit.updated_source
        changed = {edit.file_path: edit for edit in transferred.value}
        for aliases_only in (True, False):
            rewritten = u.Infra.plan_contract_rules(
                workspace,
                updated,
                annotation_rules,
                captured=captured,
                annotation_only=not aliases_only,
                class_alias_only=aliases_only,
            )
            if rewritten.failure:
                return rewritten
            for edit in rewritten.value:
                previous = changed.get(edit.file_path)
                changed[edit.file_path] = (
                    edit
                    if previous is None
                    else m.Infra.SemanticMigrationEdit(
                        file_path=edit.file_path,
                        original_source=previous.original_source,
                        updated_source=edit.updated_source,
                        retire_file=previous.retire_file,
                        source_states=tuple(edit.source_states),
                        changes=(*previous.changes, *edit.changes),
                    )
                )
                updated[edit.file_path] = edit.updated_source
        return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(
            tuple(changed.values())
        )

    @staticmethod
    def _facade_inventory(
        project: p.Infra.ProjectSpec, workspace: p.Infra.RopeWorkspaceDsl
    ) -> tuple[Path | None, dict[str, p.Infra.RopePyName]]:
        facades: dict[str, p.Infra.RopePyName] = {}
        package_dir: Path | None = None
        for entry in workspace.modules():
            if entry.package_name != project.package_name:
                continue
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"indexed module unavailable: {entry.file_path}"
                raise ValueError(msg)
            source = resource.read()
            exports = u.Infra.public_export_names_source(source)
            if not {"m", "p"}.intersection(exports) or not any(
                isinstance(node, ast.ClassDef) for node in ast.parse(source).body
            ):
                continue
            owner = u.Infra.published_facade_owner(workspace.rope_project, resource)
            if owner is not None:
                facades[owner[0]] = u.Infra.resolve_pymodule(
                    workspace.rope_project, resource
                ).get_attribute(owner[1])
                package_dir = entry.package_dir
        return package_dir, facades

    @staticmethod
    def _member(binding: p.Infra.RopePyName, name: str) -> p.Infra.RopePyName | None:
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
                    source, workspace.rope_project, module
                )
                for begin, end in u.Infra.reference_regions(expression)
            )
            for primary, scope in chain(primaries, quoted):
                name, separator, tail = primary.partition(".")
                if (
                    separator
                    and tail
                    and u.Infra.same_name(binding, u.Infra.expression_name(scope, name))
                ):
                    found.add(tail)
        return found


__all__: list[str] = ["FlextInfraCodegenProtocolModels"]
