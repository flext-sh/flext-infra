"""Projection-only contract for repository-owned Beads configuration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import codegen, config, workspace
from tests import c, m, t, tm, u


class TestsFlextInfraCodegenBeadsProjection:
    """Keep codegen on its declarative projection boundary."""

    @staticmethod
    @pytest.mark.parametrize(
        ("distribution", "kind"),
        [
            ("sample-library", c.Infra.ProjectKind.INTERNAL_FLEXT),
            ("acme-service", c.Infra.ProjectKind.INTERNAL),
        ],
    )
    @pytest.mark.slow
    def test_governed_builder_uses_project_owned_catalogue(
        tmp_path: Path,
        distribution: str,
        kind: c.Infra.ProjectKind,
    ) -> None:
        """Plan real repositories without borrowing another project's identity."""
        root = tmp_path / distribution
        pyproject = u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=distribution,
                database=distribution.replace("-", "_"),
                issue_prefix=distribution,
            ),
        )
        catalogue = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        tm.ok(
            u.Cli.toml_write_mapping(
                pyproject,
                {
                    **tm.ok(u.Cli.toml_read_json(pyproject)),
                    "build-system": {
                        "requires": list(catalogue.scaffold.build.requirements),
                        "build-backend": catalogue.scaffold.build.backend,
                    },
                },
            ),
        )
        project = u.Tests.project_spec(distribution)
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {
                                "kind": kind.value,
                                "project": project.model_dump(mode="json"),
                            },
                        },
                    },
                },
            ),
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        declared = tm.ok(
            workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
                root, inputs=inputs
            ),
        )

        plan = u.Tests.governed_project_plan(root)

        tm.that(plan.issues, eq=())
        tm.that(plan.workspace.repository, eq=declared.repository)
        tm.that(plan.workspace.repository.kind, eq=kind)
        tm.that(plan.workspace.repository.package, eq=True)
        tm.that(plan.workspace.project, eq=declared.project)
        for managed in inputs.spec.managed_file_specs:
            tm.that((root / managed.path).parent.is_dir(), eq=True)
        package_dir = root / c.Infra.DEFAULT_SRC_DIR / project.package_name
        for family in u.Infra.facade_families().values():
            if (package_dir / family.directory).is_dir():
                tm.that(
                    (package_dir / f"{family.module}.py").read_text(encoding="utf-8"),
                    has=f"class {project.class_stem}{family.suffix}:",
                )
        tm.that(
            tuple(path.name for path in (root / c.Infra.DEFAULT_SRC_DIR).iterdir()),
            eq=(project.package_name,),
        )

    @staticmethod
    def _standalone_governed_plan(root: Path) -> m.Infra.CodegenPlan:
        """Plan a standalone fixture with city participation disabled.

        Returns:
            The governed codegen plan for the standalone project.

        """
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="project_database",
                issue_prefix="project-prefix",
            ),
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME,
                {"Infra": {"codegen": {"repository": {"gascity_enabled": False}}}},
            ),
        )
        return u.Tests.governed_project_plan(root)

    @staticmethod
    def _planned_envrc_local_entry(root: Path) -> m.Infra.CodegenFilePlan | None:
        """Return the planned local activation artifact.

        Returns:
            The local activation entry, or None when it is unplanned.

        """
        plan = u.Tests.governed_project_plan(root)
        return next(
            (item for item in plan.files if item.path.name == ".envrc.local"),
            None,
        )

    @pytest.mark.parametrize("prefix", [None, ("tracker-wrapper", "read", "beads")])
    def test_ownership_policy_roundtrips_through_repository_identity(
        self,
        tmp_path: Path,
        prefix: t.StrTuple | None,
    ) -> None:
        """Project the selected command without assuming a particular backend."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
            custom_issue_types=("triage",),
        )
        identity = tm.ok(workspace.FlextInfraWorkspaceDetector.load_beads_spec(root))
        if prefix is not None:
            tm.ok(
                u.Cli.yaml_dump(
                    root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME,
                    {
                        "Infra": {
                            "codegen": {
                                "toolchain": {
                                    "beads": {"ownership_command_prefix": list(prefix)},
                                },
                            },
                        },
                    },
                ),
            )
        policy = tm.ok(u.Infra.load_codegen_inputs(root)).spec.toolchain.beads
        rendered = tm.not_none(
            u.Tests.planned_text(
                u.Tests.governed_project_plan(root),
                "config/beads.yaml",
            ),
        )
        (root / "config" / "beads.yaml").write_text(rendered, encoding="utf-8")

        observed = tm.ok(workspace.FlextInfraWorkspaceDetector.load_beads_spec(root))

        tm.that(observed.ownership_command_prefix, eq=policy.ownership_command_prefix)
        tm.that(observed.custom_issue_types, eq=identity.custom_issue_types)
        tm.that(observed.workspace, eq=identity.workspace)
        tm.that(observed.database, eq=identity.database)
        tm.that(observed.issue_prefix, eq=identity.issue_prefix)
        if prefix is not None:
            tm.that(observed.ownership_command_prefix, eq=prefix)
        cwd = tm.not_none(observed.ownership_command_cwd)
        tm.fail(cwd.is_absolute())
        tm.that((root / cwd).resolve(), eq=root.resolve())

    @pytest.mark.parametrize("prefix", [None, (), ("",)])
    @staticmethod
    def test_ownership_policy_requires_a_nonempty_command(
        prefix: t.StrTuple | None,
    ) -> None:
        """Missing or empty selected policy never becomes a default backend."""
        policy = config.Infra.codegen.toolchain.beads
        payload = policy.model_dump(round_trip=True)
        if prefix is None:
            del payload["ownership_command_prefix"]
        else:
            payload["ownership_command_prefix"] = prefix
        with pytest.raises(ValueError, match="ownership_command_prefix"):
            type(policy).model_validate(payload)

    @staticmethod
    def _project(
        root: Path,
        *,
        database: str,
        issue_prefix: str,
        custom_issue_types: t.StrTuple = (),
    ) -> Path:
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database=database,
                issue_prefix=issue_prefix,
            ),
            custom_issue_types=custom_issue_types,
        )
        return root

    def test_local_identity_renders_declarative_beads_routing(
        self,
        tmp_path: Path,
    ) -> None:
        """Test local identity renders declarative beads routing."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )

        plan = u.Tests.governed_project_plan(root)
        rendered_config = u.Tests.planned_text(plan, c.Infra.BEADS_CONFIG_RELPATH)
        rendered_metadata = u.Tests.planned_text(plan, c.Infra.BEADS_METADATA_RELPATH)

        if rendered_config is None:
            pytest.fail("local identity must produce the declarative Beads config")
        # `issue_prefix` is the key bd itself resolves (`bd config get
        # issue_prefix`); a hyphen-only prefix reads as unset, so bd appended its
        # own key on first write. A Gas City rig also carries gc's canonical
        # mirror keys: gc rewrites a managed rig's config into exactly that key
        # set on every adopt and start, so a projection in any other form left
        # every governed checkout dirty after each gc pass.
        beads = config.Infra.codegen.toolchain.beads
        parsed = tm.ok(u.Cli.yaml_parse(rendered_config))
        tm.that(parsed["issue_prefix"], eq="project-prefix")
        tm.that(parsed["issue-prefix"], eq="project-prefix")
        tm.that(parsed["dolt.mode"], eq=beads.dolt_mode)
        tm.that(
            parsed["dolt"],
            eq={"disable-event-flush": beads.dolt_disable_event_flush},
        )
        tm.fail("dolt.disable-event-flush" in parsed)
        # A checkout with no workspace manifest declares city participation by
        # fleet default (True): the endpoint keys mirror the inherited city and
        # `types.custom` stays generator-owned.
        tm.that(rendered_config, has="gc.endpoint_origin:")
        tm.that(rendered_config, has="gc.endpoint_status:")
        tm.that(rendered_config, has="types.custom:")
        tm.that(rendered_config, has="dolt.auto-start:")
        if rendered_metadata is None:
            pytest.fail("local identity must produce the declarative Beads marker")
        metadata = u.Tests.json_payload(rendered_metadata)
        tm.that(metadata["backend"], eq="dolt")
        tm.that(metadata["database"], eq="dolt")
        tm.that(metadata["dolt_database"], eq="project_database")
        tm.that(
            metadata["dolt_mode"],
            eq=config.Infra.codegen.toolchain.beads.dolt_mode,
        )
        # A fresh checkout has no checkout-owned identity.toml. Conform owns
        # the portable routing marker but never mints the ledger identity.
        tm.fail("project_id" in metadata)
        tm.that(set(metadata), eq={"backend", "database", "dolt_mode", "dolt_database"})
        # gc writes this marker as a sorted-key JSON object; the projection uses
        # the same order so gc's first write after adoption is byte-identical.
        tm.that(list(metadata), eq=sorted(metadata))

    def test_gascity_disabled_renders_standalone_beads_config(
        self,
        tmp_path: Path,
    ) -> None:
        """A disabled city never moves runtime ownership into generated config."""
        plan = self._standalone_governed_plan(tmp_path / "project")
        rendered_config = u.Tests.planned_text(plan, c.Infra.BEADS_CONFIG_RELPATH)
        rendered_mise = u.Tests.planned_text(plan, ".mise.toml")

        if rendered_config is None:
            pytest.fail("standalone identity must produce the declarative Beads config")
        tm.that(rendered_config, has='issue_prefix: "project-prefix"')
        tm.that(rendered_config, lacks="issue-prefix:")
        tm.that(rendered_config, lacks="dolt.auto-start:")
        # The mode mirror and the event-flush switch are read only by gc; a
        # standalone ledger carries neither (bd takes the flush switch from its
        # environment and the mode from metadata.json).
        tm.that(rendered_config, lacks="dolt.mode:")
        tm.that(rendered_config, lacks="disable-event-flush")
        tm.that(rendered_config, lacks="gc.endpoint_origin")
        tm.that(rendered_config, lacks="gc.endpoint_status")
        tm.that(rendered_config, lacks="Gas City contract")
        if rendered_mise is None:
            pytest.fail("standalone identity must produce the managed Mise manifest")
        # bd and gc are host binaries owned by the global mise config; a
        # project manifest never declares either distribution.
        tm.that(rendered_mise, lacks="beads")
        tm.that(rendered_mise, lacks="gascity")

    def test_mise_manifest_leaves_make_system_owned(self, tmp_path: Path) -> None:
        """The generated ``.mise.toml`` never declares make.

        Make, curl and Git are system-owned: the generated Makefile resolves the
        physical make that invoked it before changing PATH, so recursive
        lifecycle calls keep that invoker instead of a Mise shim (toolchain
        tools table, config/codegen.yaml).
        """
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )

        plan = u.Tests.governed_project_plan(root)
        rendered_mise = u.Tests.planned_text(plan, ".mise.toml")

        if rendered_mise is None:
            pytest.fail("conform must produce the managed .mise.toml")
        tm.fail("make" in config.Infra.codegen.toolchain.tool_versions)
        tm.that(rendered_mise, lacks="\nmake = ")
        tm.that(rendered_mise, lacks="conda")
        tm.that(rendered_mise, lacks="stale")

    def test_generated_envrc_excludes_storage_routing(self, tmp_path: Path) -> None:
        """The project activation leaves Beads routing to native discovery."""
        plan = self._standalone_governed_plan(tmp_path / "project")
        rendered_envrc = u.Tests.planned_text(plan, ".envrc")

        if rendered_envrc is None:
            pytest.fail("standalone identity must produce the managed .envrc")
        tm.that(rendered_envrc, lacks="AGENTS_GAS_CITY_ROOT")
        tm.that(rendered_envrc, lacks="dolt-state.json")
        tm.that(rendered_envrc, lacks="jq -er")
        tm.that(rendered_envrc, lacks="BEADS_DOLT_")
        tm.that(rendered_envrc, lacks="BEADS_DIR")

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
            "source_env_if_exists "
            '"${HOME}/.config/environment.d/projects/agent-tools.envrc"\n'
            "# End SECTION: Gas City Beads activation\n"
            "export CUSTOM_OVERRIDE=1\n",
            encoding="utf-8",
        )

        entry = self._planned_envrc_local_entry(root)

        if entry is None or entry.desired_content is None:
            pytest.fail("custom overrides must keep .envrc.local planned")
        desired = entry.desired_content.decode("utf-8")
        tm.that(desired, has="export CUSTOM_OVERRIDE=1")
        tm.that(desired, lacks="SECTION")
        tm.that(desired, lacks="Generated by")
        tm.that(desired, lacks="GT_ROOT")

    def test_envrc_local_without_custom_content_is_removed(
        self,
        tmp_path: Path,
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

        entry = self._planned_envrc_local_entry(root)

        if entry is None:
            pytest.fail("residue-only .envrc.local must be planned for removal")
        tm.that(entry.desired_content, none=True)

    @pytest.mark.slow
    @pytest.mark.parametrize("gascity_enabled", [True, False])
    def test_envrc_is_storage_neutral_in_both_workspace_modes(
        self,
        tmp_path: Path,
        *,
        gascity_enabled: bool,
    ) -> None:
        """Workspace association never changes the storage-neutral activation."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {"repository": {"gascity_enabled": gascity_enabled}},
                    },
                },
            ),
        )

        rendered_envrc = u.Tests.planned_text(
            u.Tests.governed_project_plan(root),
            ".envrc",
        )

        if rendered_envrc is None:
            pytest.fail("a governed identity must produce the managed .envrc")
        tm.that(rendered_envrc, lacks="AGENTS_GAS_CITY_ROOT")
        tm.that(rendered_envrc, lacks="BEADS_DOLT_")

    def test_metadata_projection_preserves_a_minted_ledger_identity(
        self,
        tmp_path: Path,
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
            '{"backend":"dolt"}\n',
            encoding="utf-8",
        )

        rendered = u.Tests.planned_text(
            u.Tests.governed_project_plan(root),
            c.Infra.BEADS_METADATA_RELPATH,
        )
        if rendered is None:
            pytest.fail("local identity must produce the Beads marker")
        metadata = u.Tests.json_payload(rendered)
        tm.that(metadata["project_id"], eq=minted)
        tm.that(
            set(metadata),
            eq={"database", "backend", "dolt_mode", "dolt_database", "project_id"},
        )
        tm.that(list(metadata), eq=sorted(metadata))

    def test_projection_preserves_the_manual_identity_input(
        self,
        tmp_path: Path,
    ) -> None:
        """Test projection preserves the manual identity input."""
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )
        identity = root / "config" / "beads.yaml"
        before = identity.read_bytes()

        _ = u.Tests.governed_project_plan(root)

        tm.that(identity.read_bytes(), eq=before)

    @staticmethod
    def test_beads_gate_lock_is_tolerated_runtime_state(tmp_path: Path) -> None:
        """The bd gate serialization marker never fails composed verification.

        The bd client writes ``dolt.gate.lock`` beside the ledger on every gate
        transaction — the same projection class as ``.exclusive-lock`` and
        ``.sync.lock``. A composed project whose member holds one (live or left
        by a dead holder) must still verify; an actual stranger file must not.
        """
        route = tmp_path / c.Infra.BEADS_DIRNAME
        route.mkdir(mode=0o700)
        (route / Path(c.Infra.BEADS_CONFIG_RELPATH).name).write_text(
            "{}\n",
            encoding="utf-8",
        )
        (route / "dolt.gate.lock").write_text("", encoding="utf-8")

        state = codegen.FlextInfraCodegenConform.beads_route_state(tmp_path)

        tm.fail(state.failure)
        tm.ok(state.value)

        (route / "stranger.txt").write_text("unexpected\n", encoding="utf-8")

        broken = codegen.FlextInfraCodegenConform.beads_route_state(tmp_path)

        tm.ok(broken.failure)
        tm.ok(broken.error is not None and "stranger.txt" in broken.error)
