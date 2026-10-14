"""Cohesive external-tool-runner mixin (deptry, mypy stubs, pip-check) for detection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraDependencyDetectionRunnersMixin:
    """Mixin holding raw-run contract plus external analysis-tool runners."""

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
        *,
        config_path: Path | None = None,
        json_output_path: Path | None = None,
    ) -> p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]:
        """Consume every native deptry finding over the project's production source.

        Returns:
            The resulting ``p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]``.

        """
        result_type = r[t.Pair[t.SequenceOf[t.JsonMapping], int]]
        settings = config_path or project_path / c.PYPROJECT_FILENAME
        out_file = json_output_path or (
            project_path / f".deptry-report-{u.generate_id()}.json"
        )
        captured = u.Infra.capture_deptry_scan(
            project_path,
            venv_bin,
            config_path=settings,
            json_output_path=out_file,
        )
        if captured.failure:
            return result_type.from_failure(captured)
        if json_output_path is None:
            cleaned = u.Cli.atomic_delete_binary_file_guarded(
                captured.value.report_state
            )
            if cleaned.failure:
                return result_type.from_failure(cleaned)
        return result_type.ok((
            tuple(item.model_dump(mode="json") for item in captured.value.report.root),
            captured.value.native.outcome.raw_return_code,
        ))

    @staticmethod
    def run_mypy_stub_hints(
        project_path: Path,
    ) -> p.Result[t.Pair[t.StrSequence, t.StrSequence]]:
        """Run mypy via the command runner to detect missing stubs and hint packages.

        Returns:
            The resulting ``p.Result[t.Pair[t.StrSequence, t.StrSequence]]``.

        """
        # Why: current mypy emits ANSI color codes around quoted module/package
        # names even when stdout is a pipe, splicing escape sequences inside
        # the literal `for "name"` text that MYPY_STUB_RE/MYPY_HINT_RE match —
        # silently zeroing every detected stub hint. `--no-color-output`
        # matches the plain-text contract the regexes already assume (see
        # gates/mypy.py, which disables color for the same reason).
        cmd = u.Infra.mypy_limited_command(
            m.Infra.MypyInvocation(
                targets=(project_path / c.Infra.DEFAULT_SRC_DIR,),
                config_file=project_path / c.PYPROJECT_FILENAME,
            ),
        )
        result = u.Cli.run_raw(
            cmd,
            cwd=project_path,
            timeout=u.Infra.mypy_runner_timeout(),
        )
        if result.failure:
            return r[t.Pair[t.StrSequence, t.StrSequence]].fail(
                u.Infra.mypy_launch_failure_diagnostic(
                    result.error or "Mypy process launch failed",
                ),
            )
        command_output: p.Cli.CommandOutput = result.value
        if resource_diagnostic := u.Infra.mypy_failure_diagnostic(command_output):
            return r[t.Pair[t.StrSequence, t.StrSequence]].fail(resource_diagnostic)
        output = f"{command_output.stdout}\n{command_output.stderr}"
        hinted = {
            match.group(1).strip()
            for match in c.Infra.MYPY_HINT_RE.finditer(output)
            if match.group(1).strip()
        }
        missing = {
            match.group(1).strip()
            for match in c.Infra.MYPY_STUB_RE.finditer(output)
            if match.group(1).strip()
        }
        return r[t.Pair[t.StrSequence, t.StrSequence]].ok((
            sorted(hinted),
            sorted(missing),
        ))

    @staticmethod
    def run_pip_check(
        repository_root: Path,
        venv_bin: Path,
    ) -> p.Result[t.Pair[t.StrSequence, int]]:
        """Check the elected environment through the managed UV package checker.

        Returns:
            The resulting ``p.Result[t.Pair[t.StrSequence, int]]``.

        """
        result = u.Cli.run_raw(
            [
                c.Infra.UV,
                "pip",
                c.Infra.VERB_CHECK,
                "--python",
                str(venv_bin.parent),
            ],
            cwd=repository_root,
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if result.failure:
            return r[t.Pair[t.StrSequence, int]].from_failure(result)
        cmd_result: p.Cli.CommandOutput = result.value
        outcome = cmd_result.outcome
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code not in {0, 1}
        ):
            return r[t.Pair[t.StrSequence, int]].fail(
                f"UV package check failed: "
                f"{m.Cli.ProcessOutcome.model_validate(outcome, from_attributes=True).model_dump_json()}\n"
                f"stdout:\n{cmd_result.stdout}\nstderr:\n{cmd_result.stderr}",
            )
        lines = f"{cmd_result.stdout}\n{cmd_result.stderr}".strip().splitlines()
        return r[t.Pair[t.StrSequence, int]].ok((
            lines,
            outcome.raw_return_code,
        ))


__all__: list[str] = ["FlextInfraDependencyDetectionRunnersMixin"]
