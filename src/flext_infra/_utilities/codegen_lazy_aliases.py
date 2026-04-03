"""Single-letter alias resolution for lazy-init generation.

Resolves ``c``, ``m``, ``t``, ``u``, ``p`` etc. aliases by inspecting
canonical facade modules and walking parent package MRO chains.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, t
from flext_infra._utilities.codegen_lazy_scanning import (
    FlextInfraUtilitiesCodegenLazyScanning as _scan,
)
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery


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
        for alias, suffix in c.Infra.ALIAS_TO_SUFFIX.items():
            expected_module = "typings" if suffix == "Types" else suffix.lower()
            if self._existing_alias_is_canonical(
                lazy_map, alias, suffix, expected_module
            ):
                continue
            facade_target = self._find_facade_target(lazy_map, suffix, expected_module)
            if facade_target is not None:
                lazy_map[alias] = facade_target
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
        for name, (mod, _attr) in list(lazy_map.items()):
            basename = mod.rsplit(".", 1)[-1]
            if (
                name.endswith(suffix)
                and mod.count(".") >= 1
                and basename == expected_module
            ):
                return (mod, name)
        return None

    @staticmethod
    def _discover_parent_package(pkg_dir: Path) -> str | None:
        """Discover the parent flext package by inspecting constants.py MRO."""
        result = FlextInfraUtilitiesDiscovery.resolve_parent_constants(
            pkg_dir,
            return_module=True,
        )
        if not result or result == "flext_core":
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
            if (candidate / "pyproject.toml").is_file():
                return candidate
        return None

    @staticmethod
    def _build_package_candidates(base_dir: Path, package_name: str) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        candidates: MutableSequence[Path] = []
        if root_segment in {"tests", "examples", "scripts"}:
            candidates.append(base_dir / package_path)
        candidates.append(base_dir / "src" / package_path)
        if root_segment not in {"tests", "examples", "scripts"}:
            candidates.extend([
                base_dir / "tests" / package_path,
                base_dir / "examples" / package_path,
                base_dir / "scripts" / package_path,
            ])
        return tuple(candidates)

    def _build_workspace_package_candidates(self, package_name: str) -> Sequence[Path]:
        package_path = Path(*package_name.split("."))
        root_segment = package_path.parts[0] if package_path.parts else ""
        patterns: MutableSequence[str] = []
        if root_segment in {"tests", "examples", "scripts"}:
            patterns.append(str(Path("*") / package_path))
        else:
            patterns.append(str(Path("*") / "src" / package_path))
        if root_segment not in {"tests", "examples", "scripts"}:
            patterns.extend([
                str(Path("*") / "tests" / package_path),
                str(Path("*") / "examples" / package_path),
                str(Path("*") / "scripts" / package_path),
            ])
        candidates: MutableSequence[Path] = []
        for pattern in patterns:
            candidates.extend(sorted(self._root.glob(pattern)))
        return tuple(candidates)


__all__ = ["FlextInfraUtilitiesCodegenLazyAliases"]
