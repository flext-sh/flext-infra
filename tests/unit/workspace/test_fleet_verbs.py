"""Exercise fleet verbs through the real public CLI and member Make recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from shlex import quote
from signal import SIGTERM

import pytest

from flext_infra import main
from flext_infra.workspace import FlextInfraWorkspaceFleetVerbs
from tests import c, m, tm, u


class TestsFlextInfraWorkspaceFleetVerbs:
    """A workspace verb reaches every governed member through its own Make."""

    @staticmethod
    def _workspace(
        root: Path,
        *,
        exit_code: int = 0,
        signal_make: bool = False,
    ) -> Path:
        """Compose a governed workspace whose member records each fleet verb.

        Returns:
            The attached member checkout.
        """
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        log = quote(str(root / "fleet.log"))
        verbs = " ".join(verb.value for verb in c.Infra.FleetVerb)
        signal_command = 'kill -TERM "$$PPID"; ' if signal_make else ""
        (member / "Makefile").write_text(
            f".PHONY: {verbs}\n"
            f"{verbs}:\n"
            f"\t@printf '%s|%s|%s\\n' '$(CURDIR)' '$@' \"$${{MAKELEVEL:-0}}\""
            f" >> {log}; "
            "printf 'fleet-fixture-output\\n'; "
            f"{signal_command}"
            f"exit {exit_code}\n",
            encoding=c.DEFAULT_ENCODING,
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

    @staticmethod
    def _runtime_graph(
        root: Path, *, provider_failure: bool = False
    ) -> tuple[str, ...]:
        """Compose real Make consumers with dev and examples backedges."""
        identity = u.Tests.BeadsIdentity(
            workspace="fleet-order",
            database="fleet_order",
            issue_prefix="fleet",
        )
        u.Tests.WorktreeFixture.initialize_governed_project(
            root, "fixture-workspace", beads=identity
        )
        names = ("a-consumer", "z-provider", "b-ready")
        log = quote(str(root / "fleet.log"))
        for name in names:
            member = root / name
            u.Tests.WorktreeFixture.initialize_governed_project(
                member, name, beads=identity
            )
            u.Tests.WorktreeFixture.attach_submodule(
                root, member, distribution=name, relative_path=name
            )
            dependencies = ["z-provider"] if name == "a-consumer" else []
            backedge = ["a-consumer"] if name == "z-provider" else []
            (member / c.PYPROJECT_FILENAME).write_text(
                f"[project]\nname = '{name}'\nversion = '1.0'\n"
                f"dependencies = {dependencies!r}\n"
                "[dependency-groups]\n"
                f"dev = {backedge!r}\nexamples = {backedge!r}\n",
                encoding=c.DEFAULT_ENCODING,
            )
            status = 7 if name == "z-provider" and provider_failure else 0
            (member / c.Infra.MAKEFILE_FILENAME).write_text(
                ".PHONY: fix\nfix:\n"
                f"\t@printf '%s|%s\\n' '{name}' '$(CURDIR)' >> {log}\n"
                f"\t@printf 'member-output-{name}\\n'; exit {status}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        u.Tests.commit_git_changes(root, "declare complete fleet runtime graph")
        return ("b-ready", "z-provider", "a-consumer")

    def test_executes_runtime_waves_serially_from_workspace_root(
        self, tmp_path: Path
    ) -> None:
        """Actual Make executions follow runtime waves despite dev backedges."""
        root = tmp_path / "workspace"
        order = self._runtime_graph(root)

        tm.that(self._run(root, c.Infra.FleetVerb.FIX), eq=0)

        report = self._report(root)
        tm.that(report.scope, eq=tuple(root / name for name in order))
        tm.that(
            tuple(row.command[-2] for row in report.receipts),
            eq=tuple(f"{name}/Makefile" for name in order),
        )
        tm.that(
            (root / "fleet.log").read_text(encoding=c.DEFAULT_ENCODING).splitlines(),
            eq=[f"{name}|{root}" for name in order],
        )

    def test_provider_failure_prevents_later_member_execution(
        self, tmp_path: Path
    ) -> None:
        """A failed provider preserves attempted receipts and stops the consumer."""
        root = tmp_path / "workspace"
        order = self._runtime_graph(root, provider_failure=True)

        tm.that(self._run(root, c.Infra.FleetVerb.FIX) != 0, eq=True)

        report = self._report(root)
        tm.that(report.scope, eq=tuple(root / name for name in order))
        tm.that(len(report.receipts), eq=2)
        tm.that(report.receipts[-1].error is not None, eq=True)
        tm.that(
            (root / "fleet.log").read_text(encoding=c.DEFAULT_ENCODING).splitlines(),
            eq=[f"{name}|{root}" for name in order[:2]],
        )
        tm.that(
            report.receipts[-1].output_file.read_text(encoding=c.DEFAULT_ENCODING),
            has="member-output-z-provider",
        )

    def test_missing_member_makefile_prevents_all_effects(self, tmp_path: Path) -> None:
        """Every required Makefile is admitted before the first invocation."""
        root = tmp_path / "workspace"
        self._runtime_graph(root)
        (root / "a-consumer" / c.Infra.MAKEFILE_FILENAME).unlink()

        tm.that(self._run(root, c.Infra.FleetVerb.FIX) != 0, eq=True)

        tm.that((root / "fleet.log").exists(), eq=False)

    def test_runtime_cycle_prevents_all_member_effects(self, tmp_path: Path) -> None:
        """The public fleet service preserves the canonical runtime-cycle failure."""
        root = tmp_path / "workspace"
        self._runtime_graph(root)
        project = root / "z-provider" / c.PYPROJECT_FILENAME
        project.write_text(
            project.read_text(encoding=c.DEFAULT_ENCODING).replace(
                "dependencies = []",
                "dependencies = ['a-consumer']",
                1,
            ),
            encoding=c.DEFAULT_ENCODING,
        )

        service = FlextInfraWorkspaceFleetVerbs(
            repository_root=root,
            verb=c.Infra.FleetVerb.FIX,
        )
        with pytest.raises(ValueError, match="^cyclic dependency graph:"):
            service.execute()

        tm.that((root / "fleet.log").exists(), eq=False)

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
            eq=((root, (c.Infra.MAKE, "-f", "sample-member/Makefile", verb.value)),),
        )
        for row in report.receipts:
            assert row.outcome is not None
            tm.that(u.Cli.process_succeeded(row.outcome), eq=True)
            tm.that(row.outcome.timed_out, eq=False)
            tm.that(row.outcome.forwarded_signal, eq=None)
        tm.that(all(row.error is None for row in report.receipts), eq=True)
        tm.that(
            report.receipts[0].output_file.read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
            has="fleet-fixture-output",
        )
        tm.that(
            (root / "fleet.log").read_text(encoding=c.DEFAULT_ENCODING).splitlines(),
            # A top-level Make exports MAKELEVEL=1 to its recipe; the
            # inherited level 3 would have produced 4.
            eq=[f"{root}|{verb.value}|1"],
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
        assert failed.outcome is not None
        tm.that(failed.outcome.raw_return_code != 0, eq=True)
        tm.that(failed.outcome.timed_out, eq=False)
        tm.that(failed.outcome.forwarded_signal, eq=None)
        tm.that(failed.error is not None, eq=True)
        tm.that(
            failed.output_file.read_text(encoding=c.DEFAULT_ENCODING),
            has="fleet-fixture-output",
        )

    def test_member_make_signal_retains_the_native_negative_return_code(
        self,
        tmp_path: Path,
    ) -> None:
        """A real terminated Make process remains distinct from recipe findings."""
        root = tmp_path / "workspace"
        self._workspace(root, signal_make=True)

        tm.that(self._run(root, c.Infra.FleetVerb.FIX) != 0, eq=True)

        failed = self._report(root).receipts[0]
        assert failed.outcome is not None
        tm.that(failed.outcome.raw_return_code, eq=-int(SIGTERM))
        tm.that(failed.outcome.timed_out, eq=False)
        # The child terminated Make; the operator forwarded no signal.
        tm.that(failed.outcome.forwarded_signal, eq=None)
        tm.that(failed.error is not None, eq=True)

    def test_standalone_rejects_before_any_member_effect(
        self,
        tmp_path: Path,
    ) -> None:
        """A standalone checkout has no members to carry a verb to."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "standalone")

        tm.that(self._run(root, c.Infra.FleetVerb.MOD) != 0, eq=True)

        tm.that((root / c.Infra.FLEET_REPORT_RELATIVE_PATH).exists(), eq=False)
