"""Artifact SSOT invariant tests (mro-jnm1.1 / mro-jnm1.2 / mro-jnm1.4).

Doctrine: the test is NOT a second source-of-truth. It never freezes a
duplicate copy of the config; it asserts the *laws* each derived projection
must satisfy against the REAL ``config.Infra.codegen.artifacts`` SSOT —
shape, bidirectional filter (presence-in-projection == flag), size, order,
and cross-surface relations. Each assertion stays true and meaningful if the
projection were re-implemented as a hand-written loop.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from flext_infra import config, t
from flext_infra.workspace.vscode import FlextInfraWorkspaceVscode

CodegenSpec = type(config.Infra.codegen)


@pytest.fixture(scope="module")
def codegen() -> CodegenSpec:
    """Load the real codegen config SSOT once per module (pure in-memory)."""
    return config.Infra.codegen


class TestsCodegenArtifactSsot:
    """Invariant laws for every projection derived from the artifact SSOT."""

    def test_artifact_list_is_single_source(self, codegen: CodegenSpec) -> None:
        """Every artifact name is unique and non-empty (SSOT well-formed)."""
        names = [artifact.name for artifact in codegen.artifacts]
        assert len(names) == len(set(names))
        assert all(names)

    # P1 — vscode_files_exclude_map -------------------------------------

    def test_vscode_files_exclude_map_shape(self, codegen: CodegenSpec) -> None:
        """Every key is a ``**/<name>`` glob and every value is True."""
        mapping = codegen.vscode_files_exclude_map
        for key, value in mapping.items():
            assert re.fullmatch(r"\*\*/[^/]+", key), key
            assert value is True

    def test_vscode_files_exclude_map_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence in the map equals the artifact's vscode_exclude flag."""
        mapping = codegen.vscode_files_exclude_map
        for artifact in codegen.artifacts:
            assert (f"**/{artifact.name}" in mapping) == artifact.vscode_exclude, (
                artifact.name
            )
        assert len(mapping) == sum(
            artifact.vscode_exclude for artifact in codegen.artifacts
        )

    def test_vscode_files_exclude_map_order(self, codegen: CodegenSpec) -> None:
        """Map preserves artifact declaration order (renderer keeps it)."""
        mapping = codegen.vscode_files_exclude_map
        assert list(mapping) == [
            f"**/{artifact.name}"
            for artifact in codegen.artifacts
            if artifact.vscode_exclude
        ]

    def test_vscode_files_exclude_map_anchors(self, codegen: CodegenSpec) -> None:
        """Anchors evaluated against real config flags (non-vacuous)."""
        mapping = codegen.vscode_files_exclude_map
        by_name = {artifact.name: artifact for artifact in codegen.artifacts}
        # .mypy_cache really has vscode_exclude=true in config/codegen.yaml.
        assert by_name[".mypy_cache"].vscode_exclude is True
        assert mapping["**/.mypy_cache"] is True
        # conftest.py is source-scan-only: vscode_exclude=false in real config.
        assert by_name["conftest.py"].vscode_exclude is False
        assert "**/conftest.py" not in mapping

    # P2 — vscode_watcher_exclude_map ------------------------------------

    def test_vscode_watcher_exclude_map_shape(self, codegen: CodegenSpec) -> None:
        """Every key is a ``**/<name>/**`` glob and every value is True."""
        mapping = codegen.vscode_watcher_exclude_map
        for key, value in mapping.items():
            assert re.fullmatch(r"\*\*/[^/]+/\*\*", key), key
            assert value is True

    def test_vscode_watcher_exclude_map_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence in the map equals the artifact's watch_exclude flag."""
        mapping = codegen.vscode_watcher_exclude_map
        for artifact in codegen.artifacts:
            assert (f"**/{artifact.name}/**" in mapping) == artifact.watch_exclude, (
                artifact.name
            )
        assert len(mapping) == sum(
            artifact.watch_exclude for artifact in codegen.artifacts
        )

    def test_vscode_watcher_diverges_from_files_exclude(
        self, codegen: CodegenSpec
    ) -> None:
        """Divergence anchor: the two maps use different predicates.

        ``site`` is the real config artifact with vscode_exclude=true and
        watch_exclude=false — present in P1, absent in P2.
        """
        by_name = {artifact.name: artifact for artifact in codegen.artifacts}
        site = by_name["site"]
        assert site.vscode_exclude is True
        assert site.watch_exclude is False
        assert "**/site" in codegen.vscode_files_exclude_map
        assert "**/site/**" not in codegen.vscode_watcher_exclude_map
        assert "**/.mypy_cache/**" in codegen.vscode_watcher_exclude_map

    # P3 — vscode_search_exclude_map -------------------------------------

    def test_vscode_search_exclude_map_equals_files_exclude(
        self, codegen: CodegenSpec
    ) -> None:
        """THE law: search.exclude is the same projection as files.exclude."""
        assert dict(codegen.vscode_search_exclude_map) == dict(
            codegen.vscode_files_exclude_map
        )

    # P4 — source_scan_ignored -------------------------------------------

    def test_source_scan_ignored_shape(self, codegen: CodegenSpec) -> None:
        """Raw unique names in a tuple — no glob characters or path parts."""
        ignored = codegen.source_scan_ignored
        assert isinstance(ignored, tuple)
        assert all("*" not in name and "/" not in name for name in ignored)
        assert len(ignored) == len(set(ignored))

    def test_source_scan_ignored_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence in the tuple equals the artifact's source_scan_ignore flag."""
        ignored = codegen.source_scan_ignored
        for artifact in codegen.artifacts:
            assert (artifact.name in ignored) == artifact.source_scan_ignore, (
                artifact.name
            )

    def test_source_scan_ignored_independence_anchor(
        self, codegen: CodegenSpec
    ) -> None:
        """conftest.py is scanned-out but NOT vscode-excluded (independence)."""
        assert "conftest.py" in codegen.source_scan_ignored
        assert "**/conftest.py" not in codegen.vscode_files_exclude_map

    # P5 — gitignore_artifact_patterns -----------------------------------

    def test_gitignore_artifact_patterns_transform_law(
        self, codegen: CodegenSpec
    ) -> None:
        """TRANSFORM law: emitted pattern ends with ``/`` iff is_dir."""
        patterns = codegen.gitignore_artifact_patterns
        for artifact in codegen.artifacts:
            if not artifact.gitignore:
                continue
            emitted = artifact.name + "/" if artifact.is_dir else artifact.name
            assert emitted in patterns, artifact.name
            assert emitted.endswith("/") == artifact.is_dir

    def test_gitignore_artifact_patterns_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence of the transformed pattern equals the gitignore flag."""
        patterns = codegen.gitignore_artifact_patterns
        for artifact in codegen.artifacts:
            emitted = artifact.name + "/" if artifact.is_dir else artifact.name
            assert (emitted in patterns) == artifact.gitignore, artifact.name

    def test_gitignore_artifact_patterns_shape(self, codegen: CodegenSpec) -> None:
        """No ``**/`` prefix anywhere; patterns are unique."""
        patterns = codegen.gitignore_artifact_patterns
        assert isinstance(patterns, tuple)
        assert all(not pattern.startswith("**/") for pattern in patterns)
        assert len(patterns) == len(set(patterns))

    def test_gitignore_artifact_patterns_order(self, codegen: CodegenSpec) -> None:
        """Byte output order is load-bearing: stripped patterns track SSOT order."""
        patterns = codegen.gitignore_artifact_patterns
        assert [pattern.rstrip("/") for pattern in patterns] == [
            artifact.name for artifact in codegen.artifacts if artifact.gitignore
        ]

    def test_gitignore_artifact_patterns_anchors(self, codegen: CodegenSpec) -> None:
        """Dir artifacts gain a slash; file artifacts stay bare (real flags)."""
        patterns = codegen.gitignore_artifact_patterns
        by_name = {artifact.name: artifact for artifact in codegen.artifacts}
        # .mypy_cache: real config has is_dir=true, gitignore=true.
        assert by_name[".mypy_cache"].is_dir is True
        assert by_name[".mypy_cache"].gitignore is True
        assert ".mypy_cache/" in patterns
        # .mcp.json: real config has is_dir=false, gitignore=true.
        mcp = by_name[".mcp.json"]
        assert mcp.is_dir is False
        assert mcp.gitignore is True
        assert ".mcp.json" in patterns
        assert ".mcp.json/" not in patterns

    # P6 — gitignore_sections ---------------------------------------------

    def test_gitignore_sections_dedup_and_merge(self, codegen: CodegenSpec) -> None:
        """Headline dedup law + artifact patterns are a subset of the flat body."""
        sections = codegen.gitignore_sections
        flat = [pattern for section in sections for pattern in section.patterns]
        assert len(flat) == len(set(flat))
        assert set(codegen.gitignore_artifact_patterns) <= set(flat)

    def test_gitignore_sections_static_origin_proof(self, codegen: CodegenSpec) -> None:
        """``.env`` reaches .gitignore from the static secrets section only."""
        sections = codegen.gitignore_sections
        flat = [pattern for section in sections for pattern in section.patterns]
        assert ".env" in flat
        assert ".env" not in codegen.gitignore_artifact_patterns

    def test_gitignore_sections_header_order(self, codegen: CodegenSpec) -> None:
        """Section headers are present in declared order (bodies not pinned)."""
        assert [section.name for section in codegen.gitignore_sections] == [
            "Python and build artifacts",
            "FLEXT",
            "Environment and secrets",
            "Editors and OS",
        ]

    def test_gitignore_sections_anchors(self, codegen: CodegenSpec) -> None:
        """Artifact-origin and static-origin anchors coexist in the body."""
        sections = codegen.gitignore_sections
        flat = [pattern for section in sections for pattern in section.patterns]
        assert ".mypy_cache/" in flat  # artifact origin
        assert ".env" in flat  # static secrets origin

    # Rendered-surface anchor (cheap, in-process) -------------------------

    def test_rendered_vscode_settings_anchor(self) -> None:
        """Rendered settings.json carries the SSOT maps byte-for-byte."""
        settings: t.MutableJsonMapping = {}
        FlextInfraWorkspaceVscode.apply_canonical_settings(
            settings, Path("/nonexistent-workspace-root")
        )
        files_exclude = settings["files.exclude"]
        search_exclude = settings["search.exclude"]
        watcher_exclude = settings["files.watcherExclude"]
        assert isinstance(files_exclude, dict)
        assert files_exclude["**/.mypy_cache"] is True
        assert "**/conftest.py" not in files_exclude
        assert search_exclude == files_exclude
        assert isinstance(watcher_exclude, dict)
        assert watcher_exclude["**/.mypy_cache/**"] is True
        assert "**/site/**" not in watcher_exclude
