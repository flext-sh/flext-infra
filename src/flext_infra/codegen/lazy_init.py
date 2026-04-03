"""Lazy-init ``__init__.py`` generator (PEP 562).

Auto-discovers exports from sibling ``.py`` files and generates clean
lazy-loading ``__init__.py`` files using ``flext_core.lazy``.

Scanning logic lives in ``_utilities_codegen_lazy_scanning``.
Alias resolution lives in ``_utilities_codegen_lazy_aliases``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraCodegenGeneration,
    c,
    r,
    s,
    t,
    u,
)


class FlextInfraCodegenLazyInit(s[int]):
    """Generates ``__init__.py`` with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and generates clean lazy-loading ``__init__.py`` files.
    Processes bottom-up so child packages are generated before parents.
    """

    def __init__(self, workspace_root: Path) -> None:
        """Initialize lazy init generator with workspace root."""
        super().__init__()
        self._root: Path = workspace_root
        self._aliases = u.Infra(workspace_root)
        self._modified_files: t.Infra.StrSet = set()

    @property
    def modified_files(self) -> Sequence[str]:
        """Return generated __init__.py files that changed on disk."""
        return tuple(sorted(self._modified_files))

    @override
    def execute(self) -> r[int]:
        return r[int].ok(self.run(check_only=False))

    def run(self, *, check_only: bool = False) -> int:
        """Process all package directories bottom-up and generate PEP 562 inits."""
        self._modified_files.clear()
        pkg_dirs = self._find_package_dirs()
        total, ok, errors, _dir_exports = self._generate_all_inits(
            pkg_dirs,
            check_only=check_only,
        )
        if not check_only:
            self._fix_import_cycles(pkg_dirs)
        u.info(
            f"Lazy-init summary: {ok} generated, {errors} errors"
            f" ({total} dirs scanned)",
        )
        return errors

    def _generate_all_inits(
        self,
        pkg_dirs: Sequence[Path],
        *,
        check_only: bool,
    ) -> tuple[int, int, int, MutableMapping[str, t.Infra.LazyImportMap]]:
        total = ok = errors = 0
        dir_exports: MutableMapping[str, t.Infra.LazyImportMap] = {}
        for pkg_dir in pkg_dirs:
            total += 1
            result, exports = self._process_directory(
                pkg_dir,
                check_only=check_only,
                dir_exports=dir_exports,
            )
            if exports:
                dir_exports[str(pkg_dir)] = exports
            if result is None:
                continue
            if result < 0:
                errors += 1
            else:
                ok += 1
        return total, ok, errors, dir_exports

    @staticmethod
    def _fix_import_cycles(pkg_dirs: Sequence[Path]) -> None:
        cycle_fixes = 0
        for pkg_dir in pkg_dirs:
            init_file = pkg_dir / c.Infra.Files.INIT_PY
            if not init_file.is_file():
                continue
            modified, changes = u.break_import_cycles(pkg_dir)
            if modified:
                for change in changes:
                    u.info(f"  CYCLE-FIX: {change}")
                cycle_fixes += len(changes)
        if cycle_fixes:
            u.info(f"Cycle-fix: {cycle_fixes} circular imports resolved")

    def _find_package_dirs(self) -> Sequence[Path]:
        pkg_dirs: t.Infra.PathSet = set()
        files_result = u.iter_python_files(workspace_root=self._root)
        if files_result.is_failure:
            return []
        for py_file in files_result.value:
            if any(
                part.startswith(".") or part in {"vendor", "node_modules", ".venv"}
                for part in py_file.parts
            ):
                continue
            parent = py_file.parent
            if u.dir_has_py_files(parent):
                pkg_dirs.add(parent)
        return sorted(pkg_dirs, key=lambda p: len(p.parts), reverse=True)

    def _process_directory(
        self,
        pkg_dir: Path,
        *,
        check_only: bool,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> t.Infra.LazyInitProcessResult:
        init_path = pkg_dir / c.Infra.Files.INIT_PY
        current_pkg = u.discover_package_from_file(init_path)
        if not current_pkg:
            return (None, {})
        docstring = u.read_existing_docstring(init_path)
        if not docstring:
            docstring = u.default_docstring(pkg_dir.name)
        lazy_map = u.build_sibling_export_index(pkg_dir, current_pkg)
        child_packages_for_lazy = u.collect_child_packages(
            pkg_dir,
            current_pkg,
            dir_exports,
        )
        collapse_packages = u.collect_descendant_packages(
            pkg_dir,
            current_pkg,
            dir_exports,
        )
        u.merge_child_exports(pkg_dir, current_pkg, lazy_map, dir_exports)
        child_packages_for_tc = collapse_packages
        inline_constants, version_entries = u.extract_version_exports(
            pkg_dir,
            current_pkg,
        )
        version_runtime_modules: t.Infra.StrSet = {
            module_path for module_path, _attr_name in version_entries.values()
        }
        if not version_runtime_modules and (
            inline_constants and (pkg_dir / "__version__.py").exists()
        ):
            version_runtime_modules.add(
                f"{current_pkg}.{c.Infra.Dunders.VERSION}"
                if current_pkg
                else c.Infra.Dunders.VERSION,
            )
        for export_name, entry in version_entries.items():
            lazy_map.setdefault(export_name, entry)
        if not pkg_dir.name.startswith("_"):
            self._aliases.resolve_aliases(lazy_map, pkg_dir=pkg_dir)
            self._ensure_public_facade_aliases(lazy_map, current_pkg)
        for infra_name in ("cleanup_submodule_namespace", "lazy_getattr"):
            lazy_map.pop(infra_name, None)
        eager_tvars = frozenset(
            u.detect_eager_typevar_names(pkg_dir) & set(lazy_map),
        )
        for k in inline_constants:
            lazy_map.pop(k, None)
        exports = sorted(set(lazy_map) | set(inline_constants) | eager_tvars)
        if not exports:
            return (None, dict(lazy_map))
        if check_only:
            return (0, dict(lazy_map))
        return self._write_init(
            init_path,
            docstring,
            exports,
            lazy_map,
            inline_constants,
            current_pkg,
            eager_tvars,
            wildcard_runtime_imports=tuple(sorted(version_runtime_modules)),
            child_packages_for_lazy=child_packages_for_lazy,
            child_packages_for_tc=child_packages_for_tc,
        )

    def _write_init(
        self,
        init_path: Path,
        docstring: str,
        exports: t.StrSequence,
        lazy_map: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
        eager_imports: t.Infra.LazyImportMap | None = None,
        wildcard_runtime_imports: t.StrSequence | None = None,
        child_packages_for_lazy: t.StrSequence | None = None,
        child_packages_for_tc: t.StrSequence | None = None,
    ) -> t.Infra.LazyInitWriteResult:
        try:
            generated = FlextInfraCodegenGeneration.generate_file(
                docstring,
                exports,
                lazy_map,
                inline_constants,
                current_pkg,
                eager_typevar_names,
                eager_imports,
                wildcard_runtime_imports,
                child_packages_for_lazy=child_packages_for_lazy or [],
                child_packages_for_tc=child_packages_for_tc or [],
            )
            previous = (
                init_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                if init_path.exists()
                else None
            )
            if previous != generated:
                init_path.write_text(generated, encoding=c.Infra.Encoding.DEFAULT)
                self._modified_files.add(str(init_path))
                u.run_ruff_fix(init_path, quiet=True)
        except (OSError, ValueError) as exc:
            u.error(f"generating {init_path}: {exc}")
            return (-1, dict(lazy_map))
        rel_path = (
            init_path.relative_to(self._root)
            if self._root in init_path.parents
            else init_path
        )
        u.info(f"  OK: {rel_path} — {len(exports)} exports")
        return (0, dict(lazy_map))

    @staticmethod
    def _ensure_public_facade_aliases(
        lazy_map: t.Infra.MutableLazyImportMap,
        current_pkg: str,
    ) -> None:
        """Backfill canonical aliases from same-package public facade modules."""
        for alias, suffix in c.Infra.ALIAS_TO_SUFFIX.items():
            if alias in lazy_map:
                continue
            expected_module = "typings" if suffix == "Types" else suffix.lower()
            module_path = (
                f"{current_pkg}.{expected_module}" if current_pkg else expected_module
            )
            candidates = sorted(
                name
                for name, (mod, _attr) in lazy_map.items()
                if mod == module_path and name.endswith(suffix)
            )
            if candidates:
                lazy_map[alias] = (module_path, candidates[0])


__all__ = ["FlextInfraCodegenLazyInit"]
