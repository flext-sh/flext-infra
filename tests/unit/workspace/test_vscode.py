"""Canonical VS Code settings merge contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from flext_tests import tm

from flext_infra.workspace.vscode import FlextInfraWorkspaceVscode


def _write_project(project_root: Path) -> None:
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )


def _write_settings(project_root: Path, content: str) -> Path:
    settings_path = project_root / ".vscode" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    _ = settings_path.write_text(content, encoding="utf-8")
    return settings_path


class TestsFlextInfraWorkspaceVscode:
    """Behavior contract for the config-driven VS Code settings merge."""

    def test_applies_canonical_settings_and_preserves_custom_keys(
        self, tmp_path: Path
    ) -> None:
        """Enforce canonical keys while preserving project-specific entries."""
        project_root = tmp_path / "project"
        _write_project(project_root)
        settings_path = _write_settings(
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

        result = FlextInfraWorkspaceVscode.sync_settings(project_root, apply=True)

        tm.ok(result)
        tm.that(result.value, eq=True)
        doc = json.loads(settings_path.read_text(encoding="utf-8"))
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")
        tm.that(
            doc["python.defaultInterpreterPath"],
            eq="${workspaceFolder}/.venv/bin/python",
        )
        tm.that(
            doc["python-envs.workspaceSearchPaths"],
            eq=["./.venv", "./*/.venv", "./apps/*/.venv"],
        )
        tm.that(doc["files.exclude"]["**/dbt_packages"], eq=True)
        tm.that(doc["files.exclude"]["**/.venv"], eq=True)
        tm.that(doc["files.watcherExclude"]["**/.venv/**"], eq=True)
        tm.that(doc["files.watcherExclude"]["**/target/**"], eq=True)
        tm.that(doc["search.exclude"]["**/node_modules"], eq=True)
        overrides = doc["python.analysis.diagnosticSeverityOverrides"]
        tm.that(overrides["reportUnknownMemberType"], eq="none")
        tm.that(overrides["reportUntypedBaseClass"], eq="none")
        tm.that(doc["python.languageServer"], eq="None")
        tm.that(
            doc["terminal.integrated.env.linux"]["VIRTUAL_ENV"],
            eq="${workspaceFolder}/.venv",
        )

    def test_second_run_is_idempotent(self, tmp_path: Path) -> None:
        """Produce zero changes when a merged project runs again."""
        project_root = tmp_path / "project"
        _write_project(project_root)

        first = FlextInfraWorkspaceVscode.sync_settings(project_root, apply=True)
        second = FlextInfraWorkspaceVscode.sync_settings(project_root, apply=True)

        tm.ok(first)
        tm.that(first.value, eq=True)
        tm.ok(second)
        tm.that(second.value, eq=False)

    def test_derives_member_venv_globs_from_workspace_manifest(
        self, tmp_path: Path
    ) -> None:
        """Derive shallow venv globs from config/workspace.yaml member paths."""
        project_root = tmp_path / "workspace"
        _write_project(project_root)
        config_dir = project_root / "config"
        config_dir.mkdir()
        (config_dir / "workspace.yaml").write_text(
            "version: 2\nmembers:\n  - name: a\n    path: apps/a\n  - name: b\n    path: libs/b\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceVscode.render_merged_settings(project_root)

        tm.ok(result)
        doc = json.loads(result.value)
        tm.that(
            doc["python-envs.workspaceSearchPaths"],
            eq=[
                "./.venv",
                "./*/.venv",
                "./apps/*/.venv",
                "./apps/a/.venv",
                "./libs/b/.venv",
            ],
        )

    def test_jsonc_comments_and_trailing_commas_are_tolerated(
        self, tmp_path: Path
    ) -> None:
        """Parse VS Code JSONC content before merging canonical keys."""
        project_root = tmp_path / "project"
        _write_project(project_root)
        settings_path = _write_settings(
            project_root, '{\n  // project note\n  "editor.formatOnSave": true,\n}\n'
        )

        result = FlextInfraWorkspaceVscode.sync_settings(project_root, apply=True)

        tm.ok(result)
        doc = json.loads(settings_path.read_text(encoding="utf-8"))
        tm.that(doc["editor.formatOnSave"], eq=True)
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")

    def test_invalid_json_fails_without_writing(self, tmp_path: Path) -> None:
        """Return a typed failure and never rewrite an unparseable file."""
        project_root = tmp_path / "project"
        _write_project(project_root)
        broken = "{ invalid json"
        settings_path = _write_settings(project_root, broken)

        result = FlextInfraWorkspaceVscode.sync_settings(project_root, apply=True)

        tm.fail(result)
        tm.that(settings_path.read_text(encoding="utf-8"), eq=broken)

    def test_missing_pyproject_returns_noop(self, tmp_path: Path) -> None:
        """Skip directories that are not Python projects."""
        result = FlextInfraWorkspaceVscode.sync_settings(
            tmp_path / "missing", apply=True
        )

        tm.ok(result)
        tm.that(result.value, eq=False)
