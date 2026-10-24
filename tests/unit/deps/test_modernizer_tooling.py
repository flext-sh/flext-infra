"""Tooling phase tests for deps modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sysconfig
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path

import pytest
from typing_extensions import TypeForm

from flext_infra import FlextInfraConfig, check, config, deps
from tests import c, m, t, tm, u


class TestsFlextInfraDepsModernizerTooling:
    """Declarative tests for the Ruff phase and analyzer surface policy."""

    @staticmethod
    def _pairs(
        entries: Sequence[tuple[str, t.JsonValue]],
    ) -> list[t.JsonValue]:
        """Render native option pairs as YAML sequences.

        Returns:
            One two-element sequence per option pair.

        """
        return [[key, value] for key, value in entries]

    @staticmethod
    def _yaml_settings_payload(
        document: m.Infra.ToolConfigDocument,
    ) -> t.JsonDict:
        """Recreate YAML settings lists while retaining unrelated validated fields.

        Returns:
            A document payload exercising only the native settings ingress.

        """
        return document.model_dump(
            mode="json", by_alias=True, exclude_computed_fields=True
        )

    @staticmethod
    def test_native_settings_yaml_pairs_validate_as_tuples(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """YAML-shaped lists become tuples without changing native option values."""
        payload = TestsFlextInfraDepsModernizerTooling._yaml_settings_payload(
            tool_config_document,
        )
        validated = m.Infra.ToolConfigDocument.model_validate(payload)
        tm.that(validated.settings, eq=tool_config_document.settings)
        for pairs in validated.settings.values():
            tm.that(type(pairs), eq=tuple)
            for pair in pairs:
                tm.that(type(pair), eq=tuple)

    @staticmethod
    @pytest.mark.parametrize(
        ("table", "key", "value"),
        [
            ("pyright", "stubPath", "local_typing"),
            ("pyright", "options", {"stubPath": "local_typing"}),
            ("mypy", "custom_typeshed_dir", "local_typing"),
            ("pyrefly", "search-path", ["typings/vendor"]),
            ("stubgen", "output", "local_typing"),
        ],
    )
    def test_stub_options_are_rejected_through_real_tooling_layers(
        tmp_path: Path,
        table: str,
        key: str,
        value: t.JsonValue,
    ) -> None:
        """Project overlays cannot restore a local root, producer or nested override."""
        root = u.Tests.git_repository(tmp_path, "stub-policy")
        path = root / c.CONFIG_DIR_NAME / "tooling.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                path,
                {
                    "Infra": {"tooling": {"settings": {table: [[key, value]]}}},
                },
            )
        )
        tm.fail(u.Infra.load_tooling_inputs(root), has="Local stub")

    @staticmethod
    def test_stub_options_cannot_be_claimed_by_derived_settings(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Moving a forbidden native key to a derived layer grants no permission."""
        payload = {
            **tool_config_document.model_dump(
                by_alias=True, exclude_computed_fields=True
            ),
            "derived-settings": {
                **tool_config_document.derived_settings,
                "pyright": (
                    *tool_config_document.derived_settings["pyright"],
                    "stubPath",
                ),
            },
        }
        with pytest.raises(m.ValidationError, match="Local stub"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        "path", ["typings/vendor", "vendor-stubs", "stubs", "src/site-packages/stubs"]
    )
    def test_topology_cannot_reintroduce_local_stub_paths(
        tmp_path: Path,
        path: str,
    ) -> None:
        """Derived native search paths obey the same law as native option pairs."""
        root = u.Tests.git_repository(tmp_path, "path-policy")
        declaration = root / c.CONFIG_DIR_NAME / "tooling.yaml"
        declaration.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                declaration,
                {
                    "Infra": {
                        "tooling": {
                            "tools": {
                                "pyrefly": {
                                    "path-rules": {
                                        "project-shared-search-paths": [path]
                                    },
                                }
                            }
                        }
                    },
                },
            )
        )
        tm.fail(u.Infra.load_tooling_inputs(root), has="Local stub search roots")

    @staticmethod
    def test_source_paths_and_installed_dependency_typing_are_preserved(
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Search-path option names and installed third-party stubs stay legal."""
        paths: list[t.JsonValue] = [
            "src",
            "../member/src",
            "src/pkg/_typings",
            f"{sysconfig.get_path('purelib')}/vendor-stubs",
        ]
        document = tool_config_document
        payload = TestsFlextInfraDepsModernizerTooling._yaml_settings_payload(document)
        removed_options = {("mypy", "mypy_path"), ("pyright", "extraPaths")}
        derived: t.JsonDict = {
            table: [key for key in keys if (table, key) not in removed_options]
            for table, keys in document.derived_settings.items()
        }
        extra: Mapping[str, tuple[str, t.JsonValue]] = {
            "mypy": ("mypy_path", paths),
            "pyright": ("extraPaths", paths),
        }
        settings: t.JsonDict = {
            table: TestsFlextInfraDepsModernizerTooling._pairs(
                (*entries, extra[table]) if table in extra else entries,
            )
            for table, entries in document.settings.items()
        }
        payload["derived-settings"] = derived
        payload["settings"] = settings
        root = u.Tests.git_repository(tmp_path, "source-policy")
        declaration = root / c.CONFIG_DIR_NAME / "tooling.yaml"
        declaration.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.yaml_dump(declaration, {"Infra": {"tooling": payload}}))
        validated = tm.ok(u.Infra.load_tooling_inputs(root)).document
        for table, key in (("mypy", "mypy_path"), ("pyright", "extraPaths")):
            tm.that(dict(validated.settings[table])[key], eq=paths)

    @staticmethod
    @pytest.mark.parametrize("relative_to_project", [False, True])
    def test_member_tooling_paths_use_elected_root_not_process_cwd(
        tmp_path: Path,
        *,
        relative_to_project: bool,
    ) -> None:
        """Attached member overlays bind installed typing to their actual root."""
        root = u.Tests.git_repository(tmp_path, "member-policy")
        path = os.path.relpath(
            f"{sysconfig.get_path('purelib')}/vendor-stubs",
            start=root if relative_to_project else Path.cwd(),
        )
        declaration = root / c.CONFIG_DIR_NAME / "tooling.yaml"
        declaration.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                declaration,
                {
                    "Infra": {
                        "tooling": {
                            "tools": {
                                "pyrefly": {
                                    "path-rules": {
                                        "project-shared-search-paths": [path]
                                    },
                                }
                            }
                        }
                    },
                },
            )
        )
        loaded = u.Infra.load_tooling_inputs(root)
        if relative_to_project:
            tm.that(
                tm.ok(
                    loaded
                ).document.tools.pyrefly.path_rules.project_shared_search_paths,
                eq=(path,),
            )
        else:
            tm.fail(loaded, has="Local stub search roots")

    @staticmethod
    @pytest.mark.parametrize(
        "pair",
        [[], ["option"], ["option", True, False], [1, True], ["", True], "ab"],
    )
    def test_native_settings_reject_invalid_pair_shapes(
        tool_config_document: m.Infra.ToolConfigDocument,
        pair: t.JsonValue,
    ) -> None:
        """Sequence normalization never repairs malformed native declarations."""
        payload = TestsFlextInfraDepsModernizerTooling._yaml_settings_payload(
            tool_config_document,
        )
        payload["settings"] = {"invalid_table": [pair]}
        with pytest.raises(m.ValidationError, match=r"settings\.invalid_table"):
            _ = m.Infra.ToolConfigDocument.model_validate(payload)

    @staticmethod
    def test_native_tool_configurations_round_trip_without_mutating_policy(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Every configured root remains valid native TOML with detached values."""
        original = deepcopy(tool_config_document.settings)
        roots = {table.partition(".")[0] for table in original}
        for root in sorted(roots):
            native = u.Infra.native_tool_configuration(tool_config_document, root)
            rendered = u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(native))
            tm.that(u.Tests.toml_payload(rendered), eq=native)
            mutable_options: list[t.MutableJsonMapping] = []
            for table, entries in original.items():
                owner, separator, nested = table.partition(".")
                if owner != root:
                    continue
                observed = u.Cli.toml_mapping_ensure_path(
                    native, nested.split(".") if separator else ()
                )
                for key, value in u.Infra.configuration_pairs(entries).items():
                    tm.that(observed[key], eq=value)
                    if u.mapping(observed[key]):
                        mutable_options.append(
                            u.Cli.toml_mapping_ensure_table(observed, key)
                        )
            for option in mutable_options:
                option.clear()
        tm.that(tool_config_document.settings, eq=original)

    @staticmethod
    def test_native_tooling_render_keeps_caller_nested_tables_unchanged() -> None:
        """Missing output tables never become mutations of the caller's tree."""
        options: t.MappingKV[str, t.JsonMapping] = {
            "fixture_native": {
                "branch": {
                    "keep": [{"label": "last"}, {"label": "first"}],
                    "ratio": 1.25,
                }
            },
            "fixture_native.branch.child": {
                "enabled": True,
                "order": ["zulu", " alpha "],
            },
        }
        original = deepcopy(options)
        rendered = tm.ok(
            deps.FlextInfraPyprojectModernizer.tooling_configuration(options)
        )
        tm.that(options, eq=original)
        tm.that(
            u.Tests.toml_table_at(
                rendered, "tool", "fixture_native", "branch", "child"
            ),
            eq=options["fixture_native.branch.child"],
        )
        tm.that(
            u.Tests.toml_table_at(rendered, "tool", "fixture_native", "branch")["keep"],
            eq=u.Tests.toml_mapping(options["fixture_native"]["branch"])["keep"],
        )

    @staticmethod
    def test_native_tool_configuration_rejects_an_undeclared_root(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """An unavailable native root cannot become an empty successful policy."""
        roots = {table.partition(".")[0] for table in tool_config_document.settings}
        missing = "undeclared_tool"
        while missing in roots:
            missing = f"_{missing}"
        with pytest.raises(KeyError) as rejected:
            u.Infra.native_tool_configuration(tool_config_document, missing)
        tm.that(rejected.value.args, eq=(missing,))

    @staticmethod
    @pytest.mark.slow
    def test_new_native_root_and_subtable_survive_template_and_conformance(
        tmp_path: Path,
    ) -> None:
        """New native options require only YAML and retain complete ordered values."""
        root = u.Tests.git_repository(tmp_path, "project")
        workspace = u.Tests.standalone_workspace(root)
        project = u.Tests.project_spec(workspace.repository.name)
        native_root = "fixture_native_tool"
        while native_root in {
            table.partition(".")[0] for table in config.Infra.tooling.settings
        }:
            native_root = f"_{native_root}"
        ordered: t.JsonValueList = ["zulu", " alpha ", "middle"]
        spacing = "  value  "
        records: t.JsonValueList = [
            {"label": "second", "enabled": True},
            {"label": "first", "enabled": False},
        ]
        pairs: t.JsonValueList = [
            ["ordered", ["replaced"]],
            ["ordered", ordered],
            ["records", records],
            ["spacing", spacing],
            ["retired_option", "old"],
        ]
        declarations: t.JsonDict = {
            native_root: pairs,
            f"{native_root}.parser": [
                ["ratio", 1.25],
                ["options", {"enabled": True}],
            ],
        }
        path = root / "config" / "tooling.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.yaml_dump(path, {"Infra": {"tooling": {"settings": declarations}}}))
        tm.that(
            u.Infra.native_tool_configuration(
                tm.ok(u.Infra.load_tooling_inputs(root)).document, native_root
            )["ordered"],
            eq=ordered,
        )
        modernizer = deps.FlextInfraPyprojectModernizer(
            repository_root=root,
            skip_comments=True,
            skip_check=True,
        )
        topology = m.Infra.PyprojectDeclaredTopology()
        source = (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING)
        metadata = u.Tests.toml_table_at(source, "project")
        entry = next(
            item
            for item in config.Infra.codegen.templates.entries
            if item.destination == c.PYPROJECT_FILENAME
        )
        source = tm.ok(
            u.Cli.template_render(
                FlextInfraConfig.ssot_config_dir().parent
                / "templates"
                / config.Infra.codegen.templates.root
                / tm.not_none(entry.source),
                m.RootModel[t.JsonDict].model_validate({
                    **project.model_dump(mode="json", exclude_computed_fields=True),
                    "dist": workspace.repository.distribution,
                    "version": metadata["version"],
                    "scaffold": config.Infra.codegen.scaffold.model_dump(mode="json"),
                    "project_dependencies": metadata["dependencies"],
                    "development_dependencies": u.Tests.toml_table_at(
                        source, "dependency-groups"
                    )["dev"],
                    "python_required_version": (
                        config.Infra.codegen.toolchain.python_required_version
                    ),
                    "make_profile": c.Infra.MakeProfile.STANDALONE,
                    "tooling_runtime": tm.ok(
                        modernizer.resolve_tooling_context(
                            m.Infra.ToolingContextRequest(
                                environment_dir=root / c.Infra.ENVIRONMENT_DIRECTORY,
                                planned_sources={},
                                project_name=workspace.repository.distribution,
                                package_name=project.package_name,
                                path=root / c.PYPROJECT_FILENAME,
                                scaffold_project=config.Infra.codegen.scaffold.project,
                                topology=topology,
                                runtime_dependency_overlay=(),
                                declared_project_dependencies=u.Tests.strings(
                                    metadata["dependencies"]
                                ),
                            )
                        )
                    ).model_dump(mode="json"),
                    "root_packages": [],
                    "root_modules": [],
                    "repository_namespace_packages": [],
                    "packaged_data_paths": [],
                    "packaged_data_excludes": [],
                    "project_declaration_resource": None,
                    "hatch_build_hook_path": "",
                    "namespace_scan_dirs": [],
                    "cli_module": False,
                    "repository": "",
                    "flext_git_base_url": u.Tests.provider().base_url,
                    "flext_git_branch": "fixture-branch",
                    "uv_link_mode": config.Infra.codegen.toolchain.uv_link_mode,
                }),
            )
        )
        tm.that(
            u.Tests.toml_table_at(source, "tool", native_root),
            eq=u.Infra.native_tool_configuration(
                tm.ok(u.Infra.load_tooling_inputs(root)).document, native_root
            ),
        )
        source = tm.ok(
            modernizer.conform_source(
                source, path=root / c.PYPROJECT_FILENAME, topology=topology
            )
        )
        tm.that(
            u.Tests.toml_table_at(source, "tool", native_root)["ordered"], eq=ordered
        )
        tm.that(
            u.Tests.toml_table_at(source, "tool", native_root)["records"], eq=records
        )
        tm.that(
            u.Tests.toml_table_at(source, "tool", native_root)["spacing"], eq=spacing
        )
        declarations[native_root] = pairs[:-1]
        tm.ok(u.Cli.yaml_dump(path, {"Infra": {"tooling": {"settings": declarations}}}))
        source = tm.ok(
            modernizer.conform_source(
                source, path=root / c.PYPROJECT_FILENAME, topology=topology
            )
        )
        tm.that(
            u.Tests.toml_table_at(source, "tool", native_root),
            lacks="retired_option",
        )
        tm.that(
            tm.ok(
                modernizer.conform_source(
                    source, path=root / c.PYPROJECT_FILENAME, topology=topology
                )
            ),
            eq=source,
        )

    @staticmethod
    def _applied(
        tool_config_document: m.Infra.ToolConfigDocument,
        project_dir: Path,
        source: str = "",
    ) -> t.Pair[t.MutableJsonMapping, t.JsonMapping]:
        """Apply the Ruff phase twice to one named payload; return payload and ruff.

        Returns:
            The resulting ``t.Pair[t.MutableJsonMapping, t.JsonMapping]``.

        """
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(f'[project]\nname = "{project_dir.name}"\n{source}'),
        )
        phase = deps.FlextInfraEnsureRuffConfigPhase(
            tool_config_document,
        )
        path = project_dir / c.PYPROJECT_FILENAME
        _ = phase.apply_payload(payload, path=path)
        tm.that(phase.apply_payload(payload, path=path), empty=True)
        return payload, u.Tests.toml_mapping(
            u.Tests.toml_mapping(payload["tool"])["ruff"],
        )

    @staticmethod
    def test_typecheck_policy_keeps_tracked_surfaces_visible(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Keep every tracked Python surface visible to all four analyzers."""
        tools = tool_config_document.tools
        tracked_surfaces = frozenset({"examples", "scripts", "src", "tests"})
        hidden_globs = frozenset({
            "**/examples",
            "**/examples/**",
            "**/tests",
            "**/tests/**",
        })

        tm.that(
            frozenset(
                u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "src", list[str]
                )
            ),
            eq=tracked_surfaces,
        )
        tm.that(
            frozenset(
                u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "namespace-packages", list[str]
                )
            ),
            eq=frozenset({"examples", "scripts", "tests"}),
        )
        tm.that(frozenset(tools.pyright.path_rules.env_dirs), eq=tracked_surfaces)
        tm.that(
            hidden_globs.isdisjoint(tools.pyright.path_rules.default_excludes),
            eq=True,
        )
        tm.that(frozenset(tools.pyrefly.path_rules.env_dirs), eq=tracked_surfaces)
        tm.that(
            hidden_globs.isdisjoint(
                u.Infra.native_tool_setting(
                    tool_config_document,
                    "pyrefly",
                    "project-excludes",
                    TypeForm(t.StrSequence),
                )
            ),
            eq=True,
        )

    def test_ruff_phase_sets_expected_state(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Render Ruff policy, drop stale sections, and converge on second apply."""
        ruff_policy = tool_config_document.tools.ruff
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src" / "flext_sample").mkdir(parents=True)
        (project_dir / "src" / "flext_sample" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        stale_pattern = "stale-pattern.py"

        payload, ruff = self._applied(
            tool_config_document,
            project_dir,
            '[lint]\nselect = ["E501"]\n'
            '[tool.ruff.lint.pylint]\nallow-dunder-method-names = ["__basse__"]\n'
            f'[tool.ruff.lint.per-file-ignores]\n"{stale_pattern}" = ["E402"]\n',
        )

        tm.that(payload, lacks="lint")
        # The artifact registry is Ruff's only exclusion source; a standalone
        # project adds no workspace exclusions and Ruff keeps its own defaults.
        tm.that(
            ruff["extend-exclude"],
            eq=sorted(config.Infra.codegen.analyzer_exclude_globs),
        )
        tm.that(ruff, lacks="exclude")
        tm.that(
            ruff["line-length"],
            eq=u.Infra.native_tool_setting(
                tool_config_document, "ruff", "line-length", int
            ),
        )
        tm.that(
            ruff["target-version"],
            eq="py" + config.Infra.codegen.toolchain.python_version.replace(".", ""),
        )
        # The declared src list stays the SSOT; the projection filters it to
        # roots that exist (a retired tree must not name analyzer entries),
        # with roots the active plan is materializing accepted as present.
        tm.that(
            frozenset(u.Tests.toml_strings(ruff["src"])),
            eq=frozenset(
                root
                for root in u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "src", list[str]
                )
                if (project_dir / root).is_dir()
            ),
        )
        tm.that(
            u.Tests.toml_mapping(ruff["format"])["docstring-code-format"],
            eq=u.Infra.native_tool_setting(
                tool_config_document, "ruff.format", "docstring-code-format", bool
            ),
        )
        lint = u.Tests.toml_mapping(ruff["lint"])
        tm.that(
            list(
                u.Tests.toml_strings(
                    u.Tests.toml_mapping(lint["pylint"])["allow-dunder-method-names"],
                ),
            ),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling,
                "ruff.lint.pylint",
                "allow-dunder-method-names",
                list[str],
            ),
        )
        tm.that(
            list(u.Tests.toml_strings(lint["unfixable"])),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff.lint", "unfixable", list[str]
            ),
        )
        tm.that(
            list(u.Tests.toml_strings(lint["extend-safe-fixes"])),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff.lint", "extend-safe-fixes", list[str]
            ),
        )
        delegated = check.FlextInfraGateRegistry.default().delegated_lint_rules(
            ruff_policy.lint.rule_owners,
            check_gates=config.Infra.codegen.make.check_gates_default,
            repair_gates=(
                *config.Infra.codegen.make.check_gates_fixable,
                *config.Infra.codegen.make.fmt_gates,
            ),
        )
        tm.that(
            lint["ignore"],
            eq=sorted({
                *delegated,
                *ruff_policy.lint.ruling_disabled_rules,
                *u.Infra.native_tool_setting(
                    tool_config_document,
                    "ruff.lint",
                    "ignore",
                    TypeForm(t.StrSequence),
                ),
            }),
        )
        tm.that(
            list(
                u.Tests.toml_strings(
                    u.Tests.toml_mapping(lint["isort"])["known-first-party"],
                ),
            ),
            eq=sorted({
                "flext_sample",
            }),
        )
        tm.that(lint, lacks="per-file-ignores")

    @staticmethod
    def test_project_cannot_declare_its_own_ruff_exemption(
        tmp_path: Path,
    ) -> None:
        """A project cannot reintroduce retired exemption configuration."""
        project_dir = tmp_path / "flext-sample"
        config_dir = project_dir / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "sample.yaml").write_text(
            "ManagedArtifacts:\n"
            "  Ruff:\n"
            "    per_file_ignores:\n"
            "      src/flext_sample/_config.py: [N802]\n",
            encoding="utf-8",
        )

        tm.fail(u.Infra.load_project_managed_artifacts(project_dir), has="Ruff")

    def test_ruff_phase_skips_nonmember_workspace_namespaces(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Exclude nonmember consumer namespaces from FLEXT first-party names."""
        repository_root = tmp_path / "workspace"
        project_dir = repository_root / "demo-migration-tool"
        _ = u.Tests.WorktreeFixture.governed_workspace_with_member(
            repository_root,
            workspace="workspace",
            member="flext-core",
        )
        (project_dir / "src" / "demo_migration_tool").mkdir(parents=True)
        (project_dir / "src" / "demo_migration_tool" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        (project_dir / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "demo-migration-tool"\nversion = "0.1.0"\n'
            'dependencies = ["flext-core>=0.1.0"]\n',
            encoding="utf-8",
        )
        _, ruff = self._applied(
            tool_config_document,
            repository_root,
            'dependencies = ["flext-core>=0.1.0"]\n',
        )

        known_first_party = u.Tests.toml_strings(
            u.Tests.toml_mapping(u.Tests.toml_mapping(ruff["lint"])["isort"])[
                "known-first-party"
            ],
        )
        tm.that(known_first_party, has="flext_core")
        tm.that(known_first_party, lacks="demo_migration_tool")
