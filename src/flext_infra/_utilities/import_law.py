"""Import-law facts: namespaces, layers, lazy exports and facade routes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from time import monotonic
from typing import Literal

from flext_cli import settings, u

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)


class FlextInfraUtilitiesImportLaw:
    """Single owner of the import-law facts the enforcement routes read."""

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

    @staticmethod
    def family_letter(namespace_dir: Path, file_path: Path) -> str | None:
        """Return the facade letter of the family package holding one module.

        Returns:
            The family letter, or None outside every family package.

        """
        relative = file_path.resolve().relative_to(namespace_dir.resolve())
        return next(
            (
                letter
                for part in (*relative.parts[:-1], relative.stem)
                for letter, family in (
                    FlextInfraUtilitiesCodegenNamespace.facade_families().items()
                )
                if part in {family.directory, family.module}
            ),
            None,
        )

    @staticmethod
    def _module_bindings(tree: ast.Module) -> t.MappingKV[str, ast.stmt]:
        """Return the module-level statement binding each top-level name.

        Returns:
            The first declaring statement for each module-level name.

        """
        bindings: t.MutableMappingKV[str, ast.stmt] = {}
        for statement in tree.body:
            names: list[str] = []
            match statement:
                case ast.Import(names=aliases) | ast.ImportFrom(names=aliases):
                    names = [
                        alias.asname or alias.name.partition(".")[0]
                        for alias in aliases
                    ]
                case (
                    ast.FunctionDef(name=name)
                    | ast.AsyncFunctionDef(name=name)
                    | ast.ClassDef(name=name)
                ):
                    names = [name]
                case ast.Assign(targets=targets):
                    names = [
                        target.id for target in targets if isinstance(target, ast.Name)
                    ]
                case ast.AnnAssign(target=ast.Name(id=name)):
                    names = [name]
                case _:
                    pass
            for bound in names:
                bindings.setdefault(bound, statement)
        return bindings

    @classmethod
    def lazy_source(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
        *,
        sources: t.MappingKV[Path, str] | None = None,
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
        sources: t.MappingKV[Path, str] | None = None,
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
        candidates: t.MutableMappingKV[str, str] = {}
        due = 0.0
        scanned = 0
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
            due = cls.codemod_progress(
                f"import publication lookup project={scope.project_root} "
                f"consumer={scope.file_path} symbol={module}.{name} "
                f"scanned={scanned} provider={source_path}",
                due,
            )
            scanned += 1
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
            candidates.setdefault(identity, owner)
        cls.codemod_progress(
            f"import publication ancestry project={scope.project_root} "
            f"consumer={scope.file_path} symbol={module}.{name} "
            f"scanned={scanned} candidates={len(candidates)}",
            due,
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
        sources: t.MappingKV[Path, str] | None = None,
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
    def _declared_binding(
        cls, tree: ast.Module, name: str
    ) -> tuple[str, ast.stmt | None]:
        """Follow module-level name aliases without executing the provider.

        Returns:
            The original bound name and its declaring statement.

        Raises:
            ValueError: When aliases form a cycle.

        """
        bindings = cls._module_bindings(tree)
        seen: set[str] = set()
        while name not in seen:
            seen.add(name)
            binding = bindings.get(name)
            if not isinstance(binding, ast.Assign | ast.AnnAssign) or not isinstance(
                binding.value, ast.Name
            ):
                return name, binding
            name = binding.value.id
        msg = f"Cyclic declared binding: {name}"
        raise ValueError(msg)

    @classmethod
    def _declaration_identity(
        cls,
        scope: m.Infra.ImportLawScope,
        module: str,
        name: str,
        seen: frozenset[str],
        *,
        sources: t.MappingKV[Path, str] | None = None,
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
        if not isinstance(
            binding, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            msg = f"Missing declared public import: {identity}"
            raise TypeError(msg)
        return identity

    @staticmethod
    def model_utility_target(
        project: p.Infra.RopeProject,
        qualified: str,
        *,
        binding: p.Infra.RopePyName | None = None,
    ) -> t.Triple[str, str, str] | None:
        """Prove a model helper's native static identity and lazy publication.

        Returns:
            The published package, owner and member of a source static method.

        Raises:
            ValueError: If the method needs facade dispatch or is not published.
            TypeError: If the source declaration is not a module AST.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if binding is None:
            binding = FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_binding(
                project, qualified
            )
        if binding.get_object().get_kind() not in {
            "function",
            "method",
            "staticmethod",
            "classmethod",
        }:
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
            if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
            and method.lineno == line
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
        exported_owner = FlextInfraUtilitiesImportLaw.resolve_declared_binding(
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
        resources: t.SequenceOf[p.Infra.RopeResource],
        sources: t.MappingKV[Path, str],
    ) -> t.SequenceOf[
        t.Pair[p.Infra.RopeContractRule, t.SequenceOf[p.Infra.RopeResource]]
    ]:
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
        sources: t.MappingKV[Path, str],
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
            cls.import_namespace(root, path, sources=sources)
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
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
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
        frame: t.Pair[m.Infra.ImportLawScope, p.Infra.RopePyModule],
        sources: t.MappingKV[Path, str],
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
        frame: t.Pair[m.Infra.ImportLawScope, p.Infra.RopePyModule],
        sources: t.MappingKV[Path, str],
    ) -> tuple[str, str, str | None, str] | None:
        """Resolve one published family binding into its consumer spelling.

        Returns:
            Local spelling, member, publication package and declared owner.

        Raises:
            ValueError: If a destination has no lazy publication.

        """
        context, module = frame
        binding = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, identity
        )
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
        owner_binding = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, f"{provider.get_name()}.{owner}"
        )
        package = cls.lazy_source(context, provider.get_name(), owner, sources=sources)
        local = cls._family_owner_spelling(module.get_scope(), owner_binding, owner)
        if package is None and not FlextInfraUtilitiesRopeRuntimeModules.same_name(
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

    @staticmethod
    def _family_owner_spelling(
        scope: p.Infra.RopeScope,
        binding: p.Infra.RopePyName,
        owner: str,
    ) -> str:
        """Resolve direct and module-qualified spellings of one native owner.

        Returns:
            The existing local spelling, or the declared owner name.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
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

    @staticmethod
    def import_contract_bindings(
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
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for expression, expected in rule.bindings.items():
            identity = runtime.qualified_name(project, expected)
            root = expression.split(".", 1)[0]
            root_name = runtime.expression_name(scope, root)
            if root_name is None:
                continue
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

    @classmethod
    def import_namespace(
        cls,
        project_root: Path,
        file_path: Path,
        *,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> t.Pair[Path, str] | None:
        """Return the namespace directory and dotted module of one file.

        A namespace is a top-level package of a project: the source package
        under ``src/`` or an internal tier (``tests``, ``examples``,
        ``scripts``) whose directory carries an ``__init__.py``.

        Returns:
            The namespace directory and the file's dotted module name, or
            ``None`` when the file belongs to no namespace of the project.

        """
        root = project_root.resolve()
        resolved = file_path.resolve()
        if not resolved.is_relative_to(root):
            return None
        relative = resolved.relative_to(root)
        source_dir = root / c.Infra.DEFAULT_SRC_DIR
        if relative.parts and relative.parts[0] == c.Infra.DEFAULT_SRC_DIR:
            relative = resolved.relative_to(source_dir)
            base = source_dir
        else:
            base = root
        namespace_name, *module_parts = relative.parts
        if not module_parts:
            return None
        namespace_dir = base / namespace_name
        init = namespace_dir / c.Infra.INIT_PY
        if not (init.is_file() if sources is None else init in sources):
            return None
        parts = relative.with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return namespace_dir, ".".join(parts)

    @staticmethod
    def module_import_layer(module: str) -> int:
        """Return the layer rank of one dotted module of a namespace.

        A module's layer is the first path segment, from its namespace
        downwards, that names a layer either directly (``settings``,
        ``config``, ``base``, ``services``, ``api``, ``cli``) or through the
        facade family it stands for (``_models`` and ``models.py`` stand for
        ``m``); a module naming no layer sits in the ``other`` slot.

        Returns:
            The index of the module's layer in the declared order.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        families = {
            family.module: letter
            for letter, family in (
                FlextInfraUtilitiesCodegenNamespace.facade_families().items()
            )
        }
        for part in module.split(".")[1:]:
            stem = part.lstrip("_")
            layer = families.get(stem, stem)
            if layer in order:
                return order.index(layer)
        return order.index(c.Infra.IMPORT_LAW_OTHER_LAYER)

    @staticmethod
    def import_module_role(module: str) -> Literal["layer0", "family", "consumer"]:
        """Classify a module from the canonical singleton and family vocabulary.

        Layer-zero declarations cannot depend on their own namespace, even
        through a typing guard. Family assembly may retain canonical private
        imports; it cannot consume the facade it produces.

        Returns:
            The resulting ``Literal['layer0', 'family', 'consumer']``.

        """
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        for part in module.split(".")[1:]:
            stem = part.lstrip("_")
            if any(stem == family.module for family in families.values()):
                return "family"
            if any(
                stem == role or stem.startswith(f"{role}_")
                for role in c.Infra.IMPORT_LAW_ROOT_SINGLETONS
            ):
                return "layer0"
            if stem in config.Infra.tooling.lazy_init.import_layer_order:
                return "consumer"
        return "consumer"

    @staticmethod
    def import_direct_module(namespace_dir: Path, file_path: Path) -> bool:
        """Return whether one module keeps direct leaf imports.

        A layer-zero settings/config module and a family
        ``base.py`` (a ``base.py`` inside a private ``_<family>/`` package)
        retain their upstream/direct providers instead of re-entering the
        namespace's lazy root. This routing constraint does not exempt them
        from import-boundary validation.

        Returns:
            Whether the module is exempt from root-alias and lazy routing.

        """
        relative = file_path.resolve().relative_to(namespace_dir.resolve())
        module = ".".join((namespace_dir.name, *relative.with_suffix("").parts))
        if FlextInfraUtilitiesImportLaw.import_module_role(module) == "layer0":
            return True
        return (
            len(relative.parts) > 1
            and relative.name == c.Infra.IMPORT_LAW_FAMILY_BASE_FILE
            and relative.parts[-2].startswith("_")
        )

    @staticmethod
    def import_lazy_exports(
        project_root: Path,
        package: str,
        *,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> t.StrMapping | None:
        """Map each name one owned package ``__init__`` publishes to its module.

        The package resolves under ``src/`` or the project root (internal
        tiers). Relative targets resolve against the package; a target naming
        another distribution (``flext_cli``) stays absolute. The parse is
        memoized by the existing source parser using the exact published
        content. Each lookup resolves the current file, so same-process
        publication and newly created packages cannot retain retired routes.

        Returns:
            The published name to absolute defining module mapping, or
            ``None`` when the dotted name is a module, a missing path or a
            package of another project.

        Raises:
            ValueError: If the package init declares its lazy map indirectly.

        """
        top, *rest = package.split(".")
        bases = (project_root / c.Infra.DEFAULT_SRC_DIR, project_root)
        owner = next(
            (
                base
                for base in bases
                if (
                    (base / top / c.Infra.INIT_PY).is_file()
                    if sources is None
                    else base / top / c.Infra.INIT_PY in sources
                )
            ),
            None,
        )
        if owner is None:
            return None
        init = owner.joinpath(top, *rest, c.Infra.INIT_PY)
        if not (init.is_file() if sources is None else init in sources):
            return None
        targets, references = (
            FlextInfraUtilitiesRopeAnalysis.lazy_import_mapping_source(
                init.read_text(encoding=c.DEFAULT_ENCODING)
                if sources is None
                else sources[init],
            )
        )
        if references:
            msg = f"{init}: lazy map is declared through {', '.join(references)}"
            raise ValueError(msg)
        return {
            name: f"{package}{module}" if module.startswith(".") else module
            for module, names in targets
            for name in names
        }

    @staticmethod
    def import_package_dir(
        project_root: Path,
        package: str,
        *,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> Path | None:
        """Return the directory of one dotted package the project owns.

        Returns:
            The package directory, or ``None`` for a module, a missing path or
            a package of another project.

        """
        top, *rest = package.split(".")
        for base in (project_root / c.Infra.DEFAULT_SRC_DIR, project_root):
            init = base / top / c.Infra.INIT_PY
            if not (init.is_file() if sources is None else init in sources):
                continue
            candidate = base.joinpath(top, *rest)
            init = candidate / c.Infra.INIT_PY
            return (
                candidate
                if (init.is_file() if sources is None else init in sources)
                else None
            )
        return None

    @staticmethod
    def import_bootstrap_dependency(
        namespace: str,
        module: str,
        import_graph: t.MappingKV[str, frozenset[str]],
    ) -> bool:
        """Identify modules the root executes before lazy exports are installed.

        Returns:
            Whether routing the module through its root would re-enter bootstrap.

        """
        pending = list(import_graph.get(namespace, ()))
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == module:
                return True
            if current not in visited:
                visited.add(current)
                pending.extend(import_graph.get(current, ()))
        return False

    @staticmethod
    def import_facade_dependencies(
        module: str,
        root_exports: t.StrMapping,
        import_graph: t.MappingKV[str, frozenset[str]],
    ) -> frozenset[str]:
        """Return facade aliases whose providers depend on the importing module."""
        dependencies: set[str] = set()
        for alias in c.Infra.ALIAS_NAMES | c.Infra.IMPORT_LAW_ROOT_SINGLETONS:
            provider = root_exports.get(alias)
            if provider is None:
                continue
            pending = [provider]
            visited: set[str] = set()
            while pending:
                current = pending.pop()
                if current == module:
                    dependencies.add(alias)
                    break
                if current not in visited:
                    visited.add(current)
                    pending.extend(import_graph.get(current, ()))
        return frozenset(dependencies)

    @staticmethod
    def resolve_declared_binding(
        project: p.Infra.RopeProject,
        module_name: str,
        alias_name: str,
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> p.Infra.RopePyName | None:
        """Follow the existing native lazy routes without losing tuple aliases.

        Returns:
            The declared native binding, or None when the final provider lacks it.

        Raises:
            ValueError: If a lazy route cycles or does not name one binding.

        """
        provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
            project.get_module(module_name)
        )
        visited: set[t.Pair[str, str]] = set()
        while True:
            resource = provider.get_resource()
            if resource is None:
                break
            if resource.is_folder():
                resource = project.get_resource(f"{resource.path}/{c.Infra.INIT_PY}")
            identity = provider.get_name(), alias_name
            if identity in visited:
                msg = f"cyclic lazy export {identity}"
                raise ValueError(msg)
            visited.add(identity)
            path = Path(resource.real_path).resolve()
            source = (
                sources[path]
                if path.is_relative_to(root) and path in sources
                else (
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        resource, path
                    ).read()
                )
            )
            route = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                provider.get_name(), path, source, project=project, pymodule=provider
            ).get(alias_name)
            if route is None:
                break
            if len(route.attributes) != 1:
                msg = f"declaration export is not a named binding: {identity}"
                raise ValueError(msg)
            alias_name = route.attributes[0]
            provider = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                project.get_module(route.target)
            )
        return provider.get_attributes().get(alias_name)


__all__: list[str] = ["FlextInfraUtilitiesImportLaw"]
