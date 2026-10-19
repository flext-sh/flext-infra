"""Import-law facts: namespaces, layers, lazy exports and facade routes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from flext_infra import c, config, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesImportLaw:
    """Single owner of the import-law facts the enforcement routes read."""

    @staticmethod
    def model_utility_target(
        project: p.Infra.RopeProject,
        qualified: str,
    ) -> t.Triple[str, str, str] | None:
        """Prove a model helper's native static identity and lazy publication.

        Returns:
            The published package, owner and member of a source static method.

        Raises:
            ValueError: If the method needs facade dispatch or is not published.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = runtime.qualified_name(project, qualified)
        if binding.get_object().get_kind() not in {"function", "method", "classmethod"}:
            return None
        holder, line = binding.get_definition_location()
        if holder is None or line is None:
            msg = f"model utility has no source owner: {qualified}"
            raise ValueError(msg)
        tree = holder.get_ast()
        if not isinstance(tree, ast.Module):
            msg = f"model utility has no source declaration: {qualified}"
            raise ValueError(msg)
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
        exported = runtime.qualified_name(
            project, f"{owner.name}.{method.name}", module_name=public_module
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
        """Bind a family's new calls through its declared helper, never its facade."""
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
        """Apply existing family publication law to one consumer's native goals."""
        from flext_infra import m
        from flext_infra.refactor import FlextInfraImportNormalization

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
        letter = FlextInfraImportNormalization._family_letter(namespace, path)
        if letter is None:
            return rule
        family = FlextInfraUtilitiesCodegenNamespace.facade_families()[letter]
        directory = namespace / family.directory
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        scope = module.get_scope()
        goal, imports, bindings = rule.goal, dict(rule.imports), dict(rule.bindings)
        for expression, identity in rule.bindings.items():
            binding = runtime.qualified_name(project, identity)
            provider = binding.get_object().get_module()
            provider_resource = (
                provider.get_resource() if provider is not None else None
            )
            if provider is None or provider_resource is None:
                continue
            provider_path = Path(provider_resource.real_path).resolve()
            own_utility = letter == "m" and provider_path.is_relative_to(
                namespace
                / FlextInfraUtilitiesCodegenNamespace.facade_families()["u"].directory
            )
            if own_utility and cls.model_utility_target(project, identity) is None:
                message = (
                    f"model utility destination is not a static method: {identity}"
                )
                raise ValueError(message)
            if not own_utility and not provider_path.is_relative_to(directory):
                continue
            relative = identity.removeprefix(f"{provider.get_name()}.")
            owner, separator, member = relative.partition(".")
            if not separator or owner not in (
                FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                    sources[provider_path]
                )
            ):
                continue
            owner_binding = runtime.qualified_name(
                project, f"{provider.get_name()}.{owner}"
            )
            package = FlextInfraImportNormalization._lazy_source(
                m.Infra.ImportLawScope(
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
                ),
                provider.get_name(),
                owner,
                sources=sources,
            )
            local = next(
                (
                    name
                    for name, candidate in scope.get_names().items()
                    if runtime.same_name(owner_binding, candidate)
                ),
                owner,
            )
            if not runtime.same_name(owner_binding, scope.get_names().get(local)):
                local = next(
                    (
                        f"{name}.{owner}"
                        for name, candidate in scope.get_names().items()
                        if runtime.same_name(
                            owner_binding,
                            candidate.get_object().get_attributes().get(owner),
                        )
                    ),
                    local,
                )
            if package is None and not runtime.same_name(
                owner_binding, scope.get_names().get(local)
            ):
                message = f"{identity}: same-family destination has no lazy publication"
                raise ValueError(message)
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

    @staticmethod
    def import_contract_bindings(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        offset: int,
    ) -> bool:
        """Prove each destination and its preceding unconditional import."""
        from flext_infra import p

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


__all__: list[str] = ["FlextInfraUtilitiesImportLaw"]
