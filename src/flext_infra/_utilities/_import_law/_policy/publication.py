"""Import-law facts: namespaces, layers, lazy exports and facade routes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from time import monotonic
from typing import ClassVar

from flext_cli import settings, u

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectDiscovery,
)
from flext_infra._utilities._import_law._policy.namespace import (
    FlextInfraUtilitiesImportLawPolicyNamespace,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)


class FlextInfraUtilitiesImportLawPolicyPublication(
    FlextInfraUtilitiesImportLawPolicyNamespace,
):
    """Declare the publication facts of the composed import policy."""

    # Shared publication-scan progress. The heartbeat deadline and the
    # cumulative totals live on the composed policy class so every lookup
    # of a pass throttles against one interval and the aggregate rows carry
    # running totals instead of per-symbol detail.
    _scan_due = 0.0
    _scan_consumers: ClassVar[t.Infra.MutableSetOf[Path]] = set()
    _scan_lookups = 0
    _scan_files = 0
    _scan_providers = 0

    @staticmethod
    def codemod_progress(message: str, due: float = 0) -> float:
        """Report active source work at the configured heartbeat interval.

        Returns:
            The next monotonic deadline for an interval progress row.

        """
        now = monotonic()
        if now < due:
            return due
        u.Cli.info(f"mod: {message}")
        return now + settings.cli_process_heartbeat_seconds

    @classmethod
    def _publication_scan_summary(cls) -> None:
        """Emit one aggregate publication-scan row and reset the shared totals."""
        if not cls._scan_lookups:
            return
        u.Cli.info(
            f"mod: import publication scan summary project-lookups="
            f"{cls._scan_lookups} consumers={len(cls._scan_consumers)} "
            f"files-scanned={cls._scan_files} "
            f"providers-found={cls._scan_providers}"
        )
        cls._scan_lookups = 0
        cls._scan_consumers.clear()
        cls._scan_files = 0
        cls._scan_providers = 0

    @classmethod
    def family_letter(cls, namespace_dir: Path, file_path: Path) -> str | None:
        """Return the facade letter of the family package holding one module.

        Returns:
            The family letter, or None outside every family package.

        """
        relative = file_path.resolve().relative_to(namespace_dir.resolve())
        return next(
            (
                letter
                for letter, family in (
                    FlextInfraUtilitiesCodegenNamespace.facade_families().items()
                )
                if family.directory in relative.parts[:-1]
                or (len(relative.parts) == 1 and relative.stem == family.module)
            ),
            None,
        )

    @classmethod
    def lazy_source(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
        *,
        sources: Mapping[Path, str] | None = None,
    ) -> str | None:
        """Return the nearest package that lazily publishes one leaf object.

        Returns:
            The publishing package, or None when no parent route is needed.

        """
        package = module.rpartition(".")[0]
        directory = cls.import_package_dir(scope.project_root, module, sources=sources)
        if directory is not None:
            return cls._declared_subpackage_source(scope, module, name, sources=sources)
        if not package or scope.module in {module, package}:
            return None
        if (
            cls.import_lazy_exports(scope.project_root, module, sources=sources)
            is not None
        ):
            return None
        exports = cls.import_lazy_exports(scope.project_root, package, sources=sources)
        if exports is None or exports.get(name) != module:
            return None
        return package

    @classmethod
    def _declared_subpackage_source(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
        *,
        sources: Mapping[Path, str] | None = None,
    ) -> str | None:
        """Discover a unique source declaration published by its own package.

        Returns:
            The declaring package, or no declared destination.

        Raises:
            ValueError: When independent declarations publish the same name.

        """
        directory = cls.import_package_dir(scope.project_root, module, sources=sources)
        if directory is None:
            return None
        candidates: MutableMapping[str, str] = {}
        cls._scan_lookups += 1
        cls._scan_consumers.add(scope.file_path)
        for source_path in sorted(
            directory.rglob("*.py")
            if sources is None
            else (
                path
                for path in sources
                if path.is_relative_to(directory) and path.suffix == c.Infra.EXT_PYTHON
            ),
            key=lambda path: (len(path.parts), path),
        ):
            cls._scan_files += 1
            cls._scan_due = cls.codemod_progress(
                f"import publication scan project={scope.project_root} "
                f"consumers={len(cls._scan_consumers)} "
                f"lookups={cls._scan_lookups} "
                f"files-scanned={cls._scan_files} "
                f"providers-found={cls._scan_providers} "
                f"(heartbeat {settings.cli_process_heartbeat_seconds:g}s)",
                cls._scan_due,
            )
            if source_path.name == c.Infra.INIT_PY:
                continue
            source = (
                source_path.read_text(encoding=c.DEFAULT_ENCODING)
                if sources is None
                else sources[source_path]
            )
            if name not in (
                FlextInfraUtilitiesRopeAnalysis.public_export_names_source(source)
            ):
                continue
            declaration = cls._module_bindings(ast.parse(source)).get(name)
            if not isinstance(
                declaration,
                ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.ImportFrom,
            ):
                continue
            relative = source_path.relative_to(directory)
            owner = ".".join((module, *relative.parent.parts))
            identity = cls._declaration_identity(
                scope,
                f"{owner}.{source_path.stem}",
                name,
                frozenset(),
                sources=sources,
            )
            cls._scan_providers += 1
            candidates.setdefault(identity, owner)
        cls._scan_due = cls.codemod_progress(
            f"import publication scan done project={scope.project_root} "
            f"consumers={len(cls._scan_consumers)} lookups={cls._scan_lookups} "
            f"files-scanned={cls._scan_files} "
            f"providers-found={cls._scan_providers} "
            f"symbol={module}.{name} candidates={len(candidates)}",
            cls._scan_due,
        )
        ancestors = cls._declared_ancestors(scope, tuple(candidates), sources=sources)
        candidates = {
            identity: owner
            for identity, owner in candidates.items()
            if identity not in ancestors
        }
        if len(candidates) > 1:
            msg = (
                f"Ambiguous declared public import {module}.{name}: "
                f"{sorted(candidates)}"
            )
            raise ValueError(msg)
        return next(iter(candidates.values()), None)

    @classmethod
    def _declared_ancestors(
        cls,
        scope: m.Infra.ImportLawScope,
        identities: t.StrTuple,
        *,
        sources: Mapping[Path, str] | None = None,
    ) -> frozenset[str]:
        """Find explicit source ancestors of the published declarations.

        Returns:
            Canonical identities extended by another declaration.

        """
        ancestors: set[str] = set()
        for identity in identities:
            provider, _, symbol = identity.rpartition(".")
            parent = cls.import_package_dir(
                scope.project_root, provider.rpartition(".")[0], sources=sources
            )
            if parent is None:
                continue
            path = parent / f"{provider.rpartition('.')[2]}.py"
            tree = ast.parse(
                path.read_text(encoding=c.DEFAULT_ENCODING)
                if sources is None
                else sources[path]
            )
            declaration = cls._module_bindings(tree).get(symbol)
            if not isinstance(declaration, ast.ClassDef):
                continue
            for expression in declaration.bases:
                base = (
                    expression.value
                    if isinstance(expression, ast.Subscript)
                    else expression
                )
                if isinstance(base, ast.Attribute) and base.attr != symbol:
                    continue
                receiver = base.value if isinstance(base, ast.Attribute) else base
                if not isinstance(receiver, ast.Name):
                    continue
                bound, binding = cls._declared_binding(tree, receiver.id)
                if isinstance(binding, ast.ImportFrom) and binding.module:
                    imported = next(
                        (
                            alias
                            for alias in binding.names
                            if (alias.asname or alias.name) == bound
                        ),
                        None,
                    )
                    if imported is not None and (
                        isinstance(base, ast.Attribute) or imported.name == symbol
                    ):
                        ancestors.add(
                            cls._declaration_identity(
                                scope,
                                f"{binding.module}.{imported.name}"
                                if isinstance(base, ast.Attribute)
                                else binding.module,
                                base.attr
                                if isinstance(base, ast.Attribute)
                                else imported.name,
                                frozenset(),
                                sources=sources,
                            )
                        )
        return frozenset(ancestors)

    @classmethod
    def _declaration_identity(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
        seen: frozenset[str],
        *,
        sources: Mapping[Path, str] | None = None,
    ) -> str:
        """Follow explicit reexports to their source, rejecting cyclic bindings.

        Returns:
            The canonical declaration's qualified identity.

        Raises:
            ValueError: When a reexport cycles or has no declared binding.
            TypeError: When the binding is not a source declaration.

        """
        identity = f"{module}.{name}"
        if identity in seen:
            msg = f"Cyclic declared public import: {identity}"
            raise ValueError(msg)
        exports = cls.import_lazy_exports(scope.project_root, module, sources=sources)
        if exports is not None and name in exports:
            return cls._declaration_identity(
                scope, exports[name], name, seen | {identity}, sources=sources
            )
        parent = cls.import_package_dir(
            scope.project_root, module.rpartition(".")[0], sources=sources
        )
        if parent is None:
            return identity
        path = parent / f"{module.rpartition('.')[2]}.py"
        if not (path.is_file() if sources is None else path in sources):
            msg = f"Missing declared public import: {identity}"
            raise ValueError(msg)
        binding = cls._module_bindings(
            ast.parse(
                path.read_text(encoding=c.DEFAULT_ENCODING)
                if sources is None
                else sources[path]
            )
        ).get(name)
        if isinstance(binding, ast.ImportFrom):
            alias = next(
                alias for alias in binding.names if (alias.asname or alias.name) == name
            )
            parts = module.split(".")[:-1]
            target = (
                ".".join((
                    *parts[: len(parts) - binding.level + 1],
                    binding.module or "",
                )).rstrip(".")
                if binding.level
                else binding.module
            )
            if target:
                return cls._declaration_identity(
                    scope, target, alias.name, seen | {identity}, sources=sources
                )
        if isinstance(binding, ast.Assign) and isinstance(binding.value, ast.Name):
            return cls._declaration_identity(
                scope, module, binding.value.id, seen | {identity}, sources=sources
            )
        if not isinstance(binding, c.Infra.AST_DEFINITION_TYPES):
            msg = f"Missing declared public import: {identity}"
            raise TypeError(msg)
        return identity

    @classmethod
    def model_utility_target(
        cls,
        project: p.Infra.RopeProject,
        qualified: str,
        *,
        binding: p.Infra.RopePyName | None = None,
    ) -> tuple[str, str, str] | None:
        """Prove a model helper's native static identity and lazy publication.

        Returns:
            The published package, owner and member of a source static method.

        Raises:
            ValueError: If the method needs facade dispatch or is not published.
            TypeError: If the source declaration is not a module AST.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        if binding is None:
            binding = FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_binding(
                project, qualified
            )
        if not FlextInfraUtilitiesRopeRuntime.py_function(binding.get_object()):
            return None
        holder, line = binding.get_definition_location()
        if holder is None or line is None:
            msg = f"model utility has no source owner: {qualified}"
            raise ValueError(msg)
        tree = holder.get_ast()
        if not isinstance(tree, ast.Module):
            msg = f"model utility has no source declaration: {qualified}"
            raise TypeError(msg)
        declarations = [
            (owner, method)
            for owner in tree.body
            if isinstance(owner, ast.ClassDef)
            for method in owner.body
            if isinstance(method, c.Infra.AST_FUNCTION_TYPES) and method.lineno == line
        ]
        if len(declarations) != 1:
            msg = f"model utility has no unique static owner: {qualified}"
            raise ValueError(msg)
        owner, method = declarations[0]
        owner_scope = next(
            scope
            for scope in holder.get_scope().get_scopes()
            if scope.get_start() == owner.lineno
        )
        staticmethod_binding = runtime.qualified_name(project, "builtins.staticmethod")
        if not any(
            runtime.same_name(
                staticmethod_binding, runtime.resolve_symbol(owner_scope, decorator)
            )
            for decorator in method.decorator_list
        ):
            msg = f"model utility requires facade dispatch: {qualified}"
            raise ValueError(msg)
        public_module = holder.get_name().rpartition(".")[0]
        exported_owner = cls.resolve_declared_binding(
            project, public_module, owner.name, Path(project.root.real_path), {}
        )
        exported = (
            exported_owner.get_object().get_attributes().get(method.name)
            if exported_owner is not None
            else None
        )
        if not runtime.same_name(binding, exported):
            msg = f"model utility owner is not lazy-published: {qualified}"
            raise ValueError(msg)
        return public_module, owner.name, method.name

    @classmethod
    def import_contract_routes(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        resources: Sequence[p.Infra.RopeResource],
        sources: Mapping[Path, str],
    ) -> Sequence[tuple[p.Infra.RopeContractRule, Sequence[p.Infra.RopeResource]]]:
        """Bind a family's new calls through its declared helper, never its facade.

        Returns:
            Contract routes grouped by their rewritten goal and native bindings.

        """
        routes: list[tuple[p.Infra.RopeContractRule, list[p.Infra.RopeResource]]] = []
        for resource in resources:
            routed = cls._import_contract_rule(project, rule, resource, sources)
            group = next(
                (
                    entry
                    for entry in routes
                    if entry[0].goal == routed.goal
                    and entry[0].imports == routed.imports
                    and entry[0].bindings == routed.bindings
                ),
                None,
            )
            if group is None:
                routes.append((routed, [resource]))
            else:
                group[1].append(resource)
        return tuple((selected, tuple(items)) for selected, items in routes)

    @classmethod
    def _import_contract_rule(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        resource: p.Infra.RopeResource,
        sources: Mapping[Path, str],
    ) -> p.Infra.RopeContractRule:
        """Apply existing family publication law to one consumer's native goals.

        Returns:
            The original rule or its same-family publication route.

        Raises:
            TypeError: If the consumer is not a native source module.

        """
        path = Path(resource.real_path).resolve()
        root = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            Path(project.root.real_path), path, source_project=project
        )
        located = (
            cls.import_namespace(root, path, sources=sources, source_project=project)
            if root is not None
            else None
        )
        if root is None or located is None or not rule.bindings:
            return rule
        namespace, module_name = located
        letter = cls.family_letter(namespace, path)
        if letter is None:
            return rule
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        if not FlextInfraUtilitiesRopeRuntime.source_module(module):
            message = f"family contract consumer is not a source module: {path}"
            raise TypeError(message)
        context = m.Infra.ImportLawScope(
            project_root=root,
            file_path=path,
            namespace_dir=namespace,
            module=module_name,
            layer=cls.module_import_layer(module_name),
            own_exports=frozenset(
                FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                    module.source_code
                )
            ),
            family_letter=letter,
        )
        return cls._family_contract_rule(project, rule, (context, module), sources)

    @classmethod
    def _family_contract_rule(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        frame: tuple[m.Infra.ImportLawScope, p.Infra.RopePyModule],
        sources: Mapping[Path, str],
    ) -> p.Infra.RopeContractRule:
        """Rewrite eligible bindings without changing unrelated imports.

        Returns:
            The original rule or a copy carrying family-local destinations.

        """
        goal, imports, bindings = rule.goal, dict(rule.imports), dict(rule.bindings)
        for expression, identity in rule.bindings.items():
            route = cls._family_binding_route(project, identity, frame, sources)
            if route is None:
                continue
            local, member, package, owner = route
            destination = f"{local}.{member}"
            del bindings[expression]
            bindings[destination] = identity
            old_root = expression.split(".", 1)[0]
            if not any(name.split(".", 1)[0] == old_root for name in bindings):
                imports.pop(old_root, None)
            if package is not None and "." not in local:
                imports[local] = f"from {package} import {owner}" + (
                    f" as {local}" if local != owner else ""
                )
            goal = goal.replace(expression, destination)
        if (goal, imports, bindings) == (rule.goal, rule.imports, rule.bindings):
            return rule
        return m.Infra.RopeContractRule.model_validate(
            rule, from_attributes=True
        ).model_copy(update={"goal": goal, "imports": imports, "bindings": bindings})

    @classmethod
    def _family_binding_route(
        cls,
        project: p.Infra.RopeProject,
        identity: str,
        frame: tuple[m.Infra.ImportLawScope, p.Infra.RopePyModule],
        sources: Mapping[Path, str],
    ) -> tuple[str, str, str | None, str] | None:
        """Resolve one published family binding into its consumer spelling.

        Returns:
            Local spelling, member, publication package and declared owner.

        Raises:
            ValueError: If a destination has no lazy publication.

        """
        context, module = frame
        binding = FlextInfraUtilitiesRopeRuntime.qualified_name(project, identity)
        provider = binding.get_object().get_module()
        resource = provider.get_resource() if provider is not None else None
        if provider is None or resource is None:
            return None
        path = Path(resource.real_path).resolve()
        if not cls._family_provider_admitted(project, identity, binding, context, path):
            return None
        owner, separator, member = identity.removeprefix(
            f"{provider.get_name()}."
        ).partition(".")
        if not separator or owner not in (
            FlextInfraUtilitiesRopeAnalysis.public_export_names_source(sources[path])
        ):
            return None
        owner_binding = FlextInfraUtilitiesRopeRuntime.qualified_name(
            project, f"{provider.get_name()}.{owner}"
        )
        package = cls.lazy_source(context, provider.get_name(), owner, sources=sources)
        local = cls._family_owner_spelling(module.get_scope(), owner_binding, owner)
        if package is None and not FlextInfraUtilitiesRopeRuntime.same_name(
            owner_binding, module.get_scope().get_names().get(local)
        ):
            message = f"{identity}: same-family destination has no lazy publication"
            raise ValueError(message)
        return local, member, package, owner

    @classmethod
    def _family_provider_admitted(
        cls,
        project: p.Infra.RopeProject,
        identity: str,
        binding: p.Infra.RopePyName,
        context: m.Infra.ImportLawScope,
        path: Path,
    ) -> bool:
        """Check family ownership and the model-to-utility static boundary.

        Returns:
            Whether the provider belongs to the routed family.

        Raises:
            ValueError: If a model utility destination is not a static method.

        """
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        if context.family_letter is None:
            message = "family provider routing requires a declared family letter"
            raise ValueError(message)
        own_utility = context.family_letter == "m" and path.is_relative_to(
            context.namespace_dir / families["u"].directory
        )
        if (
            own_utility
            and cls.model_utility_target(project, identity, binding=binding) is None
        ):
            message = f"model utility destination is not a static method: {identity}"
            raise ValueError(message)
        return own_utility or path.is_relative_to(
            context.namespace_dir / families[context.family_letter].directory
        )

    @classmethod
    def _family_owner_spelling(
        cls,
        scope: p.Infra.RopeScope,
        binding: p.Infra.RopePyName,
        owner: str,
    ) -> str:
        """Resolve direct and module-qualified spellings of one native owner.

        Returns:
            The existing local spelling, or the declared owner name.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        local = next(
            (
                name
                for name, candidate in scope.get_names().items()
                if runtime.same_name(binding, candidate)
            ),
            owner,
        )
        if runtime.same_name(binding, scope.get_names().get(local)):
            return local
        return next(
            (
                f"{name}.{owner}"
                for name, candidate in scope.get_names().items()
                if runtime.same_name(
                    binding, candidate.get_object().get_attributes().get(owner)
                )
            ),
            local,
        )

    @classmethod
    def import_contract_bindings(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        offset: int,
    ) -> bool:
        """Prove each destination and its preceding unconditional import.

        Returns:
            True when every present destination preserves its native identity.

        Raises:
            ValueError: If a destination is shadowed or lacks its preceding import.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        for expression, expected in rule.bindings.items():
            identity = runtime.qualified_name(project, expected)
            root = expression.split(".", 1)[0]
            root_name = runtime.expression_name(scope, root)
            if root_name is None:
                binding = (
                    module
                    .get_source_binding_index()
                    .context_at(offset)
                    .environment.lookup(root)
                )
                if binding is None:
                    continue
                actual = binding
            else:
                actual = runtime.expression_name(scope, expression)
            if not runtime.same_name(identity, actual):
                message = (
                    f"{rule.id}: destination {expression} is shadowed "
                    f"in {module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
            if isinstance(
                root_name, (p.Infra.RopeImportedName, p.Infra.RopeImportedModule)
            ) and not runtime.imported_binding_precedes(project, module, root, offset):
                message = (
                    f"{rule.id}: destination {expression} has no preceding "
                    f"unconditional import in {module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
        return True


__all__: list[str] = ["FlextInfraUtilitiesImportLawPolicyPublication"]
