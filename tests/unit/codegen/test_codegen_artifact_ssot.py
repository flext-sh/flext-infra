"""Artifact SSOT derivation tests (mro-jnm1.1 / mro-jnm1.4).

Prove the single ``artifacts`` list in ``config/codegen.yaml`` derives the
exact VS Code exclude maps and source_scan ignores that were previously
hardcoded in four places.
"""

from __future__ import annotations

from flext_infra import config


class TestsCodegenArtifactSsot:
    """Derived projections must equal the historical hardcoded literals."""

    _EXPECTED_VSCODE_NAMES: tuple[str, ...] = (
        "__pycache__",
        "__pyrefly_virtual__",
        ".agents",
        ".beads",
        ".benchmarks",
        ".cache",
        ".claude",
        ".code-review-graph",
        ".codegraph",
        ".dolt",
        ".dolt_dropped_databases",
        ".doltcfg",
        ".git",
        ".mypy_cache",
        ".omo",
        ".pytest_cache",
        ".reports",
        ".ropeproject",
        ".ruff_cache",
        ".scope",
        ".serena",
        ".sisyphus",
        ".state",
        ".superpowers",
        ".trash",
        ".turbo",
        ".venv",
        ".venv.*",
        "build",
        "dist",
        "node_modules",
        "site",
        "target",
    )
    _EXPECTED_WATCH_EXTRA: tuple[str, ...] = (".pylance_cache", "*.egg-info")
    _EXPECTED_SOURCE_SCAN: frozenset[str] = frozenset({
        ".cache",
        ".claude",
        ".git",
        ".mypy_cache",
        ".pyrefly_cache",
        ".pytest_cache",
        ".reports",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "conftest.py",
        "dist",
        "dist-packages",
        "legado",
        "node_modules",
        "site-packages",
        "vendor",
        "venv",
    })

    def test_vscode_files_exclude_map_matches_legacy(self) -> None:
        """files.exclude derives the exact legacy entries in legacy order."""
        derived = config.Infra.codegen.vscode_files_exclude_map
        expected = {f"**/{name}": True for name in self._EXPECTED_VSCODE_NAMES}
        assert dict(derived) == expected
        assert list(derived) == list(expected)

    def test_vscode_search_exclude_map_equals_files_exclude(self) -> None:
        """search.exclude is the same projection as files.exclude."""
        codegen = config.Infra.codegen
        assert dict(codegen.vscode_search_exclude_map) == dict(
            codegen.vscode_files_exclude_map
        )

    def test_vscode_watcher_exclude_map_matches_legacy(self) -> None:
        """Watcher-exclude map drops site, adds .pylance_cache and *.egg-info."""
        derived = config.Infra.codegen.vscode_watcher_exclude_map
        watch_names = [
            name for name in self._EXPECTED_VSCODE_NAMES if name != "site"
        ]
        # Legacy watcher order: .pylance_cache after .omo, *.egg-info after .venv.*
        watch_names.insert(watch_names.index(".pytest_cache"), ".pylance_cache")
        watch_names.insert(watch_names.index("build"), "*.egg-info")
        expected = {f"**/{name}/**": True for name in watch_names}
        assert dict(derived) == expected
        assert list(derived) == list(expected)
        assert set(self._EXPECTED_WATCH_EXTRA).issubset(
            {key.removeprefix("**/").removesuffix("/**") for key in derived}
        )

    def test_source_scan_ignored_matches_legacy(self) -> None:
        """source_scan ignores derive the exact legacy ignored_resources set."""
        derived = config.Infra.codegen.source_scan_ignored
        assert set(derived) == self._EXPECTED_SOURCE_SCAN
        assert len(derived) == len(self._EXPECTED_SOURCE_SCAN)

    def test_artifact_list_is_single_source(self) -> None:
        """Every artifact name is unique and non-empty."""
        names = [artifact.name for artifact in config.Infra.codegen.artifacts]
        assert len(names) == len(set(names))
        assert all(names)
