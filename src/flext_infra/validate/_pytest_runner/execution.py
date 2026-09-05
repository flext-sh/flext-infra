"""Strict process lifecycle for the canonical pytest runner."""

from __future__ import annotations

import shlex
import sys
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.validate._pytest_runner.command import FlextInfraPytestRunnerCommand
from flext_infra.validate._pytest_runner.reports import FlextInfraPytestRunnerReports
from flext_infra.validate.testmon_db import FlextInfraTestmonDbInspector

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraPytestRunnerExecution(
    FlextInfraPytestRunnerCommand, FlextInfraPytestRunnerReports
):
    """Execute pytest once and reject incomplete evidence."""

    def _inspect_cache(
        self, *, digest: str | None
    ) -> p.Result[m.Infra.TestmonCacheState]:
        """Run the SQLite integrity owner for the external database."""
        return FlextInfraTestmonDbInspector(
            repository_root=self.root, db_path=self.testmon_db, pre_run_digest=digest
        ).execute()

    @override
    def execute(self) -> p.Result[int]:
        """Execute one whole-suite cached or full testmon invocation."""
        pytest = config.Infra.tooling.tools.pytest
        report_dir = self._report_directory()
        pytest_log = report_dir / "pytest.log"
        u.Cli.ensure_dir(self.testmon_db.parent).unwrap()
        pre_digest = FlextInfraTestmonDbInspector.digest_file(self.testmon_db)
        cache_restored = False
        if pre_digest is not None:
            pre_state = self._inspect_cache(digest=pre_digest).unwrap()
            cache_restored = pre_state.restored_accepted
            if not cache_restored:
                msg = f"testmon preflight rejected cache: {pre_state.reason}"
                raise RuntimeError(msg)
        command = self.build_command(report_dir)
        u.Cli.atomic_write_text_file(
            report_dir / "command.txt", f"{shlex.join(command)}\n"
        ).unwrap()
        deadline = m.Cli.ProcessDeadline(
            expires_at_monotonic=self.started_at_monotonic + pytest.run_timeout_seconds,
            termination_grace_seconds=pytest.termination_grace_seconds,
            timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
        )
        child_env = u.Cli.process_env(
            remove_keys=c.Infra.PYTEST_INHERITED_ENV_REMOVE_KEYS,
            overrides={
                c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                    self.root / c.Infra.DEFAULT_SRC_DIR
                ),
                c.Infra.PYTEST_ENV_TESTMON_DATAFILE: str(self.testmon_db),
            },
        )
        exit_code = u.Cli.run_to_file(
            command,
            pytest_log,
            cwd=self.root,
            env=child_env,
            live=True,
            deadline=deadline,
        ).unwrap()
        if exit_code != 0:
            return r.ok(exit_code)
        state = self._inspect_cache(digest=pre_digest).unwrap()
        if not state.restored_accepted and not state.saveable:
            msg = f"testmon cache is unusable: {state.reason}"
            raise RuntimeError(msg)
        accounting = self._accounting(
            report_dir / "junit.xml", pytest_log, cache_restored=cache_restored
        ).unwrap()
        self._validate_coverage(report_dir).unwrap()
        diagnostics = self._diagnostics(report_dir).unwrap()
        self._write_diagnostics(report_dir, diagnostics)
        rejected = any((
            diagnostics.failed_count,
            diagnostics.error_count,
            diagnostics.warning_count,
            diagnostics.skipped_count,
        ))
        final_exit = 1 if rejected else 0
        summary = (
            f"executed={accounting.executed_count}\n"
            f"deselected={accounting.deselected_count}\n"
            f"cache_restored={accounting.cache_restored}\n"
            f"failed={diagnostics.failed_count}\nerrors={diagnostics.error_count}\n"
            f"warnings={diagnostics.warning_count}\nskipped={diagnostics.skipped_count}\n"
            f"cache_state={state.reason}\nexit={final_exit}\n"
        )
        u.Cli.atomic_write_text_file(report_dir / "summary.txt", summary).unwrap()
        u.Cli.atomic_write_text_file(
            self.root / self.reports / "latest.txt", f"{report_dir.name}\n"
        ).unwrap()
        sys.stderr.write(f"Reports: {report_dir}\n")
        return r.ok(final_exit)


__all__: list[str] = ["FlextInfraPytestRunnerExecution"]
