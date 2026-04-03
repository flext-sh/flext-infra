"""Import normalization helpers for the transformer layer.

Centralizes the ``Helper`` logic previously nested inside
``FlextInfraTransformerImportNormalizer``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Mapping, MutableMapping
from functools import lru_cache
from pathlib import Path

from flext_core import FlextUtilities, m
from flext_infra import (
    FlextInfraUtilitiesYaml,
    c,
    t,
)


class FlextInfraNormalizerContext(m.ArbitraryTypesModel):
    """Analysis context for import normalization."""

    file_path: Path
    project_package: str
    declared_alias: str
    alias_tiers: t.IntMapping
    universal_aliases: frozenset[str]


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


__all__ = ["FlextInfraNormalizerContext", "FlextInfraUtilitiesImportNormalizer"]
