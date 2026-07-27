"""Canonical VS Code settings codegen merge contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config
from flext_infra.services.codegen import FlextInfraCodegen


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

    def test_derives_member_venv_globs_from_workspace_manifest(
        self, tmp_path: Path
    ) -> None:
        """Derive shallow venv globs from config/workspace.yaml member paths."""
        project_root = tmp_path / "workspace"
        project_root.mkdir()
        config_dir = project_root / "config"
        config_dir.mkdir()
        (config_dir / "workspace.yaml").write_text(
            "version: 2\nmembers:\n  - name: a\n    path: apps/a\n"
            "  - name: b\n    path: libs/b\n",
            encoding="utf-8",
        )

        result = FlextInfraCodegen.render_vscode_settings(project_root)

        tm.ok(result)
        doc = json.loads(result.value)
        search_paths = doc[c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY]
        tm.that(
            search_paths,
            eq=[
                *config.Infra.codegen.vscode.list_settings[
                    c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
                ],
                "./apps/a/.venv",
                "./libs/b/.venv",
            ],
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
