"""Native declaration retirement elected by project-owned contract rules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from flext_infra import c, m, p, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
    FlextInfraUtilitiesTypesSemanticNesting,
)


class FlextInfraUtilitiesSemanticDeclarationRetirement(
    FlextInfraUtilitiesSemanticDeclarationRelocation,
):
    """Complete the existing contract planner through the native relocation owner."""

    @staticmethod
    def contract_assignment(
        binding: p.Infra.RopePyName,
    ) -> (
        tuple[
            p.Infra.RopeSourceModule,
            p.Infra.RopeScope,
            p.Infra.RopeSourceAssignmentLayout,
        ]
        | None
    ):
        """Locate one original alias or direct assignment through native metadata.

        Returns:
            Its source module, lexical scope and unique native assignment layout.

        Raises:
            ValueError: If an elected binding has ambiguous direct assignments.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        alias = runtime.annotation_alias_definition(binding)
        module, line = binding.get_definition_location()
        if alias is not None:
            _declaration, scope = alias
            module = scope.pyobject.get_module()
        elif isinstance(module, p.Infra.RopeSourceModule) and line is not None:
            scope = module.get_scope().get_inner_scope_for_line(line)
        else:
            return None
        if not isinstance(module, p.Infra.RopeSourceModule) or scope.get_kind() not in {
            "Module",
            "Class",
        }:
            return None
        layouts = tuple(
            layout
            for layout in module.get_source_binding_index().assignment_layouts(
                scope, resolve_values=True
            )
            if layout.kind in {"TypeAlias", "Assign"}
            and len(layout.targets) == 1
            and runtime.same_name(
                binding, scope.get_defined_names().get(layout.targets[0][0])
            )
        )
        if len(layouts) > 1:
            message = "ownership transfer has ambiguous assignment declarations"
            raise ValueError(message)
        return (module, scope, layouts[0]) if layouts else None

    @classmethod
    def contract_transfer_module(
        cls, binding: p.Infra.RopePyName
    ) -> p.Infra.RopeSourceModule:
        """Retain native source ownership without inferring a lazy alias value.

        Returns:
            The original source module of a class, callable or assignment.

        Raises:
            TypeError: If the binding has no governed native source declaration.

        """
        assignment = cls.contract_assignment(binding)
        if assignment is not None:
            return assignment[0]
        value = binding.get_object()
        types = FlextInfraUtilitiesRopeRuntimeTypes
        if types.py_function(value) or types.py_class(value):
            return types.require_source_module(value.get_module())
        message = "ownership transfer requires a native source declaration"
        raise TypeError(message)

    @classmethod
    def _retiring_binding_name(cls, binding: p.Infra.RopePyName) -> str:
        """Read the original declaration name without alias-value inference.

        Returns:
            The exact native assignment target or class/callable name.

        """
        assignment = cls.contract_assignment(binding)
        if assignment is not None:
            return assignment[2].targets[0][0]
        return FlextInfraUtilitiesRopeRuntimeTypes.require_named_object(
            binding.get_object(), "retiring declaration"
        ).get_name()

    @staticmethod
    def contract_transfer_binding(
        project: p.Infra.RopeProject,
        identity: tuple[str, str],
        owned_modules: Mapping[str, t.Infra.RopeSourcePath],
    ) -> p.Infra.RopePyName | None:
        """Resolve only an original owned resource, never an installed SDK fallback.

        Returns:
            The owned native binding, or ``None`` when the provider or any
            expression part is not an owned original.

        """
        provider, expression = identity
        path = owned_modules.get(provider)
        if path is None:
            return None
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            ),
            path,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        return FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            module.get_scope(), expression
        )

    @classmethod
    def retire_contract_owners(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        proposed: MutableMapping[t.Infra.RopeSourcePath, str],
        rules: Sequence[p.Infra.RopeContractRule],
        owned_modules: Mapping[str, t.Infra.RopeSourcePath],
    ) -> tuple[t.Infra.RopeImplementationPaths, t.Infra.RopeImplementationPaths]:
        """Retire elected declarations only after native receiver completeness.

        Returns:
            The retired wrapper paths and the transfer destination paths. An
            external library owner, missing receiver or unproven transfer
            raises ``TypeError`` or ``ValueError``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        retired: t.Infra.RopeMutablePaths = set()
        destinations: t.Infra.RopeMutablePaths = set()
        source_project = workspace.rope_project
        for rule in rules:
            if rule.ownership_transfer is None:
                continue
            owner = cls.contract_rule_root(
                workspace.repository_root, rule, source_project=source_project
            )
            project = runtime.snapshot_project(
                workspace.rope_project,
                proposed,
            )
            try:
                path, destination = cls._retire_contract_rule(
                    project,
                    rule,
                    proposed,
                    (owner, owned_modules),
                    destinations=tuple(
                        runtime.qualified_name(project, identity)
                        for transfer in rules
                        if transfer.ownership_transfer is not None
                        for identity in transfer.bindings.values()
                    ),
                )
                if path is not None:
                    retired.add(path)
                if destination is not None:
                    destinations.add(destination)
            finally:
                project.close()

        return frozenset(retired), frozenset(destinations)

    @classmethod
    def _retire_contract_rule(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        proposed: MutableMapping[t.Infra.RopeSourcePath, str],
        ownership: tuple[Path, Mapping[str, t.Infra.RopeSourcePath]],
        *,
        destinations: Sequence[p.Infra.RopePyName],
    ) -> tuple[t.Infra.RopeSourcePath | None, t.Infra.RopeSourcePath | None]:
        """Retire one elected ownership transfer after receiver completeness.

        Returns:
            The retired wrapper path, when the wrapper emptied, and the
            transfer destination path.

        Raises:
            ValueError: If the transfer has no single destination, no native
                receiver, leaves the project scope or cannot be proven.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        owner, owned_modules = ownership
        if rule.ownership_transfer is None:
            return None, None
        binding = cls.contract_transfer_binding(
            project, rule.ownership_transfer, owned_modules
        )
        if binding is None:
            return None, None
        if len(rule.bindings) != 1:
            message = f"{rule.id}: ownership transfer requires one destination"
            raise ValueError(message)
        elected = next(iter(rule.bindings.values()))
        destination = runtime.qualified_name(project, elected)
        destinations_path: t.Infra.RopeSourcePath | None = None
        for selected in (binding, destination):
            provider = cls.contract_transfer_module(selected)
            resource = provider.get_resource()
            if resource is None:
                message = f"{rule.id}: ownership requires a native source resource"
                raise ValueError(message)
            path = Path(resource.real_path).resolve()
            if path not in proposed or not path.is_relative_to(owner):
                message = (
                    f"{rule.id}: ownership transfer is outside its project: {path}"
                )
                raise ValueError(message)
            if selected is destination:
                destinations_path = path
        retired_path, removed = cls._retire_contract_declaration(
            project, binding, destination, proposed, destinations=destinations
        )
        return (retired_path if removed else None), destinations_path

    @classmethod
    def _authenticated_retirement_owner(
        cls,
        binding: p.Infra.RopePyName,
        proposed: Mapping[t.Infra.RopeSourcePath, str],
    ) -> tuple[p.Infra.RopePyModule, tuple[t.Infra.RopeSourcePath, str]]:
        """Authenticate the native declaration owner of the binding.

        Returns:
            The defining module and the governed ``(path, source)`` it owns.

        Raises:
            ValueError: If the scope, module or governed source is missing.

        """
        module = cls.contract_transfer_module(binding)
        resource = module.get_resource()
        if resource is None:
            message = "ownership transfer has no native definition resource"
            raise ValueError(message)
        path = Path(resource.real_path).resolve()
        return module, (path, proposed[path])

    @classmethod
    def _retiring_declaration_span(
        cls,
        module: p.Infra.RopePyModule,
        definition: p.Infra.RopeSourceDefinition,
        path: t.Infra.RopeSourcePath,
    ) -> tuple[p.Infra.RopePyName | None, p.Infra.RopeAstNode]:
        """Resolve the retiring declaration and its provably empty wrappers.

        Returns:
            The optional lexical container and the cached native definition node.

        Raises:
            TypeError: If the target is not a native source definition.
            ValueError: If no native declaration matches the scope, the
                retiring wrapper cannot be proven or the declaration has no
                native end span.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        parents = FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_parent_map(
            module.get_ast()
        )
        target = definition.get_ast()
        if not isinstance(target, c.Infra.AST_DEFINITION_TYPES):
            msg = "retirement requires a native source definition"
            raise TypeError(msg)
        container: p.Infra.RopePyName | None = None
        parent = parents.get(id(target))
        while (
            isinstance(parent, ast.ClassDef)
            and not (
                parent.bases
                or parent.keywords
                or parent.decorator_list
                or parent.type_params
            )
            and all(
                item is target
                or isinstance(item, ast.Pass)
                or (
                    isinstance(item, ast.Expr)
                    and isinstance(item.value, ast.Constant)
                    and isinstance(item.value.value, str)
                )
                for item in parent.body
            )
        ):
            parent_scope = runtime.scope_at(
                module,
                runtime.source_offset(module.source_code, parent),
                declaration_line=parent.lineno,
            )
            container = runtime.expression_name(parent_scope, parent.name)
            if container is None:
                message = f"unproven retiring lexical container: {path}:{parent.name}"
                raise ValueError(message)
            target, parent = parent, parents.get(id(parent))
        if target.end_lineno is None:
            message = f"retiring declaration has no native end span: {path}"
            raise ValueError(message)
        return container, target

    @classmethod
    def _verify_transfer_compatibility(
        cls,
        binding: p.Infra.RopePyName,
        destination: p.Infra.RopePyName,
    ) -> None:
        """Reject transfers that change the native callable or callback shape.

        Raises:
            ValueError: If the callable signature, native kind or callback
                signature changes across the transfer.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        value = binding.get_object()
        if types.py_function(value):
            if cls._native_contract_signature(
                binding
            ) != cls._native_contract_signature(destination):
                message = "ownership transfer changes the native callable signature"
                raise ValueError(message)
            return
        destination_value = destination.get_object()
        if not types.py_class(destination_value):
            message = "ownership transfer changes a class into a different native kind"
            raise ValueError(message)
        previous = value.get_attributes().get("__call__")
        current = destination_value.get_attributes().get("__call__")
        if previous is not None and (
            current is None
            or (
                not runtime.same_name(previous, current)
                and cls._native_contract_signature(previous)
                != cls._native_contract_signature(current)
            )
        ):
            message = "ownership transfer changes the native callback signature"
            raise ValueError(message)

    @classmethod
    def _drop_changed_orphaned_imports(
        cls,
        project: p.Infra.RopeProject,
        proposed: MutableMapping[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Remove newly orphaned imports from every changed governed module."""
        for changed, after in tuple(proposed.items()):
            resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                project.get_resource(
                    changed.relative_to(Path(project.root.real_path)).as_posix()
                ),
                changed,
            )
            before_module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project, resource
            )
            if after != before_module.source_code:
                proposed[changed] = cls.remove_orphaned_imports(
                    project,
                    resource,
                    before_module.source_code,
                    after,
                )

    @classmethod
    def _prove_retired_module_emptiness(
        cls,
        module: p.Infra.RopePyModule,
        container: p.Infra.RopePyName | None,
    ) -> bool:
        """Prove the retired wrapper keeps no live module behavior.

        Returns:
            Whether the retired module body became provably empty.

        Raises:
            ValueError: If a retiring wrapper still carries live behavior.

        """
        tree = module.get_ast()
        empty = all(
            (isinstance(item, ast.ImportFrom) and item.module == "__future__")
            or (
                isinstance(item, ast.Expr)
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            )
            or (
                isinstance(item, c.Infra.AST_ASSIGNMENT_TYPES)
                and isinstance(item.value, c.Infra.AST_SEQUENCE_DISPLAY_TYPES)
                and not item.value.elts
                and len(
                    targets := item.targets
                    if isinstance(item, ast.Assign)
                    else (item.target,)
                )
                == 1
                and isinstance(targets[0], ast.Name)
                and targets[0].id == "__all__"
            )
            for item in tree.body
        )
        if container is not None and not empty:
            message = f"retiring wrapper has live module behavior: {module.get_name()}"
            raise ValueError(message)
        return empty

    @classmethod
    def _retire_contract_declaration(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        destination: p.Infra.RopePyName,
        proposed: MutableMapping[t.Infra.RopeSourcePath, str],
        *,
        destinations: Sequence[p.Infra.RopePyName],
    ) -> tuple[t.Infra.RopeSourcePath, bool]:
        """Remove only the native declaration and provably empty lexical owners.

        Returns:
            The retiring module path and whether its body became provably
            empty.

        Raises:
            TypeError: If the native declaration or its span is unavailable.
            ValueError: If the declaration has no native source resource.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        analysis_exports = FlextInfraUtilitiesRopeAnalysisExports
        if cls.contract_assignment(binding) is not None:
            return cls._retire_contract_assignment(
                project,
                binding,
                destination,
                proposed,
                destinations=destinations,
            )
        module, (path, source) = cls._authenticated_retirement_owner(binding, proposed)
        definition = binding.get_object()
        if not isinstance(definition, p.Infra.RopeSourceDefinition):
            msg = "retiring declaration has no native source AST"
            raise TypeError(msg)
        container, target = cls._retiring_declaration_span(module, definition, path)
        if (
            not isinstance(target, c.Infra.AST_DEFINITION_TYPES)
            or target.end_lineno is None
        ):
            msg = "retiring declaration has no complete native span"
            raise TypeError(msg)
        cls._prove_contract_retirement(
            project,
            proposed,
            owners=(binding, container),
            destinations=destinations,
            span=(path, target.lineno, target.end_lineno),
        )
        cls._verify_transfer_compatibility(binding, destination)
        if container is not None:
            cls._retire_contract_bases(project, proposed, container)
            source = proposed[path]
        lines = cls._source_lines(source)
        first_line = min(
            (item.lineno for item in target.decorator_list), default=target.lineno
        )
        edits = [
            m.Infra.SourceRewrite(
                start=lines.get_line_start(first_line),
                end=lines.get_line_end(target.end_lineno)
                + int(source[lines.get_line_end(target.end_lineno) :].startswith("\n")),
                text="",
            )
        ]
        resource = module.get_resource()
        if resource is None:
            msg = f"retiring declaration has no native resource: {path}"
            raise ValueError(msg)
        source = refactors.content_change(
            resource=resource, source=source, rewrites=edits
        ).new_contents
        if container is not None:
            with FlextInfraUtilitiesRopeModulePatch.candidate_module(
                module, source
            ) as export_module:
                if FlextInfraUtilitiesRopeModulePatch.runtime_alias_bindings(
                    export_module, alias="__all__"
                ):
                    exports = analysis_exports.public_export_names_source(export_module)
                    source = FlextInfraUtilitiesRopeModulePatch.rewrite_all_declaration(
                        export_module,
                        names=[name for name in exports if name != target.name],
                    )
        proposed[path] = source
        cls._drop_changed_orphaned_imports(project, proposed)
        empty = cls._prove_retired_module_emptiness(
            FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project,
                proposed[path],
                resource=module.get_resource(),
            ),
            container,
        )
        if empty:
            proposed[path] = ""
        return path, empty

    @classmethod
    def _retire_contract_assignment(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        destination: p.Infra.RopePyName,
        proposed: MutableMapping[t.Infra.RopeSourcePath, str],
        *,
        destinations: Sequence[p.Infra.RopePyName],
    ) -> tuple[t.Infra.RopeSourcePath, bool]:
        """Retire a lazy alias or an already-rebound pure reference assignment.

        Returns:
            Its original source path and whether that module became empty.

        Raises:
            ValueError: If alias parameters or the native destination are unproven.

        """
        declaration = cls.contract_assignment(binding)
        if declaration is None:
            message = "retiring assignment lost its native declaration"
            raise ValueError(message)
        module, scope, layout = declaration
        receiver = cls.contract_assignment(destination)
        if layout.kind == "TypeAlias":
            if (
                receiver is None
                or receiver[2].kind != "TypeAlias"
                or layout.type_parameters
                or receiver[2].type_parameters
            ):
                message = "alias transfer lacks matching native parameter proof"
                raise ValueError(message)
        elif (
            layout.root_binding is None
            or not FlextInfraUtilitiesRopeRuntimeModules.same_name(
                destination, layout.value_binding
            )
        ):
            message = "retiring assignment is not a direct destination reference"
            raise ValueError(message)
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            module.get_resource(), "retiring assignment"
        )
        path = Path(resource.real_path).resolve()
        source = proposed[path]
        first, last = layout.region
        start_line = module.lines.get_line_number(first)
        end_line = module.lines.get_line_number(last - 1)
        cls._prove_contract_retirement(
            project,
            proposed,
            owners=(binding, None),
            destinations=destinations,
            span=(path, start_line, end_line),
        )
        first = module.lines.get_line_start(start_line)
        last = module.lines.get_line_end(end_line)
        last += int(source[last:].startswith("\n"))
        rewritten = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            (m.Infra.SourceRewrite(start=first, end=last, text=""),),
        ).new_contents
        if scope.get_kind() == "Module":
            with FlextInfraUtilitiesRopeModulePatch.candidate_module(
                module, rewritten
            ) as candidate:
                rewritten = (
                    FlextInfraUtilitiesRopeModulePatch.remove_runtime_alias_export(
                        candidate, alias=layout.targets[0][0]
                    )
                )
        proposed[path] = rewritten
        cls._drop_changed_orphaned_imports(project, proposed)
        return path, cls._prove_retired_module_emptiness(
            FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, proposed[path], resource=resource
            ),
            None,
        )

    @staticmethod
    def _contract_signature(node: p.Infra.RopeAstNode) -> t.Infra.RopeCallableSignature:
        """Compare calling conventions, not migrated declaration annotations.

        Returns:
            The structural callable signature tuple.

        Raises:
            TypeError: If the node is not a function definition.
            ValueError: If a callable default expression is unproven.

        """
        if not isinstance(node, c.Infra.AST_FUNCTION_TYPES):
            message = "native signature proof requires a function definition"
            raise TypeError(message)
        args = node.args
        if any(
            item is not None and not isinstance(item, ast.Constant)
            for item in (*args.defaults, *args.kw_defaults)
        ):
            message = "ownership transfer has an unproven callable default expression"
            raise ValueError(message)
        return (
            tuple(item.arg for item in args.posonlyargs),
            tuple(item.arg for item in args.args),
            args.vararg.arg if args.vararg is not None else None,
            tuple(item.arg for item in args.kwonlyargs),
            args.kwarg.arg if args.kwarg is not None else None,
            tuple(ast.dump(item) for item in args.defaults),
            tuple(
                ast.dump(item) if item is not None else None
                for item in args.kw_defaults
            ),
            isinstance(node, ast.AsyncFunctionDef),
        )

    @classmethod
    def _native_contract_signature(
        cls, binding: p.Infra.RopePyName
    ) -> tuple[t.Infra.RopeCallableSignature, str]:
        """Include native binding kind without executing the authored callable.

        Returns:
            The structural signature paired with the native binding kind.

        Raises:
            TypeError: If the binding has no native source scope.
            ValueError: If the binding is not a native callable.

        """
        value = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(value):
            message = (
                "ownership transfer changes a callable into a different native kind"
            )
            raise ValueError(message)
        kind = value.get_scope().get_kind()
        if kind is None:
            message = "ownership callable has no native source scope kind"
            raise TypeError(message)
        return cls._contract_signature(value.get_ast()), kind

    @classmethod
    def _require_governed_inventory(
        cls,
        project: p.Infra.RopeProject,
        observed: Mapping[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Require every workspace Python file in the governed inventory.

        Raises:
            ValueError: If a non-generated workspace source is missing from
                the governed inventory.

        """
        for resource in project.get_python_files():
            path = Path(resource.real_path).resolve()
            if path not in observed:
                source = resource.read()
                if not source.startswith(c.Infra.AUTOGEN_HEADER):
                    message = (
                        "ownership transfer requires complete governed inventory: "
                        f"{path}"
                    )
                    raise ValueError(message)
                # Generated exports are regenerated in the same publication group.

    @classmethod
    def _prove_contract_retirement(
        cls,
        project: p.Infra.RopeProject,
        sources: Mapping[t.Infra.RopeSourcePath, str],
        *,
        owners: tuple[p.Infra.RopePyName, p.Infra.RopePyName | None],
        destinations: Sequence[p.Infra.RopePyName],
        span: tuple[Path, int, int],
    ) -> None:
        """Prove all governed uses without evaluating opaque receiver expressions."""
        cls._require_governed_inventory(project, sources)
        reflectors = tuple(
            FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                project, name, module_name="builtins"
            )
            for name in ("getattr", "hasattr", "setattr", "delattr")
        )
        member = cls._retiring_binding_name(owners[0])
        for path, source in sources.items():
            cls._prove_retirement_source(
                project,
                (path, source),
                (*owners, member),
                (destinations, reflectors),
                span,
            )

    @classmethod
    def _prove_retirement_source(
        cls,
        project: p.Infra.RopeProject,
        entry: tuple[Path, str],
        owners: tuple[p.Infra.RopePyName, p.Infra.RopePyName | None, str],
        callees: tuple[Sequence[p.Infra.RopePyName], Sequence[p.Infra.RopePyName]],
        span: tuple[Path, int, int],
    ) -> None:
        path, source = entry
        if source.startswith(c.Infra.AUTOGEN_HEADER):
            return
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding, container, member = owners
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            ),
            path,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        tree = module.get_ast()

        def covers(line: int) -> bool:
            return path == span[0] and span[1] <= line <= span[2]

        resolutions: dict[tuple[int, str], p.Infra.RopePyName | None] = {}

        def resolves(node: p.Infra.RopeAstNode) -> p.Infra.RopePyName | None:
            scope = runtime.scope_at(module, runtime.source_offset(source, node))
            key = (id(scope), node.to_source() if hasattr(node, "to_source") else str(node))
            if key not in resolutions:
                resolutions[key] = runtime.resolve_symbol(scope, node)
            return resolutions[key]

        def whole_owner(actual: p.Infra.RopePyName | None) -> bool:
            return (
                container is not None
                and actual is not None
                and (
                    runtime.same_name(container, actual)
                    or actual.get_object() is binding.get_object().get_module()
                )
            )

        def carries(expression: p.Infra.RopeAstNode) -> bool:
            return cls._carries_retirement_owner(
                expression, resolves, whole_owner, binding, member
            )

        cls._prove_retirement_exports(module, entry, (binding, container), span[0])
        cls._prove_retirement_nodes(
            tree,
            covers,
            resolves,
            (whole_owner, carries),
            (binding, container, path, callees, member),
        )
        if path != span[0]:
            cls._prove_retirement_aliases(
                module, tree, resolves, whole_owner, (binding, container, path)
            )

        def quoted(scope: p.Infra.RopeScope, expression: str) -> str | None:
            cls._prove_retirement_annotation(
                scope, expression, covers, (binding, container), path
            )
            return None

        FlextInfraUtilitiesTypesSemanticNesting.rewrite_quoted_types(
            (project, resource), source, quoted
        )

    @classmethod
    def _prove_retirement_nodes(
        cls,
        tree: ast.Module,
        covers: Callable[[int], bool],
        resolves: Callable[[p.Infra.RopeAstNode], p.Infra.RopePyName | None],
        probes: tuple[
            Callable[[p.Infra.RopePyName | None], bool],
            Callable[[p.Infra.RopeAstNode], bool],
        ],
        context: tuple[
            p.Infra.RopePyName,
            p.Infra.RopePyName | None,
            Path,
            tuple[Sequence[p.Infra.RopePyName], Sequence[p.Infra.RopePyName]],
            str,
        ],
    ) -> None:
        binding, container, path, callees, member = context
        whole_owner, carries = probes
        parents = FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Name | ast.Attribute | ast.Call) or covers(
                node.lineno
            ):
                continue
            if isinstance(node, c.Infra.AST_NAME_REFERENCE_TYPES):
                cls._prove_retirement_reference(
                    node, parents, resolves, probes, (binding, container, path)
                )
            if isinstance(node, ast.Call):
                cls._prove_retirement_call(
                    node,
                    resolves,
                    whole_owner,
                    carries,
                    (
                        *callees,
                        member,
                        path,
                    ),
                )

    @staticmethod
    def _prove_retirement_annotation(
        scope: p.Infra.RopeScope,
        expression: str,
        covers: Callable[[int], bool],
        owners: tuple[p.Infra.RopePyName, p.Infra.RopePyName | None],
        path: Path,
    ) -> None:
        binding, container = owners
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if not covers(scope.get_start()):
            actual = runtime.expression_name(scope, expression)
            if runtime.same_name(binding, actual) or (
                container is not None and runtime.same_name(container, actual)
            ):
                msg = (
                    "ownership transfer has a surviving annotation: "
                    f"{path}:{expression}"
                )
                raise ValueError(msg)

    @staticmethod
    def _carries_retirement_owner(
        expression: p.Infra.RopeAstNode,
        resolves: Callable[[p.Infra.RopeAstNode], p.Infra.RopePyName | None],
        whole_owner: Callable[[p.Infra.RopePyName | None], bool],
        binding: p.Infra.RopePyName,
        member: str,
    ) -> bool:
        if not isinstance(expression, ast.AST):
            msg = "native carrier proof requires an AST expression"
            raise TypeError(msg)
        qualifiers = {
            id(node.value)
            for node in ast.walk(expression)
            if isinstance(node, ast.Attribute)
        }
        return any(
            actual is not None
            and (
                whole_owner(actual)
                or FlextInfraUtilitiesRopeRuntimeModules.same_name(
                    binding,
                    actual.get_object().get_attributes().get(member),
                )
            )
            for part in ast.walk(expression)
            if isinstance(part, c.Infra.AST_NAME_REFERENCE_TYPES)
            and id(part) not in qualifiers
            for actual in (resolves(part),)
        )

    @staticmethod
    def _prove_retirement_exports(
        module: p.Infra.RopePyModule,
        entry: tuple[Path, str],
        owners: tuple[p.Infra.RopePyName, p.Infra.RopePyName | None],
        owner_path: Path,
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        path, _source = entry
        binding, container = owners
        for name in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
            FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(module)
        ):
            exported = module.get_attributes().get(name)
            if path != owner_path and (
                runtime.same_name(binding, exported)
                or (container is not None and runtime.same_name(container, exported))
            ):
                msg = f"ownership transfer has an exported old alias: {path}:{name}"
                raise ValueError(msg)

    @staticmethod
    def _prove_retirement_aliases(
        module: p.Infra.RopePyModule,
        tree: ast.Module,
        resolves: Callable[[p.Infra.RopeAstNode], p.Infra.RopePyName | None],
        whole_owner: Callable[[p.Infra.RopePyName | None], bool],
        context: tuple[p.Infra.RopePyName, p.Infra.RopePyName | None, Path],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding, container, path = context
        for name, imported in module.get_scope().get_defined_names().items():
            if not (runtime.same_name(binding, imported) or whole_owner(imported)):
                continue
            if not any(
                container is not None
                and runtime.same_name(container, resolves(base))
                and any(
                    isinstance(part, ast.Name) and part.id == name
                    for part in ast.walk(base)
                )
                for declaration in ast.walk(tree)
                if isinstance(declaration, ast.ClassDef)
                for base in declaration.bases
            ):
                msg = (
                    f"ownership transfer has a surviving imported alias: {path}:{name}"
                )
                raise ValueError(msg)

    @staticmethod
    def _prove_retirement_reference(
        node: ast.Name | ast.Attribute,
        parents: Mapping[int, p.Infra.RopeAstNode],
        resolves: Callable[[p.Infra.RopeAstNode], p.Infra.RopePyName | None],
        probes: tuple[
            Callable[[p.Infra.RopePyName | None], bool],
            Callable[[p.Infra.RopeAstNode], bool],
        ],
        context: tuple[p.Infra.RopePyName, p.Infra.RopePyName | None, Path],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        whole_owner, carries = probes
        binding, container, path = context
        actual = resolves(node)
        parent = parents.get(id(node))
        base = isinstance(parent, ast.ClassDef) and node in parent.bases
        ancestor = parents.get(id(parent))
        module_base = (
            isinstance(parent, ast.Attribute)
            and container is not None
            and runtime.same_name(container, resolves(parent))
            and isinstance(ancestor, ast.ClassDef)
            and parent in ancestor.bases
        )
        if runtime.same_name(binding, actual) or (
            container is not None and runtime.same_name(container, actual) and not base
        ):
            msg = f"ownership transfer has surviving native usage: {path}:{node.lineno}"
            raise ValueError(msg)
        if (
            actual is not None
            and whole_owner(actual)
            and actual.get_object() is binding.get_object().get_module()
            and not module_base
        ):
            msg = f"ownership transfer has surviving module usage: {path}:{node.lineno}"
            raise ValueError(msg)
        if (
            isinstance(node, ast.Attribute)
            and node.attr in {"__dict__", "__getattribute__"}
            and carries(node.value)
        ):
            msg = f"ownership transfer has dynamic owner access: {path}:{node.lineno}"
            raise ValueError(msg)

    @staticmethod
    def _prove_retirement_call(
        node: ast.Call,
        resolves: Callable[[p.Infra.RopeAstNode], p.Infra.RopePyName | None],
        whole_owner: Callable[[p.Infra.RopePyName | None], bool],
        carries: Callable[[p.Infra.RopeAstNode], bool],
        context: tuple[
            Sequence[p.Infra.RopePyName],
            Sequence[p.Infra.RopePyName],
            str,
            Path,
        ],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        destinations, reflectors, member, path = context
        callee = resolves(node.func)
        if any(runtime.same_name(target, callee) for target in destinations):
            return
        arguments = (*node.args, *(item.value for item in node.keywords))
        if not any(carries(argument) for argument in arguments):
            return
        if (
            any(runtime.same_name(item, callee) for item in reflectors)
            and len(node.args) > 1
        ):
            selector = node.args[1]
            if (
                isinstance(selector, ast.Constant)
                and isinstance(selector.value, str)
                and selector.value != member
                and all(
                    not carries(argument) or resolves(argument) is not None
                    for argument in arguments
                )
                and not any(whole_owner(resolves(argument)) for argument in arguments)
            ):
                return
        msg = f"ownership transfer has marker/dynamic owner usage: {path}:{node.lineno}"
        raise ValueError(msg)

    @classmethod
    def _retire_contract_bases(
        cls,
        project: p.Infra.RopeProject,
        sources: MutableMapping[t.Infra.RopeSourcePath, str],
        container: p.Infra.RopePyName,
    ) -> None:
        """Remove only class-header edges to the proven empty native container."""
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        for path, source in tuple(sources.items()):
            resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                project.get_resource(
                    path.relative_to(Path(project.root.real_path)).as_posix()
                ),
                path,
            )
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            changes: list[p.Infra.SourceRewrite] = []
            tree = module.get_ast()
            for node in ast.walk(tree):
                rewrite = cls._retired_base_rewrite(
                    module, (path, source), node, container
                )
                if rewrite is not None:
                    changes.append(rewrite)
            if changes:
                sources[path] = refactors.content_change(
                    resource, source, changes
                ).new_contents

    @classmethod
    def _retired_base_rewrite(
        cls,
        module: p.Infra.RopePyModule,
        entry: tuple[Path, str],
        node: ast.AST,
        container: p.Infra.RopePyName,
    ) -> p.Infra.SourceRewrite | None:
        if not isinstance(node, ast.ClassDef) or not node.bases:
            return None
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        path, source = entry
        scope = runtime.scope_at(
            module, runtime.source_offset(source, node), declaration_line=node.lineno
        )
        removed = tuple(
            base
            for base in node.bases
            if runtime.same_name(container, runtime.resolve_symbol(scope, base))
        )
        if not removed:
            return None
        header, (_words, first, last) = cls._retired_base_header(
            module, scope, node, path
        )
        first_line, _ = module.logical_lines.logical_line_in(node.lineno)
        header_start = module.lines.get_line_start(first_line)
        arguments = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
            header, first + 1, last - 1, ","
        )
        keep = [
            header[left:right]
            for left, right in arguments
            if not any(
                header_start + left
                <= runtime.source_offset(source, base)
                < header_start + right
                for base in removed
            )
        ]
        return m.Infra.SourceRewrite(
            start=header_start + first + 1,
            end=header_start + last - 1,
            text=",".join(keep),
        )

    @classmethod
    def _retired_base_header(
        cls,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        node: ast.ClassDef,
        path: Path,
    ) -> tuple[str, tuple[p.Infra.RopeWorder, int, int]]:
        owner = FlextInfraUtilitiesRopeRuntimeModules.expression_name(scope, node.name)
        if owner is None:
            message = f"retiring base has no native declaring class: {path}:{node.name}"
            raise ValueError(message)
        value = owner.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(value):
            message = f"retiring base has a non-class owner: {path}:{node.name}"
            raise TypeError(message)
        class_scope = value.get_scope()
        located = cls._header_argument_span(class_scope, module)
        if located is None:
            message = f"retiring base has no native class header: {path}:{node.name}"
            raise ValueError(message)
        return located


__all__ = ["FlextInfraUtilitiesSemanticDeclarationRetirement"]
