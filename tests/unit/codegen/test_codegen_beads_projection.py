"""Projection-only contract for repository-owned Beads configuration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm

from tests.unit.workspace.worktree_fixture import WorktreeFixture


class TestsCodegenBeadsProjection:
    """Keep codegen on its declarative projection boundary."""

    @staticmethod
    def _project(
        root: Path,
        *,
        database: str,
        issue_prefix: str,
        custom_issue_types: tuple[str, ...] = (),
    ) -> Path:
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="fixture-workspace",
            database=database,
            issue_prefix=issue_prefix,
            custom_issue_types=custom_issue_types,
        )
        return root

    @staticmethod
    def _plan(root: Path) -> m.Infra.CodegenPlan:
        result = FlextInfraCodegenConform(workspace_root=root).plan(
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
        return None if match is None else match.rendered

    def test_local_identity_renders_only_declarative_beads_files(
        self, tmp_path: Path
    ) -> None:
        root = self._project(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
            custom_issue_types=("incident",),
        )

        plan = self._plan(root)
        rendered_config = self._rendered(plan, c.Infra.BEADS_CONFIG_RELPATH)
        rendered_metadata = self._rendered(plan, c.Infra.BEADS_METADATA_RELPATH)

        if rendered_config is None or rendered_metadata is None:
            pytest.fail("local identity must produce both Beads projections")
        beads = config.Infra.codegen.toolchain.beads
        tm.that(rendered_config, has='issue-prefix: "project-prefix"')
        tm.that(rendered_config, has='issue_prefix: "project-prefix"')
        tm.that(rendered_config, has=f"gc.endpoint_origin: {beads.endpoint_origin}")
        tm.that(rendered_config, has=f"gc.endpoint_status: {beads.endpoint_status}")
        tm.that(
            rendered_config,
            has="types.custom: " + ",".join(("incident", *beads.required_custom_types)),
        )
        tm.that("dolt.host" in rendered_config, eq=False)
        tm.that("dolt.port" in rendered_config, eq=False)
        metadata = json.loads(rendered_metadata)
        tm.that(metadata["database"], eq="dolt")
        tm.that(metadata["backend"], eq="dolt")
        tm.that(metadata["dolt_database"], eq="project_database")
        tm.that(metadata["dolt_mode"], eq="server")
        tm.that(set(metadata), eq={"database", "backend", "dolt_mode", "dolt_database"})
        tm.that(hasattr(plan, "beads"), eq=False)

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
        tm.that("endpoint" in tool_fields, eq=False)
        tm.that("endpoint_origin" in tool_fields, eq=True)
        tm.that("endpoint_status" in tool_fields, eq=True)
        tm.that("required_custom_types" in tool_fields, eq=True)
