"""Per-package and per-module export resolution for the lazy-init planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_infra import c, m, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraCodegenLazyInitPlannerExportsMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        lazy_init: m.Infra.LazyInitConfig
        _module_exports_cache: MutableMapping[
            tuple[str, bool, bool, bool, bool, bool],
            t.LazyAliasMap,
        ]

        def _package_entry(
            self,
            pkg_dir: Path,
        ) -> m.Infra.RopePackageIndexEntry | None: ...

        def _add(
            self,
            index: t.MutableLazyAliasMap,
            name: str,
            target: t.StrPair,
        ) -> None: ...

    def _package_exports(
        self,
        context: m.Infra.LazyInitPackageContext,
    ) -> t.MutableLazyAliasMap:
        """Return the lazy export map for a package (excluding child packages).

        Returns:
            The lazy export map for a package (excluding child packages).

        Raises:
            ValueError: If unindexed publication source; or if declared publication
                module is shadowed by a package.

        """
        package_entry = self._package_entry(context.pkg_dir)
        module_entries = self._enumerated_module_entries(context, package_entry)
        u.Cli.info(
            f"lazy-init: export inventory package={context.current_pkg} "
            f"modules={len(module_entries)}"
        )
        index: t.MutableLazyAliasMap = {}
        for py_file, module_name in module_entries:
            if self._skipped_export_module(context, py_file):
                continue
            entry = self.rope_workspace.module(py_file)
            if entry is None:
                msg = f"unindexed publication source: {py_file}"
                raise ValueError(msg)
            targets = self._module_exports(
                py_file,
                entry.module_name,
                export_options=m.Infra.ExportOptions(
                    allow_main=True,
                    allow_assignments=True,
                    allow_functions=True,
                    require_explicit_all=True,
                ),
            )
            child_entry = self._package_entry(py_file.parent / py_file.stem)
            if targets and child_entry is not None and child_entry.package_name:
                msg = (
                    "declared publication module is shadowed by a package: "
                    f"{module_name}"
                )
                raise ValueError(msg)
            for name, target in targets.items():
                self._add(index, name, target)
        return index

    def _enumerated_module_entries(
        self,
        context: m.Infra.LazyInitPackageContext,
        package_entry: m.Infra.RopePackageIndexEntry | None,
    ) -> t.MutableSequenceOf[t.Pair[Path, str]]:
        """Enumerate a package's modules from the rope index or the filesystem.

        Operator init law (2026-09-16): every package with public children —
        underscore internals included — carries a light lazy-init export
        surface. When the rope index does not track the package, enumerate
        direct children from the filesystem instead of rendering an empty
        init; emptiness here is a defect, never canonical. The rope index
        exposes modules in its own scan order, which follows the filesystem's
        directory-entry order and therefore differs between machines. Sorting
        the entries makes the rendered lazy map — whose insertion order the
        generated ``__init__`` preserves — byte-identical for the same sources
        on every host.

        Returns:
            The resulting sorted module entries.

        """
        module_entries: t.MutableSequenceOf[t.Pair[Path, str]] = (
            sorted(
                (
                    (entry.file_path, entry.module_name)
                    for entry in package_entry.modules
                ),
                key=operator.itemgetter(0, 1),
            )
            if package_entry is not None
            else []
        )
        if not module_entries:
            module_entries = [
                (
                    child,
                    f"{context.current_pkg}.{child.stem}"
                    if context.current_pkg
                    else child.stem,
                )
                for child in self.rope_workspace.rope_project.source_children(
                    context.pkg_dir,
                )
                if child.suffix == c.Infra.EXT_PYTHON
                and self.rope_workspace.rope_project.source_query(child, "isfile")
                if child.name != c.Infra.INIT_PY
            ]
        return module_entries

    @staticmethod
    def _skipped_export_module(
        context: m.Infra.LazyInitPackageContext,
        py_file: Path,
    ) -> bool:
        """Whether a module never enters its package's lazy export map.

        Each directory publishes its direct modules' declarations. Its own
        initializer propagates those declarations and is never an input.

        Returns:
            The resulting ``bool``.

        """
        return py_file.parent != context.pkg_dir or py_file.name == c.Infra.INIT_PY

    def _module_exports(
        self,
        py_file: Path,
        module_path: str,
        *,
        export_options: m.Infra.ExportOptions | None = None,
    ) -> t.MutableLazyAliasMap:
        """Return the lazy export map for one Python module (cache-backed).

        Returns:
            The lazy export map for one Python module (cache-backed).

        Raises:
            ValueError: If unindexed publication resource.

        """
        resolved_export_options = export_options or m.Infra.ExportOptions(
            require_explicit_all=True,
        )
        cache_key = (
            str(py_file.resolve()),
            resolved_export_options.include_dunder,
            resolved_export_options.allow_main,
            resolved_export_options.allow_assignments,
            resolved_export_options.allow_functions,
            resolved_export_options.require_explicit_all,
        )
        cached = self._module_exports_cache.get(cache_key)
        if cached is not None:
            return dict(cached)
        if self.rope_workspace.resource(py_file) is None:
            msg = f"unindexed publication resource: {py_file}"
            raise ValueError(msg)
        names = self.rope_workspace.exports(
            py_file,
            export_options=resolved_export_options,
        )
        if not names:
            u.Cli.info(f"lazy-init: empty module exports module={module_path}")
        exports = {name: (module_path, name) for name in names}
        policy = u.Infra.publication_policy(
            py_file,
            rope_project=self.rope_workspace.rope_project,
            current_pkg=module_path.rpartition(".")[0],
        )
        alias = policy.expected_alias
        if alias is not None:
            resource = self.rope_workspace.resource(py_file)
            if resource is None:
                msg = f"unindexed publication resource: {py_file}"
                raise ValueError(msg)
            module = u.Infra.resolve_pymodule(
                self.rope_workspace.rope_project, resource
            ).get_module()
            tree = ast.parse(module.source_code)
            body = u.Infra.export_declaration_body(tree)
            if body is not tree.body:
                owner = next(
                    node for node in tree.body if isinstance(node, ast.ClassDef)
                )
                if owner.name in exports or alias in exports:
                    # Class-owned facades publish the root; layout owns its alias.
                    exports[alias] = (
                        module_path,
                        alias
                        if alias in exports and alias in module.get_attributes()
                        else owner.name,
                    )
        self._module_exports_cache[cache_key] = exports
        return dict(exports)


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerExportsMixin"]
