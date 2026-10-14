"""Tests for canonical dependency source selection by topology role.

Published project metadata preserves Git requirements in every topology.
Generated native resolution views exclusively own development path bindings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from flext_infra import FlextInfraConfig, config
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, tm, u


class TestsFlextInfraPyprojectConformTopologySources:
    """Tests for ``FlextInfraPyprojectConformTopologySources``."""

    _ROLE = c.Infra.MakeProfile

    @pytest.mark.slow
    @pytest.mark.parametrize("source_matches", [False, True])
    def test_modern_candidate_declaration_reaches_the_existing_requirement_owner(
        self,
        tmp_path: Path,
        *,
        source_matches: bool,
    ) -> None:
        """Modern config pins declared categories without changing their line."""
        root, _ = u.Tests.render_make_environment(
            tmp_path / "modern",
            self._ROLE.STANDALONE,
        )
        dependency = self._member_ref("flext-tests", "flext-tests")
        candidate = m.Infra.DependencyCommitSourceSpec(
            distribution=dependency.distribution,
            url=(
                dependency.url if source_matches
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
                {"Infra": {"codegen": {"repository": {
                    "integration": line.model_dump(mode="json"),
                    "candidate_dependencies": [candidate.model_dump(mode="json")],
                }}}},
            ),
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        workspace = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root, inputs=inputs),
        )
        tm.that(workspace.candidate_dependencies, eq=(candidate,))
        tm.that(workspace.integration, eq=line)
        requirement = (
            f"{self._inline_requirement(dependency)} ; "
            "implementation_name == 'cpython'"
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
            tm.that(
                generated.error or "", has="candidate dependency Git URL differs"
            )
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
        sources = [
            {"distribution": first.distribution, "url": first.url, "commit": "a" * 40},
            {
                "distribution": (
                    first.distribution.upper() if duplicate == "distribution"
                    else second.distribution
                ),
                "url": second.url if duplicate == "distribution" else first.url,
                "commit": "b" * 40,
            },
        ]
        layer = FlextInfraConfig.config_layer_paths_for_repository(
            root, filename=c.Infra.CODEGEN_CONFIG_FILENAME
        )[-1]
        tm.ok(u.Cli.yaml_dump(
            layer, {"Infra": {"codegen": {"repository": {
                "candidate_dependencies": sources,
            }}}},
        ))

        loaded = u.Infra.load_codegen_inputs(root)

        tm.that(loaded.failure, eq=True)
        tm.that(loaded.error or "", has="must be unique")

    def _member_ref(self, distribution: str, path: str) -> m.Infra.RepositoryRef:
        """Declare one standalone-capable member through the provider contract.

        Returns:
            The resulting ``m.Infra.RepositoryRef``.

        """
        return u.Tests.repository_ref(
            distribution,
            role=self._ROLE.STANDALONE,
            path=Path(path),
        )

    @staticmethod
    def _workspace(
        *members: m.Infra.RepositoryRef,
        role: c.Infra.MakeProfile = c.Infra.MakeProfile.WORKSPACE,
    ) -> m.Infra.WorkspaceSpec:
        """Compose one workspace fixture from its declared member references.

        Returns:
            The resulting ``m.Infra.WorkspaceSpec``.

        """
        return u.Tests.workspace_spec(
            u.Tests.repository_ref("workspace", role=role),
            subprojects=tuple(members),
        )

    @staticmethod
    def _inline_requirement(ref: m.Infra.RepositoryRef) -> str:
        """Render the direct-source form derived from the declared fixture branch.

        Returns:
            The resulting ``str``.

        """
        return f"{ref.distribution} @ git+{ref.url}@{u.Tests.provider_branch()}"

    @staticmethod
    def _toolchain_resolution() -> m.Infra.UvResolutionSpec:
        """Declare the fleet toolchain's uv resolver keys with no exclusions.

        Returns:
            The resulting ``m.Infra.UvResolutionSpec``.

        """
        toolchain = config.Infra.codegen.toolchain
        return m.Infra.UvResolutionSpec(
            link_mode=toolchain.uv_link_mode,
            constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
            environments=tuple(toolchain.uv_environments),
        )

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

    def test_overlay_preserves_custom_values_and_rederives_owned_members(
        self,
        tmp_path: Path,
    ) -> None:
        """The real overlay consumes ownership comments before the next render."""
        member = self._member_ref("acme-engine", "libraries/engine")
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\n'
            'dev = ["hypothesis>=6"]\n'
        )
        options = u.Infra.PyprojectConformOptions(
            repository_root=tmp_path,
            flext_line=u.Tests.integration(),
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(member),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, first))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                merged,
                workspace=self._workspace(member),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(
            second,
            eq=first,
            msg="\n".join(unified_diff(first.splitlines(), second.splitlines())),
        )
        # A later explicit CUSTOM duplicate does not inherit the owned marker.
        custom_member = self._inline_requirement(member)
        live = first.replace(
            "dev = [\n",
            f'dev = [\n    "{custom_member}",\n',
            1,
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, live))
        tm.that(
            set(u.Tests.toml_strings_at(merged, "dependency-groups", "dev")),
            eq={"hypothesis>=6", custom_member},
        )

    def test_overlay_preserves_custom_codegen_and_rederives_member_groups(
        self,
        tmp_path: Path,
    ) -> None:
        """Template composition retains CUSTOM codegen additions and provenance."""
        member = self._member_ref("acme-engine", "libraries/engine")
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n'
            '[dependency-groups]\ndev = ["hypothesis>=6"]\n',
            encoding="utf-8",
        )
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\ndev = []\n'
        )
        template = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["ruff>=1"]\ndev = []\n'
        )
        options = u.Infra.PyprojectConformOptions(
            repository_root=tmp_path,
            flext_line=u.Tests.integration(),
        )
        workspace = self._workspace(member)
        initial = tm.ok(u.Infra.overlay_preserved(template, source))
        tm.that(
            u.Tests.toml_strings_at(initial, "dependency-groups", "codegen"),
            eq=("build>=1", "ruff>=1"),
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                initial,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        merged = tm.ok(u.Infra.overlay_preserved(template, first))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "codegen"),
            eq=("build>=1", "ruff>=1"),
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                merged,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(
            second,
            eq=first,
            msg="\n".join(unified_diff(first.splitlines(), second.splitlines())),
        )

    def test_marked_same_value_outside_dev_preserves_custom_dev(self) -> None:
        """An ownership-looking comment in QA cannot own a DEV occurrence."""
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ndev = ["hypothesis>=6"]\n'
            'qa = [\n    "hypothesis>=6", # flext: derived member environment\n]\n'
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )
        tm.that(
            u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, source))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    first,
                    workspace=self._workspace(),
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                ),
            ),
            eq=first,
        )

    def test_full_line_comments_do_not_become_owned_dev_items(self) -> None:
        """Commented-out values and multiple hashes do not enter the item stream."""
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            "[dependency-groups]\ndev = [\n"
            '    # "hypothesis>=6", # flext: derived member environment\n'
            '    # "retired-generated>=1", # flext: derived member environment\n'
            '    "hypothesis>=6", # note # flext: derived member environment\n'
            "]\n"
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )
        tm.that(
            u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, source))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )

    def test_unmarked_duplicate_survives_direct_overlay_removal_and_fixed_point(
        self,
        tmp_path: Path,
    ) -> None:
        """Ownership is per occurrence throughout both generation entry paths."""
        member = self._member_ref("acme-driver", "plugins/driver")
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n'
            '[dependency-groups]\nqa = ["hypothesis>=6"]\n',
            encoding="utf-8",
        )
        seed = '[project]\nname = "workspace"\nversion = "1.0.0"\n'
        options = u.Infra.PyprojectConformOptions(
            repository_root=tmp_path,
            flext_line=u.Tests.integration(),
        )
        owned = tm.ok(
            u.Infra.pyproject_conform(
                seed,
                workspace=self._workspace(member),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        live = owned.replace("dev = [\n", 'dev = [\n    "hypothesis>=6",\n', 1)
        for entry in (live, tm.ok(u.Infra.overlay_preserved(seed, live))):
            first = tm.ok(
                u.Infra.pyproject_conform(
                    entry,
                    workspace=self._workspace(),
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                ),
            )
            tm.that(
                u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
                eq=("hypothesis>=6",),
            )
            for repeat in (first, tm.ok(u.Infra.overlay_preserved(seed, first))):
                actual = tm.ok(
                    u.Infra.pyproject_conform(
                        repeat,
                        workspace=self._workspace(),
                        required_dev_dependencies=(),
                        uv_resolution=self._toolchain_resolution(),
                        options=options,
                    )
                )
                tm.that(
                    actual,
                    eq=first,
                    msg="\n".join(
                        unified_diff(first.splitlines(), actual.splitlines())
                    ),
                )

    def test_root_missing_member_metadata_fails_loud(self, tmp_path: Path) -> None:
        """A declared package without metadata is not silently omitted."""
        member = self._member_ref("acme-engine", "libraries/engine")
        result = u.Infra.pyproject_conform(
            '[project]\nname = "workspace"\nversion = "1.0.0"\n',
            workspace=self._workspace(member),
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=u.Infra.PyprojectConformOptions(
                repository_root=tmp_path,
                flext_line=u.Tests.integration(),
            ),
        )
        tm.that(result.failure, eq=True)

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
                (f"{infra.distribution} @ git+{infra.url}@{u.Tests.provider_branch()}"),
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
        tm.that(result.failure, eq=True)
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
        tm.that(result.failure, eq=True)
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
        tm.that(result.failure, eq=True)
        tm.that(result.error or "", contains="not declared requirements: flext-cli")

    def test_removing_candidate_removes_global_override(self) -> None:
        """A normal branch resolution leaves no stale candidate override.

        With the candidate gone and the SSOT override list empty, the whole
        ``override-dependencies`` key is removed — never replaced by a
        member-computed self-override.
        """
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
        uv_table = u.Tests.toml_table_at(rendered, "tool", "uv")
        tm.that("override-dependencies" in uv_table, eq=False)

    def _assert_direct_source(self, rendered: str, ref: m.Infra.RepositoryRef) -> None:
        """Assert the canonical standalone output: one direct Git requirement."""
        dependencies = u.Tests.toml_strings_at(rendered, "project", "dependencies")
        tm.that(dependencies, eq=(self._inline_requirement(ref),))
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        tool = parsed.get("tool")
        uv_sources = (
            u.Tests.toml_mapping(u.Tests.toml_mapping(tool).get("uv")).get("sources")
            if tool
            else None
        )
        tm.that(
            uv_sources,
            eq=None,
        )

    def test_member_render_is_context_independent(self) -> None:
        """A member renders identically attached or standalone, without nesting.

        Authored native workspace and custom source declarations are retained;
        their spelling never grants the generator ownership of their contents.
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
            f'{unused.distribution} = {{path = "vendor/custom", editable = false}}\n'
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
            uv.get("sources"),
            eq={
                unused.distribution: {
                    "path": "vendor/custom",
                    "editable": False,
                },
            },
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
            eq=(self._inline_requirement(runtime),),
        )
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

    def test_standalone_preserves_declared_nonlocal_source(self) -> None:
        """Conformance owns local topology, not a user's independent Git source."""
        dependency = self._member_ref("flext-custom", "flext-custom")
        source_entry = {"git": dependency.url, "rev": u.Tests.provider_branch()}
        source = u.Cli.toml_dumps(
            u.Cli.toml_document_from_mapping({
                "project": {"name": "consumer", "version": "0.1.0", "dependencies": []},
                "tool": {"uv": {"sources": {dependency.distribution: source_entry}}},
            }),
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(role=self._ROLE.STANDALONE),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )
        tm.that(
            u.Tests.toml_table_at(rendered, "tool", "uv", "sources"),
            eq={dependency.distribution: source_entry},
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
        tm.that(
            uv_sources,
            eq=None,
        )

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
