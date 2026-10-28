"""Cohesive external-tool-runner mixin (deptry, pip-check) for detection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDepsDetectionRunners:
    """Mixin holding raw-run contract plus external analysis-tool runners."""

    @staticmethod
    def run_deptry(
        project_path: Path,
        venv_bin: Path,
        *,
        config_path: Path | None = None,
        json_output_path: Path | None = None,
    ) -> p.Result[tuple[Sequence[t.JsonMapping], int]]:
        """Consume every native deptry finding over the project's production source.

        Returns:
            The resulting ``p.Result[tuple[Sequence[t.JsonMapping], int]]``.

        """
        result_type = r[tuple[Sequence[t.JsonMapping], int]]
        settings = config_path or project_path / c.PYPROJECT_FILENAME
        reports = u.Cli.ensure_dir(project_path / c.Infra.REPORTS_DIR_NAME)
        if reports.failure:
            return result_type.from_failure(reports)
        out_file = json_output_path or (
            reports.value / f"deptry-report-{u.generate_id()}.json"
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
    def run_pip_check(
        repository_root: Path,
        venv_bin: Path,
    ) -> p.Result[tuple[Sequence[str], int]]:
        """Check the elected environment through the managed UV package checker.

        Returns:
            The resulting ``p.Result[tuple[Sequence[str], int]]``.

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
            return r[tuple[Sequence[str], int]].from_failure(result)
        cmd_result: p.Cli.CommandOutput = result.value
        outcome = cmd_result.outcome
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code not in {0, 1}
        ):
            receipt = m.Cli.ProcessOutcome.model_validate(
                outcome,
                from_attributes=True,
            ).model_dump_json()
            return r[tuple[Sequence[str], int]].fail(
                "UV package check failed: "
                f"{receipt}\n"
                f"stdout:\n{cmd_result.stdout}\nstderr:\n{cmd_result.stderr}",
            )
        lines = f"{cmd_result.stdout}\n{cmd_result.stderr}".strip().splitlines()
        return r[tuple[Sequence[str], int]].ok((
            lines,
            outcome.raw_return_code,
        ))


__all__: list[str] = ["FlextInfraDepsDetectionRunners"]
