"""The Mise transaction selects exactly the planned per-repository configurations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, t
from flext_infra.codegen._conform import FlextInfraCodegenConformFilePlans
from tests import tm, u


class TestsFlextInfraCodegenConformMiseConfigPlans:
    """One planned Mise configuration per selected repository, fail-loud otherwise."""

    @staticmethod
    def _plan(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        *,
        uv_environments: t.VariadicTuple[m.Infra.UvEnvironmentPlan],
        files: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> m.Infra.CodegenPlan:
        """Build the public plan carrier with the selection under test.

        Args:
            root: The root path of the project.
            workspace: The workspace specification.
            uv_environments: A tuple of UV environment plans.
            files: A tuple of file plans.

        Returns:
            An instance of `m.Infra.CodegenPlan` representing the public plan carrier.

        """
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        return m.Infra.CodegenPlan(
            request=request,
            repositories=(),
            workspace=workspace,
            make_spec=config.Infra.codegen.make,
            uv_environments=uv_environments,
            files=files,
        )

    @staticmethod
    def _mise_file_plan(root: Path) -> m.Infra.CodegenFilePlan:
        """Plan one real .mise.toml projection from its on-disk state.

        Args:
            root: The root path of the project.

        Returns:
            An instance of `m.Infra.CodegenFilePlan` representing the planned file.

        """
        path = root / c.Infra.MISE_TOML_FILENAME
        path.write_text('min_version = "2024"\n', encoding="utf-8")
        state = u.Cli.atomic_read_binary_file_state(path, required=True)
        return m.Infra.CodegenFilePlan(
            project=root,
            path=path,
            before=tm.ok(state),
            desired_content=b'min_version = "2024"\n',
            desired_mode=0o644,
        )

    def test_empty_environment_plan_fails_before_the_transaction(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A plan without uv environments cannot reach the Mise transaction."""
        root = infra_git_repo
        plan = self._plan(
            root,
            u.Tests.standalone_workspace(root, config.Infra.name),
            uv_environments=(),
            files=(),
        )

        selected = FlextInfraCodegenConformFilePlans.mise_config_plans(plan)

        assert selected.failure
        assert "carries no uv environment plan" in (selected.error or "")

    def test_one_environment_selects_its_configuration(
        self,
        infra_git_repo: Path,
    ) -> None:
        """Each selected repository contributes exactly its own configuration."""
        root = infra_git_repo
        environment = m.Infra.UvEnvironmentPlan(
            project_root=root,
            environment_root=root,
            python_version=config.Infra.codegen.toolchain.python_version,
            groups=("dev",),
        )
        file_plan = self._mise_file_plan(root)
        plan = self._plan(
            root,
            u.Tests.standalone_workspace(root, config.Infra.name),
            uv_environments=(environment,),
            files=(file_plan,),
        )

        selected = FlextInfraCodegenConformFilePlans.mise_config_plans(plan)

        assert not selected.failure
        assert tuple(item.path for item in selected.value) == (
            root / c.Infra.MISE_TOML_FILENAME,
        )

    def test_environment_without_its_configuration_fails(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A selected repository whose configuration plan is absent fails loud."""
        root = infra_git_repo
        environment = m.Infra.UvEnvironmentPlan(
            project_root=root,
            environment_root=root,
            python_version=config.Infra.codegen.toolchain.python_version,
            groups=("dev",),
        )
        plan = self._plan(
            root,
            u.Tests.standalone_workspace(root, config.Infra.name),
            uv_environments=(environment,),
            files=(),
        )

        selected = FlextInfraCodegenConformFilePlans.mise_config_plans(plan)

        assert selected.failure
        assert "one Mise configuration per repository" in (selected.error or "")
