"""Projection-only contract for repository-owned Beads configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u, u as test_u
from tests.unit.workspace import WorktreeFixture


class TestsCodegenBeadsProjection:
    """Keep codegen on its declarative projection boundary."""

    @staticmethod
    def _project(root: Path, *, database: str, issue_prefix: str) -> Path:
        WorktreeFixture.initialize_governed_project(
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
        result = FlextInfraCodegenConform(repository_root=root).plan(
            m.Infra.CodegenConformRequest(
                root=root,
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
            else test_u.Tests.codegen_file_text(match)
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
        tm.that(rendered_config, has="gc.endpoint_origin: inherited_city")
        tm.that(rendered_config, has="gc.endpoint_status: verified")
        tm.that(rendered_config, has="types.custom:")
        # Beads owns and mints metadata at first use. Codegen must not create
        # that runtime artifact in a fresh checkout.
        tm.that(rendered_metadata, none=True)
        tm.that(hasattr(plan, "beads"), eq=False)

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
