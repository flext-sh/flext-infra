"""Command-replay runner test utilities for flext-infra."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import override

from flext_infra import r
from tests import m, p, t


class TestsFlextInfraUtilitiesReplayRunnerMixin:
    """Protocol-compatible command runner replaying one fixed result."""

    class DeptryRunner(p.Cli.CommandRunner):
        """Protocol-compatible runner backed by a real Result."""

        def __init__(self, result: p.Result[m.Cli.CommandOutput]) -> None:
            """Store the typed command result."""
            self._result = result
            self.commands: MutableSequence[t.StrSequence] = []

        def _command_result(self) -> p.Result[m.Cli.CommandOutput]:
            """Return the result this invocation must replay.

            The only thing a replaying runner varies is where its result
            comes from, so subclasses override this instead of
            re-declaring every protocol signature.
            """
            return self._result

        def _replay(
            self,
            cmd: t.StrSequence,
            *,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            """Record the invocation and replay this runner's stored result."""
            del cwd, timeout, env, remove_env_keys, input_data, capture
            self.commands.append(tuple(cmd))
            result = self._command_result()
            if result.failure:
                return r[p.Cli.CommandOutput].from_failure(result)
            return r[p.Cli.CommandOutput].ok(result.value)

        @override
        def run_raw(
            self,
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            return self._replay(
                cmd,
                cwd=cwd,
                timeout=timeout,
                env=env,
                remove_env_keys=remove_env_keys,
                input_data=input_data,
                capture=capture,
            )

        @override
        def run(
            self,
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            replay = self._replay(
                cmd,
                cwd=cwd,
                timeout=timeout,
                env=env,
                remove_env_keys=remove_env_keys,
                input_data=input_data,
                capture=capture,
            )
            if replay.failure:
                return r[p.Cli.CommandOutput].from_failure(replay)
            output = replay.value
            if output.outcome.raw_return_code != 0:
                return r[p.Cli.CommandOutput].fail(
                    output.stderr or output.stdout or "Command failed"
                )
            return r[p.Cli.CommandOutput].ok(output)

        @override
        def run_bytes(
            self,
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
        ) -> p.Result[p.Cli.CommandBytesOutput]:
            """Return the configured command payload with byte-exact streams."""
            self.commands.append(tuple(cmd))
            del cmd, cwd, timeout, env, remove_env_keys, input_data
            result = self._command_result()
            if result.failure:
                return r[p.Cli.CommandBytesOutput].from_failure(result)
            output = result.value
            return r[p.Cli.CommandBytesOutput].ok(
                m.Cli.CommandBytesOutput(
                    stdout=output.stdout.encode(),
                    stderr=output.stderr.encode(),
                    outcome=output.outcome,
                    duration=output.duration,
                )
            )

        @override
        def capture(
            self,
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
        ) -> p.Result[str]:
            """Provide the typed test helper `capture`."""
            del input_data
            result = self.run(
                cmd, cwd=cwd, timeout=timeout, env=env, remove_env_keys=remove_env_keys
            )
            if result.failure:
                return r[str].from_failure(result)
            return r[str].ok(result.unwrap().stdout.strip())

        @override
        def run_checked(
            self,
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[bool]:
            """Provide the typed test helper `run_checked`."""
            del input_data, capture
            result = self.run(
                cmd, cwd=cwd, timeout=timeout, env=env, remove_env_keys=remove_env_keys
            )
            if result.failure:
                return r[bool].from_failure(result)
            return r[bool].ok(True)

        @override
        def run_live(
            self,
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
        ) -> p.Result[p.Cli.CommandOutput]:
            """Provide the typed test helper `run_live`.

            Live output is a property of the real process, not of a replayed
            result, so this behaves exactly like the checked `run`.
            """
            return self.run(
                cmd,
                cwd=cwd,
                timeout=timeout,
                env=env,
                remove_env_keys=remove_env_keys,
                input_data=input_data,
            )

        @override
        def run_to_file(
            self,
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            heartbeat_seconds: float | None = None,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[p.Cli.ProcessOutcome]:
            """Provide the typed test helper `run_to_file`."""
            del input_data, live, heartbeat_seconds, deadline
            result = self.run_raw(
                cmd, cwd=cwd, timeout=timeout, env=env, remove_env_keys=remove_env_keys
            )
            if result.failure:
                return r[p.Cli.ProcessOutcome].from_failure(result)
            output_path = (
                output_file if isinstance(output_file, Path) else Path(output_file)
            )
            output_path.write_text(
                f"{result.value.stdout}{result.value.stderr}", encoding="utf-8"
            )
            return r[p.Cli.ProcessOutcome].ok(result.value.outcome)


__all__: list[str] = ["TestsFlextInfraUtilitiesReplayRunnerMixin"]
