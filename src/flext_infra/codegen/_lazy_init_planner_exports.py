"""Per-package and per-module export resolution for the lazy-init planner.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, t, u


class FlextInfraCodegenLazyInitPlannerExportsMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        lazy_init: m.Infra.LazyInitConfig
        _module_exports_cache: dict[
            tuple[str, bool, bool, bool, bool, bool], t.LazyAliasMap
        ]
        _version_module_name: str

        def _package_entry(
            self, pkg_dir: Path
        ) -> m.Infra.RopePackageIndexEntry | None: ...

        def _add(
            self, index: t.MutableLazyAliasMap, name: str, target: t.StrPair
        ) -> None: ...

        def _is_registered_import(
            self, project_root: Path | None, module_name: str
        ) -> bool: ...

        @staticmethod
        def _publish(name: str, *, allow_main: bool) -> bool: ...

    def _package_exports(
        self, context: m.Infra.LazyInitPackageContext
    ) -> t.MutableLazyAliasMap:
        """Return the lazy export map for a package (excluding child packages)."""
        package_entry = self._package_entry(context.pkg_dir)
        if package_entry is None:
            return {}
        index: t.MutableLazyAliasMap = {}
        # mro-i6nq.10: Generated support modules are output, never public input.
        skip_names = {
            c.Infra.INIT_PY,
            "__main__.py",
            self._version_module_name,
            *c.Infra.OBSOLETE_GENERATED_INIT_FILES,
        }
        for module_entry in package_entry.modules:
            py_file = module_entry.file_path
            child_dir = py_file.parent / py_file.stem
            child_entry = self._package_entry(child_dir)
            # NOTE (multi-agent, mro-wkii.17.26.2): the validated namespace
            # convention below owns pytest exclusion; this early guard handles
            # only generated artifacts and modules shadowed by packages.
            is_generated_support = (
                py_file.name in skip_names
                or c.Infra.GENERATED_EXPORT_SIDECAR_RE.match(py_file.name) is not None
                or py_file.stem in c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES
            )
            shadowed_by_package = child_entry is not None and bool(
                child_entry.package_name
            )
            if is_generated_support or shadowed_by_package:
                continue
            if self._is_registered_import(
                module_entry.project_root, module_entry.module_name
            ):
                continue
            convention = self.rope_workspace.convention(
                py_file, rel_path=py_file.relative_to(context.pkg_dir)
            )
            policy = convention.module_policy
            if not policy.include_in_lazy_init or not module_entry.module_name:
                continue
            # mro-wkii.17.26 (codex): the declarative namespace policy owns
            # package ABI; do not rediscover symbols it classified as private.
            if not policy.export_symbols:
                continue
            require_explicit_all = (
                u.Infra.matches_root_namespace_file(py_file.name)
                and policy.expected_alias is not None
                and u.Infra.matches_project_namespace_package(context.current_pkg)
                and not context.pkg_dir.name.startswith("_")
            )
            targets = self._module_exports(
                py_file,
                convention.module_name,
                export_options=m.Infra.ExportOptions(
                    allow_main=policy.allow_main_export,
                    allow_assignments=(
                        policy.allow_type_alias or policy.expected_alias is not None
                    ),
                    allow_functions=policy.is_fixture_module,
                    require_explicit_all=require_explicit_all,
                ),
            )
            if require_explicit_all and not targets:
                msg = (
                    "governed root facade missing explicit exports "
                    f"(expected __all__ in {py_file})"
                )
                raise ValueError(msg)
            if (
                policy.expected_alias
                and targets
                and u.Infra.matches_project_namespace_package(context.current_pkg)
                and u.Infra.matches_root_namespace_file(py_file.name)
            ):
                targets.setdefault(
                    policy.expected_alias,
                    (module_entry.module_name, policy.expected_alias),
                )
            for name, target in targets.items():
                self._add(index, name, target)
        return index

    def _module_exports(
        self,
        py_file: Path,
        module_path: str,
        *,
        export_options: m.Infra.ExportOptions | None = None,
    ) -> t.MutableLazyAliasMap:
        """Return the lazy export map for one Python module (cache-backed)."""
        resolved_export_options = export_options or m.Infra.ExportOptions()
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
            return {}
        names = self.rope_workspace.exports(
            py_file,
            export_options=resolved_export_options.model_copy(
                update={
                    "require_explicit_all": (
                        resolved_export_options.require_explicit_all
                        and not resolved_export_options.include_dunder
                    )
                }
            ),
        )
        exports = {
            name: (module_path, name)
            for name in names
            if resolved_export_options.include_dunder
            or self._publish(name, allow_main=resolved_export_options.allow_main)
        }
        self._module_exports_cache[cache_key] = exports
        return dict(exports)
