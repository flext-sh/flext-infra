"""Silent failure quality gate.

Enforces silent-failure detection across every Python project the workspace
discovers. Per-project opt-out is expressed via the absence of Python
sources (``iter_python_files`` returning empty), not via a hand-curated
project-name allowlist.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra.constants import c
from flext_infra.detectors.silent_failure_detector import (
    FlextInfraSilentFailureDetector,
)
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraSilentFailureGate(FlextInfraGate):
    """Block silent failure sentinels in any Python project under the workspace."""

    gate_id: ClassVar[str] = "silent-failure"
    gate_name: ClassVar[str] = "Silent Failure"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = "Flext Silent Failure Detector"
    tool_url: ClassVar[str] = "internal://flext-infra/silent-failure"

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Check."""
        _ = ctx
        started = time.monotonic()
        files_result = u.Infra.iter_python_files(
            project_dir,
            project_roots=[project_dir],
        )
        if files_result.failure:
            issue = m.Infra.Issue(
                file=c.Infra.PYPROJECT_FILENAME,
                line=1,
                column=1,
                code=self.gate_id,
                message=files_result.error or "silent-failure scan failed",
            )
            return self._build_gate_result(
                result=m.Infra.GateResult(
                    gate=self.gate_id,
                    project=project_dir.name,
                    passed=False,
                    errors=[issue.formatted],
                    duration=round(time.monotonic() - started, 3),
                ),
                issues=[issue],
                raw_output=issue.message,
                ctx=ctx,
            )
        rope_project = u.Infra.init_rope_project(project_dir)
        try:
            issues = [
                issue
                for file_path in files_result.value
                for issue in FlextInfraSilentFailureDetector.detect_file(
                    m.Infra.DetectorContext(
                        file_path=file_path,
                        project_root=project_dir,
                        rope_project=rope_project,
                    )
                )
            ]
        finally:
            rope_project.close()
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=len(issues) == 0,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output="\n".join(issue.formatted for issue in issues),
            ctx=ctx,
        )

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Build check command."""
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse check output."""
        _ = result, project_dir, ctx
        return True, ()


__all__: list[str] = ["FlextInfraSilentFailureGate"]
