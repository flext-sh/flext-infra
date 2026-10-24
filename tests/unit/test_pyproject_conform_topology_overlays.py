"""Tests for canonical dependency source selection by topology role.

Published project metadata preserves Git requirements in every topology.
Generated native resolution views exclusively own development path bindings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import m, t, tm, u
from tests.unit.pyproject_conform_topology_support import (
    TestsFlextInfraPyprojectConformTopologySupport,
)


class TestsFlextInfraPyprojectConformTopologyOverlays(
    TestsFlextInfraPyprojectConformTopologySupport,
):
    """Overlay, candidate-commit, and render-context contracts by topology role."""

    def _assert_custom_dev_survives(self, source: str) -> str:
        """Conform and overlay ``source``; its only DEV entry must stay custom.

        Returns:
            The conformed document.

        """
        first = tm.ok(self._conform(source, self._workspace()))
        tm.that(
            u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, source))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        return first

    def test_overlay_preserves_custom_values_and_rederives_owned_members(
        self,
        tmp_path: Path,
    ) -> None:
        """The real overlay consumes ownership comments before the next render."""
        member = self._member_ref("acme-engine", "libraries/engine")
        self._write_member(tmp_path, member)
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\n'
            'dev = ["hypothesis>=6"]\n'
        )
        options = self._integration(tmp_path)
        workspace = self._workspace(member)
        first = tm.ok(self._conform(source, workspace, options))
        merged = tm.ok(u.Infra.overlay_preserved(source, first))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        self._assert_fixed_point(first, workspace, options, source=merged)
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
        self._write_member(
            tmp_path,
            member,
            '[dependency-groups]\ndev = ["hypothesis>=6"]\n',
        )
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\ndev = []\n'
        )
        template = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["ruff>=1"]\ndev = []\n'
        )
        options = self._integration(tmp_path)
        workspace = self._workspace(member)
        initial = tm.ok(u.Infra.overlay_preserved(template, source))
        tm.that(
            u.Tests.toml_strings_at(initial, "dependency-groups", "codegen"),
            eq=("build>=1", "ruff>=1"),
        )
        first = tm.ok(self._conform(initial, workspace, options))
        merged = tm.ok(u.Infra.overlay_preserved(template, first))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "codegen"),
            eq=("build>=1", "ruff>=1"),
        )
        self._assert_fixed_point(first, workspace, options, source=merged)

    def test_marked_same_value_outside_dev_preserves_custom_dev(self) -> None:
        """An ownership-looking comment in QA cannot own a DEV occurrence."""
        first = self._assert_custom_dev_survives(
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ndev = ["hypothesis>=6"]\n'
            'qa = [\n    "hypothesis>=6", # flext: derived member environment\n]\n'
        )
        self._assert_fixed_point(first, self._workspace())

    def test_full_line_comments_do_not_become_owned_dev_items(self) -> None:
        """Commented-out values and multiple hashes do not enter the item stream."""
        _ = self._assert_custom_dev_survives(
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            "[dependency-groups]\ndev = [\n"
            '    # "hypothesis>=6", # flext: derived member environment\n'
            '    # "retired-generated>=1", # flext: derived member environment\n'
            '    "hypothesis>=6", # note # flext: derived member environment\n'
            "]\n"
        )

    def test_unmarked_duplicate_survives_direct_overlay_removal_and_fixed_point(
        self,
        tmp_path: Path,
    ) -> None:
        """Ownership is per occurrence throughout both generation entry paths."""
        member = self._member_ref("acme-driver", "plugins/driver")
        self._write_member(
            tmp_path,
            member,
            '[dependency-groups]\nqa = ["hypothesis>=6"]\n',
        )
        seed = '[project]\nname = "workspace"\nversion = "1.0.0"\n'
        options = self._integration(tmp_path)
        owned = tm.ok(self._conform(seed, self._workspace(member), options))
        live = owned.replace("dev = [\n", 'dev = [\n    "hypothesis>=6",\n', 1)
        for entry in (live, tm.ok(u.Infra.overlay_preserved(seed, live))):
            first = tm.ok(self._conform(entry, self._workspace(), options))
            tm.that(
                u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
                eq=("hypothesis>=6",),
            )
            for repeat in (first, tm.ok(u.Infra.overlay_preserved(seed, first))):
                self._assert_fixed_point(
                    first,
                    self._workspace(),
                    options,
                    source=repeat,
                )

    def test_root_missing_member_metadata_fails_loud(self, tmp_path: Path) -> None:
        """A declared package without metadata is not silently omitted."""
        member = self._member_ref("acme-engine", "libraries/engine")
        result = self._conform(
            '[project]\nname = "workspace"\nversion = "1.0.0"\n',
            self._workspace(member),
            self._integration(tmp_path),
        )
        tm.that(result.failure, eq=True)

    def test_candidate_commit_is_project_specific_and_reaches_fixed_point(self) -> None:
        """An explicit candidate changes only its declared distribution."""
        cli = self._member_ref("flext-cli", "flext-cli")
        infra = self._member_ref("flext-infra", "flext-infra")
        candidate_commit = "a" * 40
        workspace = self._candidate_workspace(
            cli,
            infra,
            candidate=cli,
            commit=candidate_commit,
        )
        rendered = tm.ok(
            self._conform(
                '[project]\nname = "workspace"\nversion = "0.1.0"\n'
                'dependencies = ["flext-cli", "flext-infra"]\n',
                workspace,
                self._integration(),
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
            eq=(
                workspace.repository.distribution,
                f"{cli.distribution} @ git+{cli.url}@{candidate_commit}",
            ),
        )
        self._assert_fixed_point(rendered, workspace, self._integration())

    def test_candidate_url_must_match_declared_requirement_source(self) -> None:
        """A commit cannot redirect an existing direct requirement to another repo."""
        cli = self._member_ref("flext-cli", "flext-cli")
        foreign = self._member_ref("flext-core", "flext-core")
        result = self._conform(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(cli)}"]\n',
            self._candidate_workspace(
                cli,
                candidate=cli,
                commit="b" * 40,
                url=foreign.url,
            ),
            self._integration(),
        )
        tm.that(result.failure, eq=True)
        tm.that(result.error or "", contains="candidate dependency Git URL differs")

    def test_candidate_cannot_invent_a_missing_dependency_origin(self) -> None:
        """A candidate pins an owned source; it cannot create provenance."""
        cli = self._member_ref("flext-cli", "flext-cli")
        result = self._conform(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            'dependencies = ["flext-cli"]\n',
            self._candidate_workspace(candidate=cli, commit="c" * 40),
            self._integration(),
        )
        tm.that(result.failure, eq=True)
        tm.that(result.error or "", contains="no declared Git provenance")

    def test_candidate_must_be_a_declared_requirement(self) -> None:
        """A stale candidate entry cannot silently leave the resolver unchanged."""
        cli = self._member_ref("flext-cli", "flext-cli")
        result = self._conform(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n',
            self._candidate_workspace(candidate=cli, commit="d" * 40),
            self._integration(),
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
        rendered = tm.ok(self._conform(source, workspace, self._integration()))
        tm.that(
            u.Tests.toml_strings_at(rendered, "tool", "uv", "override-dependencies"),
            eq=(workspace.repository.distribution,),
        )

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
        rendered = tm.ok(self._conform(source, attached, self._integration()))
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
        self._assert_fixed_point(rendered, standalone, self._integration())
        self._assert_fixed_point(rendered, attached, self._integration())

    def test_standalone_preserves_declared_nonlocal_source(self) -> None:
        """Conformance owns local topology, not a user's independent Git source."""
        dependency = self._member_ref("flext-custom", "flext-custom")
        source_entry: dict[str, t.JsonValue] = {
            "git": dependency.url,
            "rev": u.Tests.provider_branch(),
        }
        document: dict[str, t.JsonValue] = {
            "project": {"name": "consumer", "version": "0.1.0", "dependencies": []},
            "tool": {"uv": {"sources": {dependency.distribution: source_entry}}},
        }
        source = u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(document))
        rendered = tm.ok(
            self._conform(source, self._workspace(role=self._ROLE.STANDALONE)),
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

        rendered = tm.ok(self._conform(external, workspace))

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

        rendered = tm.ok(self._conform(publishable_project, workspace))

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
            self._conform(
                f'[project]\nname = "{consumer.distribution}"\n'
                'version = "0.1.0"\n'
                f'dependencies = ["{requirement}"]\n',
                workspace,
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

        rendered = tm.ok(self._conform(member_source, workspace))

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

        result = self._conform(
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
            f'dependencies = ["{foreign}"]\n',
            workspace,
        )

        tm.fail(result, has="internal dependency Git URL differs from manifest")
