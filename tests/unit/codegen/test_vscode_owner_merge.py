"""Owner-merge dispatch for governed .vscode/settings.json artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, c, config, infra, t
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.services.codegen import FlextInfraCodegen
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import m, tm, u


class TestsFlextInfraVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    @staticmethod
    def test_scoped_config_uses_project_then_local_layers(tmp_path: Path) -> None:
        """Two injected repositories retain independent committed and local choices."""
        key = "python.analysis.userFileIndexingLimit"
        baseline = u.type_adapter(int).validate_python(
            config.Infra.codegen.vscode.scalar_settings[key],
        )
        project_choice = baseline + 7
        local_choice = baseline + 13
        other_choice = baseline + 23
        first = tmp_path / "first"
        second = tmp_path / "second"
        for root, chosen in ((first, project_choice), (second, other_choice)):
            directory = root / c.CONFIG_DIR_NAME
            directory.mkdir(parents=True)
            tm.ok(
                u.Cli.yaml_dump(
                    directory / c.Infra.CODEGEN_CONFIG_FILENAME,
                    {
                        "Infra": {
                            "codegen": {"vscode": {"scalar_settings": {key: chosen}}}
                        }
                    },
                ),
            )
        local = (
            first
            / c.CONFIG_DIR_NAME
            / Path(c.Infra.CODEGEN_CONFIG_FILENAME).with_name(
                f"{Path(c.Infra.CODEGEN_CONFIG_FILENAME).stem}.local.yaml",
            )
        )
        tm.ok(
            u.Cli.yaml_dump(
                local,
                {
                    "Infra": {
                        "codegen": {"vscode": {"scalar_settings": {key: local_choice}}}
                    }
                },
            ),
        )
        chosen = tm.ok(FlextInfraCodegen.load_vscode_spec(first))
        other = tm.ok(FlextInfraCodegen.load_vscode_spec(second))
        tm.that(chosen.scalar_settings[key], eq=local_choice)
        tm.that(other.scalar_settings[key], eq=other_choice)
        tm.that(
            FlextInfraConfig.config_sources_for_repository(
                first,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )[-2:],
            eq=(first / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME, local),
        )

    @staticmethod
    def test_runtime_surface_creates_only_declared_binding_outputs(
        tmp_path: Path,
    ) -> None:
        """The real apply entry keeps setup binding separate from source generation."""
        root = tmp_path / "project"
        workspace = u.Tests.standalone_workspace(root)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.RUNTIME_BINDINGS,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        published = tm.ok(infra.codegen_conform(request, initial_workspace=workspace))
        targets = {
            root / entry.path
            for entry in config.Infra.codegen.managed_files
            if entry.runtime_binding
        }
        tm.that({file.path for file in published.plan.files}, eq=targets)
        tm.that(set(published.written_files).issubset(targets), eq=True)
        checked = request.model_copy(
            update={"mode": c.Infra.CodegenConformMode.CHECK},
        )
        tm.ok(infra.codegen_conform(checked, initial_workspace=workspace))

    @staticmethod
    def test_invalid_member_config_keeps_valid_workspace_binding(
        tmp_path: Path,
    ) -> None:
        """A rejected member declaration preserves the native cause and valid sibling."""
        root = tmp_path / "parent"
        member = u.Tests.WorktreeFixture.copied_member(
            root,
            "fixture-parent",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member,
            distribution="fixture-member",
            relative_path=member.relative_to(root).as_posix(),
        )
        directory = member / c.CONFIG_DIR_NAME
        directory.mkdir(exist_ok=True)
        local = directory / Path(c.Infra.CODEGEN_CONFIG_FILENAME).with_name(
            "codegen.local.yaml",
        )
        tm.ok(
            u.Cli.yaml_dump(
                local,
                {
                    "Infra": {
                        "codegen": {
                            "vscode": {
                                "scalar_settings": {
                                    "operator.invalid": {"cannot": "be a scalar"},
                                },
                            },
                        },
                    },
                },
            ),
        )
        rejected = infra.codegen_conform(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.RUNTIME_BINDINGS,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )
        tm.fail(rejected)
        tm.that(rejected.exception, is_=ValueError)
        with pytest.raises(RuntimeError) as raised:
            rejected.unwrap()
        tm.that(raised.value.__cause__, eq=rejected.exception)
        settings_path = root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        settings = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(
                u.Cli.json_parse(settings_path.read_text(encoding=c.DEFAULT_ENCODING))
            ),
        )
        interpreter = u.type_adapter(str).validate_python(
            settings["python.defaultInterpreterPath"],
        )
        tm.that(
            (root / interpreter.removeprefix("${workspaceFolder}/")).resolve(),
            eq=u.Infra.runtime_python(root),
        )
        tm.that(local.is_file(), eq=True)

    @staticmethod
    def test_runtime_binding_rejects_versioned_policy() -> None:
        """A physical runtime binding cannot masquerade as a portable source."""
        governed = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        with pytest.raises(ValueError, match="runtime binding must be runtime-local"):
            m.Infra.ManagedFileSpec.model_validate({
                **governed.model_dump(),
                "tracking": "versioned",
                "runtime_binding": True,
            })

    @staticmethod
    def test_runtime_ignore_projection_follows_declared_paths(tmp_path: Path) -> None:
        """Git consumes a local-artifact rule derived from an arbitrary declaration."""
        root = tmp_path / "project"
        root.mkdir()
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        path = Path("generated") / "runtime.json"
        artifact = m.Infra.ManagedFileSpec(
            path=path,
            owner=c.Infra.CODEGEN_OWNER_VSCODE,
            policy="merge",
            tracking="runtime-local",
        )
        codegen = config.Infra.codegen.model_copy(
            update={"managed_files": (artifact,)},
        )
        rendered = tm.ok(
            u.Infra.render_project_gitignore(
                codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
            ),
        )
        (root / c.Infra.GITIGNORE).write_text(rendered, encoding=c.DEFAULT_ENCODING)
        ignored = tm.ok(
            u.Cli.run(
                (c.Infra.GIT, "check-ignore", "--no-index", path.as_posix()),
                cwd=root,
            ),
        )
        tm.that(ignored.stdout.strip(), eq=path.as_posix())

    @staticmethod
    def test_runtime_selection_plans_missing_declared_bindings(
        tmp_path: Path,
    ) -> None:
        """Binding-only planning creates absent outputs through their actual owner."""
        root = tmp_path / "project"
        workspace = u.Tests.standalone_workspace(root)
        target = tm.ok(FlextInfraWorkspaceDetector.conform_target(root, workspace))
        declared = tuple(
            item
            for item in config.Infra.codegen.managed_files
            if item.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        codegen = config.Infra.codegen.model_copy(
            update={"managed_files": declared},
        )
        planner = FlextInfraCodegenConform(repository_root=root)
        plans = tm.ok(planner.plan_runtime_bindings(target, codegen))
        expected = {root / item.path for item in declared if item.runtime_binding}
        tm.that({plan.path for plan in plans}, eq=expected)
        for plan in plans:
            tm.that(plan.desired_content, is_=bytes)
            tm.that(u.Infra.codegen_file_requires_effect(plan), eq=True)

    @staticmethod
    def test_explicit_settings_preserve_local_custom_content(tmp_path: Path) -> None:
        """A typed resolved project spec keeps local keys outside its ownership."""
        root = tmp_path / "project"
        path = root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        path.parent.mkdir(parents=True)
        original = '{"workbench.colorTheme": "operator-theme"}\n'
        path.write_text(original, encoding=c.DEFAULT_ENCODING)
        spec = config.Infra.codegen.vscode.model_copy(
            update={
                "scalar_settings": {
                    **config.Infra.codegen.vscode.scalar_settings,
                    "editor.fontLigatures": True,
                },
            },
        )
        rendered = tm.ok(
            FlextInfraCodegen.render_vscode_settings(
                root,
                runtime_root=root,
                spec=spec,
            ),
        )
        settings = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(rendered)),
        )
        tm.that(settings["editor.fontLigatures"], eq=True)
        tm.that(settings["workbench.colorTheme"], eq="operator-theme")
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

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
            if key == "python.defaultInterpreterPath":
                interpreter = u.type_adapter(str).validate_python(doc[key])
                projected = root / interpreter.removeprefix("${workspaceFolder}/")
                tm.that(projected.resolve(), eq=u.Infra.runtime_python(root))
            elif key == "pyrefly.lspPath":
                executable = u.type_adapter(str).validate_python(doc[key])
                projected = root / executable.removeprefix("${workspaceFolder}/")
                tm.that(
                    projected.parent.resolve(),
                    eq=u.Infra.runtime_python(root).parent,
                )
            else:
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
        path = member / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.atomic_write_text_file(
                path,
                tm.ok(
                    u.Cli.json_dumps({
                        "terminal.integrated.env.linux": {
                            "PATH": "${workspaceFolder}/.venv/bin:${env:PATH}",
                            "VIRTUAL_ENV": "${workspaceFolder}/.venv",
                        },
                        "ruff.interpreter": ["${workspaceFolder}/.venv/bin/python"],
                        "ruff.path": ["${workspaceFolder}/.venv/bin/ruff"],
                        "operator.note": (
                            "${workspaceFolder}/.venv-is-not-the-environment"
                        ),
                    }),
                ),
            ),
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
        executable = u.type_adapter(str).validate_python(doc["pyrefly.lspPath"])
        projected_tool = member / executable.removeprefix("${workspaceFolder}/")
        tm.that(
            projected_tool.parent.resolve(),
            eq=u.Infra.runtime_python(member).parent,
        )
        terminal = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            doc["terminal.integrated.env.linux"],
        )
        environment = u.type_adapter(str).validate_python(terminal["VIRTUAL_ENV"])
        tm.that(
            (member / environment.removeprefix("${workspaceFolder}/")).resolve(),
            eq=u.Infra.runtime_environment_dir(member),
        )
        interpreter_list = u.type_adapter(t.StrSequence).validate_python(
            doc["ruff.interpreter"],
        )
        tm.that(
            (
                member / interpreter_list[0].removeprefix("${workspaceFolder}/")
            ).resolve(),
            eq=u.Infra.runtime_python(member),
        )
        tm.that(
            doc["operator.note"],
            eq="${workspaceFolder}/.venv-is-not-the-environment",
        )
        tm.that(str(tmp_path) in rendered, eq=False)
