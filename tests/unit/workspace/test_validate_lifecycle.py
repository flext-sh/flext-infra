"""Public lifecycle planning and real native Make first-failure receipts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, main
from flext_infra.workspace import FlextInfraWorkspaceLifecycle
from tests import c, m, p, tm, u


class TestsFlextInfraWorkspaceLifecycle:
    """Observe real topology and process boundaries without substitute recipes."""

    @staticmethod
    def _request(root: Path) -> p.Infra.WorkspaceRequest:
        """Construct the same typed request the public CLI validates.

        Returns:
            The repository request.

        """
        return m.Infra.WorkspaceRequest(repository_root=root)

    def test_plan_uses_root_cwd_and_declared_steps_without_duplicate_fanout(
        self,
        tmp_path: Path,
    ) -> None:
        """Root-owned stages execute once; member consumers use their Makefile."""
        root = tmp_path / "workspace"
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)

        report = tm.ok(
            FlextInfraWorkspaceLifecycle.plan_request(self._request(root)),
        )

        tm.that(report.scope, eq=(root, member))
        expected = tuple(
            (repository, step.verb)
            for step in config.Infra.codegen.make.lifecycle_steps
            for repository in (
                report.scope if step.scope == "each" else (report.workspace_root,)
            )
        )
        tm.that(
            tuple((row.repository_root, row.command[-1]) for row in report.receipts),
            eq=expected,
        )
        for receipt in report.receipts:
            tm.that(receipt.cwd, eq=root)
            tm.that(receipt.outcome, eq=None)
            if receipt.repository_root == member:
                tm.that(
                    receipt.command[:-1],
                    eq=(c.Infra.MAKE, "-f", str(member / c.Infra.MAKEFILE_FILENAME)),
                )
            else:
                tm.that(receipt.command[:-1], eq=(c.Infra.MAKE,))
        tm.that((root / c.Infra.LIFECYCLE_REPORT_RELATIVE_PATH).exists(), eq=False)

    def test_standalone_plan_has_the_same_public_acceptance_boundary(
        self,
        tmp_path: Path,
    ) -> None:
        """A standalone project retains every declared acceptance command."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "standalone")

        report = tm.ok(
            FlextInfraWorkspaceLifecycle.plan_request(self._request(root)),
        )

        tm.that(report.scope, eq=(root,))
        tm.that(
            tuple(row.command[-1] for row in report.receipts),
            eq=tuple(step.verb for step in config.Infra.codegen.make.lifecycle_steps),
        )

    def test_native_make_failure_retains_first_outcome_and_unreached_commands(
        self,
        tmp_path: Path,
    ) -> None:
        """A real unprovisioned fixture has no Makefile; native Make rejects it."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "unprovisioned")
        tm.that((root / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)
        with u.Tests.env_vars_context(env_vars={"MAKEFLAGS": "-n -j8"}):
            result = FlextInfraWorkspaceLifecycle.execute_request(self._request(root))

        tm.fail(result)
        report = m.Infra.LifecycleReport.model_validate_json(
            (root / c.Infra.LIFECYCLE_REPORT_RELATIVE_PATH).read_bytes(),
        )
        first, *unreached = report.receipts
        tm.that(first.outcome is not None, eq=True)
        if first.outcome is not None:
            tm.that(u.Cli.process_succeeded(first.outcome), eq=False)
        tm.that(first.applicable, eq=True)
        tm.that(first.error, empty=False)
        tm.that(first.output_file.is_file(), eq=True)
        tm.that(first.before_files, eq=first.after_files)
        tm.that(
            tuple(item.path for item in first.before_files),
            eq=tuple(
                root / relative
                for relative in config.Infra.codegen.make.lifecycle_observed_files
            ),
        )
        tm.that(
            all(
                row.outcome is None
                and (row.applicable is None or row.applicable is False)
                for row in unreached
            ),
            eq=True,
        )
        tm.that(all(not row.output_file.exists() for row in unreached), eq=True)
        tm.that(report.executed_commands, eq=1)
        tm.that(report.failed_commands, eq=1)
        tm.that(
            report.unreached_commands + report.inapplicable_commands,
            eq=len(unreached),
        )

    def test_context_applicability_is_declared_and_not_reported_as_execution(
        self,
        tmp_path: Path,
    ) -> None:
        """An inapplicable context row keeps a reason and no process receipt."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "standalone")
        ci = config.Infra.codegen.make.ci
        with u.Tests.env_vars_context(env_vars={ci.variable: ci.value}):
            report = tm.ok(
                FlextInfraWorkspaceLifecycle.plan_request(self._request(root)),
            )
        for step, receipt in zip(
            config.Infra.codegen.make.lifecycle_steps,
            report.receipts,
            strict=True,
        ):
            tm.that(receipt.execution_context, eq="ci")
            tm.that(receipt.outcome, eq=None)
            if "ci" not in step.contexts:
                tm.that(receipt.applicable, eq=False)
                tm.that(receipt.applicability_reason, empty=False)
            else:
                tm.that(receipt.applicable, eq=None)
        tm.that(report.executed_commands, eq=0)

    def test_route_rejects_partial_project_selection_without_effects(
        self,
        tmp_path: Path,
    ) -> None:
        """The public request never accepts a partial fleet selector."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "standalone")

        tm.that(
            main([
                c.Infra.CLI_GROUP_WORKSPACE,
                "validate-lifecycle",
                "--repository-root",
                str(root),
                "--projects",
                ".",
            ]) != 0,
            eq=True,
        )
        tm.that((root / c.Infra.LIFECYCLE_REPORT_RELATIVE_PATH).exists(), eq=False)

    def test_ci_targets_only_the_invoking_root_without_electing_member_effects(
        self,
        tmp_path: Path,
    ) -> None:
        """CI scope narrows member work independently of editable declarations."""
        root = tmp_path / "workspace"
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        ci = config.Infra.codegen.make.ci
        with u.Tests.env_vars_context(env_vars={ci.variable: ci.value}):
            report = tm.ok(
                FlextInfraWorkspaceLifecycle.plan_request(self._request(root)),
            )
        member_rows = tuple(
            row for row in report.receipts if row.repository_root == member
        )
        tm.that(member_rows, empty=False)
        for row in member_rows:
            tm.that(row.applicable, eq=False)
            tm.that(row.applicability_reason, empty=False)
            tm.that(row.outcome, eq=None)
        tm.that(report.executed_commands, eq=0)
