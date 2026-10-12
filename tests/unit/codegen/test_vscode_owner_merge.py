"""Owner-merge dispatch for governed .vscode/settings.json artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, t
from flext_infra.services.codegen import FlextInfraCodegen
from tests import m, tm, u


class TestsFlextInfraVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    @staticmethod
    def test_merge_marks_drift_and_renders_canonical_content(
        tmp_path: Path,
    ) -> None:
        """Plan a changed merge artifact with canonical and custom keys."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        _ = settings_path.write_text(
            '{"python.languageServer": "None"}\n',
            encoding="utf-8",
        )

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(result)
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(result.value)),
        )
        for key, expected_value in config.Infra.codegen.vscode.scalar_settings.items():
            tm.that(doc[key], eq=expected_value)
        for stripped in config.Infra.codegen.vscode.stripped_keys:
            tm.that(stripped in doc, eq=False)
        search_paths_key = c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
        tm.that(search_paths_key in config.Infra.codegen.vscode.list_settings, eq=False)
        tm.that(search_paths_key in doc, eq=False)

    @staticmethod
    def test_merge_reaches_fixed_point_after_apply(tmp_path: Path) -> None:
        """Replan a written merge artifact with zero residual drift."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        _ = settings_path.write_text("{}\n", encoding="utf-8")
        first = FlextInfraCodegen.render_vscode_settings(root)
        tm.ok(first)
        _ = settings_path.write_text(first.value, encoding="utf-8")

        second = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(second)
        tm.that(second.value, eq=first.value)

    @staticmethod
    def test_merge_removes_keys_absent_from_artifact_authority(
        tmp_path: Path,
    ) -> None:
        """Artifact exclude maps are exact projections, not append-only unions."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        stale_key = "**/.retired-runtime"
        _ = settings_path.write_text(
            tm.ok(u.Cli.json_dumps({"files.exclude": {stale_key: True}})),
            encoding="utf-8",
        )

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(result)
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(result.value)),
        )
        tm.that(
            doc["files.exclude"],
            eq=dict(config.Infra.codegen.vscode_files_exclude_map),
        )

    @staticmethod
    def test_merge_strips_retired_pyright_keys(tmp_path: Path) -> None:
        """Pylance settingsNotOverridable keys must be stripped, not preserved."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        _ = settings_path.write_text(
            tm.ok(
                u.Cli.json_dumps({
                    "python.analysis.typeCheckingMode": "standard",
                    "python.analysis.diagnosticSeverityOverrides": {
                        "reportMissingTypeStubs": "error",
                    },
                    "ruff.nativeServer": True,
                }),
            ),
            encoding="utf-8",
        )

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(result)
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(result.value)),
        )
        tm.that("python.analysis.typeCheckingMode" in doc, eq=False)
        tm.that("python.analysis.diagnosticSeverityOverrides" in doc, eq=False)
        tm.that("ruff.nativeServer" in doc, eq=False)

    @staticmethod
    def test_attached_member_projects_its_workspace_interpreter(tmp_path: Path) -> None:
        """Opening an attached member resolves its physical workspace runtime."""
        parent = tmp_path / "parent"
        member = u.Tests.WorktreeFixture.copied_member(
            parent,
            "fixture-parent",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        u.Tests.WorktreeFixture.attach_submodule(
            parent,
            member,
            distribution="fixture-member",
            relative_path=member.relative_to(parent).as_posix(),
        )
        rendered = tm.ok(FlextInfraCodegen.render_vscode_settings(member))
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(rendered)),
        )
        interpreter = u.type_adapter(str).validate_python(
            doc["python.defaultInterpreterPath"],
        )
        projected = member / interpreter.removeprefix("${workspaceFolder}/")
        tm.that(projected.resolve(), eq=u.Infra.runtime_python(member))
        tm.that(str(tmp_path) in rendered, eq=False)
