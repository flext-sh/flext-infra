"""Fleet execution through installed editables and generated native member verbs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from signal import SIGTERM

import pytest

from flext_infra import FlextInfraCli
from flext_infra.workspace import (
    FlextInfraWorkspaceEnvironmentProvenance,
    FlextInfraWorkspaceFleetVerbs,
)
from tests import c, m, tm, u


class TestsFlextInfraWorkspaceFleetVerbs:
    """Observe actual generated Make consumers in their provisioned runtime."""

    @staticmethod
    def _run(root: Path, verb: c.Infra.FleetVerb) -> int:
        """Invoke the public fleet CLI without replacing any member recipe.

        Returns:
            The resulting CLI exit code.

        """
        return FlextInfraCli.infra_main([
            c.Infra.CLI_GROUP_WORKSPACE,
            c.Infra.FLEET_ROUTE_NAME,
            "--repository-root",
            str(root),
            "--verb",
            verb.value,
        ])

    @staticmethod
    def _report(root: Path) -> m.Infra.LifecycleReport:
        """Read the invocation's native process receipts.

        Returns:
            The validated native lifecycle report.

        """
        return m.Infra.LifecycleReport.model_validate_json(
            (root / c.Infra.FLEET_REPORT_RELATIVE_PATH).read_bytes(),
        )

    @staticmethod
    def _members(root: Path) -> tuple[m.Infra.RepositoryRef, ...]:
        """Authenticate installed sources before observing their runtime order.

        Returns:
            The installed members in declared workspace dependency order.

        """
        members = tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.editable_members(root),
        )
        by_distribution = {member.distribution: member for member in members}
        return tuple(
            by_distribution[name]
            for name in u.Infra.workspace_dependency_order(root, members)
        )

    @pytest.mark.parametrize("verb", [c.Infra.FleetVerb.FIX, c.Infra.FleetVerb.FMT])
    def test_generated_member_verbs_use_authenticated_sources_and_root_cwd(
        self,
        installed_fleet_workspace: Path,
        verb: c.Infra.FleetVerb,
    ) -> None:
        """Actual formatter and repair commands retain declared dependency order."""
        root = installed_fleet_workspace
        members = self._members(root)
        tm.that(members, empty=False)
        with u.Tests.env_vars_context(
            env_vars={"MAKEFLAGS": "-n -j8", "MAKELEVEL": "3"},
        ):
            tm.that(self._run(root, verb), eq=0)
        report = self._report(root)
        tm.that(report.scope, eq=tuple(root / member.path for member in members))
        tm.that(report.executed_commands, eq=len(members))
        tm.that(report.unreached_commands, eq=0)
        for member, receipt in zip(members, report.receipts, strict=True):
            tm.that(receipt.cwd, eq=root)
            tm.that(receipt.repository_root, eq=root / member.path)
            tm.that(
                receipt.command,
                eq=(
                    c.Infra.MAKE,
                    "-f",
                    (member.path / c.Infra.MAKEFILE_FILENAME).as_posix(),
                    verb.value,
                ),
            )
            outcome = tm.not_none(receipt.outcome)
            tm.ok(u.Cli.process_succeeded(outcome))
            tm.that(receipt.applicable, eq=True)
            tm.that(receipt.error, eq=None)
            tm.ok(receipt.output_file.is_file())

    def test_native_formatter_failure_preserves_unreached_consumers(
        self,
        installed_fleet_workspace: Path,
    ) -> None:
        """Invalid Python reaches the actual formatter and stops dependent effects."""
        root = installed_fleet_workspace
        members = self._members(root)
        provider, consumer = members
        source = next((root / provider.path / "src").rglob("*.py"))
        invalid = "def invalid( ->:\n"
        source.write_text(invalid, encoding=c.DEFAULT_ENCODING)

        tm.ok(self._run(root, c.Infra.FleetVerb.FMT) != 0)

        report = self._report(root)
        tm.that(report.scope, eq=tuple(root / member.path for member in members))
        tm.that(len(report.receipts), eq=len(members))
        failed, unreached = report.receipts
        outcome = tm.not_none(failed.outcome)
        tm.fail(u.Cli.process_succeeded(outcome))
        tm.that(failed.error, empty=False)
        tm.that(failed.output_file.read_text(encoding=c.DEFAULT_ENCODING), empty=False)
        tm.that(unreached.repository_root, eq=root / consumer.path)
        tm.that(unreached.outcome, eq=None)
        tm.that(unreached.applicable, eq=None)
        tm.that(report.failed_commands, eq=1)
        tm.that(report.unreached_commands, eq=1)
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=invalid)

    def test_missing_required_makefile_prevents_all_member_effects(
        self,
        installed_fleet_workspace: Path,
    ) -> None:
        """Authenticate the complete selected Make surface before any mutation."""
        root = installed_fleet_workspace
        members = self._members(root)
        report_path = root / c.Infra.FLEET_REPORT_RELATIVE_PATH
        before = report_path.read_bytes() if report_path.exists() else None
        (root / members[-1].path / c.Infra.MAKEFILE_FILENAME).unlink()

        tm.ok(self._run(root, c.Infra.FleetVerb.FMT) != 0)

        after = report_path.read_bytes() if report_path.exists() else None
        tm.that(after, eq=before)

    def test_native_hook_signal_retains_negative_status_and_unreached_consumer(
        self,
        native_fleet_signal_hook: Path,
    ) -> None:
        """The exact generated fleet Make ancestry terminates without parent effects."""
        root = native_fleet_signal_hook
        members = self._members(root)

        tm.ok(self._run(root, c.Infra.FleetVerb.FMT) != 0)

        report = self._report(root)
        tm.that(report.scope, eq=tuple(root / member.path for member in members))
        failed, unreached = report.receipts
        outcome = tm.not_none(failed.outcome)
        tm.that(outcome.raw_return_code, eq=-int(SIGTERM))
        tm.that(outcome.forwarded_signal, eq=None)
        tm.fail(outcome.timed_out)
        tm.that(failed.error, empty=False)
        tm.that(
            failed.output_file.read_text(encoding=c.DEFAULT_ENCODING),
            has="Native fleet hook sends SIGTERM to its exact Make ancestry",
        )
        tm.that(unreached.outcome, eq=None)
        tm.that(report.failed_commands, eq=1)
        tm.that(report.unreached_commands, eq=1)

    def test_runtime_cycle_prevents_member_execution(
        self,
        installed_fleet_workspace: Path,
    ) -> None:
        """The live declared runtime graph rejects a cycle before native effects."""
        root = installed_fleet_workspace
        provider, consumer = self._members(root)
        manifest = root / provider.path / c.PYPROJECT_FILENAME
        payload = u.Tests.toml_payload(manifest.read_text(encoding=c.DEFAULT_ENCODING))
        project = u.Tests.toml_mapping(payload["project"])
        tm.ok(
            u.Cli.toml_write_mapping(
                manifest,
                {
                    **payload,
                    "project": {
                        **project,
                        "dependencies": [
                            *u.Tests.toml_strings(project["dependencies"]),
                            consumer.distribution,
                        ],
                    },
                },
            ),
        )
        service = FlextInfraWorkspaceFleetVerbs(
            repository_root=root,
            verb=c.Infra.FleetVerb.FMT,
        )
        with pytest.raises(ValueError, match=r"^cyclic dependency graph:"):
            service.execute()

    def test_standalone_rejects_before_any_member_effect(
        self,
        installed_artifact_consumer: Path,
    ) -> None:
        """An actual provisioned standalone consumer has no fleet mutation scope."""
        root = installed_artifact_consumer
        tm.ok(self._run(root, c.Infra.FleetVerb.FMT) != 0)
        tm.fail((root / c.Infra.FLEET_REPORT_RELATIVE_PATH).exists())
