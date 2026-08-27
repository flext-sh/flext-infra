"""Canonical VS Code settings codegen merge contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from flext_infra import c, config
from flext_infra.services.codegen import FlextInfraCodegen
from flext_tests import tm


def _write_settings(project_root: Path, content: str) -> Path:
    settings_path = project_root / ".vscode" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    _ = settings_path.write_text(content, encoding="utf-8")
    return settings_path


class TestsFlextInfraCodegenVscode:
    """Behavior contract for the config-driven VS Code settings codegen owner."""

    def test_applies_canonical_settings_and_preserves_custom_keys(
        self, tmp_path: Path
    ) -> None:
        """Enforce canonical keys while preserving project-specific entries."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        _write_settings(
            project_root,
            json.dumps({
                "python.languageServer": "None",
                "files.exclude": {"**/dbt_packages": True},
                "python.analysis.diagnosticSeverityOverrides": {
                    "reportUnknownMemberType": "none"
                },
            })
            + "\n",
        )

        result = FlextInfraCodegen.render_vscode_settings(project_root)

        tm.ok(result)
        doc = json.loads(result.value)
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")
        tm.that(
            doc["python.defaultInterpreterPath"],
            eq="${workspaceFolder}/.venv/bin/python",
        )
        search_paths = doc[c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY]
        tm.that(
            search_paths,
            eq=list(
                config.Infra.codegen.vscode.list_settings[
                    c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
                ]
            ),
        )
        tm.that("./apps/*/.venv" in search_paths, eq=False)
        tm.that(doc["files.exclude"]["**/dbt_packages"], eq=True)
        tm.that(doc["files.exclude"]["**/.mypy_cache"], eq=True)
        overrides = doc["python.analysis.diagnosticSeverityOverrides"]
        tm.that(overrides["reportUnknownMemberType"], eq="none")
        tm.that(overrides["reportUntypedBaseClass"], eq="none")
        tm.that(doc["python.languageServer"], eq="None")

    def test_render_reaches_fixed_point(self, tmp_path: Path) -> None:
        """Rendering a document that was already rendered produces no drift."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        first = FlextInfraCodegen.render_vscode_settings(project_root)
        tm.ok(first)
        _write_settings(project_root, first.value)
        second = FlextInfraCodegen.render_vscode_settings(project_root)
        tm.ok(second)
        tm.that(second.value, eq=first.value)

    def test_workspace_and_subproject_receive_the_same_canonical_settings(
        self, tmp_path: Path
    ) -> None:
        """Do not specialize VS Code settings from repository topology."""
        project_root = tmp_path / "workspace"
        project_root.mkdir()
        (project_root / ".gitmodules").write_text(
            '[submodule "apps/a"]\n\tpath = apps/a\n\turl = ../a.git\n',
            encoding="utf-8",
        )
        subproject_root = tmp_path / "subproject"
        subproject_root.mkdir()

        workspace_result = FlextInfraCodegen.render_vscode_settings(project_root)
        subproject_result = FlextInfraCodegen.render_vscode_settings(subproject_root)

        tm.ok(workspace_result)
        tm.ok(subproject_result)
        tm.that(subproject_result.value, eq=workspace_result.value)
        doc = json.loads(workspace_result.value)
        search_paths = doc[c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY]
        tm.that(
            search_paths,
            eq=list(
                config.Infra.codegen.vscode.list_settings[
                    c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
                ]
            ),
        )

    def test_invalid_json_fails_without_producing_a_document(
        self, tmp_path: Path
    ) -> None:
        """Return a typed failure when the existing settings are unparseable."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        _write_settings(project_root, "{ invalid json")

        result = FlextInfraCodegen.render_vscode_settings(project_root)

        tm.fail(result)
        tm.that(result.error, none=False)
