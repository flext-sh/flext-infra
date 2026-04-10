"""Silent failure quality gate for first-wave FLEXT projects."""

from __future__ import annotations

import time
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import (
    FlextInfraGate,
    FlextInfraSilentFailureDetector,
    c,
    m,
    t,
    u,
)


class FlextInfraSilentFailureGate(FlextInfraGate):
    """Block silent failure sentinels in the first remediation wave."""

    gate_id: ClassVar[str] = "silent-failure"
    gate_name: ClassVar[str] = "Silent Failure"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = "Flext Silent Failure Detector"
    tool_url: ClassVar[str] = "internal://flext-infra/silent-failure"
    _FIRST_WAVE_PROJECTS: ClassVar[frozenset[str]] = frozenset({
        "flext-infra",
        "flext-core",
        "flext-cli",
        "flext-tests",
        "flext-ldif",
        "flext-ldap",
        "algar-oud-mig",
    })

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        started = time.monotonic()
        if project_dir.name not in self._FIRST_WAVE_PROJECTS:
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=time.monotonic() - started,
                raw_output="silent-failure gate not enforced for this project",
            )
        files_result = u.Infra.iter_python_files(
            project_dir,
            project_roots=[project_dir],
        )
        if files_result.is_failure:
            issue = m.Infra.Issue(
                file=c.Infra.Files.PYPROJECT_FILENAME,
                line=1,
                column=1,
                code=self.gate_id,
                message=files_result.error or "silent-failure scan failed",
            )
            return self._build_gate_result(
                project=project_dir.name,
                passed=False,
                issues=[issue],
                duration=time.monotonic() - started,
                raw_output=issue.message,
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
            project=project_dir.name,
            passed=len(issues) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output="\n".join(issue.formatted for issue in issues),
        )

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        _ = result, project_dir, ctx
        return True, ()


__all__ = ["FlextInfraSilentFailureGate"]
