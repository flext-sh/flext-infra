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

from flext_infra import c, config, t, u
from flext_infra.services.codegen import FlextInfraCodegen
from flext_tests import tm

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
        tm.that(len(names), eq=len(set(names)))
        tm.that(all(names), eq=True)

    # P1 — vscode_files_exclude_map -------------------------------------

    def test_vscode_files_exclude_map_shape(self, codegen: CodegenSpec) -> None:
        """Every key is a ``**/<name>`` glob and every value is True."""
        mapping = codegen.vscode_files_exclude_map
        for key, value in mapping.items():
            tm.that(re.fullmatch(r"\*\*/[^/]+", key) is not None, eq=True, msg=key)
            tm.that(value, eq=True)

    def test_vscode_files_exclude_map_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence in the map equals the artifact's vscode_exclude flag."""
        mapping = codegen.vscode_files_exclude_map
        for artifact in codegen.artifacts:
            tm.that(
                f"**/{artifact.name}" in mapping,
                eq=artifact.vscode_exclude,
                msg=artifact.name,
            )
        tm.that(
            len(mapping),
            eq=sum(artifact.vscode_exclude for artifact in codegen.artifacts),
        )

    def test_vscode_files_exclude_map_order(self, codegen: CodegenSpec) -> None:
        """Map preserves artifact declaration order (renderer keeps it)."""
        mapping = codegen.vscode_files_exclude_map
        tm.that(
            list(mapping),
            eq=[
                f"**/{artifact.name}"
                for artifact in codegen.artifacts
                if artifact.vscode_exclude
            ],
        )

    def test_vscode_files_exclude_map_anchors(self, codegen: CodegenSpec) -> None:
        """Anchors evaluated against real config flags (non-vacuous)."""
        mapping = codegen.vscode_files_exclude_map
        by_name = {artifact.name: artifact for artifact in codegen.artifacts}
        # .mypy_cache really has vscode_exclude=true in config/codegen.yaml.
        tm.that(by_name[".mypy_cache"].vscode_exclude, eq=True)
        tm.that(mapping["**/.mypy_cache"], eq=True)
        # conftest.py is source-scan-only: vscode_exclude=false in real config.
        tm.that(by_name["conftest.py"].vscode_exclude, eq=False)
        tm.that(mapping, lacks="**/conftest.py")

    # P2 — vscode_watcher_exclude_map ------------------------------------

    def test_vscode_watcher_exclude_map_shape(self, codegen: CodegenSpec) -> None:
        """Every key is a ``**/<name>/**`` glob and every value is True."""
        mapping = codegen.vscode_watcher_exclude_map
        for key, value in mapping.items():
            tm.that(re.fullmatch(r"\*\*/[^/]+/\*\*", key) is not None, eq=True, msg=key)
            tm.that(value, eq=True)

    def test_vscode_watcher_exclude_map_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence in the map equals the artifact's watch_exclude flag."""
        mapping = codegen.vscode_watcher_exclude_map
        for artifact in codegen.artifacts:
            tm.that(
                f"**/{artifact.name}/**" in mapping,
                eq=artifact.watch_exclude,
                msg=artifact.name,
            )
        tm.that(
            len(mapping),
            eq=sum(artifact.watch_exclude for artifact in codegen.artifacts),
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
        tm.that(site.vscode_exclude, eq=True)
        tm.that(site.watch_exclude, eq=False)
        tm.that(codegen.vscode_files_exclude_map, has="**/site")
        tm.that(codegen.vscode_watcher_exclude_map, lacks="**/site/**")
        tm.that(codegen.vscode_watcher_exclude_map, has="**/.mypy_cache/**")

    # P3 — vscode_search_exclude_map -------------------------------------

    def test_vscode_search_exclude_map_equals_files_exclude(
        self, codegen: CodegenSpec
    ) -> None:
        """THE law: search.exclude is the same projection as files.exclude."""
        tm.that(
            dict(codegen.vscode_search_exclude_map),
            eq=dict(codegen.vscode_files_exclude_map),
        )

    # P4 — source_scan_ignored -------------------------------------------

    def test_source_scan_ignored_shape(self, codegen: CodegenSpec) -> None:
        """Raw unique names in a tuple — no glob characters or path parts."""
        ignored = codegen.source_scan_ignored
        tm.that(isinstance(ignored, tuple), eq=True)
        tm.that(all("*" not in name and "/" not in name for name in ignored), eq=True)
        tm.that(len(ignored), eq=len(set(ignored)))

    def test_source_scan_ignored_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence in the tuple equals the artifact's source_scan_ignore flag."""
        ignored = codegen.source_scan_ignored
        for artifact in codegen.artifacts:
            tm.that(
                artifact.name in ignored,
                eq=artifact.source_scan_ignore,
                msg=artifact.name,
            )

    def test_source_scan_ignored_independence_anchor(
        self, codegen: CodegenSpec
    ) -> None:
        """conftest.py is scanned-out but NOT vscode-excluded (independence)."""
        tm.that(codegen.source_scan_ignored, has="conftest.py")
        tm.that(codegen.vscode_files_exclude_map, lacks="**/conftest.py")

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
            tm.that(patterns, has=emitted, msg=artifact.name)
            tm.that(emitted.endswith("/"), eq=artifact.is_dir)

    def test_gitignore_artifact_patterns_filter_bidirectional(
        self, codegen: CodegenSpec
    ) -> None:
        """Presence of the transformed pattern equals the gitignore flag."""
        patterns = codegen.gitignore_artifact_patterns
        for artifact in codegen.artifacts:
            emitted = artifact.name + "/" if artifact.is_dir else artifact.name
            tm.that(emitted in patterns, eq=artifact.gitignore, msg=artifact.name)

    def test_gitignore_artifact_patterns_shape(self, codegen: CodegenSpec) -> None:
        """No ``**/`` prefix anywhere; patterns are unique."""
        patterns = codegen.gitignore_artifact_patterns
        tm.that(isinstance(patterns, tuple), eq=True)
        tm.that(all(not pattern.startswith("**/") for pattern in patterns), eq=True)
        tm.that(len(patterns), eq=len(set(patterns)))

    def test_gitignore_artifact_patterns_order(self, codegen: CodegenSpec) -> None:
        """Byte output order is load-bearing: stripped patterns track SSOT order."""
        patterns = codegen.gitignore_artifact_patterns
        tm.that(
            [pattern.rstrip("/") for pattern in patterns],
            eq=[artifact.name for artifact in codegen.artifacts if artifact.gitignore],
        )

    def test_gitignore_artifact_patterns_anchors(self, codegen: CodegenSpec) -> None:
        """Dir artifacts gain a slash; file artifacts stay bare (real flags)."""
        patterns = codegen.gitignore_artifact_patterns
        by_name = {artifact.name: artifact for artifact in codegen.artifacts}
        # .mypy_cache: real config has is_dir=true, gitignore=true.
        tm.that(by_name[".mypy_cache"].is_dir, eq=True)
        tm.that(by_name[".mypy_cache"].gitignore, eq=True)
        tm.that(patterns, has=".mypy_cache/")
        # .mcp.json: real config has is_dir=false, gitignore=true.
        mcp = by_name[".mcp.json"]
        tm.that(mcp.is_dir, eq=False)
        tm.that(mcp.gitignore, eq=True)
        tm.that(patterns, has=".mcp.json")
        tm.that(patterns, lacks=".mcp.json/")

    # P6 — gitignore_sections ---------------------------------------------

    def test_gitignore_sections_dedup_and_merge(self, codegen: CodegenSpec) -> None:
        """Every derived artifact is governed, and repeats stay where declared.

        Global uniqueness is NOT the law: an ignore file is order-sensitive, so
        repeating ``.beads/*`` after an intervening ``!.beads/`` is what keeps
        that directory scanned. Deduplicating the repeat silently un-ignores its
        contents, so only the appended artifact tail is deduplicated.

        Nor are artifact patterns unconditionally appended: when the SSOT already
        governs a path -- including re-allowing it with ``!`` -- appending a bare
        ignore would contradict the declared policy. The law is therefore that
        every artifact is *accounted for*, either governed or appended.
        """
        sections = codegen.gitignore_sections
        flat = [pattern for section in sections for pattern in section.patterns]
        governed = {
            pattern.lstrip("!")
            for section in codegen.scaffold.gitignore_sections
            for pattern in section.patterns
        }

        unaccounted = [
            pattern
            for pattern in codegen.gitignore_artifact_patterns
            if pattern not in flat and pattern not in governed
        ]

        tm.that(unaccounted, eq=[])

    def test_gitignore_sections_static_origin_proof(self, codegen: CodegenSpec) -> None:
        """Environment patterns reach .gitignore from the static section only."""
        sections = codegen.gitignore_sections
        flat = [pattern for section in sections for pattern in section.patterns]
        tm.that(flat, has=".env")
        tm.that(flat, has="!.env.example")
        tm.that(codegen.gitignore_artifact_patterns, lacks=".env")
        tm.that(codegen.gitignore_artifact_patterns, lacks="!.env.example")

    def test_gitignore_sections_header_order(self, codegen: CodegenSpec) -> None:
        """The projection preserves the declared section order (P0: no frozen names).

        Ignore files are order-sensitive, so the contract is that the declared
        sections appear first, in the order the SSOT declares them. Retyping
        today's section names here would freeze a config-owned value and break
        on any legitimate policy change, so the expectation is read from the
        same scaffold SSOT the projection consumes.

        Derived artifacts are appended as one trailing section, so the declared
        names are an ordered prefix rather than the whole sequence.
        """
        declared = [section.name for section in codegen.scaffold.gitignore_sections]
        derived = [section.name for section in codegen.gitignore_sections]

        tm.that(derived[: len(declared)], eq=declared)
        tm.that(
            derived[len(declared) :] in ([], [c.Infra.GITIGNORE_DERIVED_SECTION_NAME]),
            eq=True,
        )

    def test_workspace_root_makefile_has_one_generation_owner(
        self, codegen: CodegenSpec
    ) -> None:
        """Keep one Makefile template owner for every supported profile."""
        makefile_entries = [
            entry
            for entry in codegen.templates.entries
            if entry.destination == "Makefile"
        ]

        tm.that(makefile_entries, len=1)
        tm.that(makefile_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_gitignore_sections_anchors(self, codegen: CodegenSpec) -> None:
        """Artifact-origin and static-origin anchors coexist in the body."""
        sections = codegen.gitignore_sections
        flat = [pattern for section in sections for pattern in section.patterns]
        tm.that(flat, has=".mypy_cache/")
        tm.that(flat, has=".env")

    # Rendered-surface anchor (cheap, in-process) -------------------------

    def test_rendered_vscode_settings_anchor(self) -> None:
        """Rendered settings.json carries the SSOT maps byte-for-byte."""
        rendered = tm.ok(
            FlextInfraCodegen.render_vscode_settings(Path("nonexistent-workspace-root"))
        )
        parsed = tm.ok(u.Cli.json_parse(rendered))
        settings = t.Cli.JSON_MAPPING_ADAPTER.validate_python(parsed)
        files_exclude = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            settings["files.exclude"]
        )
        search_exclude = settings["search.exclude"]
        watcher_exclude = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            settings["files.watcherExclude"]
        )
        tm.that(files_exclude["**/.mypy_cache"], eq=True)
        tm.that("**/conftest.py" in files_exclude, eq=False)
        tm.that(search_exclude, eq=files_exclude)
        tm.that(watcher_exclude["**/.mypy_cache/**"], eq=True)
        tm.that("**/site/**" in watcher_exclude, eq=False)
