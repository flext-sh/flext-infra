"""Import-law facts: namespaces, layers, lazy exports and facade routes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Literal

from flext_infra import c, config, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeAnalysis,
)


class FlextInfraUtilitiesImportLaw:
    """Single owner of the import-law facts the enforcement routes read."""

    @classmethod
    def import_namespace(
        cls,
        project_root: Path,
        file_path: Path,
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
        if not (namespace_dir / c.Infra.INIT_PY).is_file():
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
        stems = tuple(part.lstrip("_") for part in module.split(".")[1:])
        if any(
            stem.startswith(tuple(c.Infra.IMPORT_LAW_ROOT_SINGLETONS)) for stem in stems
        ):
            return "layer0"
        families = FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        if any(family.module in stems for family in families):
            return "family"
        return "consumer"

    @staticmethod
    def import_direct_module(namespace_dir: Path, file_path: Path) -> bool:
        """Return whether one module keeps direct leaf imports.

        A settings/config module (any path segment starting with ``settings``
        or ``config``, with or without leading underscores) and a family
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
    @cache
    def import_lazy_exports(
        project_root: Path,
        package: str,
    ) -> t.StrMapping | None:
        """Map each name one owned package ``__init__`` publishes to its module.

        The package resolves under ``src/`` or the project root (internal
        tiers). Relative targets resolve against the package; a target naming
        another distribution (``flext_cli``) stays absolute. The parse is
        memoized per ``(project_root, package)``: one governed-file scan
        resolves the same root exports once per namespace, never once per
        module.

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
            (base for base in bases if (base / top / c.Infra.INIT_PY).is_file()),
            None,
        )
        if owner is None:
            return None
        init = owner.joinpath(top, *rest, c.Infra.INIT_PY)
        if not init.is_file():
            return None
        targets, references = (
            FlextInfraUtilitiesRopeAnalysis.lazy_import_mapping_source(
                init.read_text(encoding=c.DEFAULT_ENCODING),
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
    def import_package_dir(project_root: Path, package: str) -> Path | None:
        """Return the directory of one dotted package the project owns.

        Returns:
            The package directory, or ``None`` for a module, a missing path or
            a package of another project.

        """
        top, *rest = package.split(".")
        for base in (project_root / c.Infra.DEFAULT_SRC_DIR, project_root):
            if not (base / top / c.Infra.INIT_PY).is_file():
                continue
            candidate = base.joinpath(top, *rest)
            return candidate if (candidate / c.Infra.INIT_PY).is_file() else None
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
