"""Cohesive external-tool-runner mixin (deptry, mypy stubs, pip-check) for detection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
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
        extend_exclude: t.StrSequence | None = None,
    ) -> p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]:
        """Consume every native deptry finding over the project's production source.

        Returns:
            The resulting ``p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]``.

        """
        result_type = r[t.Pair[t.SequenceOf[t.JsonMapping], int]]
        settings = config_path or project_path / c.PYPROJECT_FILENAME
        settings_state = u.Cli.atomic_read_binary_file_state(settings, required=True)
        if settings_state.failure:
            return result_type.from_failure(settings_state)
        source = project_path / c.Infra.DEFAULT_SRC_DIR
        if not source.is_dir():
            return result_type.fail(f"deptry production source is missing: {source}")
        out_file = json_output_path or (
            project_path / f".deptry-report-{u.generate_id()}.json"
        )
        before = u.Cli.atomic_read_binary_file_state(out_file, required=False)
        if before.failure:
            return result_type.from_failure(before)
        if before.value.content is not None:
            return result_type.fail(
                f"deptry report destination already exists: {out_file}"
            )
        result = u.Cli.run_raw(
            self._deptry_command(venv_bin, settings, out_file, extend_exclude),
            cwd=project_path,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if result.failure:
            return result_type.from_failure(result)
        cmd_result: p.Cli.CommandOutput = result.value
        outcome = cmd_result.outcome
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code not in {0, 1}
        ):
            return result_type.fail(
                f"deptry process failed: {outcome.model_dump_json()}\n"
                f"stdout:\n{cmd_result.stdout}\nstderr:\n{cmd_result.stderr}"
            )
        report_state = u.Cli.atomic_read_binary_file_state(out_file, required=True)
        if report_state.failure:
            return result_type.from_failure(report_state)
        report_bytes = report_state.value.content
        if report_bytes is None:
            return result_type.fail(
                f"deptry did not produce its native report: {out_file}"
            )
        report = r[m.Infra.DeptryNativeReport].create_from_callable(
            partial(
                m.Infra.DeptryNativeReport.model_validate_json,
                report_bytes,
                strict=True,
            )
        )
        if report.failure:
            return result_type.from_failure(report)
        verified = u.Cli.atomic_verify_binary_file_states((
            settings_state.value,
            report_state.value,
        ))
        if verified.failure:
            return result_type.from_failure(verified)
        issues = tuple(item.model_dump(mode="json") for item in report.value.root)
        if outcome.raw_return_code != int(bool(issues)):
            return result_type.fail("deptry exit status contradicts its native report")
        cleaned = self._cleanup_deptry_output(out_file, json_output_path)
        if cleaned.failure:
            return result_type.from_failure(cleaned)
        return result_type.ok((
            issues,
            outcome.raw_return_code,
        ))

    @staticmethod
    def _deptry_command(
        venv_bin: Path,
        settings: Path,
        out_file: Path,
        extend_exclude: t.StrSequence | None,
    ) -> t.MutableSequenceOf[str]:
        """Compose the deptry invocation for one project.

        Returns:
            The composed deptry command line.

        """
        cmd: t.MutableSequenceOf[str] = [
            str(venv_bin / c.Infra.DEPTRY),
            str(c.Infra.DEFAULT_SRC_DIR),
            "--config",
            str(settings),
            "--json-output",
            str(out_file),
            "--no-ansi",
        ]
        if extend_exclude:
            for excluded in extend_exclude:
                cmd.extend(["--extend-exclude", excluded])
        return cmd

    @staticmethod
    def _cleanup_deptry_output(
        out_file: Path,
        json_output_path: Path | None,
    ) -> p.Result[bool]:
        """Remove the deptry temp report unless the caller owns the output path.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if json_output_path is None:
            try:
                out_file.unlink()
            except OSError as exc:
                return r[bool].fail(
                    f"failed to cleanup deptry temp output: {exc}",
                    exception=exc,
                )
        return r[bool].ok(value=True)

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
        """Run pip check to detect dependency conflicts in workspace.

        Returns:
            The resulting ``p.Result[t.Pair[t.StrSequence, int]]``.

        """
        pip = venv_bin / "pip"
        if not pip.exists():
            return r[t.Pair[t.StrSequence, int]].ok(([], 0))
        env = {"VIRTUAL_ENV": str(venv_bin.parent)}
        result = u.Cli.run_raw(
            [str(pip), c.Infra.VERB_CHECK],
            cwd=repository_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(env=env),
        )
        if result.failure:
            return r[t.Pair[t.StrSequence, int]].from_failure(result)
        cmd_result: p.Cli.CommandOutput = result.value
        output = cmd_result.stdout
        lines = output.strip().splitlines() if output else []
        return r[t.Pair[t.StrSequence, int]].ok((
            lines,
            cmd_result.outcome.raw_return_code,
        ))


__all__: list[str] = ["FlextInfraDependencyDetectionRunnersMixin"]
