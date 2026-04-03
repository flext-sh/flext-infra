"""Single-letter alias resolution for lazy-init generation.

Resolves ``c``, ``m``, ``t``, ``u``, ``p`` etc. aliases by inspecting
canonical facade modules and walking parent package MRO chains.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesCodegenLazyScanning as _scan,
    FlextInfraUtilitiesDiscovery,
    c,
    t,
)

_CORE_RUNTIME_ALIAS_TARGETS: dict[str, t.Infra.StrPair] = {
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


class FlextInfraUtilitiesCodegenLazyAliases:
    """Resolves single-letter aliases from ALIAS_TO_SUFFIX mapping."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._root = (
            workspace_root
            if workspace_root is not None
            else FlextInfraUtilitiesDiscovery.discover_workspace_root_from_file(
                Path(__file__)
            )
        )
        self._alias_target_cache: MutableMapping[
            tuple[str, str],
            t.Infra.StrPair | None,
        ] = {}
        self._package_dir_cache: MutableMapping[
            tuple[str, str],
            Path | None,
        ] = {}

    def resolve_aliases(
        self,
        lazy_map: t.Infra.MutableLazyImportMap,
        *,
        pkg_dir: Path,
    ) -> None:
        """Resolve single-letter aliases from ALIAS_TO_SUFFIX mapping."""
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            pkg_dir / c.Infra.Files.INIT_PY
        )
        for alias, suffix in c.Infra.ALIAS_TO_SUFFIX.items():
            expected_module = "typings" if suffix == "Types" else suffix.lower()
            if self._existing_alias_is_canonical(
                lazy_map, alias, suffix, expected_module
            ):
                continue
            if (
                current_pkg == c.Infra.Packages.CORE_UNDERSCORE
                and alias in _CORE_RUNTIME_ALIAS_TARGETS
            ):
                lazy_map[alias] = _CORE_RUNTIME_ALIAS_TARGETS[alias]
                continue
            if alias == "s":
                service_target = self._find_service_target(lazy_map)
                if service_target is not None:
                    lazy_map[alias] = service_target
                    continue
            facade_target = self._find_facade_target(lazy_map, suffix, expected_module)
            if facade_target is not None:
                lazy_map[alias] = facade_target
                continue
            if alias in _CORE_RUNTIME_ALIAS_TARGETS:
                lazy_map[alias] = _CORE_RUNTIME_ALIAS_TARGETS[alias]
                continue
            if alias in lazy_map:
                continue
            parent_target = self._resolve_export_target(
                pkg_dir,
                alias,
                suffix,
                expected_module,
                seen=frozenset(),
            )
            if parent_target is not None:
                lazy_map[alias] = parent_target

    @staticmethod
    def _existing_alias_is_canonical(
        lazy_map: t.Infra.MutableLazyImportMap,
        alias: str,
        suffix: str,
        expected_module: str,
    ) -> bool:
        if alias not in lazy_map:
            return False
        existing = lazy_map[alias]
        existing_basename = existing[0].rsplit(".", 1)[-1]
        return (
            existing[1].endswith(suffix)
            and existing[0].count(".") >= 1
            and existing_basename == expected_module
        )

    @staticmethod
    def _find_facade_target(
        lazy_map: t.Infra.MutableLazyImportMap,
        suffix: str,
        expected_module: str,
    ) -> t.Infra.StrPair | None:
        candidates: MutableSequence[tuple[int, int, str, str]] = []
        for name, (mod, _attr) in list(lazy_map.items()):
            basename = mod.rsplit(".", 1)[-1]
            if (
                name.endswith(suffix)
                and mod.count(".") >= 1
                and basename == expected_module
            ):
                candidates.append((mod.count("."), mod.count("._"), mod, name))
        if not candidates:
            return None
        _depth, _private_count, module_path, export_name = min(candidates)
        return (module_path, export_name)

    @staticmethod
    def _find_service_target(
        lazy_map: t.Infra.MutableLazyImportMap,
    ) -> t.Infra.StrPair | None:
        """Resolve the canonical `s` alias from local public service/base modules."""
        for module_name, suffixes in (
            ("base", ("ServiceBase",)),
            ("service", ("Service",)),
            ("api", ("Service",)),
        ):
            for name, (mod, _attr) in list(lazy_map.items()):
                if mod.rsplit(".", 1)[-1] != module_name:
                    continue
                if any(name.endswith(suffix) for suffix in suffixes):
                    return (mod, name)
        return None

    @staticmethod
    def _discover_parent_package(pkg_dir: Path) -> str | None:
        """Discover the parent flext package by inspecting constants.py MRO."""
        result = FlextInfraUtilitiesDiscovery.resolve_parent_constants(
            pkg_dir,
            return_module=True,
        )
        if not result or result == c.Infra.Packages.CORE_UNDERSCORE:
            return result or None
        return result.split(".")[0]

    def _resolve_export_target(
        self,
        pkg_dir: Path,
        alias: str,
        suffix: str,
        expected_module: str,
        *,
        seen: frozenset[str],
    ) -> t.Infra.StrPair | None:
        cache_key = (str(pkg_dir), alias)
        if cache_key in self._alias_target_cache:
            return self._alias_target_cache[cache_key]
        pkg_key = str(pkg_dir.resolve())
        if pkg_key in seen:
            return None
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            pkg_dir / c.Infra.Files.INIT_PY
        )
        if not current_pkg:
            self._alias_target_cache[cache_key] = None
            return None
        local_exports = _scan.build_sibling_export_index(pkg_dir, current_pkg)
        target: t.Infra.StrPair | None = None
        if self._existing_alias_is_canonical(
            local_exports, alias, suffix, expected_module
        ):
            target = local_exports[alias]
        else:
            target = self._find_facade_target(local_exports, suffix, expected_module)
        if target is None:
            parent_pkg = self._discover_parent_package(pkg_dir)
            if parent_pkg:
                parent_dir = self._find_package_directory(pkg_dir, parent_pkg)
                if parent_dir is not None:
                    target = self._resolve_export_target(
                        parent_dir,
                        alias,
                        suffix,
                        expected_module,
                        seen=seen | {pkg_key},
                    )
        self._alias_target_cache[cache_key] = target
        return target

    def _find_package_directory(self, pkg_dir: Path, package_name: str) -> Path | None:
        project_root = self._discover_project_root(pkg_dir)
        cache_key = (str(project_root) if project_root else "", package_name)
        if cache_key in self._package_dir_cache:
            return self._package_dir_cache[cache_key]
        candidates: MutableSequence[Path] = []
        if project_root is not None:
            candidates.extend(
                self._build_package_candidates(project_root, package_name)
            )
        candidates.extend(self._build_package_candidates(self._root, package_name))
        candidates.extend(self._build_workspace_package_candidates(package_name))
        resolved: Path | None = None
        seen_candidates: MutableSequence[Path] = []
        for candidate in candidates:
            candidate_resolved = candidate.resolve()
            if candidate_resolved in seen_candidates:
                continue
            seen_candidates.append(candidate_resolved)
            if candidate.is_dir():
                resolved = candidate
                break
        self._package_dir_cache[cache_key] = resolved
        return resolved

    @staticmethod
    def _discover_project_root(pkg_dir: Path) -> Path | None:
        for candidate in (pkg_dir, *pkg_dir.parents):
            if (candidate / c.Infra.Files.PYPROJECT_FILENAME).is_file():
                return candidate
        return None

    @staticmethod
    def _build_package_candidates(base_dir: Path, package_name: str) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        candidates: MutableSequence[Path] = []
        if root_segment in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            candidates.append(base_dir / package_path)
        candidates.append(base_dir / c.Infra.Paths.DEFAULT_SRC_DIR / package_path)
        if root_segment not in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            candidates.extend([
                base_dir / c.Infra.Directories.TESTS / package_path,
                base_dir / c.Infra.Directories.EXAMPLES / package_path,
                base_dir / c.Infra.Directories.SCRIPTS / package_path,
            ])
        return tuple(candidates)

    def _build_workspace_package_candidates(self, package_name: str) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        patterns: MutableSequence[str] = []
        if root_segment in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            patterns.append(str(Path("*") / package_path))
        else:
            patterns.append(
                str(Path("*") / c.Infra.Paths.DEFAULT_SRC_DIR / package_path)
            )
        if root_segment not in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }:
            patterns.extend([
                str(Path("*") / c.Infra.Directories.TESTS / package_path),
                str(Path("*") / c.Infra.Directories.EXAMPLES / package_path),
                str(Path("*") / c.Infra.Directories.SCRIPTS / package_path),
            ])
        candidates: MutableSequence[Path] = []
        for pattern in patterns:
            candidates.extend(sorted(self._root.glob(pattern)))
        return tuple(candidates)


__all__ = ["FlextInfraUtilitiesCodegenLazyAliases"]
