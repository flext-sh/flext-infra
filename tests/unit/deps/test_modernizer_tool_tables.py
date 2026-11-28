"""Config-owned tool table phase tests for the deps modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from typing_extensions import TypeForm

from flext_infra import config
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.deps.phases import (
    FlextInfraEnsureRuffConfigPhase,
    FlextInfraToolTablesPhase,
)
from tests import c, m, p, t, tm, u


class TestsFlextInfraDepsModernizerToolTables:
    """Every policy table mirrors ``config.Infra.tooling`` and converges once."""

    @staticmethod
    def _applied(
        tmp_path: Path,
        source: str = "",
        *,
        tool_config: p.Infra.ToolConfigDocument | None = None,
    ) -> tuple[t.MutableJsonMapping, Sequence[str]]:
        """Apply the phase to one named project payload; return payload and changes.

        Returns:
            The resulting ``tuple[t.MutableJsonMapping, Sequence[str]]``.

        """
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        # A live package: the first-party owner derives importable packages.
        (package_dir / c.Infra.INIT_PY).write_text('"""Package."""\n', encoding="utf-8")
        u.Tests.initialize_git_repo(project_dir)
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                '[project]\nname = "flext-sample"\n'
                f'version = "{config.Infra.initial_project_version}"\n{source}',
            ),
        )
        changes = FlextInfraToolTablesPhase(
            tool_config or config.Infra.tooling,
            codegen=config.Infra.codegen,
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
        tm.that(
            ini["addopts"],
            eq=list(
                dict.fromkeys((
                    *u.Tests.strings(expected["addopts"]),
                    *(
                        f"--ignore={root}"
                        for root in config.Infra.codegen.exclusions.scenario_data_roots
                    ),
                )),
            ),
        )
        tm.that(
            set(u.Tests.strings(ini["markers"])),
            eq={"custom: custom marker", *policy.standard_markers},
        )

    @staticmethod
    def test_projected_slow_timeout_key_is_registered_by_the_loaded_plugin(
        pytestconfig: t.Tests.Config,
    ) -> None:
        """The ini key the pytest table projects is one the flext-tests plugin owns.

        ``getini`` raises ``ValueError`` for an unregistered name, which strict
        config collection turns into ``Unknown config option`` in every consumer.
        """
        tm.that(
            isinstance(pytestconfig.getini(c.Infra.FLEXT_SLOW_TIMEOUT_SECONDS), str),
            truth=True,
        )

    def test_formatting_tables_mirror_policy(self, tmp_path: Path) -> None:
        """Render codespell, hatch, tomlsort, yamlfix, and vulture."""
        tooling = config.Infra.tooling
        payload, changes = self._applied(
            tmp_path,
            f'[tool.codespell]\nskip = "{c.GIT_DIR_NAME}"\n',
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
                    tooling, "tomlsort", "sort_first", TypeForm(Sequence[str])
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
                    TypeForm(Sequence[str]),
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
        phase = FlextInfraToolTablesPhase(
            config.Infra.tooling, codegen=config.Infra.codegen
        )
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
        package_dir = project_dir / "src" / "demo_app"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text('"""Package."""\n', encoding="utf-8")
        (project_dir / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "demo-distribution"\n',
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)
        namespaces = FlextInfraToolTablesPhase.first_party_namespaces(path=project_dir)
        tm.that(namespaces, has="demo_app", lacks="demo_distribution")

    def test_tables_are_idempotent(self, tmp_path: Path) -> None:
        """A second application over the converged payload changes nothing."""
        payload, first = self._applied(tmp_path)
        second = FlextInfraToolTablesPhase(
            config.Infra.tooling, codegen=config.Infra.codegen
        ).apply_payload(
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
        u.Tests.initialize_git_repo(tmp_path)
        root_codegen = tm.ok(u.Infra.load_codegen_inputs(tmp_path)).spec
        root_topology = m.Infra.PyprojectDeclaredTopology(project_kind="platform")
        member_topology = m.Infra.PyprojectDeclaredTopology()
        root_first: str = tm.ok(
            modernizer.conform_source(
                '[project]\nname = "arbitrary-root"\n',
                path=root_path,
                topology=root_topology,
                codegen=root_codegen,
            ),
        )
        member_path = tmp_path / "arbitrary-member" / c.PYPROJECT_FILENAME
        member_path.parent.mkdir()
        u.Tests.initialize_git_repo(member_path.parent)
        member_codegen = tm.ok(u.Infra.load_codegen_inputs(member_path.parent)).spec
        member_first: str = tm.ok(
            modernizer.conform_source(
                '[project]\nname = "arbitrary-member"\n'
                'dependencies = ["flext-core", "flext-cli", "flext-ldap"]\n',
                path=member_path,
                topology=member_topology,
                codegen=member_codegen,
            ),
        )
        tm.that(
            tm.ok(
                modernizer.conform_source(
                    root_first,
                    path=root_path,
                    topology=root_topology,
                    codegen=root_codegen,
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
                    codegen=member_codegen,
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
        manifest = m.Infra.WorkspaceManifestSpec.model_validate({
            "version": (c.Infra.WORKSPACE_MANIFEST_VERSION),
            "name": (workspace.repository.name),
            "repository": (
                workspace.repository.model_copy(
                    update={"role": c.Infra.MakeProfile.WORKSPACE},
                )
            ),
            "exclusions": ((
                m.Infra.WorkspaceExclusionSpec(path=Path(excluded), reason="retired"),
            )),
            "external_dependency_paths": ((Path(excluded),)),
        })
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
        FlextInfraToolTablesPhase(
            config.Infra.tooling,
            codegen=tm.ok(u.Infra.load_codegen_inputs(project_dir)).spec,
        ).apply_payload(
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
            codegen=tm.ok(u.Infra.load_codegen_inputs(project_dir)).spec,
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
        authorized = tm.not_none(
            u.Cli.toml_mapping_child(
                u.Infra.native_tool_configuration(config.Infra.tooling, "ruff"),
                "lint",
            )
        )
        tm.that(
            self._table(payload, "ruff", "lint").get("per-file-ignores"),
            eq=authorized.get("per-file-ignores"),
        )
