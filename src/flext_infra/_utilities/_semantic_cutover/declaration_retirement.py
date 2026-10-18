"""Native declaration retirement elected by project-owned contract rules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope_analysis import FlextInfraUtilitiesRopeAnalysisExports
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
    FlextInfraUtilitiesSemanticNestingTypes,
)


class FlextInfraUtilitiesSemanticDeclarationRetirement(
    FlextInfraUtilitiesSemanticDeclarationRelocation,
):
    """Complete the existing contract planner through the native relocation owner."""

    @staticmethod
    def contract_transfer_binding(
        project: p.Infra.RopeProject,
        identity: t.Pair[str, str],
        owned_modules: t.MappingKV[str, t.Infra.RopeSourcePath],
    ) -> p.Infra.RopePyName | None:
        """Resolve only an original owned resource, never an installed SDK fallback."""
        provider, expression = identity
        path = owned_modules.get(provider)
        if path is None:
            return None
        resource = FlextInfraUtilitiesRopeCore.resource_for_path(project, path)
        attributes = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project, resource
        ).get_attributes()
        binding: p.Infra.RopePyName | None = None
        for part in expression.split("."):
            binding = attributes.get(part)
            if binding is None:
                return None
            attributes = binding.get_object().get_attributes()
        return binding

    @classmethod
    def retire_contract_owners(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        original: t.MappingKV[t.Infra.RopeSourcePath, str],
        proposed: t.MutableMappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
        epoch: p.Infra.CodemodSourceEpoch,
        owned_modules: t.MappingKV[str, t.Infra.RopeSourcePath],
    ) -> t.Pair[t.Infra.RopeImplementationPaths, t.Infra.RopeImplementationPaths]:
        """Retire elected declarations only after native receiver completeness."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        retired: t.Infra.RopeMutablePaths = set()
        destinations: t.Infra.RopeMutablePaths = set()
        for rule in rules:
            if rule.ownership_transfer is None:
                continue
            owner = cls.contract_rule_root(workspace.repository_root, rule)
            project = runtime.snapshot_project(
                workspace.rope_project, proposed, captured=epoch
            )
            try:
                binding = cls.contract_transfer_binding(
                    project, rule.ownership_transfer, owned_modules
                )
                if binding is None:
                    continue
                if len(rule.bindings) != 1:
                    message = f"{rule.id}: ownership transfer requires one destination"
                    raise ValueError(message)
                destination = runtime.qualified_name(
                    project, next(iter(rule.bindings.values()))
                )
                for selected in (binding, destination):
                    value = selected.get_object()
                    provider = value.get_module()
                    if not isinstance(provider, p.Infra.RopeSourceModule):
                        message = (
                            f"{rule.id}: an external library declaration cannot retire"
                        )
                        raise ValueError(message)
                    resource = provider.get_resource()
                    if resource is None:
                        message = (
                            f"{rule.id}: ownership requires a native source resource"
                        )
                        raise ValueError(message)
                    path = Path(resource.real_path).resolve()
                    if path not in original or not path.is_relative_to(owner):
                        message = f"{rule.id}: ownership transfer is outside its project: {path}"
                        raise ValueError(message)
                    if selected is destination:
                        destinations.add(path)
                path, removed = cls._retire_contract_declaration(
                    project, binding, destination, proposed
                )
                if removed:
                    retired.add(path)
            finally:
                project.close()
        return frozenset(retired), frozenset(destinations)

    @classmethod
    def _authenticated_retirement_owner(
        cls,
        binding: p.Infra.RopePyName,
        proposed: t.MappingKV[t.Infra.RopeSourcePath, str],
    ) -> t.Pair[p.Infra.RopePyModule, t.Pair[t.Infra.RopeSourcePath, str]]:
        """Authenticate the native class or function owner of the binding.

        Returns:
            The defining module and the governed ``(path, source)`` it owns.

        Raises:
            TypeError: If the binding has no native class or function scope.
            ValueError: If the scope, module or governed source is missing.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        value = binding.get_object()
        if not (types.py_function(value) or types.py_class(value)):
            message = "ownership transfer requires a native class or function"
            raise TypeError(message)
        scope, module = value.get_scope(), value.get_module()
        if scope is None or not isinstance(module, p.Infra.RopePyModule):
            message = "ownership transfer has no native definition scope"
            raise TypeError(message)
        resource = module.get_resource()
        if resource is None:
            message = "ownership transfer has no native definition resource"
            raise ValueError(message)
        path = Path(resource.real_path).resolve()
        return module, (path, proposed[path])

    @classmethod
    def _retiring_declaration_span(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        path: t.Infra.RopeSourcePath,
    ) -> t.Pair[p.Infra.RopePyName | None, t.Pair[ast.stmt, int]]:
        """Resolve the retiring declaration and its provably empty wrappers.

        Returns:
            The optional lexical container plus the retiring statement and its
            native end line.

        Raises:
            ValueError: If no native declaration matches the scope, the
                retiring wrapper cannot be proven or the declaration has no
                native end span.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        tree = ast.parse(source)
        parents = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        declaration = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
            and node.lineno == scope.get_start()
        )
        target = declaration
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
                runtime.source_offset(source, parent),
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
        return container, (target, target.end_lineno)

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

    @staticmethod
    def _container_export_edits(
        source: str,
        tree: ast.Module,
        target: ast.stmt,
        path: t.Infra.RopeSourcePath,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        """Rewrite the retiring container ``__all__`` without dynamic exports.

        Returns:
            The export-list rewrites that drop only the retired name.

        Raises:
            ValueError: If the container has dynamic exports or an export
                without a native source span.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        lines = source.splitlines(keepends=True)
        edits: list[m.Infra.SourceRewrite] = []
        for statement in tree.body:
            if not isinstance(statement, ast.Assign | ast.AnnAssign):
                continue
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else (statement.target,)
            )
            if not any(
                isinstance(item, ast.Name) and item.id == "__all__" for item in targets
            ):
                continue
            if not isinstance(statement.value, ast.List | ast.Tuple) or not all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in statement.value.elts
            ):
                message = f"retiring container has dynamic exports: {path}"
                raise ValueError(message)
            remaining = [
                item.value
                for item in statement.value.elts
                if isinstance(item, ast.Constant)
                and isinstance(item.value, str)
                and item.value != target.name
            ]
            if remaining:
                segment = ast.get_source_segment(source, statement.value)
                if segment is None:
                    message = f"retiring export has no native source span: {path}"
                    raise ValueError(message)
                offset = runtime.source_offset(source, statement.value)
                edits.append(
                    m.Infra.SourceRewrite(
                        start=offset,
                        end=offset + len(segment),
                        text=repr(remaining),
                    )
                )
            else:
                edits.append(
                    m.Infra.SourceRewrite(
                        start=sum(map(len, lines[: statement.lineno - 1])),
                        end=sum(map(len, lines[: statement.end_lineno])),
                        text="",
                    )
                )
        return tuple(edits)

    @classmethod
    def _drop_changed_orphaned_imports(
        cls,
        project: p.Infra.RopeProject,
        proposed: t.MutableMappingKV[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Remove newly orphaned imports from every changed governed module."""
        for changed, after in tuple(proposed.items()):
            before_module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project, cls._resource(project, changed)
            )
            if after != before_module.source_code:
                proposed[changed] = cls._remove_orphaned_imports(
                    project,
                    cls._resource(project, changed),
                    before_module.source_code,
                    after,
                )

    @classmethod
    def _prove_retired_module_emptiness(
        cls,
        proposed: t.MappingKV[t.Infra.RopeSourcePath, str],
        path: t.Infra.RopeSourcePath,
        container: p.Infra.RopePyName | None,
    ) -> bool:
        """Prove the retired wrapper keeps no live module behavior.

        Returns:
            Whether the retired module body became provably empty.

        Raises:
            ValueError: If a retiring wrapper still carries live behavior.

        """
        body = ast.parse(proposed[path]).body
        empty = all(
            (isinstance(item, ast.ImportFrom) and item.module == "__future__")
            or (
                isinstance(item, ast.Expr)
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            )
            for item in body
        )
        if container is not None and not empty:
            message = f"retiring wrapper has live module behavior: {path}"
            raise ValueError(message)
        return empty

    @classmethod
    def _retire_contract_declaration(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        destination: p.Infra.RopePyName,
        proposed: t.MutableMappingKV[t.Infra.RopeSourcePath, str],
    ) -> t.Pair[t.Infra.RopeSourcePath, bool]:
        """Remove only the native declaration and provably empty lexical owners.

        Returns:
            The retiring module path and whether its body became provably
            empty.

        Raises:
            TypeError: If the owner or destination lacks the required native
                definition shape.
            ValueError: If the transfer changes native shapes, keeps surviving
                usage or leaves an unproven wrapper.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        module, (path, source) = cls._authenticated_retirement_owner(binding, proposed)
        scope = binding.get_object().get_scope()
        container, (target, end_line) = cls._retiring_declaration_span(
            source, module, scope, path
        )
        cls._prove_contract_retirement(
            project,
            proposed,
            binding,
            destination,
            container,
            path,
            target.lineno,
            end_line,
        )
        cls._verify_transfer_compatibility(binding, destination)
        if container is not None:
            cls._retire_contract_bases(project, proposed, container)
            source = proposed[path]
            tree = ast.parse(source)
        lines = source.splitlines(keepends=True)
        first_line = min(
            (item.lineno for item in target.decorator_list), default=target.lineno
        )
        edits = [
            m.Infra.SourceRewrite(
                start=sum(map(len, lines[: first_line - 1])),
                end=sum(map(len, lines[:end_line])),
                text="",
            )
        ]
        if container is not None:
            edits.extend(cls._container_export_edits(source, tree, target, path))
        proposed[path] = refactors.content_change(
            resource=module.get_resource(), source=source, edits=edits
        ).new_contents
        cls._drop_changed_orphaned_imports(project, proposed)
        empty = cls._prove_retired_module_emptiness(proposed, path, container)
        if empty:
            proposed[path] = ""
        return path, empty

    @staticmethod
    def _contract_signature(node: p.Infra.RopeAstNode) -> t.Infra.RopeCallableSignature:
        """Compare calling conventions, not migrated declaration annotations."""
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
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
    ) -> t.Pair[t.Infra.RopeCallableSignature, str]:
        """Include native binding kind without executing the authored callable."""
        value = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(value):
            message = (
                "ownership transfer changes a callable into a different native kind"
            )
            raise ValueError(message)
        scope, module = value.get_scope(), value.get_module()
        if scope is None or not isinstance(module, p.Infra.RopePyModule):
            message = "ownership callable has no native source scope"
            raise TypeError(message)
        declaration = next(
            node
            for node in ast.walk(ast.parse(module.source_code))
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.lineno == scope.get_start()
        )
        return cls._contract_signature(declaration), value.get_kind()

    @classmethod
    def _prove_contract_retirement(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        binding: p.Infra.RopePyName,
        destination: p.Infra.RopePyName,
        container: p.Infra.RopePyName | None,
        owner_path: t.Infra.RopeSourcePath,
        first_line: int,
        last_line: int,
    ) -> None:
        """Reject surviving uses, exported aliases and opaque owner introspection."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        member = binding.get_object().get_name()
        owner_module = binding.get_object().get_module()
        observed = dict(sources)
        for resource in project.get_python_files():
            path = Path(resource.real_path).resolve()
            if path not in observed:
                source = resource.read()
                if not source.startswith(c.Infra.AUTOGEN_HEADERS):
                    message = f"ownership transfer requires complete governed inventory: {path}"
                    raise ValueError(message)
                # Generated exports are regenerated in the same publication group.
        reflectors = tuple(
            runtime.qualified_name(project, name, module_name="builtins")
            for name in ("getattr", "hasattr", "setattr", "delattr")
        )
        for path, source in observed.items():
            if source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            resource = cls._resource(project, path)
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            tree = ast.parse(source)
            parents = {
                id(child): parent
                for parent in ast.walk(tree)
                for child in ast.iter_child_nodes(parent)
            }

            def selected(node: p.Infra.RopeAstNode) -> p.Infra.RopePyName | None:
                if not isinstance(node, ast.AST):
                    message = "native ownership proof requires a source expression"
                    raise TypeError(message)
                return runtime.resolve_symbol(
                    runtime.scope_at(module, runtime.source_offset(source, node)), node
                )

            def carrier(node: p.Infra.RopeAstNode) -> bool:
                actual = selected(node)
                return actual is not None and (
                    runtime.same_name(
                        binding, actual.get_object().get_attributes().get(member)
                    )
                    or (
                        container is not None
                        and (
                            runtime.same_name(container, actual)
                            or actual.get_object() == owner_module
                        )
                    )
                )

            for (
                name
            ) in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                source
            ):
                exported = module.get_attributes().get(name)
                if (
                    runtime.same_name(binding, exported)
                    or (
                        container is not None and runtime.same_name(container, exported)
                    )
                ) and path != owner_path:
                    message = (
                        f"ownership transfer has an exported old alias: {path}:{name}"
                    )
                    raise ValueError(message)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Name | ast.Attribute | ast.Call):
                    continue
                if path == owner_path and first_line <= node.lineno <= last_line:
                    continue
                if isinstance(node, ast.Name | ast.Attribute):
                    actual = selected(node)
                    parent = parents.get(id(node))
                    old_container = container is not None and runtime.same_name(
                        container, actual
                    )
                    base = isinstance(parent, ast.ClassDef) and node in parent.bases
                    old_module = (
                        container is not None
                        and actual is not None
                        and actual.get_object() == owner_module
                    )
                    ancestor = parents.get(id(parent))
                    container_base = (
                        isinstance(parent, ast.Attribute)
                        and runtime.same_name(container, selected(parent))
                        and isinstance(ancestor, ast.ClassDef)
                        and parent in ancestor.bases
                    )
                    if runtime.same_name(binding, actual) or (
                        old_container and not base
                    ):
                        message = f"ownership transfer has surviving native usage: {path}:{node.lineno}"
                        raise ValueError(message)
                    if old_module and not container_base:
                        message = f"ownership transfer has surviving module usage: {path}:{node.lineno}"
                        raise ValueError(message)
                    if (
                        isinstance(node, ast.Attribute)
                        and node.attr
                        in {
                            "__dict__",
                            "__getattribute__",
                        }
                        and carrier(node.value)
                    ):
                        message = f"ownership transfer has dynamic owner access: {path}:{node.lineno}"
                        raise ValueError(message)
                if not isinstance(node, ast.Call):
                    continue
                callee = selected(node.func)
                if runtime.same_name(destination, callee):
                    continue
                arguments = (*node.args, *(item.value for item in node.keywords))
                if not any(carrier(argument) for argument in arguments):
                    continue
                if (
                    any(runtime.same_name(item, callee) for item in reflectors)
                    and len(node.args) > 1
                ):
                    selector = node.args[1]
                    if (
                        isinstance(selector, ast.Constant)
                        and isinstance(selector.value, str)
                        and selector.value != member
                        and not any(
                            container is not None
                            and actual is not None
                            and (
                                runtime.same_name(container, actual)
                                or actual.get_object() == owner_module
                            )
                            for argument in arguments
                            for actual in (selected(argument),)
                        )
                    ):
                        continue
                message = f"ownership transfer has marker/dynamic owner usage: {path}:{node.lineno}"
                raise ValueError(message)
            if path != owner_path:
                for name, imported in module.get_scope().get_defined_names().items():
                    retiring = runtime.same_name(binding, imported) or (
                        container is not None
                        and (
                            runtime.same_name(container, imported)
                            or imported.get_object() == owner_module
                        )
                    )
                    if retiring and not any(
                        runtime.same_name(container, selected(base))
                        and any(
                            isinstance(part, ast.Name) and part.id == name
                            for part in ast.walk(base)
                        )
                        for declaration in ast.walk(tree)
                        if isinstance(declaration, ast.ClassDef)
                        for base in declaration.bases
                    ):
                        message = f"ownership transfer has a surviving imported alias: {path}:{name}"
                        raise ValueError(message)

            def quoted(scope: p.Infra.RopeScope, expression: str) -> str | None:
                if path == owner_path and first_line <= scope.get_start() <= last_line:
                    return None
                actual = runtime.expression_name(scope, expression)
                if runtime.same_name(binding, actual) or (
                    container is not None and runtime.same_name(container, actual)
                ):
                    message = f"ownership transfer has a surviving annotation: {path}:{expression}"
                    raise ValueError(message)
                return None

            FlextInfraUtilitiesSemanticNestingTypes.rewrite_quoted_types(
                project, resource, source, quoted
            )

    @classmethod
    def _retire_contract_bases(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MutableMappingKV[t.Infra.RopeSourcePath, str],
        container: p.Infra.RopePyName,
    ) -> None:
        """Remove only class-header edges to the proven empty native container."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        for path, source in tuple(sources.items()):
            resource = cls._resource(project, path)
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            changes = []
            for node in ast.walk(ast.parse(source)):
                if not isinstance(node, ast.ClassDef) or not node.bases:
                    continue
                scope = runtime.scope_at(
                    module,
                    runtime.source_offset(source, node),
                    declaration_line=node.lineno,
                )
                removed = tuple(
                    base
                    for base in node.bases
                    if runtime.same_name(container, runtime.resolve_symbol(scope, base))
                )
                if not removed:
                    continue
                owner = runtime.expression_name(scope, node.name)
                if owner is None:
                    message = f"retiring base has no native declaring class: {path}:{node.name}"
                    raise ValueError(message)
                value = owner.get_object()
                if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(value):
                    message = f"retiring base has a non-class owner: {path}:{node.name}"
                    raise TypeError(message)
                class_scope = value.get_scope()
                if class_scope is None:
                    message = f"retiring base has no native declaring scope: {path}:{node.name}"
                    raise ValueError(message)
                located = cls._header_argument_span(value, class_scope, module)
                if located is None:
                    message = (
                        f"retiring base has no native class header: {path}:{node.name}"
                    )
                    raise ValueError(message)
                header, (_words, first, last) = located
                arguments = (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
                        header.text, first + 1, last - 1, ","
                    )
                )
                keep = [
                    header.text[left:right]
                    for left, right in arguments
                    if not any(
                        header.start_offset + left
                        <= runtime.source_offset(source, base)
                        < header.start_offset + right
                        for base in removed
                    )
                ]
                changes.append(
                    m.Infra.SourceRewrite(
                        start=header.start_offset + first + 1,
                        end=header.start_offset + last - 1,
                        text=",".join(keep),
                    )
                )
            if changes:
                sources[path] = refactors.content_change(
                    resource, source, changes
                ).new_contents


__all__ = ["FlextInfraUtilitiesSemanticDeclarationRetirement"]
