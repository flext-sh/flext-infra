"""Derive a facade letter's class from the ``__all__`` that declares it.

The owner of a facade letter is the module that declares it in its own
``__all__`` next to the class it names (``__all__ = ["FlextCliModels", "m"]``).
Resolution follows the last runtime module-scope binding of each name through imports
and plain or annotated aliases, reading editable and installed sources without
importing them. No class name is ever inferred from a package name.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping, MutableMapping, Sequence
from functools import lru_cache
from importlib.util import resolve_name
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra._utilities import FlextInfraUtilitiesPrivateImportFacades
from flext_infra._utilities._rope.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._rope.source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope.source_bases_inventory_collector import (
    FlextInfraUtilitiesRopeSourceBindingCollector,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverFacadeOwners:
    """Resolve facade letters to the class their declaring module names."""

    @classmethod
    def facade_classes(
        cls,
        package: str,
        *,
        source_root: Path,
    ) -> Mapping[str, str]:
        """Map every letter ``package`` publishes to its declared facade class.

        Per-repository resolution law: the declaring repository root is the
        only source surface. Installed environments are never consulted, where
        divergent member libraries would leak into the derivation.

        Returns:
            The resulting ``Mapping[str, str]``.

        Raises:
            ValueError: If the package declares no facade letter owners in its
                own indexed tree.

        """
        sources = {
            path: path.read_text(encoding=c.DEFAULT_ENCODING)
            for root in FlextInfraUtilitiesRopeCore.import_project_roots(source_root)
            for path in (root / c.Infra.DEFAULT_SRC_DIR / package).rglob("*.py")
        }
        modules = FlextInfraUtilitiesPrivateImportFacades.source_modules(sources)
        indexed = modules.get(package)
        if indexed is None:
            msg = f"facade package is not indexed for derivation: {package}"
            raise ValueError(msg)
        classes: MutableMapping[str, str] = {}
        with FlextInfraUtilitiesRopeCore.open_import_project(source_root) as project:
            for name in cls._module_public_exports(
                modules, package, project=project
            ):
                owner = cls._facade_letter_class(
                    modules, package, name, project=project
                )
                if owner is not None:
                    classes[name] = owner
        return classes

    @staticmethod
    def _module_public_exports(
        modules: Mapping[str, tuple[str, bool]],
        name: str,
        *,
        project: p.Infra.RopeProject,
    ) -> Sequence[str]:
        """Read one indexed module's public exports from its captured source.

        Package objects are not source modules. Read the exact source the
        cutover indexes through the native string-module owner.

        Returns:
            The module's exported public names.

        """
        entry = modules.get(name)
        if entry is None:
            return ()
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            project, entry[0]
        )
        return FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
            FlextInfraUtilitiesTypesRopeRuntime.require_source_module(module)
        )

    @classmethod
    def _facade_declared_owner(
        cls,
        modules: Mapping[str, tuple[str, bool]],
        module: str,
        letter: str,
        *,
        project: p.Infra.RopeProject,
    ) -> str:
        """Return the class ``letter`` names, or raise with the missing proof.

        Returns:
            The class ``letter`` names, or raise with the missing proof.

        Raises:
            ValueError: If ``owner is None``.

        """
        resolved = cls._facade_declared_class(
            modules, module, letter, frozenset(), project=project
        )
        if resolved is not None and resolved[1] == letter:
            owner_module, owner_name = resolved
            exported_here = cls._module_public_exports(modules, module, project=project)
            exported_owner = cls._module_public_exports(
                modules, owner_module, project=project
            )
            owner = (
                owner_name
                if owner_name in exported_here and owner_name in exported_owner
                else None
            )
        else:
            owner = cls._facade_letter_class(modules, module, letter, project=project)
        if owner is None:
            msg = (
                f"{module}.{letter} is not declared with its facade class in the "
                "__all__ of the module that binds it"
            )
            raise ValueError(msg)
        return owner

    @classmethod
    def _facade_letter_class(
        cls,
        modules: Mapping[str, tuple[str, bool]],
        module: str,
        letter: str,
        *,
        project: p.Infra.RopeProject,
    ) -> str | None:
        """Return the declared class of a letter that ``module`` publishes.

        Returns:
            The declared class of a letter that ``module`` publishes.

        Raises:
            ValueError: If ``cls._facade_declared_class(modules, module, owner,
                frozenset()) != resolved``.

        """
        resolved = cls._facade_declared_class(
            modules, module, letter, frozenset(), project=project
        )
        if resolved is None:
            return None
        owner_module, owner = resolved
        if owner == letter:
            return None
        exports = cls._module_public_exports(modules, owner_module, project=project)
        if letter not in exports or owner not in exports:
            return None
        if (
            cls._facade_declared_class(
                modules, module, owner, frozenset(), project=project
            )
            != resolved
        ):
            msg = f"{module} does not publish {owner_module}.{owner} as {owner}"
            raise ValueError(msg)
        return owner

    @staticmethod
    def _assigns_name(
        node: ast.Assign | ast.AnnAssign,
        name: str,
    ) -> bool:
        """Report whether one assignment statement binds ``name``.

        Returns:
            The resulting ``bool``.

        """
        return any(
            isinstance(bound, ast.Name) and bound.id == name
            for bound in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )

    @staticmethod
    def _assigned_value_binding(
        node: ast.Assign | ast.AnnAssign,
        module: str,
    ) -> tuple[str, str] | None:
        """Return the ``module.name`` target of a plain-name value, else ``None``.

        Returns:
            The resulting ``tuple[str, str] | None``.

        """
        return (module, node.value.id) if isinstance(node.value, ast.Name) else None

    @staticmethod
    def _imported_binding(
        node: ast.ImportFrom,
        name: str,
        package: str,
    ) -> tuple[str, str] | None:
        """Resolve the import that binds ``name`` relative to ``package``.

        Returns:
            The resulting ``tuple[str, str] | None``.

        """
        for imported in node.names:
            if (imported.asname or imported.name) == name:
                source_module = (
                    resolve_name(
                        "." * node.level + (node.module or ""),
                        package,
                    )
                    if node.level
                    else node.module or ""
                )
                return source_module, imported.name
        return None

    @classmethod
    def _facade_binding_state(
        cls,
        source: str,
        module: str,
        name: str,
        package: str,
    ) -> tuple[tuple[str, str] | None, bool]:
        """Follow module-scope execution order to the last binding of ``name``.

        Returns:
            The resulting ``(target, declared)`` binding state after the body.

        """
        target: tuple[str, str] | None = None
        declared = False
        statements = cls._facade_module_statements(source, module)
        for index, node in enumerate(statements):
            if isinstance(node, ast.AnnAssign) and node.value is None:
                # An annotation without a value does not rebind an existing name.
                continue
            if isinstance(node, ast.ClassDef) and node.name == name:
                target, declared = None, True
            elif isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES) and cls._assigns_name(
                node,
                name,
            ):
                target = cls._assigned_value_binding(node, module)
                if isinstance(node.value, ast.Name):
                    previous, previous_declared = cls._facade_binding_state(
                        ast.unparse(
                            ast.Module(body=list(statements[:index]), type_ignores=[]),
                        ),
                        module,
                        node.value.id,
                        package,
                    )
                    target = (module, node.value.id) if previous_declared else previous
                declared = False
            elif isinstance(node, ast.ImportFrom):
                binding = cls._imported_binding(node, name, package)
                if binding is not None:
                    target, declared = binding, False
        return target, declared

    @classmethod
    def _facade_declared_class(
        cls,
        modules: Mapping[str, tuple[str, bool]],
        module: str,
        name: str,
        visiting: frozenset[str],
        *,
        project: p.Infra.RopeProject,
    ) -> tuple[str, str] | None:
        """Follow the last module-scope binding of ``name`` to its class.

        Returns:
            The resulting ``tuple[str, str] | None``.

        Raises:
            ValueError: If cyclic facade binding.

        """
        identity = f"{module}.{name}"
        if identity in visiting:
            msg = f"cyclic facade binding: {identity}"
            raise ValueError(msg)
        indexed = modules.get(module)
        if indexed is None:
            return None
        source, is_package = indexed
        package = module if is_package else module.rpartition(".")[0]
        target, declared = cls._facade_binding_state(source, module, name, package)
        if declared:
            return module, name
        # The generated lazy publication has one reader: the rope aliases owner.
        lazy = cls._facade_lazy_bindings(
            source, module, is_package=is_package, project=project
        )
        if target is None and name in lazy:
            # A lazy entry binds the name through its provider module;
            # resolution continues where that module defines it.
            target = (lazy[name], name)
        # A submodule import binds a module, never a facade class.
        if target is None or ".".join(target) in modules:
            return None
        return cls._facade_declared_class(
            modules, *target, visiting | {identity}, project=project
        )

    @staticmethod
    @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
    def _facade_module_statements(
        source: str,
        module: str,
    ) -> tuple[ast.stmt, ...]:
        """Parse one module source once per content; resolution only reads it.

        Every facade letter re-resolves its bindings through the same modules,
        and each conform plan derives the facades twice (plan and fixed-point
        replan), so the key is the exact source text: an edited module is a new
        key, never a stale tree. TYPE_CHECKING declarations belong to the static
        source inventory, not this runtime publication view.

        Returns:
            The resulting ``tuple[ast.stmt, ...],``.

        """
        return tuple(
            FlextInfraUtilitiesSemanticCutoverFacadeOwners._facade_ordered_statements(
                ast.parse(source, filename=module).body,
            ),
        )

    @staticmethod
    def _facade_lazy_bindings(
        source: str,
        module: str,
        *,
        is_package: bool,
        project: p.Infra.RopeProject,
    ) -> Mapping[str, str]:
        """Index generated lazy publication within its owning import project.

        The lazy publication IS a binding statement: every name the
        ``install_lazy_exports`` map lists resolves through its provider
        module, exactly as it resolves at runtime. The map has one reader
        (``FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases``),
        which understands the generated shape and resolves native imports in
        the same project as the facade derivation.

        Returns:
            Published name to absolute provider module.

        """
        path = Path(
            c.Infra.INIT_PY if is_package else f"{module.rpartition('.')[2]}.py",
        )
        return MappingProxyType(
            FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                module,
                path,
                source,
                project=project,
            ),
        )

    @classmethod
    def _facade_ordered_statements(
        cls,
        body: Sequence[ast.stmt],
    ) -> Iterator[ast.stmt]:
        """Yield runtime bindings, excluding static-only TYPE_CHECKING bodies.

        Other conditions retain the existing conservative branch traversal.

        Yields:
            Each ``ast.stmt``.

        """
        for node in body:
            if isinstance(node, ast.If):
                is_static_only = (
                    FlextInfraUtilitiesRopeSourceBindingCollector.type_checking_test(
                        node.test,
                    )
                )
                if not is_static_only:
                    yield from cls._facade_ordered_statements(node.body)
                yield from cls._facade_ordered_statements(node.orelse)
            else:
                yield node


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverFacadeOwners"]
