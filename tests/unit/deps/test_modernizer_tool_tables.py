"""Config-owned tool table phase tests for the deps modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typing_extensions import TypeForm

from flext_infra import config
from flext_infra.deps import (
    FlextInfraEnsureRuffConfigPhase,
    FlextInfraPyprojectModernizer,
    FlextInfraToolTablesPhase,
)
from flext_infra.gates import FlextInfraMypyGate
from tests import c, e, m, t, tm, u


class TestsFlextInfraDepsModernizerToolTables:
    """Every policy table mirrors ``config.Infra.tooling`` and converges once."""

    @staticmethod
    def _applied(
        tmp_path: Path,
        source: str = "",
        *,
        tool_config: m.Infra.ToolConfigDocument | None = None,
    ) -> t.Pair[t.MutableJsonMapping, t.StrSequence]:
        """Apply the phase to one named project payload; return payload and changes.

        Returns:
            The resulting ``t.Pair[t.MutableJsonMapping, t.StrSequence]``.

        """
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        # A live package: the first-party owner derives importable packages.
        (package_dir / c.Infra.INIT_PY).write_text('"""Package."""\n', encoding="utf-8")
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                '[project]\nname = "flext-sample"\n'
                f'version = "{config.Infra.initial_project_version}"\n{source}',
            ),
        )
        changes = FlextInfraToolTablesPhase(
            tool_config or config.Infra.tooling,
        ).apply_payload(payload, path=project_dir / c.PYPROJECT_FILENAME)
        return payload, changes

    @staticmethod
    def _table(payload: t.JsonMapping, *path: str) -> t.JsonMapping:
        """Unwrap one nested table below ``[tool]``.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        table = u.Tests.toml_mapping(payload["tool"])
        for segment in path:
            table = u.Tests.toml_mapping(table[segment])
        return table

    def test_mypy_exclude_skips_scenario_trees_only(self, tmp_path: Path) -> None:
        """Mypy excludes scenario trees but keeps typed fixture modules governed."""
        payload, _ = self._applied(tmp_path)
        exclude = re.compile(str(self._table(payload, "mypy")["exclude"]))
        for root in config.Infra.codegen.exclusions.scenario_data_roots:
            tm.that(exclude.match(f"{root}/scenario/module.py"), none=False)
            tm.that(exclude.match(f"{root}/module.py"), none=True)
            tm.that(exclude.match(f"{root}/"), none=True)

    def test_mypy_table_mirrors_policy(self, tmp_path: Path) -> None:
        """Render toolchain Python plus config-owned plugins and overrides."""
        mypy_policy = config.Infra.tooling.tools.mypy
        native_options = u.Infra.native_tool_settings(config.Infra.tooling, "mypy")
        payload, _ = self._applied(
            tmp_path,
            "[tool.mypy]\n"
            'plugins = ["custom.plugin"]\n'
            'disable_error_code = ["assignment", "has-type", "redundant-cast"]\n'
            "strict_concatenate = true\n"
            'overrides = [{ module = ["stale.*"] }]\n',
        )
        mypy = self._table(payload, "mypy")
        tm.that(
            mypy["python_version"],
            eq=config.Infra.codegen.toolchain.python_version,
        )
        tm.that(mypy, lacks="strict_concatenate")
        tm.that(
            list(u.Tests.toml_strings(mypy["plugins"])),
            eq=native_options["plugins"],
        )
        if mypy_policy.ruling_disable_error_codes:
            tm.that(
                list(u.Tests.toml_strings(mypy["disable_error_code"])),
                eq=list(mypy_policy.ruling_disable_error_codes),
            )
        else:
            tm.that(mypy, lacks="disable_error_code")
        tm.that(
            list(u.Tests.toml_list(mypy["overrides"])),
            eq=[
                {
                    "module": list(entry.modules),
                    **u.Infra.configuration_pairs(entry.settings),
                }
                for entry in mypy_policy.overrides
            ],
        )
        for key, value in native_options.items():
            tm.that(mypy[key], eq=value)
        second = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            ),
        )
        changes = FlextInfraToolTablesPhase(config.Infra.tooling).apply_payload(
            second,
            path=tmp_path / "flext-sample" / c.PYPROJECT_FILENAME,
        )
        tm.that(second, eq=payload)
        tm.that(changes, empty=True)

    @staticmethod
    @pytest.mark.parametrize(
        "plugins",
        [(), ("custom.plugin",), ("pydantic.mypy", "pydantic.v1.mypy")],
    )
    def test_mypy_rejects_missing_or_v1_pydantic_plugin(
        plugins: t.StrSequence,
    ) -> None:
        """The typed policy cannot remove mandatory Pydantic 2 support."""
        tooling = config.Infra.tooling
        payload = tooling.model_dump(by_alias=True, exclude_computed_fields=True)
        payload["settings"] = {
            **tooling.settings,
            "mypy": (
                *(pair for pair in tooling.settings["mypy"] if pair[0] != "plugins"),
                ("plugins", list(plugins)),
            ),
        }
        with pytest.raises(e.PydanticValidationError, match=r"pydantic\.mypy"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @pytest.mark.slow
    @pytest.mark.parametrize("enable_unrelated", [False, True])
    def test_mypy_projected_policy_keeps_plugin_and_unsuspended_errors(
        self,
        tmp_path: Path,
        *,
        enable_unrelated: bool,
    ) -> None:
        """The real Mypy consumer retains formerly suspended plugin diagnostics."""
        tooling = config.Infra.tooling
        tooling = tooling.model_copy(
            update={
                "tools": tooling.tools.model_copy(
                    update={
                        "mypy": tooling.tools.mypy.model_copy(
                            update={"ruling_disable_error_codes": ()}
                        )
                    }
                )
            }
        )
        if enable_unrelated:
            tooling = tooling.model_copy(
                update={
                    "settings": {
                        **tooling.settings,
                        "mypy": (
                            *tooling.settings["mypy"],
                            ("enable_error_code", ["arg-type"]),
                        ),
                    }
                },
            )
        payload, _ = self._applied(tmp_path, tool_config=tooling)
        mypy = self._table(payload, "mypy")
        tm.that(
            tuple(u.Tests.toml_strings(mypy["plugins"])),
            eq=tuple(
                u.Tests.strings(
                    u.Infra.native_tool_settings(tooling, "mypy")["plugins"]
                )
            ),
        )
        tm.that(mypy, lacks="disable_error_code")
        if enable_unrelated:
            tm.that(
                mypy["enable_error_code"],
                eq=u.Infra.native_tool_settings(tooling, "mypy")["enable_error_code"],
            )
        project = tmp_path / "flext-sample"
        (project / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding="utf-8",
        )
        source = project / "src" / "flext_sample" / "model.py"
        declarations = (
            "from pydantic import BaseModel, computed_field\n"
            "class Model(BaseModel):\n"
            "    value: int\n"
            "    @computed_field\n"
            "    @property\n"
            "    def derived(self) -> int:\n"
            "        return self.value\n"
            "def missing_argument() -> Model:\n"
            "    return Model()\n"
        )
        source.write_text(declarations, encoding="utf-8")
        context = m.Infra.GateContext(
            repository_root=project,
            reports_dir=project / ".reports",
        )
        gate = FlextInfraMypyGate(project)
        initial = gate.check(project, context)
        tm.fail(initial.result.passed)
        tm.that([issue.code for issue in initial.issues], has="call-arg")

        source.write_text(
            declarations
            + "def requires_integer(value: int) -> int:\n"
            + "    return value\n"
            + 'invalid = requires_integer("incorrect")\n',
            encoding="utf-8",
        )
        rejected = gate.check(project, context)
        tm.fail(rejected.result.passed)
        tm.that([issue.code for issue in rejected.issues], has="arg-type")
        tm.that([issue.code for issue in rejected.issues], has="call-arg")

    def test_pytest_table_replaces_policy_and_merges_extensions(
        self,
        tmp_path: Path,
    ) -> None:
        """Replace policy flags while retaining declared discovery extensions."""
        policy = config.Infra.tooling.tools.pytest
        native = u.Infra.native_tool_settings(
            config.Infra.tooling, "pytest.ini_options"
        )
        configured = config.Infra.tooling.model_copy(
            update={
                "settings": {
                    **config.Infra.tooling.settings,
                    "pytest.ini_options": (
                        *config.Infra.tooling.settings["pytest.ini_options"],
                        (
                            "python_classes",
                            ["Spec*", *u.Tests.strings(native["python_classes"])],
                        ),
                    ),
                },
                "tools": config.Infra.tooling.tools.model_copy(
                    update={
                        "pytest": policy.model_copy(
                            update={
                                "standard_markers": (
                                    *policy.standard_markers,
                                    "custom: custom marker",
                                )
                            },
                        ),
                    },
                ),
            },
        )
        payload, _ = self._applied(
            tmp_path,
            "[tool.pytest.ini_options]\n"
            'python_classes = ["Spec*"]\n'
            'addopts = ["--maxfail=1"]\n'
            'markers = ["custom: custom marker"]\n',
            tool_config=configured,
        )
        ini = self._table(payload, "pytest", "ini_options")
        expected = u.Infra.native_tool_settings(configured, "pytest.ini_options")
        tm.that(ini["minversion"], eq=expected["minversion"])
        tm.that(ini["flext_slow_timeout_seconds"], eq=str(policy.slow_timeout_seconds))
        tm.that(ini["python_classes"], eq=expected["python_classes"])
        tm.that(ini["addopts"], eq=expected["addopts"])
        tm.that(
            set(u.Tests.strings(ini["markers"])),
            eq={"custom: custom marker", *policy.standard_markers},
        )

    @staticmethod
    def test_projected_slow_timeout_key_is_registered_by_the_loaded_plugin(
        pytestconfig: pytest.Config,
    ) -> None:
        """The ini key the pytest table projects is one the flext-tests plugin owns.

        ``getini`` raises ``ValueError`` for an unregistered name, which strict
        config collection turns into ``Unknown config option`` in every consumer.
        """
        tm.that(
            isinstance(pytestconfig.getini(c.Infra.FLEXT_SLOW_TIMEOUT_SECONDS), str),
            truth=True,
        )

    @pytest.mark.parametrize("follow_untyped", [False, True])
    def test_mypy_source_analysis_override_round_trips_policy(
        self,
        tmp_path: Path,
        *,
        follow_untyped: bool,
    ) -> None:
        """Project the configured import analysis flag without disabling errors."""
        tooling = config.Infra.tooling
        entry = m.Infra.MypyOverrideConfig.model_validate({
            "modules": ("arbitrary_dependency.*",),
            "settings": (("follow_untyped_imports", follow_untyped),),
            "justification": (
                "https://mypy.readthedocs.io/en/stable/"
                "config_file.html#follow-untyped-imports"
            ),
        })
        configured = tooling.model_copy(
            update={
                "tools": tooling.tools.model_copy(
                    update={
                        "mypy": tooling.tools.mypy.model_copy(
                            update={"overrides": (entry,)},
                        ),
                    },
                ),
            },
        )

        payload, _ = self._applied(tmp_path, tool_config=configured)

        tm.that(
            list(u.Tests.toml_list(self._table(payload, "mypy")["overrides"])),
            eq=[
                {
                    "module": list(entry.modules),
                    "follow_untyped_imports": follow_untyped,
                },
            ],
        )

    def test_formatting_tables_mirror_policy(self, tmp_path: Path) -> None:
        """Render codespell, hatch, tomlsort, yamlfix, pydantic-mypy, and vulture."""
        tooling = config.Infra.tooling
        payload, changes = self._applied(
            tmp_path,
            f'[tool.codespell]\nskip = "{c.GIT_DIR_NAME}"\n'
            "[tool.pydantic-mypy]\nwarn_untyped_fields = true\n",
        )
        codespell = self._table(payload, "codespell")
        tm.that(codespell, lacks="skip")
        tm.that(changes, empty=False)
        tm.that(
            codespell["check-filenames"],
            eq=u.Infra.native_tool_settings(tooling, "codespell")["check-filenames"],
        )
        tm.that(
            self._table(payload, "hatch", "metadata")["allow-direct-references"],
            eq=u.Infra.native_tool_settings(tooling, "hatch.metadata")[
                "allow-direct-references"
            ],
        )
        tomlsort = self._table(payload, "tomlsort")
        tm.that(
            tomlsort["all"], eq=u.Infra.native_tool_settings(tooling, "tomlsort")["all"]
        )
        tm.that(
            list(u.Tests.toml_strings(tomlsort["sort_first"])),
            eq=list(
                u.Infra.native_tool_setting(
                    tooling, "tomlsort", "sort_first", TypeForm(t.StrSequence)
                )
            ),
        )
        yamlfix = self._table(payload, "yamlfix")
        tm.that(
            yamlfix["line_length"],
            eq=u.Infra.native_tool_settings(tooling, "yamlfix")["line_length"],
        )
        tm.that(
            yamlfix["explicit_start"],
            eq=u.Infra.native_tool_settings(tooling, "yamlfix")["explicit_start"],
        )
        pydantic_mypy = self._table(payload, "pydantic-mypy")
        tm.that(pydantic_mypy, lacks="warn_untyped_fields")
        tm.that(
            pydantic_mypy["init_typed"],
            eq=u.Infra.native_tool_settings(tooling, "pydantic-mypy")["init_typed"],
        )
        vulture = self._table(payload, "vulture")
        tm.that(
            vulture["min_confidence"],
            eq=u.Infra.native_tool_settings(tooling, "vulture")["min_confidence"],
        )

    def test_coverage_report_measures_without_a_floor(self, tmp_path: Path) -> None:
        """Keep reporting policy and drop a floor left by an older projection."""
        coverage = u.Infra.native_tool_settings(config.Infra.tooling, "coverage.report")
        payload, changes = self._applied(
            tmp_path,
            "[tool.coverage.report]\nfail_under = 45\n",
        )
        report = self._table(payload, "coverage", "report")
        tm.that(report, lacks="fail_under")
        tm.that(changes, empty=False)
        tm.that(report["show_missing"], eq=coverage["show_missing"])
        tm.that(
            list(u.Tests.strings(self._table(payload, "coverage", "run")["omit"])),
            eq=list(
                u.Infra.native_tool_setting(
                    config.Infra.tooling,
                    "coverage.run",
                    "omit",
                    TypeForm(t.StrSequence),
                )
            ),
        )

    def test_coverage_source_round_trips_arbitrary_config(self, tmp_path: Path) -> None:
        """Project an arbitrary configured coverage source without hardcoding it."""
        tooling = config.Infra.tooling
        arbitrary_source = ("arbitrary-production-root",)
        configured = tooling.model_copy(
            update={
                "settings": {
                    **tooling.settings,
                    "coverage.run": (
                        *tooling.settings["coverage.run"],
                        ("source", list(arbitrary_source)),
                    ),
                },
            },
        )
        payload, _ = self._applied(tmp_path, tool_config=configured)
        tm.that(
            list(u.Tests.strings(self._table(payload, "coverage", "run")["source"])),
            eq=list(arbitrary_source),
        )

    def test_deptry_first_party_contains_only_the_target_package(
        self,
        tmp_path: Path,
    ) -> None:
        """A stale peer name cannot survive regeneration as a local module."""
        payload, _ = self._applied(
            tmp_path,
            'dependencies = ["flext-core>=0.1.0"]\n'
            '[tool.deptry]\nknown_first_party = ["flext_core"]\n',
        )
        tm.that(
            set(
                u.Tests.toml_strings(
                    self._table(payload, "deptry")["known_first_party"],
                ),
            ),
            eq={"flext_sample"},
        )

    def test_deptry_includes_declared_repository_namespaces(
        self,
        tmp_path: Path,
    ) -> None:
        """Shipped root namespaces are local without absorbing external peers."""
        payload, _ = self._applied(tmp_path)
        namespaces = ("deployment_assets", "shared_schema")
        project_dir = tmp_path / "flext-sample"
        for namespace in (*namespaces, "unshipped", "flext_core"):
            (project_dir / namespace).mkdir()
        phase = FlextInfraToolTablesPhase(config.Infra.tooling)
        phase.apply_payload(
            payload,
            path=project_dir / c.PYPROJECT_FILENAME,
            repository_namespace_packages=namespaces,
        )

        tm.that(
            set(
                u.Tests.toml_strings(
                    self._table(payload, "deptry")["known_first_party"],
                ),
            ),
            eq={"flext_sample", *namespaces},
        )
        tm.that(
            phase.apply_payload(
                payload,
                path=project_dir / c.PYPROJECT_FILENAME,
                repository_namespace_packages=namespaces,
            ),
            empty=True,
        )

    @staticmethod
    def test_first_party_uses_live_package_when_distribution_name_differs(
        tmp_path: Path,
    ) -> None:
        """A distribution name must not invent an importable package."""
        project_dir = tmp_path / "project"
        package_dir = project_dir / "src" / "dc_backup"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text('"""Package."""\n', encoding="utf-8")
        (project_dir / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "datacosmos-backup"\n',
            encoding="utf-8",
        )
        namespaces = FlextInfraToolTablesPhase.first_party_namespaces(path=project_dir)
        tm.that(namespaces, has="dc_backup", lacks="datacosmos_backup")

    def test_tables_are_idempotent(self, tmp_path: Path) -> None:
        """A second application over the converged payload changes nothing."""
        payload, first = self._applied(tmp_path)
        second = FlextInfraToolTablesPhase(config.Infra.tooling).apply_payload(
            payload,
            path=tmp_path / "flext-sample" / c.PYPROJECT_FILENAME,
        )
        tm.that(first, empty=False)
        tm.that(second, empty=True)

    @staticmethod
    def test_modernizer_roots_and_members_converge_without_coverage_floor(
        tmp_path: Path,
    ) -> None:
        """Roots and members converge once and never project a coverage floor."""
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=tmp_path,
            skip_check=True,
        )
        root_path = tmp_path / c.PYPROJECT_FILENAME
        root_topology = m.Infra.PyprojectDeclaredTopology(project_kind="platform")
        member_topology = m.Infra.PyprojectDeclaredTopology()
        root_first: str = tm.ok(
            modernizer.conform_source(
                '[project]\nname = "arbitrary-root"\n',
                path=root_path,
                topology=root_topology,
            ),
        )
        member_path = tmp_path / "arbitrary-member" / c.PYPROJECT_FILENAME
        member_path.parent.mkdir()
        member_first: str = tm.ok(
            modernizer.conform_source(
                '[project]\nname = "arbitrary-member"\n'
                'dependencies = ["flext-core", "flext-cli", "flext-ldap"]\n',
                path=member_path,
                topology=member_topology,
            ),
        )
        tm.that(
            tm.ok(
                modernizer.conform_source(
                    root_first,
                    path=root_path,
                    topology=root_topology,
                ),
            ),
            eq=root_first,
        )
        tm.that(
            tm.ok(
                modernizer.conform_source(
                    member_first,
                    path=member_path,
                    topology=member_topology,
                ),
            ),
            eq=member_first,
        )
        for rendered in (root_first, member_first):
            tm.that(
                u.Tests.toml_table_at(rendered, "tool", "coverage", "report"),
                lacks="fail_under",
            )

    @staticmethod
    def _workspace_with_exclusion(tmp_path: Path, excluded: str) -> Path:
        """Build a governed workspace root whose manifest excludes one tree.

        The canonical standalone fixture provides the repository identity and
        its manifest declares the retired tree under the analyzer-exclusion
        contract the detector owns (external dependency paths are the
        read-only trees the src and namespace-packages projections drop).

        Returns:
            The resulting ``Path``.

        """
        project_dir = tmp_path / "flext-sample"
        workspace = u.Tests.standalone_workspace(project_dir, project_dir.name)
        # The analysis-exclusion SSOT only governs a materialized checkout: a
        # project without its pyproject on disk declares no manifest scope,
        # and the detector's governance gates require the checkout's own
        # .gitmodules plus .git (flext-gajwa) to read the manifest at all.
        (project_dir / c.PYPROJECT_FILENAME).write_text(
            f'[project]\nname = "{project_dir.name}"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13"\n',
            encoding="utf-8",
        )
        (project_dir / c.Infra.GIT_DIR).mkdir(exist_ok=True)
        # External analysis exclusions are declared exclusively by this
        # checkout's own .gitmodules: a submodule that opts out of flext
        # management classifies as a read-only external dependency and the
        # src / namespace-packages projections drop it.
        (project_dir / c.Infra.GITMODULES).write_text(
            f'[submodule "{excluded}"]\n'
            f"\tpath = {excluded}\n"
            "\turl = https://example.invalid/retired.git\n"
            "\tbranch = main\n"
            "\tflext-managed = false\n",
            encoding="utf-8",
        )
        manifest = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=workspace.repository.name,
            repository=workspace.repository.model_copy(
                update={"role": c.Infra.MakeProfile.WORKSPACE},
            ),
            exclusions=(
                m.Infra.WorkspaceExclusionSpec(path=Path(excluded), reason="retired"),
            ),
            external_dependency_paths=(Path(excluded),),
        )
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(project_dir),
                manifest.model_dump(mode="json"),
            ),
        )
        return project_dir

    def test_vulture_paths_filter_excluded_roots(self, tmp_path: Path) -> None:
        """A workspace-excluded production root leaves the dead-code scope.

        The config list stays the SSOT; the projection filters on the
        workspace's declared analysis exclusions — order-independent across
        the deps pass and the root-materializing gen pass (invest repro:
        scripts/ retired, dead-code scope kept scanning it — bead flext-x44z3).
        """
        project_dir = self._workspace_with_exclusion(tmp_path, "scripts")
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload('[project]\nname = "flext-sample"\n'),
        )
        FlextInfraToolTablesPhase(config.Infra.tooling).apply_payload(
            payload,
            path=project_dir / c.PYPROJECT_FILENAME,
        )
        paths = u.Tests.toml_strings(self._table(payload, "vulture")["paths"])
        tm.that(paths, lacks="scripts", has="src")

    def test_ruff_root_lists_filter_excluded_roots(self, tmp_path: Path) -> None:
        """Ruff root projections drop workspace-excluded trees.

        ruff fails hard on a src entry whose directory is absent, and the
        namespace-packages contract only holds for live roots; the workspace
        SSOT's exclusions decide (bead flext-x44z3).
        """
        project_dir = self._workspace_with_exclusion(tmp_path, "scripts")
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload('[project]\nname = "flext-sample"\n'),
        )
        FlextInfraEnsureRuffConfigPhase(
            config.Infra.tooling,
        ).apply_payload(
            payload,
            path=project_dir / c.PYPROJECT_FILENAME,
        )
        table = self._table(payload, "ruff")
        tm.that(
            u.Tests.toml_strings(self._table(payload, "ruff", "lint")["extend-select"]),
            eq=tuple(
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff.lint", "extend-select", list[str]
                )
            ),
        )
        src_roots = u.Tests.toml_strings(table["src"])
        namespace_packages = u.Tests.toml_strings(table.get("namespace-packages", []))
        tm.that(src_roots, lacks="scripts", has="src")
        tm.that(namespace_packages, lacks="scripts")
        tm.that(self._table(payload, "ruff", "lint"), lacks="per-file-ignores")
