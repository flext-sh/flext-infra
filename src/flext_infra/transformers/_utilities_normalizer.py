"""Import normalization helpers for the transformer layer.

Centralizes the ``Helper`` logic previously nested inside
``FlextInfraTransformerImportNormalizer``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import deque
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

from flext_infra import FlextInfraUtilitiesDiscovery, FlextInfraUtilitiesYaml, t

_UNKNOWN_TIER = 99


class FlextInfraUtilitiesImportNormalizer:
    """Import normalization helpers for alias resolution and tier inference.

    Usage via namespace::

        from flext_infra import u

        config = u.Infra.normalizer_load_config()
        tiers = u.Infra.normalizer_alias_tiers()
    """

    @staticmethod
    @lru_cache(maxsize=1)
    def normalizer_load_config() -> Mapping[str, t.Infra.InfraValue]:
        """Load import normalization configuration from YAML."""
        rules_path = (
            Path(__file__).resolve().parent.parent
            / "rules"
            / "import-normalization.yml"
        )
        loaded = FlextInfraUtilitiesYaml.safe_load_yaml(rules_path)
        root = loaded.get("import_normalization")
        if isinstance(root, Mapping):
            normalized: dict[str, t.Infra.InfraValue] = dict(root.items())
            return normalized
        return {}

    @staticmethod
    @lru_cache(maxsize=1)
    def normalizer_alias_tiers() -> Mapping[str, int]:
        """Return configured alias-to-tier mapping."""
        config = FlextInfraUtilitiesImportNormalizer.normalizer_load_config().get(
            "alias_tiers",
        )
        if not isinstance(config, Mapping):
            return {}
        tiers: dict[str, int] = {}
        for alias_name, tier_value in config.items():
            if len(alias_name) != 1 or not alias_name.islower():
                continue
            if isinstance(tier_value, int):
                tiers[alias_name] = tier_value
        return tiers

    @staticmethod
    @lru_cache(maxsize=1)
    def normalizer_facade_filenames() -> tuple[str, ...]:
        """Return facade file names configured for normalization."""
        config = FlextInfraUtilitiesImportNormalizer.normalizer_load_config().get(
            "facade_filenames",
        )
        if not isinstance(config, list):
            return ()
        output: list[str] = [
            item for item in config if isinstance(item, str) and item.endswith(".py")
        ]
        return tuple(output)

    @staticmethod
    @lru_cache(maxsize=1)
    def normalizer_wrong_source_config() -> tuple[bool, frozenset[str]]:
        """Return wrong-source detection flag and universal aliases."""
        config = FlextInfraUtilitiesImportNormalizer.normalizer_load_config().get(
            "wrong_source",
        )
        if not isinstance(config, Mapping):
            return False, frozenset()
        enabled_raw = config.get("enabled")
        enabled = isinstance(enabled_raw, bool) and enabled_raw
        universal_raw = config.get("universal_aliases")
        universal_aliases: set[str] = set()
        if isinstance(universal_raw, list):
            for item in universal_raw:
                if isinstance(item, str) and len(item) == 1 and item.islower():
                    universal_aliases.add(item)
        return enabled, frozenset(universal_aliases)

    @staticmethod
    def normalizer_build_alias_to_defining_module(
        *,
        package_name: str,
        package_dir: Path,
        project_root: Path | None,
        alias_map: dict[str, tuple[str, ...]] | None,
    ) -> dict[str, str]:
        """Build alias-to-module map from project facades and lazy exports."""
        init_path = package_dir / "__init__.py"
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
    def normalizer_build_reachability(
        package_dir: Path,
        package_name: str,
    ) -> dict[str, frozenset[str]]:
        """Build module reachability map from import graph traversal."""
        graph = FlextInfraUtilitiesImportNormalizer.normalizer_build_import_graph(
            package_dir=package_dir,
            package_name=package_name,
        )
        reachability: dict[str, frozenset[str]] = {}
        for module_name in graph:
            visited: set[str] = set()
            queue: deque[str] = deque(graph.get(module_name, frozenset()))
            while len(queue) > 0:
                imported_module = queue.popleft()
                if imported_module in visited:
                    continue
                visited.add(imported_module)
                queue.extend(graph.get(imported_module, frozenset()))
            reachability[module_name] = frozenset(visited)
        return reachability

    @staticmethod
    def normalizer_file_to_module(
        *, file_path: Path, package_dir: Path, package_name: str
    ) -> str:
        """Convert a file path to its absolute Python module path."""
        relative = file_path.resolve().relative_to(package_dir.parent.resolve())
        module_parts = list(relative.with_suffix("").parts)
        if module_parts[-1] == "__init__":
            module_parts = module_parts[:-1]
        if not module_parts or module_parts[0] != package_name:
            msg = f"{file_path} is outside package {package_name}"
            raise ValueError(msg)
        return ".".join(module_parts)

    @staticmethod
    def normalizer_build_import_graph(
        *,
        package_dir: Path,
        package_name: str,
    ) -> dict[str, frozenset[str]]:
        """Build direct intra-package import graph from source files."""
        graph: dict[str, set[str]] = {}
        for py_file in package_dir.rglob("*.py"):
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            try:
                module_name = (
                    FlextInfraUtilitiesImportNormalizer.normalizer_file_to_module(
                        file_path=py_file,
                        package_dir=package_dir,
                        package_name=package_name,
                    )
                )
            except ValueError:
                continue
            imports: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith(f"{package_name}."):
                        imports.add(node.module)
                    elif node.module == package_name:
                        imports.add(package_name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(f"{package_name}."):
                            imports.add(alias.name)
                        elif alias.name == package_name:
                            imports.add(package_name)
            graph[module_name] = imports
        return {name: frozenset(imports) for name, imports in graph.items()}

    @staticmethod
    def normalizer_file_tier(
        *,
        file_path: Path,
        project_package: str,
        facade_to_alias: Mapping[str, str],
        alias_tiers: Mapping[str, int],
    ) -> int:
        """Infer architectural tier for a file based on facade/paths."""
        declared_alias = facade_to_alias.get(file_path.name, "")
        if declared_alias in alias_tiers:
            return alias_tiers[declared_alias]
        if len(project_package) == 0:
            return _UNKNOWN_TIER
        marker = f"/src/{project_package}/"
        file_str = str(file_path.resolve())
        if marker not in file_str:
            return _UNKNOWN_TIER
        relative = file_str.split(marker, maxsplit=1)[1]
        parts = Path(relative).parts[:-1]
        if len(parts) == 0:
            return _UNKNOWN_TIER
        first = parts[0]
        if first.startswith("_"):
            normalized = first.lstrip("_")
            if normalized == "services":
                normalized = "service"
            alias = facade_to_alias.get(f"{normalized}.py", "")
            if alias in alias_tiers:
                return alias_tiers[alias]
            if normalized == "result" and "r" in alias_tiers:
                return alias_tiers["r"]
            return 4
        return 4


__all__ = ["FlextInfraUtilitiesImportNormalizer"]
