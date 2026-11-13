"""Public conformance fixture inputs and typed invocation state.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from typing_extensions import TypeForm

from flext_infra import check, codegen, infra, u
from tests import TestsFlextInfraUtilitiesToml, c, config, m, p


class TestsFlextInfraUtilitiesConform:
    """Own conformance requests without coupling lazy-init execution fixtures."""

    @staticmethod
    def family_public_module(family: str) -> str:
        """Return the public facade module stem the core package gives a letter.

        Returns:
            The public facade module stem the core package gives a letter.

        """
        return u.Infra.facade_families()[family].module

    @staticmethod
    def ruff_policy_toml() -> str:
        """Render the fleet Ruff policy as a pyproject fragment.

        Reads the same typed SSOT production reads (P0): fixture
        workspaces carry the real rule selection, elected rule owners, native
        convention, preview, and import policy without exemption tables.

        Returns:
            The resulting ``str``.

        """
        ruff_cfg = config.Infra.tooling.tools.ruff
        delegated = check.FlextInfraGateRegistry.default().delegated_lint_rules(
            ruff_cfg.lint.rule_owners,
            check_gates=config.Infra.codegen.make.check_gates_default,
            repair_gates=(
                *config.Infra.codegen.make.check_gates_fixable,
                *config.Infra.codegen.make.fmt_gates,
            ),
        )
        options = u.Infra.native_tool_configuration(config.Infra.tooling, "ruff")
        options["target-version"] = (
            "py" + config.Infra.codegen.toolchain.python_version.replace(".", "")
        )
        lint = u.Cli.toml_mapping_ensure_table(options, "lint")
        u.Cli.toml_mapping_sync_string_list(
            lint,
            "ignore",
            sorted({
                *delegated,
                *ruff_cfg.lint.ruling_disabled_rules,
                *u.Infra.native_tool_setting(
                    config.Infra.tooling,
                    "ruff.lint",
                    "ignore",
                    TypeForm(Sequence[str]),
                ),
            }),
        )
        return u.Cli.toml_dumps(
            u.Cli.toml_document_from_mapping({"tool": {"ruff": options}})
        )

    @staticmethod
    def conform_request(
        root: Path,
        *,
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
        scope: c.Infra.CodegenConformScope = c.Infra.CodegenConformScope.SELF,
        mode: c.Infra.CodegenConformMode = c.Infra.CodegenConformMode.CHECK,
    ) -> p.Infra.CodegenConformRequest:
        """Build one codegen conform request; every default is the model's own.

        Returns:
            The resulting ``m.Infra.CodegenConformRequest``.

        """
        return m.Infra.CodegenConformRequest(
            root=root,
            what=what,
            scope=scope,
            mode=mode,
        )

    @staticmethod
    def conform_plan(
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
        *,
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
        executor_root: Path | None = None,
    ) -> p.Infra.CodegenPlan:
        """Plan one fixture workspace through the public conform boundary.

        Returns:
            The resulting ``m.Infra.CodegenPlan``.

        """
        request = TestsFlextInfraUtilitiesConform.conform_request(root, what=what)
        return TestsFlextInfraUtilitiesConform.conform_plan_result(
            root if executor_root is None else executor_root,
            request,
            workspace=workspace,
        ).unwrap()

    @staticmethod
    def conform_plan_result(
        root: Path,
        request: p.Infra.CodegenGenerateRequest,
        *,
        workspace: p.Infra.WorkspaceSpec | None = None,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan through a planner bound to the public conform collaborators.

        Returns:
            The planning result exactly as the public conform boundary binds it.

        """
        return codegen.FlextInfraCodegenConform.Generate(
            repository_root=root,
            state=m.Infra.CodegenConformState(
                repository_root=root,
                request=request,
                initial_workspace=workspace,
                ports=infra.codegen_conform_collaborators(),
                snapshot=snapshot,
            ),
            runtime_settings=infra.settings,
            initial_context=infra.context,
        ).plan(request)

    @staticmethod
    def conform_makefile_text(root: Path, workspace: p.Infra.WorkspaceSpec) -> str:
        """Render the root Makefile conform plans for one fixture workspace.

        Returns:
            The resulting ``str``.

        """
        plan = TestsFlextInfraUtilitiesConform.conform_plan(
            root,
            workspace,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        return TestsFlextInfraUtilitiesToml.codegen_file_text(makefile)


__all__ = ["TestsFlextInfraUtilitiesConform"]
