"""Projection-only contract for repository-owned Beads configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import u


class TestsFlextInfraCodegenBeadsProjection:
    """Keep codegen on its declarative projection boundary."""

    @staticmethod
    def _project(root: Path, *, database: str, issue_prefix: str) -> Path:
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="fixture-workspace",
            database=database,
            issue_prefix=issue_prefix,
        )
        return root

    @staticmethod
    def _plan(root: Path) -> m.Infra.CodegenPlan:
        for entry in config.Infra.codegen.templates.entries:
            destination = entry.destination.format(
                package_name="fixture_project", ns="fixture_project"
            )
            (root / destination).parent.mkdir(parents=True, exist_ok=True)
        for managed in config.Infra.codegen.managed_files:
            (root / managed.path).parent.mkdir(parents=True, exist_ok=True)
        # Scaffold entries create declaration family directories, and the
        # facade completeness law rejects owners without their public facade.
        package_dir = root / "src" / "fixture_project"
        for family in ("u", "p"):
            facade = package_dir / f"{c.Infra.FAMILY_PUBLIC_MODULES[family]}.py"
            if (package_dir / c.Infra.FAMILY_DIRECTORIES[family]).is_dir() and (
                not facade.is_file()
            ):
                facade.write_text(
                    f"class FixtureProject{family.capitalize()}Facade:\n    pass\n",
                    encoding="utf-8",
                )
        result = FlextInfraCodegenConform(repository_root=root).plan(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(result)
        return m.Infra.CodegenPlan.model_validate(result.value)

    @staticmethod
    def _rendered(plan: m.Infra.CodegenPlan, destination: str) -> str | None:
        match = next(
            (item for item in plan.files if item.path.as_posix().endswith(destination)),
            None,
        )
        return (
            None
            if match is None or match.desired_content is None
            else u.Tests.codegen_file_text(match)
        )

    def test_local_identity_renders_only_declarative_beads_files(
        self, tmp_path: Path
    ) -> None:
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )

        plan = self._plan(root)
        rendered_config = self._rendered(plan, c.Infra.BEADS_CONFIG_RELPATH)
        rendered_metadata = self._rendered(plan, c.Infra.BEADS_METADATA_RELPATH)

        if rendered_config is None:
            pytest.fail("local identity must produce the declarative Beads config")
        # `issue_prefix` is the key bd itself resolves (`bd config get
        # issue_prefix`); the hyphenated spelling reads as unset, so bd appended
        # its own key on first write and left every governed checkout dirty.
        tm.that(rendered_config, has='issue_prefix: "project-prefix"')
        tm.that(rendered_config, lacks="issue-prefix:")
        # A checkout with no workspace manifest declares city participation by
        # fleet default (True): the endpoint keys mirror the inherited city and
        # `types.custom` stays generator-owned.
        tm.that(rendered_config, has="gc.endpoint_origin:")
        tm.that(rendered_config, has="gc.endpoint_status:")
        tm.that(rendered_config, has="types.custom:")
        tm.that(rendered_config, has="dolt.auto-start:")
        # Beads owns and mints the ledger marker at first use (flext-l2296):
        # a fresh checkout legitimately lacks it and conform must not plan
        # the absent runtime artifact.
        tm.that(rendered_metadata, none=True)
        tm.that(hasattr(plan, "beads"), eq=False)

    def test_gascity_disabled_renders_standalone_beads_config(
        self, tmp_path: Path
    ) -> None:
        """A disabled city never moves runtime ownership into generated config."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        u.Tests.write_standalone_workspace_manifest(
            root, "fixture-project", gascity_enabled=False
        )

        plan = self._plan(root)
        rendered_config = self._rendered(plan, c.Infra.BEADS_CONFIG_RELPATH)
        rendered_mise = self._rendered(plan, ".mise.toml")

        if rendered_config is None:
            pytest.fail("standalone identity must produce the declarative Beads config")
        tm.that(rendered_config, has='issue_prefix: "project-prefix"')
        tm.that(rendered_config, lacks="issue-prefix:")
        tm.that(rendered_config, lacks="dolt.auto-start:")
        tm.that(rendered_config, lacks="gc.endpoint_origin")
        tm.that(rendered_config, lacks="gc.endpoint_status")
        tm.that(rendered_config, lacks="Gas City contract")
        if rendered_mise is None:
            pytest.fail("standalone identity must produce the managed Mise manifest")
        tm.that(rendered_mise, lacks="gascity")
        tm.that(rendered_mise, has='[tools."github:marlon-costa-dc/beads"]')

    def test_mise_manifest_provisions_managed_make(self, tmp_path: Path) -> None:
        """The generated ``.mise.toml`` must declare make as a managed tool.

        Root cause (R1): when make is absent from [tools], direnv resolves
        make from the stale host shim (conda-carried) instead of a Mise
        installation, so ``make setup`` exits 1. The projection must own
        make so the setup runtime resolves/executes it without conda.
        """
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )

        plan = self._plan(root)
        rendered_mise = self._rendered(plan, ".mise.toml")

        if rendered_mise is None:
            pytest.fail("conform must produce the managed .mise.toml")
        tm.that(rendered_mise, has='make = "latest"')
        tm.that(rendered_mise, lacks="conda")

    def test_gascity_disabled_renders_local_envrc_tier(self, tmp_path: Path) -> None:
        """A disabled city renders the repository-local bd activation tier."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        u.Tests.write_standalone_workspace_manifest(
            root, "fixture-project", gascity_enabled=False
        )

        plan = self._plan(root)
        rendered_envrc = self._rendered(plan, ".envrc")

        if rendered_envrc is None:
            pytest.fail("standalone identity must produce the managed .envrc")
        tm.that(rendered_envrc, lacks="AGENTS_GAS_CITY_ROOT")
        tm.that(rendered_envrc, lacks="dolt-state.json")
        tm.that(rendered_envrc, lacks="jq -er")
        tm.that(rendered_envrc, has='watch_file "$checkout_root/.beads/metadata.json"')
        tm.that(
            rendered_envrc, has="unset BEADS_DOLT_SERVER_HOST BEADS_DOLT_SERVER_PORT"
        )
        tm.that(rendered_envrc, has="unset BEADS_DOLT_AUTO_START")

    def test_envrc_local_generated_residue_is_normalized(self, tmp_path: Path) -> None:
        """The merge keeps custom overrides and strips stale generated sections.

        Every member checkout carries a historical generated ``Gas City Beads
        activation`` section in ``.envrc.local`` duplicating the managed
        ``.envrc`` block with drifted jq conditions; conform is the single
        activation owner and removes exactly that residue.
        """
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        _ = (root / ".envrc.local").write_text(
            "# Generated by `flext-infra codegen conform`.\n"
            "# === SECTION: Gas City Beads activation (managed) ===\n"
            "unset GT_ROOT\n"
            'source_env_if_exists "$HOME/.config/environment.d/projects/agent-tools.envrc"\n'
            "# End SECTION: Gas City Beads activation\n"
            "export CUSTOM_OVERRIDE=1\n",
            encoding="utf-8",
        )

        entry = next(
            (
                item
                for item in self._plan(root).files
                if item.path.name == ".envrc.local"
            ),
            None,
        )

        if entry is None or entry.desired_content is None:
            pytest.fail("custom overrides must keep .envrc.local planned")
        desired = entry.desired_content.decode("utf-8")
        tm.that(desired, has="export CUSTOM_OVERRIDE=1")
        tm.that(desired, lacks="SECTION")
        tm.that(desired, lacks="Generated by")
        tm.that(desired, lacks="GT_ROOT")

    def test_envrc_local_without_custom_content_is_removed(
        self, tmp_path: Path
    ) -> None:
        """A .envrc.local carrying only generated residue is deleted."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        _ = (root / ".envrc.local").write_text(
            "# Generated by `flext-infra codegen conform`.\n"
            "# === SECTION: Gas City Beads activation (managed) ===\n"
            "unset GT_ROOT\n"
            "# End SECTION: Gas City Beads activation\n",
            encoding="utf-8",
        )

        entry = next(
            (
                item
                for item in self._plan(root).files
                if item.path.name == ".envrc.local"
            ),
            None,
        )

        if entry is None:
            pytest.fail("residue-only .envrc.local must be planned for removal")
        tm.that(entry.desired_content, none=True)

    def test_gascity_enabled_sources_activate_conditionally(
        self, tmp_path: Path
    ) -> None:
        """Generated envrc sources host files only when they exist.

        Isolated CI checkouts render the same Gas City participation as a
        city-connected host, but they carry no host environment files: a hard
        ``source_env`` there breaks direnv activation and the contract gate.
        """
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        u.Tests.write_standalone_workspace_manifest(
            root, "fixture-project", gascity_enabled=True
        )

        plan = self._plan(root)
        rendered_envrc = self._rendered(plan, ".envrc")

        if rendered_envrc is None:
            pytest.fail("city participation must produce the managed .envrc")
        tm.that(rendered_envrc, has='source_env_if_exists "$HOME/.config/')
        tm.that(
            rendered_envrc,
            lacks='source_env "$HOME/.config/environment.d/projects/agent-tools.envrc"',
        )
        tm.that(rendered_envrc, has="AGENTS_GAS_CITY_ROOT must name the canonical")

    def test_metadata_projection_preserves_a_minted_ledger_identity(
        self, tmp_path: Path
    ) -> None:
        """Regenerating must not strip the checkout's own ledger identity.

        Rendering the marker without `project_id` stripped the key on every
        `make gen`, and Beads then minted a fresh identity on next access —
        rig `gmn` lost 2b1a0582-… that way (commit 3e7ba1e).
        """
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        minted = "e9a551fc-a6f8-4e0e-a961-2505f49bc8a3"
        identity = root / ".beads" / "identity.toml"
        identity.parent.mkdir(parents=True, exist_ok=True)
        identity.write_text(f'[project]\nid = "{minted}"\n')
        (root / c.Infra.BEADS_METADATA_RELPATH).write_text(
            '{"backend":"dolt"}\n', encoding="utf-8"
        )

        rendered = self._rendered(self._plan(root), c.Infra.BEADS_METADATA_RELPATH)
        if rendered is None:
            pytest.fail("local identity must produce the Beads marker")
        metadata = u.Tests.json_payload(rendered)
        tm.that(metadata["project_id"], eq=minted)
        tm.that(
            set(metadata),
            eq={"database", "backend", "dolt_mode", "dolt_database", "project_id"},
        )

    def test_projection_preserves_the_manual_identity_input(
        self, tmp_path: Path
    ) -> None:
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        identity = root / "config" / "beads.yaml"
        before = identity.read_bytes()

        _ = self._plan(root)

        tm.that(identity.read_bytes(), eq=before)

    def test_codegen_exposes_no_beads_runtime_surface(self) -> None:
        forbidden_models = ("BeadsPlan", "BeadsTrackerDeclaration")
        forbidden_operations = (
            "_beads_binary",
            "_beads_command",
            "_beads_ledger_root",
            "_verify_beads_plan",
            "beads_declaration",
            "ledger_identity_for_target",
        )

        for model_name in forbidden_models:
            tm.that(hasattr(m.Infra, model_name), eq=False)
        for operation_name in forbidden_operations:
            tm.that(hasattr(FlextInfraCodegenConform, operation_name), eq=False)
        tool_fields = m.Infra.BeadsToolSpec.model_fields
        tm.that("reported_version" in tool_fields, eq=False)
        tm.that("checksum" in tool_fields, eq=False)
        tm.that("expected_schema" in tool_fields, eq=False)
        # The declarative endpoint projection survived, but caa162de0 split the
        # single `endpoint` field into the origin/status pair. Asserting the
        # retired name kept this test red against a model that is correct.
        tm.that("endpoint" in tool_fields, eq=False)
        tm.that("endpoint_origin" in tool_fields, eq=True)
        tm.that("endpoint_status" in tool_fields, eq=True)


__all__: list[str] = ["TestsFlextInfraCodegenBeadsProjection"]
