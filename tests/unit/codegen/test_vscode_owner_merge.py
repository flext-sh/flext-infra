"""Owner-merge dispatch for governed .vscode/settings.json artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from yaml.parser import ParserError

from flext_infra import FlextInfraConfig, c, config, infra, t
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.services.codegen import FlextInfraCodegen
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import m, tm, u


class TestsFlextInfraVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    @staticmethod
    def test_full_config_loader_binds_policy_and_captured_projection(
        tmp_path: Path,
    ) -> None:
        """Gate policy and editor settings share an explicit root and source receipt."""
        root = tmp_path / "consumer"
        directory = root / c.CONFIG_DIR_NAME
        directory.mkdir(parents=True)
        path = directory / c.Infra.CODEGEN_CONFIG_FILENAME
        baseline = c.Infra.GateAcceptancePolicy(
            config.Infra.codegen.make.gate_acceptance_policy,
        )
        chosen = next(
            policy for policy in c.Infra.GateAcceptancePolicy if policy != baseline
        )
        tm.ok(
            u.Cli.yaml_dump(
                path,
                {
                    "Infra": {
                        "codegen": {"make": {"gate_acceptance_policy": chosen.value}}
                    }
                },
            ),
        )
        captured = tm.ok(u.Infra.load_codegen_inputs(root))
        tm.that(captured.spec.make.gate_acceptance_policy, eq=chosen)
        tm.that(
            tm.ok(FlextInfraCodegen.load_vscode_spec(root)),
            eq=captured.spec.vscode,
        )
        tm.ok(
            u.Cli.yaml_dump(
                path,
                {
                    "Infra": {
                        "codegen": {"make": {"gate_acceptance_policy": baseline.value}}
                    }
                },
            ),
        )
        projected = tm.ok(u.Infra.project_codegen_inputs(root, captured))
        tm.that(projected.spec.make.gate_acceptance_policy, eq=chosen)
        fresh = tm.ok(u.Infra.load_codegen_inputs(root))
        tm.that(fresh.spec.make.gate_acceptance_policy, eq=baseline)
        tm.that(projected.sources, eq=captured.sources)

    @staticmethod
    def test_repository_policy_does_not_admit_unrelated_editor_policy(
        tmp_path: Path,
    ) -> None:
        """Topology validates its own policy while editor rejection retains its cause."""
        directory = tmp_path / c.CONFIG_DIR_NAME
        directory.mkdir()
        path = directory / c.Infra.CODEGEN_CONFIG_FILENAME
        tm.ok(
            u.Cli.yaml_dump(
                path,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {"read_only": True},
                            "vscode": {"unrecognized_setting": True},
                        }
                    },
                },
            )
        )
        declaration = tm.ok(u.Infra.load_repository_declaration_inputs(tmp_path))
        tm.that(declaration.spec.read_only, eq=True)
        tm.that(path in {state.path for state in declaration.sources}, eq=True)
        complete = u.Infra.load_codegen_inputs(tmp_path)
        tm.that(complete.failure, eq=True)
        tm.that(complete.exception is not None, eq=True)
        tm.ok(
            u.Cli.yaml_dump(
                path,
                {
                    "Infra": {"codegen": {"repository": {"unknown_policy": True}}},
                },
            )
        )
        invalid = u.Infra.load_repository_declaration_inputs(tmp_path)
        tm.that(invalid.failure, eq=True)
        tm.that(invalid.exception is not None, eq=True)

    @staticmethod
    def test_captured_yaml_values_are_isolated_and_new_bytes_revalidated() -> None:
        """Memoized parsing never shares mutable values or accepts malformed edits."""
        original = b"Infra:\n  values:\n    nested: [first]\n"
        first = tm.ok(u.Infra.read_codegen_config_document(original))
        nested = t.Cli.JSON_MAPPING_ADAPTER.validate_python(first["Infra"])
        values = t.Cli.JSON_MAPPING_ADAPTER.validate_python(nested["values"])
        assert isinstance(first, dict)
        first["Infra"] = {"values": {"nested": ["changed"]}}
        again = tm.ok(u.Infra.read_codegen_config_document(original))
        tm.that(again, eq={"Infra": {"values": {"nested": ["first"]}}})
        tm.that(values["nested"], eq=["first"])
        malformed = b"Infra: [\n"
        with pytest.raises(ParserError):
            u.Infra.read_codegen_config_document(malformed)
        corrected = tm.ok(
            u.Infra.read_codegen_config_document(
                b"Infra:\n  values:\n    nested: [second]\n",
            )
        )
        tm.that(corrected, eq={"Infra": {"values": {"nested": ["second"]}}})

    @staticmethod
    def test_portable_declaration_rejects_unrepresentable_list_replacement(
        tmp_path: Path,
    ) -> None:
        """The config concatenation contract cannot silently remove prior entries."""
        key = "extension.scopes"
        spec = m.Infra.CodegenVscodeSpec.model_validate({
            **config.Infra.codegen.vscode.model_dump(),
            "list_settings": {key: ("parent",)},
        })
        planned = FlextInfraCodegen.vscode_declaration_delta(
            tmp_path,
            {key: ["child"]},
            spec=spec,
            runtime_root=tmp_path,
        )
        tm.fail(planned)
        tm.that(planned.exception, is_=ValueError)

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
    def test_runtime_binding_second_apply_preserves_physical_state(
        tmp_path: Path,
    ) -> None:
        """Applying the public binding twice settles without replacing any file."""
        root = tmp_path / "project"
        workspace = u.Tests.standalone_workspace(root)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.RUNTIME_BINDINGS,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        first = tm.ok(infra.codegen_conform(request, initial_workspace=workspace))
        before = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(file.path, required=True))
            for file in first.plan.files
        )
        tm.that(bool(before), eq=True)

        second = tm.ok(infra.codegen_conform(request, initial_workspace=workspace))

        tm.that(second.written_files, eq=())
        tm.that(
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(state.path, required=True))
                for state in before
            ),
            eq=before,
        )

    @staticmethod
    def test_invalid_member_config_keeps_valid_workspace_binding(
        tmp_path: Path,
    ) -> None:
        """A rejected member declaration preserves the cause and valid sibling."""
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
        u.Tests.WorktreeFixture.write_beads_project(
            member,
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        directory = member / c.CONFIG_DIR_NAME
        directory.mkdir(exist_ok=True)
        local = directory / Path(c.Infra.CODEGEN_CONFIG_FILENAME).with_name(
            f"{Path(c.Infra.CODEGEN_CONFIG_FILENAME).stem}.local.yaml",
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
        tm.that(rejected.exception, is_=ValueError, msg=rejected.error)
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
                **governed.model_dump(round_trip=True),
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
    def _assert_workspace_runtime_projections(member: Path, doc: t.JsonMapping) -> None:
        """Assert rendered settings resolve to the member's physical runtime."""
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
        interpreter_list: t.StrSequence = u.type_adapter(list[str]).validate_python(
            doc["ruff.interpreter"],
        )
        tm.that(
            (
                member / interpreter_list[0].removeprefix("${workspaceFolder}/")
            ).resolve(),
            eq=u.Infra.runtime_python(member),
        )

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
        original = path.read_text(encoding=c.DEFAULT_ENCODING)
        rendered = tm.ok(FlextInfraCodegen.render_vscode_settings(member))
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(rendered)),
        )
        TestsFlextInfraVscodeOwnerMerge._assert_workspace_runtime_projections(
            member,
            doc,
        )
        tm.that(
            doc["operator.note"],
            eq="${workspaceFolder}/.venv-is-not-the-environment",
        )
        tm.that(str(tmp_path) in rendered, eq=False)
        migrated = tm.ok(
            FlextInfraCodegen.vscode_declaration_delta(
                member,
                doc,
                spec=tm.ok(FlextInfraCodegen.load_vscode_spec(member)),
            ),
        )
        declaration = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            migrated.values["additional_settings"],
        )
        portable_terminal = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            declaration["terminal.integrated.env.linux"],
        )
        tm.that(
            portable_terminal["VIRTUAL_ENV"],
            eq=f"${{workspaceFolder}}/{c.Infra.ENVIRONMENT_DIRECTORY}",
        )
        standalone = tmp_path / "standalone"
        config_dir = standalone / c.CONFIG_DIR_NAME
        config_dir.mkdir(parents=True)
        tm.ok(
            u.Cli.yaml_dump(
                config_dir / c.Infra.CODEGEN_CONFIG_FILENAME,
                {"Infra": {"codegen": {"vscode": dict(migrated.values)}}},
            ),
        )
        standalone_rendered = tm.ok(
            FlextInfraCodegen.render_vscode_settings(
                standalone,
                runtime_root=standalone,
            ),
        )
        standalone_doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(standalone_rendered)),
        )
        tm.that(
            standalone_doc["terminal.integrated.env.linux"],
            eq=portable_terminal,
        )
        tm.that(standalone_doc["ruff.interpreter"], eq=declaration["ruff.interpreter"])
        tm.that(standalone_doc["operator.note"], eq=doc["operator.note"])
        tm.that(
            path.read_text(encoding=c.DEFAULT_ENCODING),
            eq=original,
        )
