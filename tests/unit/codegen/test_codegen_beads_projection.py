"""Projection-only contract for project-owned Beads configuration.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


class TestsCodegenBeadsProjection:
    """Keep flext-infra on its declarative projection boundary."""

    @staticmethod
    def _git(root: Path, *arguments: str) -> None:
        tm.ok(u.Cli.run_checked(["git", *arguments], cwd=root))

    @classmethod
    def _standalone_workspace(
        cls, root: Path, *, database: str, issue_prefix: str
    ) -> Path:
        """Create a standalone manifest whose baseline is entirely local."""
        provider = config.Infra.codegen.providers[0]
        repository = test_u.Tests.repository_ref(config.Infra.name)
        root.mkdir(parents=True)
        cls._git(root, "init", "-q", "-b", provider.branch)
        cls._git(root, "config", "user.email", "infra@example.com")
        cls._git(root, "config", "user.name", "Infra Tests")
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{repository.distribution}"\n'
            'version = "0.12.0.dev0"\nrequires-python = ">=3.13,<3.14"\n',
            encoding="utf-8",
        )
        package_init = (
            root / "src" / repository.distribution.replace("-", "_") / "__init__.py"
        )
        package_init.parent.mkdir(parents=True)
        package_init.write_text("", encoding="utf-8")
        local_repository = repository.model_copy(
            update={
                "path": Path(),
                "role": c.Infra.RepositoryRole.STANDALONE,
                "checkout": c.Infra.CheckoutKind.INDEPENDENT,
                "editable": False,
            }
        )
        spec = m.Infra.WorkspaceSpec(
            beads=m.Infra.BeadsOverrideSpec(
                version=1,
                workspace="flext",
                database=database,
                issue_prefix=issue_prefix,
            ),
            name=repository.distribution,
            repository=local_repository,
        )

        tm.ok(
            u.Cli.yaml_dump(
                root / c.Infra.BEADS_OVERRIDE_RELPATH,
                spec.beads.model_dump(mode="json"),
            )
        )
        cls._git(root, "add", "-A")
        cls._git(root, "commit", "-q", "--no-verify", "-m", "Seed workspace")
        cls._git(
            root,
            "remote",
            "add",
            "origin",
            f"{provider.base_url}/{repository.distribution}.git",
        )
        return root

    @staticmethod
    def _plan(root: Path) -> m.Infra.CodegenPlan:
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(workspace_root=root).plan(request)
        )
        return planned

    @staticmethod
    def _rendered(plan: m.Infra.CodegenPlan, destination: str) -> str | None:
        match = next(
            (item for item in plan.files if item.path.as_posix().endswith(destination)),
            None,
        )
        return match.rendered if match is not None else None

    @pytest.mark.slow
    def test_opted_standalone_renders_only_declarative_beads_files(
        self, tmp_path: Path
    ) -> None:
        root = self._standalone_workspace(
            tmp_path / "project",
            database="project_database",
            issue_prefix="project-prefix",
        )

        plan = self._plan(root)
        rendered_config = self._rendered(plan, c.Infra.BEADS_CONFIG_RELPATH)
        rendered_metadata = self._rendered(plan, c.Infra.BEADS_METADATA_RELPATH)

        if rendered_config is None or rendered_metadata is None:
            pytest.fail("opted standalone must receive both .beads projections")
        server = config.Infra.codegen.toolchain.beads.server
        if server is None:
            pytest.fail("projection SSOT must declare .beads server values")
        tm.that(rendered_config, has='issue-prefix: "project-prefix"')
        tm.that(rendered_config, has="database: project_database")
        tm.that(rendered_config, has=f"host: {server.host}")
        tm.that(rendered_config, has=f"port: {server.port}")
        metadata = json.loads(rendered_metadata)
        tm.that(metadata["dolt_database"], eq="project_database")
        tm.that(metadata["dolt_mode"], eq=server.mode)
        tm.that(hasattr(plan, "beads"), eq=False)

    def test_plain_standalone_always_receives_beads_files(self, tmp_path: Path) -> None:
        root = self._standalone_workspace(
            tmp_path / "plain", database="flext", issue_prefix="flext"
        )

        plan = self._plan(root)

        tm.that(self._rendered(plan, c.Infra.BEADS_CONFIG_RELPATH), none=False)
        tm.that(self._rendered(plan, c.Infra.BEADS_METADATA_RELPATH), none=False)

    def test_workspace_identity_is_only_projection_input(self, tmp_path: Path) -> None:
        branch_policy = config.Infra.codegen.branch_policy
        repository = test_u.Tests.repository_ref("flext")
        target = m.Infra.RepositoryConformTarget(
            repository=repository,
            root=tmp_path / "flext",
            make_profile=c.Infra.MakeProfile.WORKSPACE,
            beads_enabled=True,
            canonical_project_name=repository.distribution,
            baseline_branch=config.Infra.codegen.providers[0].branch,
            ci_enabled=True,
            external_dependency_paths=(),
            technical_branch_patterns=branch_policy.technical_branch_patterns,
            governed_branch_patterns=branch_policy.governed_branch_patterns,
        )
        workspace = m.Infra.WorkspaceSpec(
            beads=m.Infra.BeadsOverrideSpec(
                version=1,
                workspace="flext",
                database="project_database",
                issue_prefix="project-prefix",
            ),
            name=repository.distribution,
            repository=repository,
        )

        identity = FlextInfraCodegenConform.ledger_identity_for_target(
            workspace, target
        )

        tm.that(identity, eq=("project-prefix", "project_database"))

    def test_codegen_exposes_no_beads_runtime_surface(self) -> None:
        forbidden_models = ("BeadsPlan", "BeadsTrackerDeclaration")
        forbidden_operations = (
            "_beads_binary",
            "_beads_command",
            "_beads_ledger_root",
            "_verify_beads_plan",
            "beads_declaration",
        )

        for model_name in forbidden_models:
            tm.that(hasattr(m.Infra, model_name), eq=False)
        for operation_name in forbidden_operations:
            tm.that(hasattr(FlextInfraCodegenConform, operation_name), eq=False)
        tool_fields = m.Infra.BeadsToolSpec.model_fields
        tm.that("reported_version" in tool_fields, eq=False)
        tm.that("checksum" in tool_fields, eq=False)
        tm.that("expected_schema" in tool_fields, eq=False)
