"""Canonical VS Code settings codegen merge contract tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, t, tm, u


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
        project_root = u.Tests.git_repository(tmp_path, "project")
        canonical = u.Tests.json_payload(
            tm.ok(
                FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)
            )
        )
        self._write_settings(
            project_root,
            tm.ok(
                u.Cli.json_dumps({
                    "python.languageServer": "None",
                    "python.analysis.typeCheckingMode": c.ParserBooleanToken.OFF,
                    "files.exclude": {"**/.retired-cache": True},
                    "python.analysis.diagnosticSeverityOverrides": {
                        "reportUnknownMemberType": "none",
                    },
                }),
            )
            + "\n",
        )

        result = FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)
        tm.ok(result)
        doc = u.Tests.json_payload(result.value)
        tm.fail("python.analysis.typeCheckingMode" in doc)
        tm.fail("python.analysis.diagnosticSeverityOverrides" in doc)
        declared = FlextInfraCodegenConform.Generate.vscode_settings(
            config.Infra.codegen.vscode
        )
        interpreter = "python.defaultInterpreterPath"
        tm.that(doc[interpreter], eq=canonical[interpreter])
        search_paths_key = c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
        tm.that(doc[search_paths_key], eq=canonical[search_paths_key])
        excludes = u.Tests.toml_mapping(doc["files.exclude"])
        tm.fail("**/.retired-cache" in excludes)
        tm.that(excludes, eq=dict(config.Infra.codegen.vscode_files_exclude_map))
        tm.that(
            doc["python.languageServer"],
            eq=declared["python.languageServer"],
        )

    def test_strips_retired_keys_owning_pyright_config(self, tmp_path: Path) -> None:
        """Strip keys owned by [tool.pyright] to avoid Pylance warnings."""
        project_root = u.Tests.git_repository(tmp_path, "project")
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

        result = FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)

        tm.ok(result)
        doc = u.Tests.json_payload(result.value)
        tm.fail("python.analysis.typeCheckingMode" in doc)
        tm.fail("python.analysis.diagnosticSeverityOverrides" in doc)
        tm.that(
            doc["python.languageServer"],
            eq=FlextInfraCodegenConform.Generate.vscode_settings(
                config.Infra.codegen.vscode
            )["python.languageServer"],
        )

    def test_render_reaches_fixed_point(self, tmp_path: Path) -> None:
        """Rendering a document that was already rendered produces no drift."""
        project_root = u.Tests.git_repository(tmp_path, "project")

        first = FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)
        tm.ok(first)
        self._write_settings(project_root, first.value)
        second = FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)
        tm.ok(second)
        tm.that(second.value, eq=first.value)

    @staticmethod
    def test_workspace_root_and_standalone_bind_their_own_environment(
        tmp_path: Path,
    ) -> None:
        """Both environment owners render the same portable relative bindings."""
        project_root = u.Tests.git_repository(tmp_path, "workspace")
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

        result = FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)
        standalone_root = u.Tests.git_repository(tmp_path, "standalone")
        standalone = FlextInfraCodegenConform.Generate.render_vscode_settings(
            standalone_root
        )

        tm.ok(result)
        tm.ok(standalone)
        tm.that(result.value.encode(), eq=standalone.value.encode())
        doc = u.Tests.json_payload(result.value)
        interpreter = u.type_adapter(str).validate_python(
            doc["python.defaultInterpreterPath"]
        )
        selected = Path(interpreter.replace("${workspaceFolder}", str(project_root)))
        tm.that(
            selected.parent.parent.resolve(),
            eq=(project_root / c.Infra.ENVIRONMENT_DIRECTORY).resolve(),
        )

    def test_invalid_json_fails_without_producing_a_document(
        self,
        tmp_path: Path,
    ) -> None:
        """Return a typed failure when the existing settings are unparseable."""
        project_root = u.Tests.git_repository(tmp_path, "project")
        self._write_settings(project_root, "{ invalid json")

        result = FlextInfraCodegenConform.Generate.render_vscode_settings(project_root)

        tm.fail(result)
        tm.that(result.error, none=False)

    def test_project_artifacts_control_all_editor_exclusions(
        self, tmp_path: Path
    ) -> None:
        """Use the elected project catalog for file and directory exclusions."""
        u.Tests.initialize_git_repo(tmp_path)
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
            FlextInfraCodegenConform.Generate.render_vscode_settings(
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
        tm.ok(f"**/{file.name}" in elected.analyzer_exclude_globs)
        self._write_settings(tmp_path, rendered)
        tm.that(
            tm.ok(
                FlextInfraCodegenConform.Generate.render_vscode_settings(
                    tmp_path, codegen=elected
                )
            ),
            eq=rendered,
        )

    def test_retired_language_keys_leave_custom_preferences_intact(
        self, tmp_path: Path
    ) -> None:
        """Remove obsolete owned entries without replacing language preferences."""
        u.Tests.initialize_git_repo(tmp_path)
        retired = config.Infra.codegen.vscode.stripped_map_keys
        settings: t.JsonDict = {
            language: {
                **dict.fromkeys(keys, True),
                "editor.rulers": [88],
            }
            for language, keys in retired.items()
        }
        self._write_settings(tmp_path, tm.ok(u.Cli.json_dumps(settings)))
        rendered = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(tmp_path)
        )
        document = u.Tests.json_payload(rendered)
        for language, keys in retired.items():
            preferences = u.Tests.toml_mapping(document[language])
            tm.that(preferences["editor.rulers"], eq=[88])
            tm.ok(set(keys).isdisjoint(preferences))

    @staticmethod
    def test_unfamiliar_settings_accept_recursive_json_and_preserve_array_order(
        tmp_path: Path,
    ) -> None:
        """Settings remain generic JSON values with deterministic object ordering."""
        u.Tests.initialize_git_repo(tmp_path)
        values: t.JsonMapping = {
            "operator.enabled": True,
            "operator.ratio": 0.75,
            "operator.unset": None,
            "operator.nested": {"zeta": [3, 1], "alpha": {"second": False}},
            "operator.items": [{"name": "second"}, {"name": "first"}],
        }
        specification = m.Infra.CodegenVscodeSpec.model_validate({
            **config.Infra.codegen.vscode.model_dump(),
            "settings": (*config.Infra.codegen.vscode.settings, *values.items()),
        })
        rendered = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(
                tmp_path, spec=specification
            )
        )
        document = u.Tests.json_payload(rendered)
        for key, value in values.items():
            tm.that(document[key], eq=value)
        tm.that(list(document), eq=sorted(document))
        nested = u.Tests.toml_mapping(document["operator.nested"])
        tm.that(list(nested), eq=sorted(nested))
        tm.that(
            FlextInfraCodegenConform.Generate.vscode_settings(specification)[
                "operator.items"
            ],
            eq=values["operator.items"],
        )

    @staticmethod
    def test_retired_setting_removal_wins_over_declared_values(
        tmp_path: Path,
    ) -> None:
        """The explicit removal declaration wins even over the final setting pair."""
        u.Tests.initialize_git_repo(tmp_path)
        key = "operator.retiredSetting"
        specification = m.Infra.CodegenVscodeSpec.model_validate({
            **config.Infra.codegen.vscode.model_dump(),
            "settings": (*config.Infra.codegen.vscode.settings, (key, True)),
            "stripped_keys": (*config.Infra.codegen.vscode.stripped_keys, key),
        })
        rendered = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(
                tmp_path, spec=specification
            )
        )
        tm.that(u.Tests.json_payload(rendered), lacks=key)

    def test_explicit_map_union_accepts_recursive_json_and_preserves_local_keys(
        self, tmp_path: Path
    ) -> None:
        """An explicitly merged map supports JSON values beyond scalar options."""
        u.Tests.initialize_git_repo(tmp_path)
        key = "[fixture]"
        local: t.JsonDict = {"operator.local": [{"name": "retained"}]}
        declared: t.JsonMapping = {
            "operator.unset": None,
            "operator.weight": 0.25,
            "operator.nested": {"items": [{"name": "last"}, {"name": "first"}]},
        }
        self._write_settings(tmp_path, tm.ok(u.Cli.json_dumps({key: local})))
        specification = m.Infra.CodegenVscodeSpec.model_validate({
            **config.Infra.codegen.vscode.model_dump(),
            "map_union_settings": {
                **config.Infra.codegen.vscode.map_union_settings,
                key: declared,
            },
        })
        rendered = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(
                tmp_path, spec=specification
            )
        )
        tm.that(
            u.Tests.json_payload(rendered)[key],
            eq={**local, **declared},
        )

    def test_explicit_setting_pair_replaces_a_default_merged_map(
        self, tmp_path: Path
    ) -> None:
        """An explicit JSON value owns its full map after default map unions."""
        u.Tests.initialize_git_repo(tmp_path)
        key = "[fixture]"
        self._write_settings(
            tmp_path,
            tm.ok(u.Cli.json_dumps({key: {"operator.local": True}})),
        )
        replacement: t.JsonMapping = {"operator.items": ["second", "first"]}
        specification = m.Infra.CodegenVscodeSpec.model_validate({
            **config.Infra.codegen.vscode.model_dump(),
            "settings": (*config.Infra.codegen.vscode.settings, (key, replacement)),
            "map_union_settings": {
                **config.Infra.codegen.vscode.map_union_settings,
                key: {"operator.default": True},
            },
        })
        rendered = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(
                tmp_path, spec=specification
            )
        )
        tm.that(u.Tests.json_payload(rendered)[key], eq=replacement)
