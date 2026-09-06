"""Command-result sequence and generic factory test utilities for flext-infra."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import override

from flext_infra import r
from tests import c, m, p, t
from tests.utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin


class TestsFlextInfraUtilitiesReplaySequenceMixin:
    """In-order command replay and typed fixture factory helpers."""

    class SequenceRunner(TestsFlextInfraUtilitiesReplayRunnerMixin.DeptryRunner):
        """Protocol-compatible runner that replays command results in order."""

        def __init__(
            self, results: t.SequenceOf[p.Result[m.Cli.CommandOutput]]
        ) -> None:
            """Store ordered command results for replay."""
            self._results = list(results)
            self._index = 0
            self.commands: MutableSequence[t.StrSequence] = []

        def _next_result(self) -> p.Result[m.Cli.CommandOutput]:
            current = self._index
            self._index = current + 1
            if not self._results:
                return r[m.Cli.CommandOutput].fail("runner result sequence is empty")
            return (
                self._results[current]
                if current < len(self._results)
                else self._results[-1]
            )

        @override
        def _command_result(self) -> p.Result[m.Cli.CommandOutput]:
            """Replay the next stored result instead of a single one."""
            return self._next_result()

    @staticmethod
    def command_runner(
        *, stdout: str = "", stderr: str = "", returncode: int = 0
    ) -> p.Cli.CommandRunner:
        """Provide the typed test helper `command_runner`."""
        return TestsFlextInfraUtilitiesReplayRunnerMixin.DeptryRunner(
            r.ok(
                TestsFlextInfraUtilitiesReplaySequenceMixin.stub_run(
                    stdout=stdout, stderr=stderr, returncode=returncode
                )
            )
        )

    @staticmethod
    def stub_run(
        *, stdout: str = "", stderr: str = "", returncode: int = 0
    ) -> m.Cli.CommandOutput:
        """Provide the typed test helper `stub_run`."""
        return m.Cli.CommandOutput(
            stdout=stdout,
            stderr=stderr,
            outcome=m.Cli.ProcessOutcome(
                raw_return_code=returncode, timed_out=False, forwarded_signal=None
            ),
        )

    @staticmethod
    def sequence_runner(
        *results: p.Result[m.Cli.CommandOutput],
    ) -> TestsFlextInfraUtilitiesReplaySequenceMixin.SequenceRunner:
        """Build one in-order command-result replaying runner."""
        return TestsFlextInfraUtilitiesReplaySequenceMixin.SequenceRunner(list(results))

    @staticmethod
    def create_command_output(
        *, stdout: str = "", stderr: str = "", exit_code: int = 0, duration: float = 0.0
    ) -> m.Cli.CommandOutput:
        """Provide the typed test helper `create_command_output`."""
        return m.Cli.CommandOutput(
            stdout=stdout,
            stderr=stderr,
            outcome=m.Cli.ProcessOutcome(
                raw_return_code=exit_code, timed_out=False, forwarded_signal=None
            ),
            duration=duration,
        )

    @staticmethod
    def create_project_info(
        project_root: Path,
        *,
        name: str = "test-project",
        stack: str = "python",
        has_tests: bool = False,
        has_src: bool = True,
        project_class: str = "FlextTestProject",
        package_name: str = "test_project",
        make_profile: c.Infra.MakeProfile = c.Infra.MakeProfile.STANDALONE,
        declared_subproject: bool = False,
    ) -> m.Infra.ProjectInfo:
        """Provide the typed test helper `create_project_info`."""
        return m.Infra.ProjectInfo(
            name=name,
            path=project_root,
            stack=stack,
            has_tests=has_tests,
            has_src=has_src,
            project_class=project_class,
            package_name=package_name,
            make_profile=make_profile,
            declared_subproject=declared_subproject,
        )


__all__: list[str] = ["TestsFlextInfraUtilitiesReplaySequenceMixin"]
