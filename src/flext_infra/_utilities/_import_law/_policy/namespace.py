"""Import-law facts: namespaces, layers, lazy exports and facade routes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping
from functools import cache
from importlib.metadata import entry_points
from pathlib import Path
from types import MappingProxyType
from typing import Literal

import flext_core

from flext_infra import c, config, p
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectDiscovery,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesImportLawPolicyNamespace:
    """Declare the namespace facts of the composed import policy."""

    @staticmethod
    def _module_bindings(tree: ast.Module) -> Mapping[str, ast.stmt]:
        """Return the module-level statement binding each top-level name.

        Returns:
            The last declaring statement for each module-level name.

        """
        bindings: MutableMapping[str, ast.stmt] = {}
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
                bindings[bound] = statement
        return bindings

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
            if not isinstance(binding, c.Infra.AST_ASSIGNMENT_TYPES) or not isinstance(
                binding.value, ast.Name
            ):
                return name, binding
            name = binding.value.id
        msg = f"Cyclic declared binding: {name}"
        raise ValueError(msg)

    @classmethod
    def snapshot_import_namespace(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project_root: Path,
        file_path: Path,
    ) -> tuple[Path, str] | None:
        """Reuse the import-law election within one captured source epoch.

        Returns:
            The namespace location for this consumer and source, or ``None``.

        """
        key = (project_root, file_path)
        if key not in snapshot.import_namespaces:
            snapshot.import_namespaces[key] = cls.import_namespace(
                project_root, file_path, source_project=snapshot.engine
            )
        return snapshot.import_namespaces[key]

    @classmethod
    def import_namespace(
        cls,
        project_root: Path,
        file_path: Path,
        *,
        sources: Mapping[Path, str] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> tuple[Path, str] | None:
        """Return the namespace directory and dotted module of one file.

        Regular source packages and internal tiers own their root. A declared
        PEP 420 root instead delegates publication to its first regular package
        ancestor of the file, retaining the complete declared module identity.

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
        # A regular package needs no declaration lookup: the repository's
        # declared namespace packages are read only for an init-less tier.
        if not (
            source_project.source_query(init, "isfile")
            if source_project is not None
            else init in sources
            if sources is not None
            else init.is_file()
        ):
            if base != root or namespace_name not in (
                FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(
                    root, source_project=source_project
                )
            ):
                return None
            for part in module_parts[:-1]:
                namespace_dir /= part
                init = namespace_dir / c.Infra.INIT_PY
                if (
                    source_project.source_query(init, "isfile")
                    if source_project is not None
                    else init in sources
                    if sources is not None
                    else init.is_file()
                ):
                    break
            else:
                # Namespace admission does not fabricate a publishing package.
                namespace_dir = base / namespace_name
        return namespace_dir, FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
            resolved, project_root=root, source_project=source_project
        )

    @staticmethod
    @cache
    def _layer_alias_modules() -> Mapping[str, str]:
        """Derive the module stem of every declared layer alias.

        The core package binds each ``layer-aliases`` entry to a class; that
        class's module stem (and its private ``_<module>/`` package) ranks at
        the alias's declared layer. No module is listed here.

        Returns:
            The module stem of each alias mapped to the layer it ranks at.

        Raises:
            TypeError: If the core package binds an alias to no class.

        """
        modules: dict[str, str] = {}
        for alias, layer in config.Infra.tooling.lazy_init.layer_aliases.items():
            facade = getattr(flext_core, alias, None)
            if not isinstance(facade, type):
                msg = f"core package binds no class to layer alias: {alias}"
                raise TypeError(msg)
            modules[facade.__module__.rpartition(".")[2]] = layer
        return MappingProxyType(modules)

    @classmethod
    def module_import_layer(cls, module: str, *, namespace: str | None = None) -> int:
        """Return the layer rank of one dotted module of a namespace.

        A module's layer is the first path segment, from its namespace
        downwards, that names a layer either directly (``settings``,
        ``config``, ``base``, ``services``, ``api``, ``cli``) or through the
        facade family it stands for (``_models`` and ``models.py`` stand for
        ``m``) or a declared layer alias binds it to (``_result`` ranks with
        ``u``); a module naming no layer sits in the ``other`` slot.

        Returns:
            The index of the module's layer in the declared order.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        families = {
            **cls._layer_alias_modules(),
            **{
                family.module: letter
                for letter, family in (
                    FlextInfraUtilitiesCodegenNamespace.facade_families().items()
                )
            },
        }
        for index, part in enumerate(
            module.split(".")[len(namespace.split(".")) if namespace else 1 :]
        ):
            if index and not part.startswith("_"):
                continue
            stem = part.lstrip("_")
            layer = families.get(stem, stem)
            if layer in order:
                return order.index(layer)
        return order.index(c.Infra.IMPORT_LAW_OTHER_LAYER)

    @staticmethod
    @cache
    def pytest_plugin_modules() -> frozenset[str]:
        """Modules the installed distributions register as pytest11 plugins.

        Returns:
            The plugin module names read from installed entry-point metadata.

        """
        return frozenset(
            entry.module
            for entry in entry_points(group=c.Infra.IMPORT_LAW_PYTEST_PLUGIN_GROUP)
        )

    @classmethod
    def import_module_role(
        cls,
        module: str,
        *,
        namespace: str | None = None,
        bootstrap: bool = False,
    ) -> Literal["layer0", "family", "consumer"]:
        """Classify a module from the canonical singleton and family vocabulary.

        Layer-zero declarations cannot depend on their own namespace, even
        through a typing guard. Family assembly may retain canonical private
        imports; it cannot consume the facade it produces. Singleton names
        identify namespace roots only; nested declarations require native ancestry.
        Modules registered as pytest11 plugins are layer zero for pytest.
        Bootstrap membership is supplied explicitly from the captured native
        graph; this lexical classifier never resolves an installed package.

        Returns:
            The resulting ``Literal['layer0', 'family', 'consumer']``.

        """
        if bootstrap or module in cls.pytest_plugin_modules():
            return "layer0"
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        for index, part in enumerate(
            module.split(".")[len(namespace.split(".")) if namespace else 1 :]
        ):
            stem = part.lstrip("_")
            if any(stem == family.module for family in families.values()):
                return "family"
            if index == 0 and any(
                stem == role or stem.startswith(f"{role}_")
                for role in c.Infra.IMPORT_LAW_LAYER_ZERO_ROOTS
            ):
                return "layer0"
            if stem in config.Infra.tooling.lazy_init.import_layer_order:
                return "consumer"
        return "consumer"

    @classmethod
    def import_source_role(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        source: Path,
    ) -> Literal["layer0", "family", "consumer"]:
        """Resolve declaration roles by native ancestry, not consumer imports.

        Returns:
            The lexical family role or the source-defined configuration role.

        """
        role = cls.import_module_role(
            FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                source, project_root=Path(project.root.real_path)
            ),
        )
        if role != "consumer":
            return role
        runtime = FlextInfraUtilitiesRopeRuntime
        types = FlextInfraUtilitiesRopeRuntime
        roots = tuple(
            runtime.qualified_name(project, name, module_name="flext_core").get_object()
            for name in ("FlextConfig", "FlextSettings")
        )
        pending = [
            value
            for attribute in module.get_attributes().values()
            if types.py_class(value := attribute.get_object())
            and value.get_module() is module
        ]
        visited: set[int] = set()
        while pending:
            declaration = pending.pop()
            if id(declaration) in visited:
                continue
            visited.add(id(declaration))
            if any(declaration is root for root in roots):
                return "layer0"
            pending.extend(
                base for base in declaration.get_superclasses() if types.py_class(base)
            )
        return role

    @classmethod
    def import_direct_module(
        cls, namespace_dir: Path, file_path: Path, *, namespace: str
    ) -> bool:
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
        module = ".".join((namespace, *relative.with_suffix("").parts))
        if cls.import_module_role(module, namespace=namespace) == "layer0":
            return True
        return (
            len(relative.parts) > 1
            and relative.name == c.Infra.IMPORT_LAW_FAMILY_BASE_FILE
            and relative.parts[-2].startswith("_")
        )

    @classmethod
    def import_lazy_exports(
        cls,
        project_root: Path,
        package: str,
        *,
        sources: Mapping[Path, str] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Mapping[str, str] | None:
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
        directory = cls.import_package_dir(
            project_root, package, sources=sources, source_project=source_project
        )
        if directory is None:
            return None
        init = directory / c.Infra.INIT_PY
        targets, references = (
            FlextInfraUtilitiesRopeAnalysis.lazy_import_mapping_source(
                source_project.source_text(init)
                if source_project is not None
                else sources[init]
                if sources is not None
                else init.read_text(encoding=c.DEFAULT_ENCODING),
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
        sources: Mapping[Path, str] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Path | None:
        """Return the directory of one dotted package the project owns.

        Returns:
            The package directory, or ``None`` for a module, a missing path or
            a package of another project.

        """
        top, *rest = package.split(".")
        for base in (project_root / c.Infra.DEFAULT_SRC_DIR, project_root):
            candidate = base.joinpath(top, *rest)
            init = candidate / c.Infra.INIT_PY
            if (
                source_project.source_query(init, "isfile")
                if source_project is not None
                else init in sources
                if sources is not None
                else init.is_file()
            ):
                return (
                    candidate
                    if FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                        candidate,
                        project_root=project_root,
                        source_project=source_project,
                    )
                    == package
                    else None
                )
            top_init = base / top / c.Infra.INIT_PY
            if (
                source_project.source_query(top_init, "isfile")
                if source_project is not None
                else top_init in sources
                if sources is not None
                else top_init.is_file()
            ):
                return None
        return None

    @staticmethod
    def import_bootstrap_dependency(
        namespace: str,
        module: str,
        import_graph: Mapping[str, frozenset[str]],
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
        root_exports: Mapping[str, str],
        import_graph: Mapping[str, frozenset[str]],
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

    @classmethod
    def resolve_declared_binding(
        cls,
        project: p.Infra.RopeProject,
        module_name: str,
        alias_name: str,
        root: Path,
        sources: Mapping[Path, str],
    ) -> p.Infra.RopePyName | None:
        """Follow the existing native lazy routes without losing tuple aliases.

        Returns:
            The declared native binding, or None when the final provider lacks it.

        Raises:
            ValueError: If a lazy route cycles or does not name one binding.
            TypeError: If a provider package lacks its native folder contract.

        """
        provider = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
            project.get_module(module_name)
        )
        visited: set[tuple[str, str]] = set()
        while True:
            resource = provider.get_resource()
            if resource is None:
                break
            if resource.is_folder():
                # The folder's own owner addresses its initializer: an installed
                # provider lives outside the project root.
                if not isinstance(resource, p.Infra.RopeRoot):
                    msg = f"lazy route package has no folder contract: {resource.path}"
                    raise TypeError(msg)
                resource = resource.get_child(c.Infra.INIT_PY)
            path = Path(resource.real_path).resolve()
            module_name = (
                FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                    path, project_root=root, source_project=project
                )
                if path.is_relative_to(root)
                else provider.get_name()
            )
            identity = module_name, alias_name
            if identity in visited:
                msg = f"cyclic lazy export {identity}"
                raise ValueError(msg)
            visited.add(identity)
            source = (
                sources[path]
                if path.is_relative_to(root) and path in sources
                else (
                    FlextInfraUtilitiesRopeRuntime.require_file_resource(
                        resource, path
                    ).read()
                )
            )
            if not module_name:
                # Installed provider Rope cannot name (empty dotted name):
                # identity tracking is impossible, so resolve the alias
                # natively at this boundary instead of following further.
                alias_name, _boundary_declaration = cls._declared_binding(
                    ast.parse(source), alias_name
                )
                return provider.get_attributes().get(alias_name)
            route = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                module_name, path, source, project=project, pymodule=provider
            ).get(alias_name)
            if route is None:
                alias_name, _declaration = cls._declared_binding(
                    ast.parse(source), alias_name
                )
                binding = provider.get_attributes().get(alias_name)
                if not isinstance(binding, p.Infra.RopeImportedName):
                    return binding
                alias_name = binding.imported_name
                provider = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                    FlextInfraUtilitiesRopeCore.resolve_pymodule(
                        project,
                        FlextInfraUtilitiesRopeRuntime.imported_module_resource(
                            project, binding
                        ),
                    )
                )
                continue
            if len(route.attributes) != 1:
                msg = f"declaration export is not a named binding: {identity}"
                raise ValueError(msg)
            alias_name = route.attributes[0]
            provider = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                project.get_module(route.target)
            )
        return provider.get_attributes().get(alias_name)


__all__: list[str] = ["FlextInfraUtilitiesImportLawPolicyNamespace"]
