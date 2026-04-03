"""Import normalization helpers for the transformer layer.

Centralizes the ``Helper`` logic previously nested inside
``FlextInfraTransformerImportNormalizer``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
import re
from collections import deque
from collections.abc import Mapping, MutableMapping
from functools import lru_cache
from pathlib import Path

from flext_core import FlextUtilities, m
from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesYaml,
    c,
    t,
)


class FlextInfraNormalizerContext(m.ArbitraryTypesModel):
    """Analysis context for import normalization."""

    file_path: Path
    file_module: str
    project_package: str
    project_aliases: frozenset[str]
    declared_alias: str
    alias_to_defining_module: t.StrMapping
    alias_tiers: t.IntMapping
    file_tier: int
    package_reachability: t.FrozensetMapping
    wrong_source_enabled: bool
    universal_aliases: frozenset[str]
    workspace_packages: frozenset[str]


class FlextInfraUtilitiesImportNormalizer:
    """Import normalization helpers for alias resolution and tier inference.

    Usage via namespace::

        from flext_infra import u

        config = u.Infra.load_config()
        tiers = u.Infra.alias_tiers()
    """

    @staticmethod
    @lru_cache(maxsize=1)
    def load_config() -> Mapping[str, t.Infra.InfraValue]:
        """Load import normalization configuration from YAML."""
        rules_path = (
            Path(__file__).resolve().parent.parent
            / "rules"
            / "import-normalization.yml"
        )
        loaded = FlextInfraUtilitiesYaml.safe_load_yaml(rules_path)
        root = loaded.get("import_normalization")
        if FlextUtilities.is_mapping(root):
            normalized: Mapping[str, t.Infra.InfraValue] = dict(root)
            return normalized
        return {}

    @staticmethod
    @lru_cache(maxsize=1)
    def alias_tiers() -> t.IntMapping:
        """Return configured alias-to-tier mapping."""
        config = FlextInfraUtilitiesImportNormalizer.load_config().get(
            "alias_tiers",
        )
        if not isinstance(config, Mapping):
            return {}
        tiers: t.MutableIntMapping = {}
        for alias_name, tier_value in config.items():
            if len(alias_name) != 1 or not alias_name.islower():
                continue
            if isinstance(tier_value, int):
                tiers[alias_name] = tier_value
        return tiers

    @staticmethod
    @lru_cache(maxsize=1)
    def wrong_source_config() -> t.Infra.Pair[bool, frozenset[str]]:
        """Return wrong-source detection flag and universal aliases."""
        config = FlextInfraUtilitiesImportNormalizer.load_config().get(
            "wrong_source",
        )
        if not isinstance(config, Mapping):
            return False, frozenset()
        enabled_raw = config.get("enabled")
        enabled = isinstance(enabled_raw, bool) and enabled_raw
        universal_raw = config.get("universal_aliases")
        universal_aliases: t.Infra.StrSet = set()
        if isinstance(universal_raw, list):
            for item in universal_raw:
                if isinstance(item, str) and len(item) == 1 and item.islower():
                    universal_aliases.add(item)
        return enabled, frozenset(universal_aliases)

    @staticmethod
    def build_alias_to_defining_module(
        *,
        package_name: str,
        package_dir: Path,
        project_root: Path | None,
        alias_map: Mapping[str, t.Infra.VariadicTuple[str]] | None,
    ) -> t.StrMapping:
        """Build alias-to-module map from project facades and lazy exports."""
        init_path = package_dir / c.Infra.Files.INIT_PY
        alias_to_module = dict(
            FlextInfraUtilitiesDiscovery.extract_lazy_import_map(init_path),
        )
        if project_root is not None:
            alias_to_facade = FlextInfraUtilitiesDiscovery.discover_project_aliases(
                project_root,
            )
            for alias_name, facade_file in alias_to_facade.items():
                if alias_name in alias_to_module:
                    continue
                facade_module = f"{package_name}.{Path(facade_file).stem}"
                alias_to_module[alias_name] = facade_module
        if alias_map is not None:
            legacy_aliases = alias_map.get(package_name, ())
            for alias_name in legacy_aliases:
                if alias_name in alias_to_module:
                    continue
                guessed_module = f"{package_name}.{alias_name}"
                alias_to_module[alias_name] = guessed_module
        return alias_to_module

    @staticmethod
    @lru_cache(maxsize=128)
    def build_reachability(
        package_dir: Path,
        package_name: str,
    ) -> t.FrozensetMapping:
        """Build module reachability map from import graph traversal."""
        graph = FlextInfraUtilitiesImportNormalizer.build_import_graph(
            package_dir=package_dir,
            package_name=package_name,
        )
        reachability: t.MutableFrozensetMapping = {}
        for module_name in graph:
            visited: t.Infra.StrSet = set()
            queue: deque[str] = deque(graph.get(module_name, frozenset()))
            while queue:
                imported_module = queue.popleft()
                if imported_module in visited:
                    continue
                visited.add(imported_module)
                queue.extend(graph.get(imported_module, frozenset()))
            reachability[module_name] = frozenset(visited)
        return reachability

    @staticmethod
    def file_to_module(
        *,
        file_path: Path,
        package_dir: Path,
        package_name: str,
    ) -> str:
        """Convert a file path to its absolute Python module path."""
        relative = file_path.resolve().relative_to(package_dir.parent.resolve())
        module_parts = list(relative.with_suffix("").parts)
        if module_parts[-1] == c.Infra.Dunders.INIT:
            module_parts = module_parts[:-1]
        if not module_parts or module_parts[0] != package_name:
            msg = f"{file_path} is outside package {package_name}"
            raise ValueError(msg)
        return ".".join(module_parts)

    _FROM_IMPORT_RE: re.Pattern[str] = re.compile(
        r"^from\s+([\w.]+)\s+import\s",
        re.MULTILINE,
    )
    _PLAIN_IMPORT_RE: re.Pattern[str] = re.compile(
        r"^import\s+([\w., ]+)",
        re.MULTILINE,
    )

    @staticmethod
    def _collect_intra_package_imports(
        source: str,
        package_name: str,
    ) -> t.Infra.StrSet:
        """Extract intra-package import names from source text."""
        imports: t.Infra.StrSet = set()
        prefix = f"{package_name}."
        cls = FlextInfraUtilitiesImportNormalizer
        for match in cls._FROM_IMPORT_RE.finditer(source):
            module = match.group(1)
            if module.startswith(prefix) or module == package_name:
                imports.add(module)
        for match in cls._PLAIN_IMPORT_RE.finditer(source):
            names_str = match.group(1)
            for name_part in names_str.split(","):
                name = name_part.strip().split(" as ")[0].strip()
                if name.startswith(prefix) or name == package_name:
                    imports.add(name)
        return imports

    @staticmethod
    def build_import_graph(
        *,
        package_dir: Path,
        package_name: str,
    ) -> t.FrozensetMapping:
        """Build direct intra-package import graph from source files."""
        graph: MutableMapping[str, t.Infra.StrSet] = {}
        for py_file in package_dir.rglob(c.Infra.Extensions.PYTHON_GLOB):
            try:
                source = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            try:
                module_name = FlextInfraUtilitiesImportNormalizer.file_to_module(
                    file_path=py_file,
                    package_dir=package_dir,
                    package_name=package_name,
                )
            except ValueError:
                continue
            graph[module_name] = (
                FlextInfraUtilitiesImportNormalizer._collect_intra_package_imports(
                    source,
                    package_name,
                )
            )
        return {name: frozenset(imports) for name, imports in graph.items()}

    @staticmethod
    def _tier_from_directory(
        first_dir: str,
        facade_to_alias: t.StrMapping,
        alias_tiers: t.IntMapping,
    ) -> int:
        """Resolve tier from the first subdirectory name under the package."""
        if not first_dir.startswith("_"):
            return c.Infra.Tier.DEFAULT_SUBDIR
        normalized = first_dir.lstrip("_")
        if normalized == "services":
            normalized = "service"
        alias = facade_to_alias.get(f"{normalized}.py", "")
        if alias in alias_tiers:
            return alias_tiers[alias]
        if normalized == "result" and "r" in alias_tiers:
            return alias_tiers["r"]
        return c.Infra.Tier.DEFAULT_SUBDIR

    @staticmethod
    def file_tier(
        *,
        file_path: Path,
        project_package: str,
        facade_to_alias: t.StrMapping,
        alias_tiers: t.IntMapping,
    ) -> int:
        """Infer architectural tier for a file based on facade/paths."""
        declared_alias = facade_to_alias.get(file_path.name, "")
        if declared_alias in alias_tiers:
            return alias_tiers[declared_alias]
        if not project_package:
            return c.Infra.Tier.UNKNOWN
        marker = f"/src/{project_package}/"
        file_str = str(file_path.resolve())
        if marker not in file_str:
            return c.Infra.Tier.UNKNOWN
        relative = file_str.split(marker, maxsplit=1)[1]
        parts = Path(relative).parts[:-1]
        if not parts:
            return c.Infra.Tier.UNKNOWN
        return FlextInfraUtilitiesImportNormalizer._tier_from_directory(
            parts[0],
            facade_to_alias,
            alias_tiers,
        )

    @staticmethod
    def _resolve_package_dir(
        package_name: str,
        project_root: Path | None,
    ) -> Path | None:
        """Locate the on-disk package directory for a given package name."""
        if project_root is not None:
            candidate = project_root / c.Infra.Paths.DEFAULT_SRC_DIR / package_name
            if candidate.is_dir() and (candidate / c.Infra.Files.INIT_PY).is_file():
                return candidate
        if package_name:
            spec = importlib.util.find_spec(package_name)
            if spec and spec.submodule_search_locations:
                locs = list(spec.submodule_search_locations)
                if locs:
                    cand = Path(locs[0])
                    if cand.is_dir() and (cand / c.Infra.Files.INIT_PY).is_file():
                        return cand
        return None

    @staticmethod
    def _resolve_file_module(
        file_path: Path,
        package_dir: Path | None,
        package_name: str,
    ) -> str:
        """Resolve the dotted module path for *file_path*, or empty string."""
        if package_dir is None or not package_name:
            return ""
        try:
            return FlextInfraUtilitiesImportNormalizer.file_to_module(
                file_path=file_path,
                package_dir=package_dir,
                package_name=package_name,
            )
        except ValueError:
            return ""


__all__ = ["FlextInfraNormalizerContext", "FlextInfraUtilitiesImportNormalizer"]
