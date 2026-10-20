"""Owner-merge dispatch for governed .vscode/settings.json artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, c, config, infra
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.services._codegen import (
    FlextInfraCodegenVscodeMixin as FlextInfraCodegen,
)
from tests import m, t, tm, u


class TestsFlextInfraVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    @staticmethod
    def test_shared_editor_defaults_need_no_repository_override(tmp_path: Path) -> None:
        """An absent or redundant project layer renders the same portable defaults."""
        root = tmp_path / "standalone"
        directory = root / c.CONFIG_DIR_NAME
        directory.mkdir(parents=True)
        baseline = tm.ok(FlextInfraCodegen.load_vscode_spec(root))
        inherited = tm.ok(
            FlextInfraCodegen.render_vscode_settings(
                root,
                spec=baseline,
            ),
        )
        tm.that(
            FlextInfraCodegen.vscode_settings(baseline),
            eq=FlextInfraCodegen.vscode_settings(config.Infra.codegen.vscode),
        )
        tm.ok(
            u.Cli.yaml_dump(
                directory / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "vscode": {
                                "settings": baseline.settings,
                            },
                        },
                    },
                },
            ),
        )
        explicit = tm.ok(FlextInfraCodegen.load_vscode_spec(root))
        tm.that(
            FlextInfraCodegen.vscode_settings(explicit),
            eq=FlextInfraCodegen.vscode_settings(baseline),
        )
        tm.that(
            tm.ok(
                FlextInfraCodegen.render_vscode_settings(
                    root,
                    spec=explicit,
                ),
            ),
            eq=inherited,
        )
        document = tm.ok(FlextInfraCodegen.parse_vscode_settings(inherited))
        delta = tm.ok(
            FlextInfraCodegen.vscode_declaration_delta(
                root,
                document,
                spec=baseline,
            ),
        )
        tm.that(delta.values, eq={})

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
        """Topology validates its policy while editor rejection retains its cause."""
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
        nested = u.Cli.JSON_MAPPING_ADAPTER.validate_python(first["Infra"])
        values = u.Cli.JSON_MAPPING_ADAPTER.validate_python(nested["values"])
        mutable = tm.not_none(
            first if isinstance(first, dict) else None,
            msg="the parsed document is the caller's own mutable mapping",
        )
        mutable["Infra"] = {"values": {"nested": ["changed"]}}
        again = tm.ok(u.Infra.read_codegen_config_document(original))
        tm.that(again, eq={"Infra": {"values": {"nested": ["first"]}}})
        tm.that(values["nested"], eq=["first"])
        malformed = b"Infra: [\n"
        with pytest.raises(u.Yaml.YAMLError):
            u.Infra.read_codegen_config_document(malformed)
        corrected = tm.ok(
            u.Infra.read_codegen_config_document(
                b"Infra:\n  values:\n    nested: [second]\n",
            )
        )
        tm.that(corrected, eq={"Infra": {"values": {"nested": ["second"]}}})

    @staticmethod
    @pytest.mark.parametrize("replacement", [["child", "parent"], []])
    def test_portable_declaration_replaces_lists_in_exact_order(
        tmp_path: Path,
        replacement: t.JsonValue,
    ) -> None:
        """A setting pair replaces an array completely, including its empty value."""
        key = "extension.scopes"
        spec = m.Infra.CodegenVscodeSpec.model_validate({
            **config.Infra.codegen.vscode.model_dump(),
            "settings": (
                *config.Infra.codegen.vscode.settings,
                (key, ["parent", "retired"]),
            ),
        })
        planned = tm.ok(
            FlextInfraCodegen.vscode_declaration_delta(
                tmp_path,
                {key: replacement},
                spec=spec,
            )
        )
        tm.that(planned.values, eq={"settings": [[key, replacement]]})
        composed = tm.ok(FlextInfraCodegen.compose_vscode_delta(spec, planned))
        rendered = tm.ok(
            FlextInfraCodegen.render_vscode_settings(tmp_path, spec=composed)
        )
        tm.that(u.Tests.json_payload(rendered)[key], eq=replacement)

    @staticmethod
    def test_scoped_config_uses_project_then_local_layers(tmp_path: Path) -> None:
        """Two injected repositories retain independent committed and local choices."""
        key = "python.analysis.userFileIndexingLimit"
        baseline = u.type_adapter(int).validate_python(
            FlextInfraCodegen.vscode_settings(config.Infra.codegen.vscode)[key],
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
                    {"Infra": {"codegen": {"vscode": {"settings": [[key, chosen]]}}}},
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
                {"Infra": {"codegen": {"vscode": {"settings": [[key, local_choice]]}}}},
            ),
        )
        chosen = tm.ok(FlextInfraCodegen.load_vscode_spec(first))
        other = tm.ok(FlextInfraCodegen.load_vscode_spec(second))
        tm.that(FlextInfraCodegen.vscode_settings(chosen)[key], eq=local_choice)
        tm.that(FlextInfraCodegen.vscode_settings(other)[key], eq=other_choice)
        tm.that(
            FlextInfraConfig.config_sources_for_repository(
                first,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )[-2:],
            eq=(first / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME, local),
        )

    @staticmethod
    def test_generic_setting_layers_replace_values_without_merging_arrays(
        tmp_path: Path,
    ) -> None:
        """Project and local pairs retain complete, last-pair-owned JSON values."""
        root = tmp_path / "project"
        directory = root / c.CONFIG_DIR_NAME
        directory.mkdir(parents=True)
        key = "extension.scopes"
        project = directory / c.Infra.CODEGEN_CONFIG_FILENAME
        local = project.with_name(f"{project.stem}.local.yaml")
        tm.ok(
            u.Cli.yaml_dump(
                project,
                {
                    "Infra": {
                        "codegen": {
                            "vscode": {
                                "settings": [
                                    [key, ["project", "removed"]],
                                    ["operator.payload", {"removed": [1, 2]}],
                                ]
                            }
                        }
                    }
                },
            )
        )
        values: t.JsonMapping = {
            key: [],
            "operator.payload": {
                "enabled": True,
                "ratio": 0.5,
                "unset": None,
                "items": [{"name": "second"}, {"name": "first"}],
            },
        }
        tm.ok(
            u.Cli.yaml_dump(
                local,
                {"Infra": {"codegen": {"vscode": {"settings": list(values.items())}}}},
            )
        )
        elected = tm.ok(FlextInfraCodegen.load_vscode_spec(root))
        rendered = tm.ok(FlextInfraCodegen.render_vscode_settings(root, spec=elected))
        document = u.Tests.json_payload(rendered)
        for name, value in values.items():
            tm.that(FlextInfraCodegen.vscode_settings(elected)[name], eq=value)
            tm.that(document[name], eq=value)

    @staticmethod
    def test_generic_declaration_delta_round_trips_null_and_nested_values(
        tmp_path: Path,
    ) -> None:
        """Portable deltas preserve unfamiliar JSON values, including explicit null."""
        values: t.JsonMapping = {
            "operator.empty": None,
            "operator.payload": {
                "enabled": False,
                "weight": 1.25,
                "rules": [{"name": "last"}, {"name": "first"}],
            },
        }
        specification = config.Infra.codegen.vscode
        delta = tm.ok(
            FlextInfraCodegen.vscode_declaration_delta(
                tmp_path, values, spec=specification
            )
        )
        composed = tm.ok(FlextInfraCodegen.compose_vscode_delta(specification, delta))
        rendered = tm.ok(
            FlextInfraCodegen.render_vscode_settings(tmp_path, spec=composed)
        )
        document = u.Tests.json_payload(rendered)
        for key, value in values.items():
            tm.that(document[key], eq=value)

    @staticmethod
    @pytest.mark.slow
    def test_generation_plans_missing_versioned_editor_settings(
        tmp_path: Path,
    ) -> None:
        """The public generation plan includes an absent versioned editor file."""
        root = tmp_path / "project"
        u.Tests.standalone_workspace(root)
        u.Tests.copy_tracked_mise_seeds(root)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.EDITOR,
            scope=c.Infra.CodegenConformScope.SELF,
        )
        plan = tm.ok(FlextInfraCodegenConform(repository_root=root).plan(request))
        governed = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        settings_path = root / governed.path
        file = next(item for item in plan.files if item.path == settings_path)
        tm.that(file.tracking, eq=governed.tracking)
        tm.that(settings_path.exists(), eq=False)
        tm.that(
            u.Tests.codegen_file_text(file),
            eq=tm.ok(FlextInfraCodegen.render_vscode_settings(root)),
        )

    @staticmethod
    @pytest.mark.slow
    def test_editor_generation_creates_missing_directory_and_converges(
        tmp_path: Path,
    ) -> None:
        """The public editor surface creates its files without a project venv."""
        root = tmp_path / "project"
        u.Tests.standalone_workspace(root)
        u.Tests.copy_tracked_mise_seeds(root)
        request = m.Infra.CodegenGenerateRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.EDITOR,
            scope=c.Infra.CodegenConformScope.SELF,
        )
        first = tm.ok(infra.codegen_generate(request))
        governed = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        tm.that(root / governed.path in first.written_files, eq=True)
        rendered = (root / governed.path).read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(rendered, eq=tm.ok(FlextInfraCodegen.render_vscode_settings(root)))
        second = tm.ok(infra.codegen_generate(request))
        tm.that(second.written_files, empty=True)
        tm.that((root / c.Infra.VENV_DIR).exists(), eq=False)

    @staticmethod
    def test_invalid_member_config_keeps_versioned_workspace_settings(
        tmp_path: Path,
    ) -> None:
        """An invalid member never changes the workspace's committed editor file."""
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
        settings_path = root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = tm.ok(FlextInfraCodegen.render_vscode_settings(root))
        settings_path.write_text(rendered, encoding=c.DEFAULT_ENCODING)
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
                                "settings": [["", {"invalid": "empty key"}]],
                            },
                        },
                    },
                },
            ),
        )
        rejected = infra.codegen_conform(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )
        tm.fail(rejected)
        tm.that(rejected.exception, is_=ValueError, msg=rejected.error)
        with pytest.raises(ValueError, match="settings") as raised:
            rejected.unwrap()
        tm.that(raised.value is rejected.exception, eq=True)
        tm.that(settings_path.read_text(encoding=c.DEFAULT_ENCODING), eq=rendered)
        tm.that(local.is_file(), eq=True)

    @staticmethod
    def test_editor_artifact_is_versioned() -> None:
        """The editor projection belongs in Git and is generated by make gen."""
        governed = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        tm.that(governed.tracking, eq="versioned")

    @staticmethod
    def test_git_sees_generated_editor_settings(tmp_path: Path) -> None:
        """The generated ignore rules leave the editor projection available to Git."""
        root = tmp_path / "project"
        root.mkdir()
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        governed = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        settings_path = root / governed.path
        settings_path.parent.mkdir(parents=True)
        settings_path.write_text(
            tm.ok(FlextInfraCodegen.render_vscode_settings(root)),
            encoding=c.DEFAULT_ENCODING,
        )
        (root / c.Infra.GITIGNORE).write_text(
            tm.ok(
                u.Infra.render_project_gitignore(
                    config.Infra.codegen,
                    profile=c.Infra.MakeProfile.STANDALONE,
                    project_name=root.name,
                ),
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        visible = tm.ok(
            u.Cli.run(
                (
                    c.Infra.GIT,
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                    "--",
                    governed.path.as_posix(),
                ),
                cwd=root,
            ),
        )
        tm.that(visible.stdout.strip(), eq=governed.path.as_posix())

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
    def test_explicit_settings_preserve_local_custom_content(tmp_path: Path) -> None:
        """A typed resolved project spec keeps local keys outside its ownership."""
        root = tmp_path / "project"
        path = root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        path.parent.mkdir(parents=True)
        original = '{"workbench.colorTheme": "operator-theme"}\n'
        path.write_text(original, encoding=c.DEFAULT_ENCODING)
        spec = config.Infra.codegen.vscode.model_copy(
            update={
                "settings": (
                    *config.Infra.codegen.vscode.settings,
                    ("editor.fontLigatures", True),
                ),
            },
        )
        rendered = tm.ok(
            FlextInfraCodegen.render_vscode_settings(
                root,
                spec=spec,
            ),
        )
        settings = u.Cli.JSON_MAPPING_ADAPTER.validate_json(rendered)
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
        doc = u.Cli.JSON_MAPPING_ADAPTER.validate_json(result.value)
        for key, expected_value in FlextInfraCodegen.vscode_settings(
            config.Infra.codegen.vscode
        ).items():
            if key in config.Infra.codegen.vscode.stripped_keys:
                continue
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
        tm.that(
            doc[search_paths_key],
            eq=FlextInfraCodegen.vscode_settings(config.Infra.codegen.vscode)[
                search_paths_key
            ],
        )

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
        doc = u.Cli.JSON_MAPPING_ADAPTER.validate_json(result.value)
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
        doc = u.Cli.JSON_MAPPING_ADAPTER.validate_json(result.value)
        tm.that("python.analysis.typeCheckingMode" in doc, eq=False)
        tm.that("python.analysis.diagnosticSeverityOverrides" in doc, eq=False)
        tm.that("ruff.nativeServer" in doc, eq=False)

    @staticmethod
    def test_attached_member_keeps_portable_opened_folder_settings(
        tmp_path: Path,
    ) -> None:
        """Attached and independent projects emit the same portable editor bytes."""
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
        doc = u.Cli.JSON_MAPPING_ADAPTER.validate_json(rendered)
        for key, expected in FlextInfraCodegen.vscode_settings(
            config.Infra.codegen.vscode
        ).items():
            if key in config.Infra.codegen.vscode.stripped_keys:
                continue
            tm.that(doc[key], eq=expected)
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
        tm.that(
            migrated.values["settings"],
            eq=[["operator.note", doc["operator.note"]]],
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
            ),
        )
        standalone_doc = u.Cli.JSON_MAPPING_ADAPTER.validate_json(standalone_rendered)
        tm.that(
            standalone_doc["terminal.integrated.env.linux"],
            eq=FlextInfraCodegen.vscode_settings(config.Infra.codegen.vscode)[
                "terminal.integrated.env.linux"
            ],
        )
        tm.that(
            standalone_doc["ruff.interpreter"],
            eq=FlextInfraCodegen.vscode_settings(config.Infra.codegen.vscode)[
                "ruff.interpreter"
            ],
        )
        tm.that(standalone_doc["operator.note"], eq=doc["operator.note"])
        tm.that(
            path.read_text(encoding=c.DEFAULT_ENCODING),
            eq=original,
        )
