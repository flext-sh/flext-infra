"""Tests for canonical dependency source selection by topology role.

Published project metadata preserves Git requirements in every topology.
Generated native resolution views exclusively own development path bindings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from packaging.requirements import Requirement

from flext_infra import FlextInfraConfig
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, t, tm, u
from tests.unit.pyproject_conform_topology_support import (
    TestsFlextInfraPyprojectConformTopologySupport,
)


class TestsFlextInfraPyprojectConformTopologySources(
    TestsFlextInfraPyprojectConformTopologySupport,
):
    """Tests for ``FlextInfraPyprojectConformTopologySources``."""

    @pytest.mark.slow
    @pytest.mark.parametrize("source_matches", [False, True])
    def test_modern_candidate_declaration_reaches_the_existing_requirement_owner(
        self,
        tmp_path: Path,
        *,
        source_matches: bool,
    ) -> None:
        """Modern config pins declared categories without changing their line."""
        _root, workspace, candidate = self._modern_candidate_fixture(
            tmp_path,
            source_matches=source_matches,
        )
        dependency = self._member_ref("flext-tests", "flext-tests")
        line = u.Tests.integration()
        requirement = (
            f"{self._inline_requirement(dependency)} ; implementation_name == 'cpython'"
        )
        declared_requirement = Requirement(requirement)
        quoted = tm.ok(u.Cli.json_dumps(requirement))
        source = (
            f'[project]\nname = "{workspace.repository.distribution}"\n'
            'version = "0.1.0"\ndependencies = []\n'
            "[project.optional-dependencies]\n"
            f"feature = [{quoted}]\n"
            "[dependency-groups]\n"
            f"dev = [{quoted}]\n"
            'examples = [{include-group = "dev"}]\n'
        )
        generated = u.Infra.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=u.Infra.PyprojectConformOptions(flext_line=line),
        )
        if not source_matches:
            tm.ok(generated.failure)
            tm.that(generated.error or "", has="candidate dependency Git URL differs")
            return
        rendered = tm.ok(generated)
        tm.that(u.Tests.toml_strings_at(rendered, "project", "dependencies"), eq=())
        payload = u.Tests.toml_payload(rendered)
        groups = u.Tests.toml_mapping(payload["dependency-groups"])
        tm.that(groups["examples"], eq=[{"include-group": "dev"}])
        for path in (
            ("dependency-groups", "dev"),
            ("project", "optional-dependencies", "feature"),
        ):
            actual = Requirement(u.Tests.toml_strings_at(rendered, *path)[0])
            tm.that(actual.url, eq=f"git+{candidate.url}@{candidate.commit}")
            tm.that(actual.marker, eq=declared_requirement.marker)
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=workspace,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=u.Infra.PyprojectConformOptions(flext_line=line),
                ),
            ),
            eq=rendered,
        )

    def _modern_candidate_fixture(
        self,
        tmp_path: Path,
        *,
        source_matches: bool,
    ) -> t.Triple[
        Path,
        m.Infra.WorkspaceSpec,
        m.Infra.DependencyCommitSourceSpec,
    ]:
        """Render the modern fixture declaring one candidate dependency.

        Returns:
            The fixture root, its loaded workspace, and the declared candidate.

        """
        root, _ = u.Tests.render_make_environment(
            tmp_path / "modern",
            self._ROLE.STANDALONE,
        )
        dependency = self._member_ref("flext-tests", "flext-tests")
        candidate = m.Infra.DependencyCommitSourceSpec(
            distribution=dependency.distribution,
            url=(
                dependency.url
                if source_matches
                else u.Tests.repository_ref("flext-other").url
            ),
            commit="a" * 40,
        )
        line = u.Tests.integration()
        layer = FlextInfraConfig.config_layer_paths_for_repository(
            root, filename=c.Infra.CODEGEN_CONFIG_FILENAME
        )[-1]
        tm.ok(
            u.Cli.yaml_dump(
                layer,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {
                                "integration": line.model_dump(mode="json"),
                                "candidate_dependencies": [
                                    candidate.model_dump(mode="json")
                                ],
                            }
                        }
                    }
                },
            ),
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        workspace = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root, inputs=inputs),
        )
        tm.that(workspace.candidate_dependencies, eq=(candidate,))
        tm.that(workspace.integration, eq=line)
        return root, workspace, candidate

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("duplicate", ["distribution", "repository"])
    def test_modern_candidate_declaration_rejects_ambiguous_sources(
        tmp_path: Path,
        duplicate: str,
    ) -> None:
        """The modern loader runs the same unique-source contract as workspace."""
        root, _ = u.Tests.render_make_environment(
            tmp_path / "modern",
            c.Infra.MakeProfile.STANDALONE,
        )
        first = u.Tests.repository_ref("flext-tests")
        second = u.Tests.repository_ref("flext-other")
        sources: t.JsonValueList = [
            {"distribution": first.distribution, "url": first.url, "commit": "a" * 40},
            {
                "distribution": (
                    first.distribution.upper()
                    if duplicate == "distribution"
                    else second.distribution
                ),
                "url": second.url if duplicate == "distribution" else first.url,
                "commit": "b" * 40,
            },
        ]
        layer = FlextInfraConfig.config_layer_paths_for_repository(
            root, filename=c.Infra.CODEGEN_CONFIG_FILENAME
        )[-1]
        tm.ok(
            u.Cli.yaml_dump(
                layer,
                {
                    "Infra": {
                        "codegen": {"repository": {"candidate_dependencies": sources}}
                    }
                },
            )
        )

        loaded = u.Infra.load_codegen_inputs(root)

        tm.ok(loaded.failure)
        tm.that(loaded.error or "", has="must be unique")

    @pytest.mark.parametrize("package", [False, True])
    def test_packaged_root_renders_workspace_source_without_self_override(
        self, *, package: bool
    ) -> None:
        """A packaged root renders its native workspace identity source only.

        The self distribution never enters ``override-dependencies``: an
        empty SSOT resolution removes the key entirely, so a standalone
        repository locks exactly like a fleet member and keeps its full dev
        closure in the lock.
        """
        workspace = self._workspace(role=self._ROLE.STANDALONE)
        workspace = workspace.model_copy(
            update={
                "repository": workspace.repository.model_copy(
                    update={"package": package},
                ),
            },
        )
        source = (
            f'[project]\nname = "{workspace.repository.distribution}"\n'
            'version = "0.1.0"\ndependencies = []\n'
        )
        options = u.Infra.PyprojectConformOptions(
            flext_line=u.Tests.integration(),
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(parsed.get("tool")).get("uv"))
        tm.fail("sources" in uv)
        tm.fail("override-dependencies" in uv)
        repeated = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(repeated, eq=rendered)

    def test_root_members_resolve_through_the_native_workspace(self) -> None:
        """Member requirements stay as authored; uv resolves them natively."""
        workspace_line = u.Tests.integration().branch
        flext_member = self._member_ref("flext-core", "flext-core")
        other_member = self._member_ref("acme-charts", "apps/acme-charts")
        workspace = self._workspace(flext_member, other_member).model_copy(
            update={
                "integration": m.Infra.WorkspaceIntegrationSpec(
                    provider=u.Tests.integration().provider,
                    branch=workspace_line,
                ),
            },
        )
        infra = u.Tests.repository_ref("flext-infra")
        infra_requirement = self._inline_requirement(infra)
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            'dependencies = ["acme-charts", "flext-core", '
            f'"{infra_requirement}"]\n'
            '\n[dependency-groups]\nworkspace = ["flext-core"]\n'
        )
        options = self._conform_options(workspace)
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(
            set(u.Tests.toml_strings_at(rendered, "project", "dependencies")),
            eq={
                flext_member.distribution,
                other_member.distribution,
                infra_requirement,
            },
        )
        uv = u.Tests.toml_table_at(rendered, "tool", "uv")
        sources = u.Tests.toml_mapping(uv["sources"])
        for ref in workspace.subprojects:
            tm.that(
                u.Tests.toml_mapping(sources[ref.distribution]), eq={"workspace": True}
            )
        tm.that(
            u.Tests.toml_strings_at(rendered, "dependency-groups", "dev"),
            eq=(),
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(second, eq=rendered)

    def test_internal_candidates_exclude_the_reciprocal_self_requirement(
        self,
    ) -> None:
        """Each internal override candidate drops only its edge back to this project.

        Expected entries derive from the rendered override set and the project
        name, so a standalone lock never sees this project by two URLs.
        """
        cli = self._member_ref("flext-cli", "flext-cli")
        infra = self._member_ref("flext-infra", "flext-infra")
        workspace = self._workspace(cli, infra, role=self._ROLE.STANDALONE).model_copy(
            update={
                "candidate_dependencies": tuple(
                    m.Infra.DependencyCommitSourceSpec(
                        distribution=member.distribution,
                        url=member.url,
                        commit=digit * 40,
                    )
                    for member, digit in ((cli, "a"), (infra, "b"))
                ),
            },
        )
        own = "fixture-consumer"
        source = (
            f'[project]\nname = "{own}"\nversion = "0.1.0"\n'
            f'dependencies = ["{cli.distribution}", "{infra.distribution}"]\n'
        )
        options = u.Infra.PyprojectConformOptions(flext_line=u.Tests.integration())
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        overrides = u.Tests.toml_strings_at(
            rendered, "tool", "uv", "override-dependencies"
        )
        candidates = sorted(
            name
            for entry in overrides
            if (name := u.Infra.dep_name(entry)) is not None
            and name in {cli.distribution, infra.distribution}
        )
        tm.that(candidates, empty=False)
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(parsed.get("tool")).get("uv"))
        tm.that(
            uv.get("exclude-dependencies"),
            eq=[
                {"package": {"name": name}, "dependencies": [own]}
                for name in candidates
            ],
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=workspace,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                ),
            ),
            eq=rendered,
        )

    def test_declared_internal_urls_derive_overrides_and_self_exclusions(
        self,
    ) -> None:
        """Declared internal Git URL requirements become overrides at that URL.

        The override and exclusion sets derive from the project's own rendered
        requirements; no project lists them.
        """
        cli = self._member_ref("flext-cli", "flext-cli")
        infra = self._member_ref("flext-infra", "flext-infra")
        workspace = self._workspace(cli, infra, role=self._ROLE.STANDALONE)
        line = u.Tests.integration().branch
        own = "fixture-consumer"
        source = (
            f'[project]\nname = "{own}"\nversion = "0.1.0"\n'
            f'dependencies = ["{cli.distribution} @ git+{cli.url}@{line}"]\n'
            "[dependency-groups]\n"
            f'dev = ["{infra.distribution} @ git+{infra.url}@{line}"]\n'
        )
        options = u.Infra.PyprojectConformOptions(flext_line=u.Tests.integration())
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        declared = {
            name: entry
            for entry in (
                *u.Tests.toml_strings_at(rendered, "project", "dependencies"),
                *u.Tests.toml_strings_at(rendered, "dependency-groups", "dev"),
            )
            if (name := u.Infra.dep_name(entry)) is not None
            and name in {cli.distribution, infra.distribution}
        }
        tm.that(sorted(declared), eq=sorted((cli.distribution, infra.distribution)))
        overrides = u.Tests.toml_strings_at(
            rendered, "tool", "uv", "override-dependencies"
        )
        for name, entry in declared.items():
            tm.that(overrides, has=f"{name} @ {entry.partition('@')[2].strip()}")
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(parsed.get("tool")).get("uv"))
        tm.that(
            uv.get("exclude-dependencies"),
            eq=[
                {"package": {"name": name}, "dependencies": [own]}
                for name in sorted(declared)
            ],
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=workspace,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                ),
            ),
            eq=rendered,
        )

    def test_candidate_commit_is_project_specific_and_reaches_fixed_point(self) -> None:
        """An explicit candidate changes only its declared distribution."""
        cli = self._member_ref("flext-cli", "flext-cli")
        infra = self._member_ref("flext-infra", "flext-infra")
        candidate_commit = "a" * 40
        workspace = self._workspace(cli, infra, role=self._ROLE.STANDALONE).model_copy(
            update={
                "candidate_dependencies": (
                    m.Infra.DependencyCommitSourceSpec(
                        distribution=cli.distribution,
                        url=cli.url,
                        commit=candidate_commit,
                    ),
                ),
            },
        )
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            'dependencies = ["flext-cli", "flext-infra"]\n'
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        dependencies = set(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
        )
        tm.that(
            dependencies,
            eq={
                f"{cli.distribution} @ git+{cli.url}@{candidate_commit}",
                infra.distribution,
            },
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "tool", "uv", "override-dependencies"),
            eq=(f"{cli.distribution} @ git+{cli.url}@{candidate_commit}",),
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=workspace,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=u.Infra.PyprojectConformOptions(
                        flext_line=u.Tests.integration(),
                    ),
                ),
            ),
            eq=rendered,
        )

    def test_candidate_url_must_match_declared_requirement_source(self) -> None:
        """A commit cannot redirect an existing direct requirement to another repo."""
        cli = self._member_ref("flext-cli", "flext-cli")
        foreign = self._member_ref("flext-core", "flext-core")
        workspace = self._workspace(cli, role=self._ROLE.STANDALONE).model_copy(
            update={
                "candidate_dependencies": (
                    m.Infra.DependencyCommitSourceSpec(
                        distribution=cli.distribution,
                        url=foreign.url,
                        commit="b" * 40,
                    ),
                ),
            },
        )
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(cli)}"]\n'
        )
        result = u.Infra.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=u.Infra.PyprojectConformOptions(
                flext_line=u.Tests.integration(),
            ),
        )
        tm.ok(result.failure)
        tm.that(result.error or "", contains="candidate dependency Git URL differs")

    def test_candidate_cannot_invent_a_missing_dependency_origin(self) -> None:
        """A candidate pins an owned source; it cannot create provenance."""
        cli = self._member_ref("flext-cli", "flext-cli")
        workspace = self._workspace(role=self._ROLE.STANDALONE).model_copy(
            update={
                "candidate_dependencies": (
                    m.Infra.DependencyCommitSourceSpec(
                        distribution=cli.distribution,
                        url=cli.url,
                        commit="c" * 40,
                    ),
                ),
            },
        )
        result = u.Infra.pyproject_conform(
            (
                '[project]\nname = "workspace"\nversion = "0.1.0"\n'
                'dependencies = ["flext-cli"]\n'
            ),
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=u.Infra.PyprojectConformOptions(
                flext_line=u.Tests.integration(),
            ),
        )
        tm.ok(result.failure)
        tm.that(result.error or "", contains="no declared Git provenance")

    def test_candidate_must_be_a_declared_requirement(self) -> None:
        """A stale candidate entry cannot silently leave the resolver unchanged."""
        cli = self._member_ref("flext-cli", "flext-cli")
        workspace = self._workspace(role=self._ROLE.STANDALONE).model_copy(
            update={
                "candidate_dependencies": (
                    m.Infra.DependencyCommitSourceSpec(
                        distribution=cli.distribution,
                        url=cli.url,
                        commit="d" * 40,
                    ),
                ),
            },
        )
        result = u.Infra.pyproject_conform(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n',
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=u.Infra.PyprojectConformOptions(
                flext_line=u.Tests.integration(),
            ),
        )
        tm.ok(result.failure)
        tm.that(result.error or "", contains="not declared requirements: flext-cli")

    def test_removing_candidate_removes_global_override(self) -> None:
        """A normal branch resolution leaves no stale candidate override."""
        infra = self._member_ref("flext-infra", "flext-infra")
        stale_commit = "a" * 40
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(infra)}"]\n'
            "\n[tool.uv]\noverride-dependencies = "
            f'["{infra.distribution} @ git+{infra.url}@{stale_commit}"]\n'
        )
        workspace = self._workspace(infra, role=self._ROLE.STANDALONE)
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        tm.that(
            "override-dependencies" in u.Tests.toml_table_at(rendered, "tool", "uv"),
            eq=False,
        )

    def _assert_direct_source(self, rendered: str, ref: m.Infra.RepositoryRef) -> None:
        """Assert the canonical standalone output: one direct Git requirement."""
        dependencies = u.Tests.toml_strings_at(rendered, "project", "dependencies")
        tm.that(dependencies, eq=(self._inline_requirement(ref),))

    def test_member_render_is_context_independent(self) -> None:
        """A member renders identically attached or standalone, without nesting.

        Authored native workspace sources remain unchanged while the public
        requirements preserve their declared Git provenance.
        """
        runtime = self._member_ref("flext-web", "flext-web")
        dev = self._member_ref("flext-tests", "flext-tests")
        unused = self._member_ref("flext-unused", "flext-unused")
        consumer = self._member_ref("flext-api", "flext-api")
        standalone = u.Tests.workspace_spec(consumer)
        attached = standalone.model_copy(
            update={"repository": consumer.model_copy(update={"editable": True})},
        )
        source = (
            f'[project]\nname = "{consumer.distribution}"\nversion = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(runtime)}"]\n'
            "\n[dependency-groups]\n"
            f'dev = ["{self._inline_requirement(dev)}"]\n'
            "\n[tool.uv.workspace]\nmembers = []\n"
            "\n[tool.uv.sources]\n"
            f"{unused.distribution} = {{workspace = true}}\n"
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=attached,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(parsed.get("tool")).get("uv"))
        tm.that(u.Tests.toml_mapping(uv["workspace"]), eq={"members": []})
        tm.that(
            u.Tests.toml_mapping(uv["sources"]),
            eq={unused.distribution: {"workspace": True}},
        )
        self._assert_direct_source(rendered, runtime)
        detached = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=standalone,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        tm.that(detached, eq=rendered)
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=attached,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=u.Infra.PyprojectConformOptions(
                        flext_line=u.Tests.integration(),
                    ),
                ),
            ),
            eq=rendered,
        )

    def test_external_consumer_keeps_direct_git_requirement(self) -> None:
        """Test external consumer keeps direct git requirement."""
        workspace = u.Tests.workspace_spec(
            self._member_ref("acme-platform", "acme-platform"),
            subprojects=(self._member_ref("flext-core", "flext-core"),),
        )
        core = workspace.subprojects[0]
        external = (
            "[project]\n"
            'name = "acme-platform"\n'
            'version = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(core)}"]\n'
        )

        rendered = tm.ok(
            u.Infra.pyproject_conform(
                external,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )

        self._assert_direct_source(rendered, core)

    def test_publishable_project_keeps_catalog_git_provenance(self) -> None:
        """Test publishable project keeps catalog git provenance."""
        workspace = u.Tests.workspace_spec(
            self._member_ref("flext-api", "flext-api"),
            subprojects=(
                self._member_ref("flext-core", "flext-core"),
                self._member_ref("flext-api", "flext-api"),
            ),
        )
        provider = workspace.subprojects[0]
        publishable_project = (
            f'[project]\nname = "{workspace.subprojects[1].distribution}"\n'
            'version = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(provider)}"]\n'
        )

        rendered = tm.ok(
            u.Infra.pyproject_conform(
                publishable_project,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )

        self._assert_direct_source(rendered, provider)

    def test_publishable_project_preserves_declared_ref_of_unmapped_source(
        self,
    ) -> None:
        """The declared ref stays authoritative for a dependency no member owns."""
        workspace = u.Tests.workspace_spec(
            self._member_ref("flext-api", "flext-api"),
            subprojects=(
                self._member_ref("flext-core", "flext-core"),
                self._member_ref("flext-api", "flext-api"),
            ),
        )
        consumer = workspace.subprojects[1]
        unmapped = self._member_ref("flext-unmapped", "flext-unmapped")
        requirement = self._inline_requirement(unmapped)
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                (
                    f'[project]\nname = "{consumer.distribution}"\n'
                    'version = "0.1.0"\n'
                    f'dependencies = ["{requirement}"]\n'
                ),
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )

        dependencies = u.Tests.toml_strings_at(rendered, "project", "dependencies")
        tm.that(
            dependencies,
            eq=(requirement,),
        )

    def test_standalone_resolves_dependency_groups_with_direct_requirements(
        self,
    ) -> None:
        """Dev-group members resolve standalone through direct Git requirements."""
        workspace = u.Tests.workspace_spec(
            self._member_ref("flext-tests", "flext-tests"),
            subprojects=(self._member_ref("flext-core", "flext-core"),),
        )
        core = workspace.subprojects[0]
        member_source = (
            "[project]\n"
            'name = "flext-tests"\n'
            'version = "0.1.0"\n'
            "\n[dependency-groups]\n"
            f'dev = ["{self._inline_requirement(core)}"]\n'
        )

        rendered = tm.ok(
            u.Infra.pyproject_conform(
                member_source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )

        group = u.Tests.toml_strings_at(rendered, "dependency-groups", "dev")
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        tool = parsed.get("tool")
        uv_sources = (
            u.Tests.toml_mapping(u.Tests.toml_mapping(tool).get("uv")).get("sources")
            if tool
            else None
        )

        tm.that(group, eq=(self._inline_requirement(core),))
        tm.ok(not uv_sources)

    def test_member_requirement_with_a_foreign_url_fails_provenance(self) -> None:
        """A member dependency cannot point at a URL its manifest does not own."""
        workspace = u.Tests.workspace_spec(
            self._member_ref("acme-platform", "acme-platform"),
            subprojects=(self._member_ref("flext-core", "flext-core"),),
        )
        core = workspace.subprojects[0]
        host = u.Tests.provider().base_url.rstrip("/").rpartition("/")[0]
        foreign = (
            f"{core.distribution} @ git+{host}/foreign-owner/{core.distribution}.git@"
            f"{u.Tests.provider_branch()}"
        )

        result = u.Infra.pyproject_conform(
            (
                '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
                f'dependencies = ["{foreign}"]\n'
            ),
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
        )

        tm.fail(result, has="internal dependency Git URL differs from manifest")
