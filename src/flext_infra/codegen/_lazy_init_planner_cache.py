"""Package/module entry and name-resolution caches for the lazy-init planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInitPlannerCacheMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        _package_exports_cache: MutableMapping[str, frozenset[str]]
        _source_exports_cache: MutableMapping[str, frozenset[str]]
        _source_plan_cache: MutableMapping[str, m.Infra.LazyInitPlan]
        _module_file_by_name: MutableMapping[str, Path]
        _query_receipts: MutableMapping[str, m.Infra.CodegenPhaseAnalysis]

    def _declared_alias_names_for_package(self, package_name: str) -> frozenset[str]:
        """Return the facade letters a package's own modules declare in __all__.

        Only class aliases qualify (``u.Infra.facade_letter_names_source``):
        singleton instances and entry points such as ``cli``, ``infra`` and
        ``main`` belong to their declaring namespace root only.

        Returns:
            The facade letters a package's own modules declare in __all__.

        """
        cache_key = f"declared:{package_name}"
        with u.Infra.cached_source_query(
            self.rope_workspace.rope_project,
            self._source_exports_cache,
            cache_key,
            self._query_receipts,
            f"source:{cache_key}",
        ) as cached:
            if cached:
                return self._source_exports_cache[cache_key]
            return self._declared_alias_query(package_name, cache_key)

    def _declared_alias_query(
        self, package_name: str, cache_key: str
    ) -> frozenset[str]:
        """Read declaration names while the caller owns their cache receipt.

        Returns:
            The declared class aliases for this package.

        """
        # A parent outside the scan scope is read from the one package the
        # active environment declares (R32), so a standalone plan and a
        # workspace plan elect the same owner.
        indexed_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
            package_name,
        )
        package_dir = indexed_dir or self._provider_package_dir(package_name)
        declared: set[str] = set()
        if package_dir is not None:
            project = self.rope_workspace.rope_project
            for module_path in project.source_children(package_dir):
                if module_path.suffix != c.Infra.EXT_PYTHON or not project.source_query(
                    module_path,
                    "isfile",
                ):
                    continue
                # The generated initializer of this run is an output, never a
                # declaration owner. An external package's published
                # initializer IS its own root namespace: the letters it binds
                # directly to a class are that package's declared letters,
                # read by path, never imported.
                if module_path.name == c.Infra.INIT_PY and indexed_dir is not None:
                    continue
                declared.update(
                    u.Infra.facade_letter_names_source(
                        project.source_text(module_path),
                        filename=str(module_path),
                    ),
                )
        names = frozenset(declared)
        self._source_exports_cache[cache_key] = names
        return names

    def _export_names_for_package(self, package_name: str) -> frozenset[str]:
        """Return all export names for a package (init + source plans).

        Returns:
            All export names for a package (init + source plans).

        """
        with u.Infra.cached_source_query(
            self.rope_workspace.rope_project,
            self._package_exports_cache,
            package_name,
            self._query_receipts,
            f"package:{package_name}",
        ) as cached:
            if cached:
                return self._package_exports_cache[package_name]
            exports = frozenset((
                *self._package_init_exports(package_name),
                *self._source_export_names_for_package(package_name),
            ))
            self._package_exports_cache[package_name] = exports
            return exports

    def _package_init_exports(self, package_name: str) -> frozenset[str]:
        """Return names exported from the package __init__.py.

        Returns:
            Names exported from the package __init__.py.

        Raises:
            ValueError: If a facade parent outside the scan scope resolves to a
                module, not a package, in the active environment.

        """
        index = self.rope_workspace.workspace_index
        package_dir = index.package_dir_by_name.get(package_name)
        if package_dir is not None:
            init_path = package_dir / c.Infra.INIT_PY
            if self.rope_workspace.resource(init_path) is None:
                return frozenset()
            source = self.rope_workspace.rope_project.source_text(init_path)
            # A generated __init__ is the parent's published ABI — what an
            # importer sees — in the workspace exactly as when installed, so
            # both scopes elect the same nearest re-exporting parent. A
            # generated __init__ with an unresolved merge is an output this run
            # rebuilds, not an ABI: the package's sources publish for it.
            if source.startswith(c.Infra.AUTOGEN_HEADERS):
                if u.Infra.first_merge_conflict_marker(source) is not None:
                    return frozenset()
                return frozenset(u.Infra.public_export_names_source(source))
            return frozenset(
                self.rope_workspace.exports(
                    init_path,
                    export_options=m.Infra.ExportOptions(allow_assignments=True),
                ),
            )
        # Why: a parent outside the scan scope is read by
        # path from the one package the active environment declares; a name
        # that resolves nowhere raises in the resolver. A module (not a
        # package) can never have been accepted as a facade parent.
        package_dir = self._provider_package_dir(package_name)
        if package_dir is None:
            msg = (
                f"lazy-init facade parent '{package_name}' resolves to a module,"
                " not a package, in the active environment"
            )
            raise ValueError(msg)
        init_path = package_dir / c.Infra.INIT_PY
        if not self.rope_workspace.rope_project.source_query(init_path, "isfile"):
            return frozenset()
        # An external parent's generated __init__ is its published ABI (it is
        # not regenerated by this run), so its export manifest is read as-is.
        source = self.rope_workspace.rope_project.source_text(init_path)
        return frozenset(u.Infra.public_export_names_source(source))

    def _provider_package_dir(self, package_name: str) -> Path | None:
        """Use the native authenticated election for external package providers.

        Returns:
            The provider package directory, or ``None`` when the name does not
            resolve to a package.

        """
        resource = self.rope_workspace.rope_project.find_module(package_name)
        if resource is None or not resource.is_folder():
            return None
        return Path(resource.real_path)

    def _source_export_names_for_package(self, package_name: str) -> frozenset[str]:
        """Read indexed parent declarations from their authoritative siblings.

        Generated initializers are outputs of this plan, not declaration owners.
        Reuse the same source inventory that elects inherited aliases; do not
        recursively build a parent plan or retain its stale generated manifest.

        Returns:
            The resulting ``frozenset[str]``.

        """
        if package_name not in self.rope_workspace.workspace_index.package_dir_by_name:
            return frozenset()
        return self._declared_alias_names_for_package(package_name)

    def _source_package_name(self, pkg_dir: Path, inherited_key: str) -> str:
        """Return the project-root package name for the given directory.

        Returns:
            The project-root package name for the given directory.

        """
        if inherited_key == "src":
            return ""
        package_entry = self._package_entry(pkg_dir)
        if package_entry is None or package_entry.project_root is None:
            return ""
        project_pkg: str = (
            self.rope_workspace.workspace_index.project_package_by_root.get(
                str(package_entry.project_root),
                "",
            )
        )
        return project_pkg

    def _package_entry(self, pkg_dir: Path) -> m.Infra.RopePackageIndexEntry | None:
        """Return the workspace index entry for a package directory.

        Returns:
            The workspace index entry for a package directory.

        """
        return self.rope_workspace.package(pkg_dir)

    def _module_file(self, module_path: str) -> Path | None:
        """Resolve a dotted module path to its source file (lazy index build).

        Returns:
            The resulting ``Path | None``.

        """
        resolved = self._module_file_by_name.get(module_path)
        if resolved is not None:
            return resolved
        if not self._module_file_by_name:
            index = self.rope_workspace.workspace_index
            self._module_file_by_name = {
                entry.module_name: entry.file_path
                for entry in index.modules_by_path.values()
                if entry.module_name
            }
            resolved = self._module_file_by_name.get(module_path)
        return resolved


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerCacheMixin"]
