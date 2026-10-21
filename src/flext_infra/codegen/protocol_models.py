"""Project model contracts from the authenticated source graph.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from itertools import chain
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenProtocolModelRender


class FlextInfraCodegenProtocolModels(FlextInfraServiceBase[p.Infra.CodegenResult]):
    """Select source model identities and publish through ordinary conformance."""

    conform: Annotated[
        Callable[[p.Infra.CodegenConformRequest], p.Result[p.Infra.CodegenResult]],
        m.Field(
            ...,
            exclude=True,
            description="Caller-bound native conformance handler.",
        ),
    ]

    @override
    def execute(self) -> p.Result[p.Infra.CodegenResult]:
        """Execute the caller's canonical planner and publication owner.

        Returns:
            The unchanged conformance result from the bound public API.

        """
        return self.conform(
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
        """Select native Pydantic descendants and close their source annotations.

        Returns:
            Generated sources and their authenticated model identities.

        """
        result_type = r[t.Pair[t.MappingKV[Path, str], t.MappingKV[str, str]]]
        if not workspace.rope_project.authenticated_sources:
            return result_type.fail(
                "protocol projection requires authenticated native sources"
            )
        package_dir, facades = cls._facade_inventory(project, workspace)
        if package_dir is None or not {"m", "p"}.issubset(facades):
            return result_type.ok(({}, {}))
        inventory = cls._model_inventory(workspace, facades["m"])
        if inventory.failure:
            return result_type.from_failure(inventory)
        renderer = FlextInfraCodegenProtocolModelRender(
            project, workspace, inventory.value
        )
        directory = (
            package_dir / u.Infra.facade_families()["p"].directory
        ).relative_to(workspace.repository_root)
        selected = cls._select_models(renderer, facades, package_dir, directory)
        if selected.failure:
            return result_type.from_failure(selected)
        models, aliases = selected.value
        closed = cls._close_models(renderer, models, facades["p"], package_dir)
        if closed.failure:
            return result_type.from_failure(closed)
        return result_type.ok((
            renderer.render_member_modules(models, directory, aliases),
            {
                route: renderer.identity(binding.get_object())
                for route, binding in models.items()
            },
        ))

    @classmethod
    def _close_models(
        cls,
        renderer: p.Infra.CodegenProtocolModelRenderer,
        models: t.MutableMappingKV[str, p.Infra.RopePyName],
        facade: p.Infra.RopePyName,
        package: Path,
    ) -> p.Result[bool]:
        """Close model dependencies before choosing generated receiver names.

        Returns:
            Success only when every generated member has one native model identity.

        """
        renderer.imports.clear()
        # The same source renderer validates annotations and discovers every model
        # dependency, including specialized aliases and authored method signatures.
        visited_models: set[str] = set()
        while pending_models := sorted(set(models) - visited_models):
            for name in pending_models:
                binding = models[name]
                scope = binding.get_object().get_scope()
                if scope is None:
                    return r[bool].fail(
                        f"model has no authenticated declaration scope: {name}"
                    )
                renderer.render_protocol(name.rpartition(".")[2], binding, scope)
                visited_models.add(name)
            models.update(
                (route, renderer.declarations[route])
                for route in renderer.dependencies
                if not cls._external_port(facade, route, package)
            )
        members: t.MutableMappingKV[str, p.Infra.RopePyName] = {}
        for route, binding in models.items():
            member = route.rpartition(".")[2]
            previous = members.setdefault(member, binding)
            if not u.Infra.same_name(previous, binding):
                return r[bool].fail(
                    f"competing generated protocol member identities: {member}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _model_inventory(
        workspace: p.Infra.RopeWorkspaceDsl, facade: p.Infra.RopePyName
    ) -> p.Result[t.MappingKV[str, p.Infra.RopePyName]]:
        """Visit every public route while rejecting native ancestry cycles.

        Returns:
            Model bindings indexed by their public facade routes.

        """
        result_type = r[t.MappingKV[str, p.Infra.RopePyName]]
        base = u.Infra.qualified_name(
            workspace.rope_project, "BaseModel", module_name="pydantic"
        ).get_object()
        inventory: t.MutableMappingKV[str, p.Infra.RopePyName] = {}
        admissions: t.MutableMappingKV[p.Infra.RopePyObject, bool] = {}
        pending: list[
            t.Triple[str, p.Infra.RopePyName, t.VariadicTuple[p.Infra.RopePyObject]]
        ] = [("", facade, ())]
        while pending:
            prefix, namespace, ancestors = pending.pop()
            value = namespace.get_object()
            if not u.Infra.py_class(value) or value in ancestors:
                continue
            ancestry = (*ancestors, value)
            for name in sorted(value.get_attributes()):
                if name.startswith("_"):
                    continue
                route = f"{prefix}{name}"
                binding = FlextInfraCodegenProtocolModelRender.member(namespace, name)
                if binding is None:
                    # Inherited models from upstream facades (e.g. flext-core)
                    # are not native to this package's scope; skip them.
                    continue
                child = binding.get_object()
                admitted = admissions.get(child)
                if admitted is None:
                    admitted = base in u.Infra.class_ancestry(child)
                    admissions[child] = admitted
                if admitted:
                    previous = inventory.setdefault(route, binding)
                    if not u.Infra.same_name(previous, binding):
                        return result_type.fail(
                            "model facade route has competing native identities: "
                            f"{route}"
                        )
                # Models may also expose nested models through several public routes.
                if u.Infra.py_class(child):
                    pending.append((f"{route}.", binding, ancestry))
        return result_type.ok(inventory)

    @classmethod
    def _select_models(
        cls,
        renderer: p.Infra.CodegenProtocolModelRenderer,
        facades: t.MappingKV[str, p.Infra.RopePyName],
        package: Path,
        directory: Path,
    ) -> p.Result[
        t.Pair[t.MutableMappingKV[str, p.Infra.RopePyName], t.MappingKV[str, str]]
    ]:
        """Select consumed models and aliases without weakening authored ports.

        Returns:
            Selected model bindings and expanded alias annotations.

        """
        result_type = r[
            t.Pair[t.MutableMappingKV[str, p.Infra.RopePyName], t.MappingKV[str, str]]
        ]
        models: t.MutableMappingKV[str, p.Infra.RopePyName] = {}
        aliases: t.MutableMappingKV[str, str] = {}
        for name in sorted(
            cls._referenced_names(renderer.workspace, facades["p"], directory)
        ):
            if cls._external_port(facades["p"], name, package):
                continue
            candidate = FlextInfraCodegenProtocolModelRender.member(facades["m"], name)
            protocol = FlextInfraCodegenProtocolModelRender.member(facades["p"], name)
            if (
                protocol is not None
                and candidate is not None
                and any(
                    not member.startswith("_")
                    and member not in candidate.get_object().get_attributes()
                    for member in protocol.get_object().get_attributes()
                )
            ):
                manual = cls._manual_dependencies(renderer, protocol, name)
                if manual.failure:
                    return result_type.from_failure(manual)
                continue
            model_namespace = protocol_namespace = None
            if name not in renderer.declarations:
                model_namespace = cls._namespace_owner(
                    candidate, renderer.workspace.rope_project
                )
                protocol_namespace = cls._namespace_owner(
                    protocol, renderer.workspace.rope_project
                )
            # Empty markers alone do not prove that a payload reference is a namespace.
            if candidate is None or (
                model_namespace is not None
                and protocol_namespace is not None
                and (bool(model_namespace) or bool(protocol_namespace))
            ):
                manual = cls._manual_dependencies(
                    renderer,
                    protocol,
                    name,
                )
                if manual.failure:
                    return result_type.from_failure(manual)
            elif name in renderer.declarations:
                models[name] = renderer.declarations[name]
            else:
                alias = cls._model_alias(renderer, candidate, name)
                if alias.failure:
                    return result_type.from_failure(alias)
                aliases[name] = alias.value
        models.update(
            (route, renderer.declarations[route])
            for route in renderer.dependencies
            if not cls._external_port(facades["p"], route, package)
        )
        return result_type.ok((models, aliases))

    @classmethod
    def _namespace_owner(
        cls, binding: p.Infra.RopePyName | None, project: p.Infra.RopeProject
    ) -> t.MappingKV[str, p.Infra.RopePyName] | None:
        """Prove a type-publishing namespace without admitting instance contracts.

        Returns:
            Native public types, including empty marker owners, or no namespace proof.

        """
        if binding is None or not u.Infra.py_class(value := binding.get_object()):
            return None
        members = {
            name: member
            for name, member in value.get_attributes().items()
            if not name.startswith("_")
        }
        if any(
            not u.Infra.abstract_class(member.get_object())
            and u.Infra.annotation_alias_definition(member) is None
            for member in members.values()
        ):
            return None
        type_owner = u.Infra.qualified_name(project, "type", module_name="builtins")
        class_var = u.Infra.qualified_name(project, "ClassVar", module_name="typing")
        for owner in u.Infra.class_ancestry(value):
            if not u.Infra.py_class(owner):
                continue
            if not isinstance(owner, p.Infra.RopeSourceDefinition):
                return None
            node, scope = owner.get_ast(), owner.get_scope()
            if not isinstance(node, ast.ClassDef) or scope is None:
                return None
            if not all(
                cls._namespace_statement(statement, scope, (type_owner, class_var))
                for statement in node.body
            ):
                return None
        return members

    @classmethod
    def _namespace_statement(
        cls,
        statement: ast.stmt,
        scope: p.Infra.RopeScope,
        markers: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
    ) -> bool:
        """Admit only declarations and private implementation details in an owner.

        Returns:
            Whether the statement preserves a pure type-publishing namespace.

        """
        if isinstance(statement, ast.Pass | ast.ClassDef | ast.TypeAlias):
            return True
        if isinstance(statement, ast.Expr) and isinstance(
            statement.value, ast.Constant
        ):
            return (
                isinstance(statement.value.value, str)
                or statement.value.value is Ellipsis
            )
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
            return statement.name.startswith("_")
        return isinstance(statement, ast.Assign | ast.AnnAssign) and (
            cls._namespace_assignment(statement, scope, markers)
        )

    @classmethod
    def _namespace_assignment(
        cls,
        statement: ast.Assign | ast.AnnAssign,
        scope: p.Infra.RopeScope,
        markers: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
    ) -> bool:
        """Require public assignments to preserve native type declaration identity.

        Returns:
            Whether the assignment publishes only direct type aliases.

        """
        targets: t.SequenceOf[ast.expr]
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        else:
            targets = (statement.target,)
        if not all(isinstance(target, ast.Name) for target in targets):
            return False
        public = tuple(
            target.id
            for target in targets
            if isinstance(target, ast.Name) and not target.id.startswith("_")
        )
        if not public:
            return True
        if not isinstance(statement.value, ast.Name | ast.Attribute):
            return False
        return not isinstance(statement, ast.AnnAssign) or cls._namespace_annotation(
            statement.annotation, scope, public, markers
        )

    @staticmethod
    def _namespace_annotation(
        annotation: ast.expr,
        scope: p.Infra.RopeScope,
        public: t.StrSequence,
        markers: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
    ) -> bool:
        """Authenticate optional ClassVar wrapping and the declared native type target.

        Returns:
            Whether the annotation resolves to the same public type bindings.

        """
        type_owner, class_var = markers
        marker = (
            u.Infra.resolve_symbol(scope, annotation.value)
            if isinstance(annotation, ast.Subscript)
            else None
        )
        if (
            isinstance(annotation, ast.Subscript)
            and marker is not None
            and u.Infra.same_name(class_var, marker)
        ):
            annotation = annotation.slice
            marker = (
                u.Infra.resolve_symbol(scope, annotation.value)
                if isinstance(annotation, ast.Subscript)
                else None
            )
        if (
            not isinstance(annotation, ast.Subscript)
            or marker is None
            or not u.Infra.same_name(type_owner, marker)
        ):
            return False
        target = u.Infra.resolve_symbol(scope, annotation.slice)
        declared = scope.get_defined_names()
        return target is not None and all(
            name in declared and target.get_object() is declared[name].get_object()
            for name in public
        )

    @staticmethod
    def _manual_dependencies(
        renderer: p.Infra.CodegenProtocolModelRenderer,
        manual: p.Infra.RopePyName | None,
        name: str,
    ) -> p.Result[bool]:
        """Resolve annotations inside an authored port's original lexical scope.

        Returns:
            Success after preserving the authored contract's dependencies.

        """
        if manual is None:
            return r[bool].fail(
                f"referenced protocol p.{name} resolves to no declared model"
            )
        if u.Infra.assigned_name(manual) and len(manual.assignments) == 1:
            assignment = manual.assignments[0].ast_node
            module, _line = u.Infra.definition_location(manual)
            if isinstance(
                assignment, ast.Name | ast.Attribute
            ) and u.Infra.source_module(module):
                scope = u.Infra.scope_at(
                    module, u.Infra.source_offset(module.source_code, assignment)
                )
                declared = u.Infra.resolve_symbol(scope, assignment)
                if declared is None:
                    return r[bool].fail(
                        f"authored port alias has no source binding: {name}"
                    )
                manual = declared
        definition = manual.get_object()
        owner = definition.get_module()
        if not isinstance(definition, p.Infra.RopeSourceDefinition) or not (
            u.Infra.source_module(owner)
        ):
            return r[bool].fail(
                f"authored port has no native source declaration: {name}"
            )
        node = definition.get_ast()
        if not isinstance(node, ast.ClassDef):
            return r[bool].fail(
                f"authored port has no native class declaration: {name}"
            )
        walked = list(ast.walk(node))
        annotations = (
            child.annotation
            for child in walked
            if isinstance(child, ast.arg | ast.AnnAssign)
            and child.annotation is not None
        )
        returns = (
            child.returns
            for child in walked
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
            and child.returns is not None
        )
        bases = (
            base
            for child in walked
            if isinstance(child, ast.ClassDef)
            for base in child.bases
        )
        for annotation in chain(annotations, returns, bases):
            offset = u.Infra.source_offset(owner.source_code, annotation)
            renderer.source(ast.unparse(annotation), u.Infra.scope_at(owner, offset))
        return r[bool].ok(value=True)

    @classmethod
    def _model_alias(
        cls,
        renderer: p.Infra.CodegenProtocolModelRenderer,
        candidate: p.Infra.RopePyName,
        name: str,
    ) -> p.Result[str]:
        """Expand a declared alias and retain its exact model dependencies.

        Returns:
            The specialized structural annotation, or a typed declaration failure.

        """
        alias = renderer.alias_definition(candidate)
        if alias is None:
            return r[str].fail(cls._unmodeled_error(candidate, name))
        node, scope = alias
        if node.type_params:
            return r[str].fail(
                f"protocol union requires an explicit specialization: {name}"
            )
        before = set(renderer.dependencies)
        renderer.dependencies.clear()
        annotation = renderer.source(ast.unparse(node.value), scope)
        routes = tuple(renderer.dependencies)
        renderer.dependencies.update(before)
        if not routes:
            return r[str].fail(
                f"protocol alias has no source model dependencies: {name}"
            )
        return r[str].ok(annotation)

    @staticmethod
    def _unmodeled_error(candidate: p.Infra.RopePyName, name: str) -> str:
        """Describe native declaration provenance without spelling-based admission.

        Returns:
            The rejected declaration's source-kind and native ancestry.

        """
        declaration = candidate.get_object()
        module, line = u.Infra.definition_location(candidate)
        origin = (module.get_name() if module is not None else None, line)
        ancestors = tuple(
            (
                type(ancestor).__qualname__,
                ancestor.get_name() if u.Infra.abstract_class(ancestor) else None,
            )
            for ancestor in u.Infra.class_ancestry(declaration)
        )
        return (
            f"referenced protocol p.{name} is not a model declaration: "
            f"m.{name} resolved to {type(declaration).__qualname__} "
            f"at {origin!r}; native ancestry={ancestors!r}"
        )

    @classmethod
    def _external_port(
        cls, facade: p.Infra.RopePyName, route: str, package: Path
    ) -> bool:
        """Identify inherited contracts through the actual declaring resource.

        Returns:
            Whether the port is declared outside this package.

        """
        binding = FlextInfraCodegenProtocolModelRender.member(facade, route)
        owner = binding.get_object().get_module() if binding is not None else None
        resource = owner.get_resource() if owner is not None else None
        return resource is not None and not Path(resource.real_path).is_relative_to(
            package
        )

    @classmethod
    def plan_transfers(
        cls,
        project: p.Infra.ProjectSpec,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
        captured: p.Infra.CodemodSourceEpoch,
        model_identities: t.MappingKV[str, str],
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Derive native ownership transfers to the staged generated receivers.

        Returns:
            Source edits preserving original declarations and native identities.

        """
        package, facades = cls._facade_inventory(project, workspace)
        if package is None or "p" not in facades:
            return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(())
        rules, annotation_rules = cls._projection_rules(
            workspace, package, facades, model_identities
        )
        transferred = u.Infra.plan_contract_rules(
            workspace, sources, rules, captured=captured
        )
        if transferred.failure:
            return transferred
        return cls._rewrite_annotations(
            workspace, sources, annotation_rules, captured, transferred.value
        )

    @staticmethod
    def _generated_receivers(
        workspace: p.Infra.RopeWorkspaceDsl, package: Path
    ) -> t.SequenceOf[t.Quad[str, str, str, str]]:
        """Resolve staged declarations through their native receiver bindings.

        Returns:
            Module, wrapper, member and exact native receiver identity.

        Raises:
            ValueError: A staged receiver has no physical or semantic binding.
            TypeError: A staged receiver has no native module AST.

        """
        receivers: list[t.Quad[str, str, str, str]] = []
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
            declarations = (
                (wrapper.name, declaration.name)
                for wrapper in tree.body
                if isinstance(wrapper, ast.ClassDef)
                for declaration in wrapper.body
                if isinstance(declaration, ast.ClassDef)
            )
            for wrapper, declaration in declarations:
                generated = u.Infra.expression_name(
                    module.get_scope(), f"{wrapper}.{declaration}"
                )
                if generated is None:
                    msg = "generated protocol has no staged native binding"
                    raise ValueError(msg)
                receivers.append((
                    entry.module_name,
                    wrapper,
                    declaration,
                    FlextInfraCodegenProtocolModelRender.identity(
                        generated.get_object()
                    ),
                ))
        return receivers

    @classmethod
    def _projection_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        package: Path,
        facades: t.MappingKV[str, p.Infra.RopePyName],
        model_identities: t.MappingKV[str, str],
    ) -> t.Pair[list[p.Infra.RopeContractRule], list[p.Infra.RopeContractRule]]:
        """Bind model routes to their staged receivers before source rewrites.

        Returns:
            Authored ownership transfers and model annotation rewrites.

        Raises:
            ValueError: A model's native identity changed during staging.

        """
        rules: list[p.Infra.RopeContractRule] = []
        annotation_rules: list[p.Infra.RopeContractRule] = []
        for target in cls._generated_receivers(workspace, package):
            for route, model_identity in model_identities.items():
                if route.rpartition(".")[2] != target[2]:
                    continue
                model = FlextInfraCodegenProtocolModelRender.member(facades["m"], route)
                if model is None or (
                    FlextInfraCodegenProtocolModelRender.identity(model.get_object())
                    != model_identity
                ):
                    msg = f"staged model identity changed during projection: {route}"
                    raise ValueError(msg)
                annotation_rules.append(
                    cls._annotation_rule(target, model_identity, len(annotation_rules))
                )
                previous = FlextInfraCodegenProtocolModelRender.member(
                    facades["p"], route
                )
                if previous is not None:
                    transfer = cls._authored_transfer(
                        (previous, model), route, package, target, len(rules)
                    )
                    if transfer is not None:
                        rules.append(transfer)
        return rules, annotation_rules

    @staticmethod
    def _annotation_rule(
        target: t.Quad[str, str, str, str], identity: str, index: int
    ) -> p.Infra.RopeContractRule:
        """Describe a model annotation rewrite with exact native receiver binding.

        Returns:
            The declaration-driven annotation rule.

        """
        module, wrapper, member, receiver_identity = target
        receiver = f"_projected_model_{index}"
        goal = f"{receiver}.{member}"
        return m.Infra.RopeContractRule(
            id=f"project-model-annotation-{index}",
            pattern=f"${receiver}",
            goal=goal,
            arguments={"receiver": f"name={identity}"},
            imports={receiver: f"from {module} import {wrapper} as {receiver}"},
            bindings={goal: receiver_identity},
            families=("p",),
        )

    @classmethod
    def _authored_transfer(
        cls,
        bindings: t.Pair[p.Infra.RopePyName, p.Infra.RopePyName],
        route: str,
        package: Path,
        target: t.Quad[str, str, str, str],
        index: int,
    ) -> p.Infra.RopeContractRule | None:
        """Retire only an authenticated local structural model projection.

        Returns:
            The ownership transfer, or no transfer for an externally owned binding.

        """
        previous, model = bindings
        owner = cls._authored_owner(previous, model, route, package)
        if owner is None:
            return None
        identity = FlextInfraCodegenProtocolModelRender.identity(previous.get_object())
        alias = f"_projected_{index}"
        goal = f"{alias}.{target[2]}"
        return m.Infra.RopeContractRule(
            id=f"project-model-port-{index}",
            pattern="${receiver}",
            goal=goal,
            arguments={"receiver": f"name={identity}"},
            imports={alias: f"from {target[0]} import {target[1]} as {alias}"},
            bindings={goal: target[3]},
            ownership_transfer=(
                owner.get_name(),
                identity.removeprefix(f"{owner.get_name()}."),
            ),
        )

    @staticmethod
    def _authored_owner(
        previous: p.Infra.RopePyName,
        model: p.Infra.RopePyName,
        route: str,
        package: Path,
    ) -> p.Infra.RopeParsedModule | None:
        """Prove a local projection contains only its model's structural contract.

        Returns:
            The authored owner, or no local ownership transfer.

        Raises:
            ValueError: A local declaration is not a pure structural model port.

        """
        if u.Infra.same_name(previous, model):
            return None
        owner = previous.get_object().get_module()
        if not u.Infra.source_module(owner):
            return None
        resource = owner.get_resource()
        if resource is None or not Path(resource.real_path).is_relative_to(
            package / u.Infra.facade_families()["p"].directory
        ):
            return None
        if owner.source_code.startswith(c.Infra.AUTOGEN_HEADERS):
            return None
        protocol_base = u.Infra.qualified_name(
            owner.pycore.project, "Protocol", module_name="typing"
        ).get_object()
        if protocol_base not in u.Infra.class_ancestry(previous.get_object()):
            msg = f"authored projection has no native protocol ancestry: {route}"
            raise ValueError(msg)
        unexpected = {
            name
            for name in previous.get_object().get_attributes()
            if not name.startswith("_")
            and name not in model.get_object().get_attributes()
        }
        if unexpected:
            msg = (
                f"operational port cannot be retired as model data: {route}: "
                f"{sorted(unexpected)}"
            )
            raise ValueError(msg)
        return owner

    @staticmethod
    def _rewrite_annotations(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
        annotation_rules: t.SequenceOf[p.Infra.RopeContractRule],
        captured: p.Infra.CodemodSourceEpoch,
        transferred: t.VariadicTuple[p.Infra.SemanticMigrationEdit],
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Compose ownership, class-alias and annotation edits without losing evidence.

        Returns:
            One cumulative source edit per destination with original evidence intact.

        """
        updated = dict(sources)
        for edit in transferred:
            updated[edit.file_path] = edit.updated_source
        changed = {edit.file_path: edit for edit in transferred}
        for aliases_only in (True, False):
            rewritten = u.Infra.plan_contract_rules(
                workspace,
                updated,
                annotation_rules,
                captured=captured,
                options=m.Infra.ContractAdmissionOptions(
                    annotation_only=not aliases_only,
                    class_alias_only=aliases_only,
                ),
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
    ) -> t.Pair[Path | None, t.MappingKV[str, p.Infra.RopePyName]]:
        facades: t.MutableMappingKV[str, p.Infra.RopePyName] = {}
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

    @classmethod
    def _referenced_names(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        binding: p.Infra.RopePyName,
        directory: Path,
    ) -> set[str]:
        found: set[str] = set()
        for entry in workspace.modules():
            resource = workspace.resource(entry.file_path)
            if resource is None:
                msg = f"indexed module unavailable: {entry.file_path}"
                raise ValueError(msg)
            module = u.Infra.resolve_pymodule(workspace.rope_project, resource)
            source = module.source_code
            if entry.file_path.is_relative_to(
                workspace.repository_root / directory
            ) and source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
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
