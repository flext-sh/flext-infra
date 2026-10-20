"""Canonical VS Code settings codegen merge contract tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from flext_infra.services import FlextInfraCodegenVscodeMixin
from tests import c, m, tm, u


class TestsFlextInfraCodegenVscode:
    """Behavior contract for the config-driven VS Code settings codegen owner."""

    @staticmethod
    def _write_settings(project_root: Path, content: str) -> Path:
        settings_path = project_root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        _ = settings_path.write_text(content, encoding="utf-8")
        return settings_path

    def test_applies_canonical_settings_and_removes_retired_artifacts(
        self,
        tmp_path: Path,
    ) -> None:
        """Enforce canonical keys while deleting stale generated map entries."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        self._write_settings(
            project_root,
            tm.ok(
                u.Cli.json_dumps({
                    "python.languageServer": "None",
                    "python.analysis.typeCheckingMode": "off",
                    "files.exclude": {"**/.retired-cache": True},
                    "python.analysis.diagnosticSeverityOverrides": {
                        "reportUnknownMemberType": "none",
                    },
                }),
            )
            + "\n",
        )

        result = FlextInfraCodegenVscodeMixin.render_vscode_settings(project_root)
        tm.ok(result)
        doc = u.Tests.json_payload(result.value)
        tm.that("python.analysis.typeCheckingMode" in doc, eq=False)
        tm.that("python.analysis.diagnosticSeverityOverrides" in doc, eq=False)
        interpreter = "python.defaultInterpreterPath"
        tm.that(
            doc[interpreter],
            eq=config.Infra.codegen.vscode.scalar_settings[interpreter],
        )
        search_paths_key = c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
        tm.that(
            doc[search_paths_key],
            eq=config.Infra.codegen.vscode.additional_settings[search_paths_key],
        )
        excludes = u.Tests.toml_mapping(doc["files.exclude"])
        tm.that("**/.retired-cache" in excludes, eq=False)
        tm.that(excludes, eq=dict(config.Infra.codegen.vscode_files_exclude_map))
        tm.that(
            doc["python.languageServer"],
            eq=config.Infra.codegen.vscode.scalar_settings["python.languageServer"],
        )

    def test_strips_retired_keys_owning_pyright_config(self, tmp_path: Path) -> None:
        """Strip keys owned by [tool.pyright] to avoid Pylance warnings."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        self._write_settings(
            project_root,
            tm.ok(
                u.Cli.json_dumps({
                    "python.analysis.typeCheckingMode": "standard",
                    "python.analysis.diagnosticSeverityOverrides": {
                        "reportMissingTypeStubs": "error",
                    },
                    "python.languageServer": "Pylance",
                }),
            )
            + "\n",
        )

        result = FlextInfraCodegenVscodeMixin.render_vscode_settings(project_root)

        tm.ok(result)
        doc = u.Tests.json_payload(result.value)
        tm.that("python.analysis.typeCheckingMode" in doc, eq=False)
        tm.that("python.analysis.diagnosticSeverityOverrides" in doc, eq=False)
        tm.that(
            doc["python.languageServer"],
            eq=config.Infra.codegen.vscode.scalar_settings["python.languageServer"],
        )

    def test_render_reaches_fixed_point(self, tmp_path: Path) -> None:
        """Rendering a document that was already rendered produces no drift."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        first = FlextInfraCodegenVscodeMixin.render_vscode_settings(project_root)
        tm.ok(first)
        self._write_settings(project_root, first.value)
        second = FlextInfraCodegenVscodeMixin.render_vscode_settings(project_root)
        tm.ok(second)
        tm.that(second.value, eq=first.value)

    @staticmethod
    def test_python_environment_settings_are_independent_from_repository_topology(
        tmp_path: Path,
    ) -> None:
        """Keep opened-folder settings canonical for roots and subprojects."""
        project_root = tmp_path / "workspace"
        project_root.mkdir()
        provider = u.Tests.provider()
        (project_root / c.Infra.GITMODULES).write_text(
            '[submodule "app-a"]\n'
            "\tpath = apps/a\n"
            f"\turl = {provider.base_url.rstrip('/')}/app-a.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n"
            '[submodule "lib-b"]\n'
            "\tpath = libs/b\n"
            f"\turl = {provider.base_url.rstrip('/')}/lib-b.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n",
            encoding="utf-8",
        )

        result = FlextInfraCodegenVscodeMixin.render_vscode_settings(project_root)
        standalone_root = tmp_path / "standalone"
        standalone_root.mkdir()
        standalone = FlextInfraCodegenVscodeMixin.render_vscode_settings(
            standalone_root
        )

        tm.ok(result)
        tm.ok(standalone)
        tm.that(result.value.encode(), eq=standalone.value.encode())
        doc = u.Tests.json_payload(result.value)
        search_paths_key = c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
        tm.that(
            doc[search_paths_key],
            eq=config.Infra.codegen.vscode.additional_settings[search_paths_key],
        )

    def test_invalid_json_fails_without_producing_a_document(
        self,
        tmp_path: Path,
    ) -> None:
        """Return a typed failure when the existing settings are unparseable."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        self._write_settings(project_root, "{ invalid json")

        result = FlextInfraCodegenVscodeMixin.render_vscode_settings(project_root)

        tm.fail(result)
        tm.that(result.error, none=False)

    def test_project_artifacts_control_all_editor_exclusions(
        self, tmp_path: Path
    ) -> None:
        """Use the elected project catalog for file and directory exclusions."""
        directory = m.Infra.CodegenArtifactSpec(
            name="fixture-cache", analysis_exclude=True
        )
        file = m.Infra.CodegenArtifactSpec(
            name="*.fixture-backup", is_dir=False, analysis_exclude=True
        )
        elected = config.Infra.codegen.model_copy(
            update={"artifacts": (*config.Infra.codegen.artifacts, directory, file)}
        )
        rendered = tm.ok(
            FlextInfraCodegenVscodeMixin.render_vscode_settings(
                tmp_path, codegen=elected
            )
        )
        document = u.Tests.json_payload(rendered)
        for key, expected in (
            ("files.exclude", elected.vscode_files_exclude_map),
            ("search.exclude", elected.vscode_search_exclude_map),
            ("files.watcherExclude", elected.vscode_watcher_exclude_map),
        ):
            tm.that(document[key], eq=dict(expected))
        watchers = u.Tests.toml_mapping(document["files.watcherExclude"])
        tm.that(watchers, has=f"**/{file.name}")
        tm.that(watchers, lacks=f"**/{file.name}/**")
        tm.that(watchers, has=f"**/{directory.name}/**")
        tm.that(f"**/{file.name}" in elected.analyzer_exclude_globs, eq=True)
        self._write_settings(tmp_path, rendered)
        tm.that(
            tm.ok(
                FlextInfraCodegenVscodeMixin.render_vscode_settings(
                    tmp_path, codegen=elected
                )
            ),
            eq=rendered,
        )

    def test_retired_language_keys_leave_custom_preferences_intact(
        self, tmp_path: Path
    ) -> None:
        """Remove obsolete owned entries without replacing language preferences."""
        retired = config.Infra.codegen.vscode.stripped_map_keys
        settings = {
            language: {
                **dict.fromkeys(keys, True),
                "editor.rulers": [88],
            }
            for language, keys in retired.items()
        }
        self._write_settings(tmp_path, tm.ok(u.Cli.json_dumps(settings)))
        rendered = tm.ok(FlextInfraCodegenVscodeMixin.render_vscode_settings(tmp_path))
        document = u.Tests.json_payload(rendered)
        for language, keys in retired.items():
            preferences = u.Tests.toml_mapping(document[language])
            tm.that(preferences["editor.rulers"], eq=[88])
            tm.that(set(keys).isdisjoint(preferences), eq=True)
