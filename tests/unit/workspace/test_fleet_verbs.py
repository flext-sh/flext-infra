"""Exercise fleet verbs through the real public CLI and member Make recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from shlex import quote

import pytest
from flext_tests import tm

from flext_infra import main
from tests import c, m, u


class TestsFlextInfraWorkspaceFleetVerbs:
    """A workspace verb reaches every governed member through its own Make."""

    @staticmethod
    def _workspace(root: Path, *, exit_code: int = 0) -> Path:
        """Compose a governed workspace whose member records each fleet verb.

        Returns:
            The attached member checkout.
        """
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        log = quote(str(root / "fleet.log"))
        verbs = " ".join(verb.value for verb in c.Infra.FleetVerb)
        (member / "Makefile").write_text(
            f".PHONY: {verbs}\n"
            f"{verbs}:\n"
            f"\t@printf '%s|%s|%s\\n' '$(CURDIR)' '$@' \"$${{MAKELEVEL:-0}}\""
            f" >> {log}; "
            "printf 'fleet-fixture-output\\n'; "
            f"exit {exit_code}\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        return member

    @staticmethod
    def _run(root: Path, verb: c.Infra.FleetVerb) -> int:
        """Invoke the public fleet route.

        Returns:
            The CLI exit code.
        """
        return main([
            c.Infra.CLI_GROUP_WORKSPACE,
            c.Infra.FLEET_ROUTE_NAME,
            "--repository-root",
            str(root),
            "--verb",
            verb.value,
        ])

    @staticmethod
    def _report(root: Path) -> m.Infra.LifecycleReport:
        """Read the typed receipt the workspace publishes.

        Returns:
            The published fleet report.
        """
        return m.Infra.LifecycleReport.model_validate_json(
            (root / c.Infra.FLEET_REPORT_RELATIVE_PATH).read_bytes(),
        )

    @pytest.mark.parametrize("verb", tuple(c.Infra.FleetVerb))
    def test_runs_the_member_own_verb_without_inherited_make_flags(
        self,
        tmp_path: Path,
        verb: c.Infra.FleetVerb,
    ) -> None:
        """Each governed member runs the verb itself, as a top-level Make."""
        root = tmp_path / "workspace"
        member = self._workspace(root)

        with u.Tests.env_vars_context(
            env_vars={"MAKEFLAGS": "-n -j8", "MAKELEVEL": "3"},
        ):
            tm.that(self._run(root, verb), eq=0)

        report = self._report(root)
        tm.that(report.workspace_root, eq=root)
        tm.that(report.scope, eq=(member,))
        tm.that(
            tuple((row.cwd, row.command) for row in report.receipts),
            eq=((member, (c.Infra.MAKE, verb.value)),),
        )
        tm.that(all(row.exit_code == 0 for row in report.receipts), eq=True)
        tm.that(all(row.error is None for row in report.receipts), eq=True)
        tm.that(
            report.receipts[0].output_file.read_text(
                encoding=c.Cli.ENCODING_DEFAULT,
            ),
            has="fleet-fixture-output",
        )
        tm.that(
            (root / "fleet.log")
            .read_text(encoding=c.Cli.ENCODING_DEFAULT)
            .splitlines(),
            # A top-level Make exports MAKELEVEL=1 to its recipe; the
            # inherited level 3 would have produced 4.
            eq=[f"{member}|{verb.value}|1"],
        )

    def test_member_failure_fails_the_run_with_its_receipt(
        self,
        tmp_path: Path,
    ) -> None:
        """A failed member verb is red and keeps its causal output."""
        root = tmp_path / "workspace"
        self._workspace(root, exit_code=7)

        tm.that(self._run(root, c.Infra.FleetVerb.FIX) != 0, eq=True)

        failed = self._report(root).receipts[0]
        tm.that(failed.exit_code not in {None, 0}, eq=True)
        tm.that(failed.error is not None, eq=True)
        tm.that(
            failed.output_file.read_text(encoding=c.Cli.ENCODING_DEFAULT),
            has="fleet-fixture-output",
        )

    def test_standalone_rejects_before_any_member_effect(
        self,
        tmp_path: Path,
    ) -> None:
        """A standalone checkout has no members to carry a verb to."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "standalone")

        tm.that(self._run(root, c.Infra.FleetVerb.MOD) != 0, eq=True)

        tm.that((root / c.Infra.FLEET_REPORT_RELATIVE_PATH).exists(), eq=False)
