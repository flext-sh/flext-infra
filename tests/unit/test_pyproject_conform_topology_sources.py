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

from flext_infra import FlextInfraConfig, config
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
            tm.that(generated.failure, eq=True)
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
        sources: list[t.JsonValue] = [
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
        repository_overlay: dict[str, t.JsonValue] = {
            "candidate_dependencies": sources,
        }
        codegen_overlay: dict[str, t.JsonValue] = {
            "repository": repository_overlay,
        }
        overlay: dict[str, t.JsonValue] = {"Infra": codegen_overlay}
        tm.ok(u.Cli.yaml_dump(layer, overlay))

        loaded = u.Infra.load_codegen_inputs(root)

        tm.that(loaded.failure, eq=True)
        tm.that(loaded.error or "", has="must be unique")

    def test_member_request_preserves_explicit_source_over_receiver_line(
        self,
        tmp_path: Path,
    ) -> None:
        """Compose captured member extras without adding a conflicting root ref."""
        member = self._member_ref(config.Infra.name, "member")
        workspace = self._workspace(member)
        source_line = u.Tests.provider_branch()
        integration = m.Infra.WorkspaceIntegrationSpec(
            provider=workspace.repository.provider,
            branch=f"{source_line}-receiver",
        )
        workspace = workspace.model_copy(update={"integration": integration})
        member_root = tmp_path / member.path
        member_root.mkdir()
        declaration = member_root / c.PYPROJECT_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                declaration,
                "[project]\n"
                f'name = "{member.distribution}"\n'
                'version = "1.0"\n'
                "dependencies = []\n"
                "[project.optional-dependencies]\n"
                f'"{member.distribution}-feature" = []\n'
                "[dependency-groups]\ndev = []\n",
            ),
        )
        captured = tm.ok(
            u.Cli.atomic_read_binary_file_state(declaration, required=True),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                declaration,
                "captured declarations are the parser input, not the live path",
            ),
        )
        marker = 'implementation_name == "cpython"'
        request = f"{member.distribution} @ git+{member.url}@{source_line}; {marker}"
        source = (
            "[project]\n"
            f'name = "{workspace.repository.distribution}"\n'
            'version = "1.0"\n'
            f"dependencies = [{tm.ok(u.Cli.json_dumps(request))}]\n"
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    repository_root=tmp_path,
                    member_declarations=(captured,),
                ),
            ),
        )
        document = u.Cli.toml_parse_text(rendered)
        tm.that(document is not None, eq=True)
        if document is None:
            pytest.fail("composition did not produce valid TOML")
        lines = tm.ok(u.Infra.document_requirement_lines(document))
        selected = tuple(
            line
            for line in lines
            if u.Infra.dep_name(line) == u.Infra.dep_name(member.distribution)
        )
        tm.that(bool(selected), eq=True)
        for line in selected:
            tm.that(
                tm.ok(u.Infra.declared_git_source(line)),
                eq=(member.url, source_line),
            )
            tm.that(line, has=marker)
        tm.that(
            any(f"[{member.distribution}-feature]" in line for line in selected),
            eq=True,
        )

    def test_member_provisioning_requires_captured_declarations(
        self, tmp_path: Path
    ) -> None:
        """A pure metadata renderer never elects an installed producer itself."""
        member = self._member_ref(config.Infra.name, "member")
        workspace = self._workspace(member)
        source = (
            "[project]\n"
            f'name = "{workspace.repository.distribution}"\n'
            'version = "1.0"\n'
            "dependencies = []\n"
        )
        rendered = u.Infra.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=u.Infra.PyprojectConformOptions(repository_root=tmp_path),
        )
        tm.that(rendered.failure, eq=True)
        tm.that(
            rendered.error,
            has="member provisioning requires captured authenticated declarations",
        )

    @pytest.mark.parametrize("package", [False, True])
    def test_packaged_root_renders_workspace_source_without_self_override(
        self, package: bool
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
        tm.that(
            u.Tests.toml_mapping(uv.get("sources")),
            eq={},
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "tool", "uv", "override-dependencies"),
            eq=(),
        )
        if package:
            tm.that(
                u.Tests.toml_mapping(uv.get("sources")),
                eq={workspace.repository.distribution: {"workspace": True}},
            )
        else:
            tm.that("sources" in uv, eq=False)
        tm.that("override-dependencies" in uv, eq=False)
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

    def test_root_members_preserve_git_sources_of_any_family(
        self,
        tmp_path: Path,
    ) -> None:
        """Actual metadata remains portable while views own local editability."""
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
        for ref in workspace.subprojects:
            path = tmp_path / ref.path / c.PYPROJECT_FILENAME
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'[project]\nname = "{ref.distribution}"\nversion = "0.1.0"\n',
                encoding="utf-8",
            )
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            'dependencies = ["acme-charts", "flext-core", '
            f'"{infra_requirement}"]\n'
            '\n[dependency-groups]\nworkspace = ["flext-core"]\n'
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                    repository_root=tmp_path,
                ),
            ),
        )
        expected = {self._inline_requirement(ref) for ref in workspace.subprojects} | {
            infra_requirement,
        }
        tm.that(
            set(u.Tests.toml_strings_at(rendered, "project", "dependencies")),
            eq=expected,
        )
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(parsed.get("tool")).get("uv"))
        tm.that(
            u.Tests.toml_mapping(uv.get("sources")),
            eq={},
        )
        groups = u.Tests.toml_mapping(parsed.get("dependency-groups"))
        tm.that("workspace" not in groups, eq=True)
        tm.that("workspace" not in uv, eq=True)
        tm.that(
            set(u.Tests.toml_strings_at(rendered, "dependency-groups", "dev")),
            eq={self._inline_requirement(ref) for ref in workspace.subprojects},
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                    repository_root=tmp_path,
                ),
            ),
        )
        tm.that(second, eq=rendered)

    @pytest.mark.parametrize("attached", [False, True])
    def test_retired_development_requirements_do_not_reappear(
        self,
        tmp_path: Path,
        attached: bool,
    ) -> None:
        """The public generator removes retired items and preserves other inputs."""
        retired = config.Infra.codegen.scaffold.project.retired_dev
        retained = "fixture-retained-development"
        while retained in retired:
            retained += "-extra"
        entries = ", ".join(f'"{name}"' for name in (*retired, retained))
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            f"[dependency-groups]\ndev = [{entries}]\n"
        )
        workspace = self._workspace(role=self._ROLE.STANDALONE)
        expected = {retained}
        if attached:
            member = self._member_ref("fixture-retirement-member", "member")
            workspace = self._workspace(member)
            member_file = tmp_path / member.path / c.PYPROJECT_FILENAME
            member_file.parent.mkdir()
            member_file.write_text(
                '[project]\nname = "fixture-retirement-member"\nversion = "0.1.0"\n'
                f"[dependency-groups]\ndev = [{entries}]\n",
                encoding="utf-8",
            )
            expected.add(self._inline_requirement(member))
        options = u.Infra.PyprojectConformOptions(
            flext_line=u.Tests.integration(),
            repository_root=tmp_path,
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            )
        )
        tm.that(
            set(u.Tests.toml_strings_at(rendered, "dependency-groups", "dev")),
            eq=expected,
        )
        repeated = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            )
        )
        tm.that(repeated, eq=rendered)

    def test_root_requests_all_extras_groups_and_retains_constraints(
        self,
        tmp_path: Path,
    ) -> None:
        """Portable metadata retains bounds, markers and extras without bindings."""
        provider = self._member_ref("acme-engine", "libraries/engine").model_copy(
            update={"editable": False},
        )
        consumer = self._member_ref("acme-driver", "plugins/driver")
        workspace = self._workspace(provider, consumer)
        bound = f'{provider.distribution}[feature]>=1; python_version >= "3.13"'
        runtime_requirement = 'typing-extensions>=4; python_version >= "3.13"'
        provider_path = tmp_path / provider.path / c.PYPROJECT_FILENAME
        provider_path.parent.mkdir(parents=True)
        provider_path.write_text(
            f'[project]\nname = "{provider.distribution}"\nversion = "1.0.0"\n'
            '[project.optional-dependencies]\nfeature = ["idna>=3"]\n'
            '[dependency-groups]\nqa = ["pytest>=8"]\n',
            encoding="utf-8",
        )
        consumer_path = tmp_path / consumer.path / c.PYPROJECT_FILENAME
        consumer_path.parent.mkdir(parents=True)
        consumer_path.write_text(
            f'[project]\nname = "{consumer.distribution}"\nversion = "1.0.0"\n'
            f"dependencies = ['{bound}', '{runtime_requirement}']\n"
            '[dependency-groups]\nchecks = ["hypothesis>=6"]\n'
            'qa = [{include-group = "checks"}]\n',
            encoding="utf-8",
        )
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            'dependencies = ["httpx>=0.27"]\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\n'
        )
        options = u.Infra.PyprojectConformOptions(
            flext_line=u.Tests.integration(),
            repository_root=tmp_path,
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            )
        )
        dev = set(u.Tests.toml_strings_at(first, "dependency-groups", "dev"))
        tm.that(
            set(u.Tests.toml_strings_at(first, "dependency-groups", "codegen")),
            eq={"build>=1", "hypothesis>=6", "pytest>=8"},
        )
        tm.that({"pytest>=8", "hypothesis>=6"}.issubset(dev), eq=True)
        tm.that({"idna>=3", runtime_requirement}.issubset(dev), eq=True)
        tm.that(
            f"{provider.distribution}[feature] @ "
            f"git+{provider.url}@{u.Tests.integration().branch}" in dev,
            eq=True,
        )
        tm.that(
            u.Tests.toml_strings_at(first, "project", "dependencies"),
            eq=("httpx>=0.27",),
        )
        uv = u.Tests.toml_table_at(first, "tool", "uv")
        tm.that(
            bound.replace("[feature]", "")
            in u.Tests.toml_strings_at(first, "tool", "uv", "constraint-dependencies"),
            eq=True,
        )
        tm.that(
            u.Tests.toml_strings_at(first, "tool", "uv", "override-dependencies"),
            eq=(),
        )
        tm.that(
            u.Tests.toml_mapping(uv.get("sources")),
            eq={},
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    first,
                    workspace=workspace,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                )
            ),
            eq=first,
        )

    def test_removed_member_environment_drops_only_owned_dev_entries(
        self,
        tmp_path: Path,
    ) -> None:
        """Membership/group removal preserves real CUSTOM constraints and bootstrap."""
        provider = self._member_ref("acme-engine", "libraries/engine")
        consumer = self._member_ref("acme-driver", "plugins/driver")
        workspace = self._workspace(provider, consumer)
        for member in workspace.subprojects:
            path = tmp_path / member.path / c.PYPROJECT_FILENAME
            path.parent.mkdir(parents=True)
            path.write_text(
                f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n'
                '[dependency-groups]\nqa = ["hypothesis>=6"]\n',
                encoding="utf-8",
            )
        custom_member = self._inline_requirement(provider)
        custom_bound = 'idna>=3; python_version >= "3.13"'
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            'dependencies = ["httpx>=0.27"]\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\n'
            f"dev = [\"{custom_member}\", '{custom_bound}']\n"
        )
        options = u.Infra.PyprojectConformOptions(
            repository_root=tmp_path,
            flext_line=u.Tests.integration(),
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        (tmp_path / consumer.path / c.PYPROJECT_FILENAME).write_text(
            f'[project]\nname = "{consumer.distribution}"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        remaining = self._workspace(consumer)
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=remaining,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        dev = set(u.Tests.toml_strings_at(second, "dependency-groups", "dev"))
        tm.that(custom_member in dev, eq=True)
        tm.that(custom_bound in dev, eq=True)
        tm.that("hypothesis>=6" in dev, eq=False)
        tm.that(self._inline_requirement(consumer) in dev, eq=True)
        tm.that(
            u.Tests.toml_strings_at(second, "dependency-groups", "codegen"),
            eq=("build>=1",),
        )
        sources = u.Tests.toml_mapping(
            u.Tests.toml_table_at(second, "tool", "uv").get("sources"),
        )
        tm.that(provider.distribution in sources, eq=False)
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    second,
                    workspace=remaining,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                ),
            ),
            eq=second,
        )

