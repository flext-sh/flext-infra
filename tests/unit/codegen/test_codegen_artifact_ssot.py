"""Behavioral contracts for projections derived from the artifact SSOT."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, t, u
from flext_infra.services.codegen import FlextInfraCodegen

CodegenSpec = type(config.Infra.codegen)


@pytest.fixture(scope="module")
def codegen() -> CodegenSpec:
    """Provide the production codegen configuration."""
    return config.Infra.codegen


class TestsCodegenArtifactSsot:
    """Validate public projections against arbitrary valid SSOT values."""

    def test_artifacts_are_well_formed(self, codegen: CodegenSpec) -> None:
        """Require unique, non-empty artifact names."""
        names = tuple(artifact.name for artifact in codegen.artifacts)
        tm.that(len(names), eq=len(set(names)))
        tm.that(all(names), eq=True)

    def test_vscode_file_projection(self, codegen: CodegenSpec) -> None:
        """Derive file exclusions exclusively from their configured flags."""
        expected = {
            f"**/{artifact.name}": True
            for artifact in codegen.artifacts
            if artifact.vscode_exclude
        }
        actual = dict(codegen.vscode_files_exclude_map)
        tm.that(actual, eq=expected)
        tm.that(all(re.fullmatch(r"\*\*/[^/]+", key) for key in actual), eq=True)
        tm.that(dict(codegen.vscode_search_exclude_map), eq=actual)

    def test_vscode_watcher_projection(self, codegen: CodegenSpec) -> None:
        """Derive watcher exclusions exclusively from their configured flags."""
        expected = {
            f"**/{artifact.name}/**": True
            for artifact in codegen.artifacts
            if artifact.watch_exclude
        }
        actual = dict(codegen.vscode_watcher_exclude_map)
        tm.that(actual, eq=expected)
        tm.that(all(re.fullmatch(r"\*\*/[^/]+/\*\*", key) for key in actual), eq=True)

    def test_source_scan_projection(self, codegen: CodegenSpec) -> None:
        """Derive source scan exclusions as raw artifact names."""
        expected = tuple(
            artifact.name
            for artifact in codegen.artifacts
            if artifact.source_scan_ignore
        )
        actual = codegen.source_scan_ignored
        tm.that(actual, eq=expected)
        tm.that(all("*" not in name and "/" not in name for name in actual), eq=True)

    def test_gitignore_artifact_projection(self, codegen: CodegenSpec) -> None:
        """Derive ordered file and directory patterns from configured artifacts."""
        expected = tuple(
            f"{artifact.name}/" if artifact.is_dir else artifact.name
            for artifact in codegen.artifacts
            if artifact.gitignore
        )
        actual = codegen.gitignore_artifact_patterns
        tm.that(actual, eq=expected)
        tm.that(all(not pattern.startswith("**/") for pattern in actual), eq=True)

    def test_gitignore_sections_account_for_every_artifact(
        self, codegen: CodegenSpec
    ) -> None:
        """Keep every generated pattern governed or emitted."""
        emitted = {
            pattern
            for section in codegen.gitignore_sections
            for pattern in section.patterns
        }
        governed = {
            pattern.lstrip("!")
            for section in codegen.scaffold.gitignore_sections
            for pattern in section.patterns
        }
        unaccounted = tuple(
            pattern
            for pattern in codegen.gitignore_artifact_patterns
            if pattern not in emitted and pattern not in governed
        )
        tm.that(unaccounted, empty=True)

    def test_gitignore_section_order(self, codegen: CodegenSpec) -> None:
        """Preserve SSOT section order before any derived tail section."""
        declared = tuple(
            section.name for section in codegen.scaffold.gitignore_sections
        )
        derived = tuple(section.name for section in codegen.gitignore_sections)
        tm.that(derived[: len(declared)], eq=declared)
        tm.that(
            derived[len(declared) :] in {(), (c.Infra.GITIGNORE_DERIVED_SECTION_NAME,)},
            eq=True,
        )

    def test_workspace_root_makefile_has_one_owner(self, codegen: CodegenSpec) -> None:
        """Keep workspace-root Makefile generation in the single project template."""
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == "Makefile"
        )
        tm.that(len(entries), eq=1)
        tm.that(entries[0].profiles, has="workspace-root")

    def test_rendered_vscode_settings_follow_ssot(
        self, tmp_path: Path, codegen: CodegenSpec
    ) -> None:
        """Render the public surface and compare it with production projections."""
        rendered = tm.ok(FlextInfraCodegen.render_vscode_settings(tmp_path))
        settings = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_loads(rendered))
        )
        tm.that(settings["files.exclude"], eq=dict(codegen.vscode_files_exclude_map))
        tm.that(settings["search.exclude"], eq=dict(codegen.vscode_search_exclude_map))
        tm.that(
            settings["files.watcherExclude"],
            eq=dict(codegen.vscode_watcher_exclude_map),
        )
