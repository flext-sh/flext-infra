"""Deferred self-reference quality gate.

Blocks two structural defects that share one root cause — a nested model that
cannot name what it depends on while its own class body executes:

* ``default_factory=lambda: Outer.Sibling()`` postpones a name resolution the
  definition order should have satisfied, turning a structural defect into a
  runtime one that no static gate can see.
* a field annotated with its own owner cannot be instantiated while that
  owner is still incomplete.

The canonical repair is diamond-FLEXT composition: hoist the referenced model
into its own namespace class, inherit that namespace, and reference the model
as a resolved base-class attribute.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.detectors.deferred_self_reference_detector import (
    FlextInfraDeferredSelfReferenceDetector,
)
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraDeferredSelfReferenceGate(FlextInfraGate):
    """Block deferred self-reference and recursive models in any Python project."""

    gate_id: ClassVar[str] = "deferred-self-reference"
    gate_name: ClassVar[str] = "Deferred Self Reference"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = "Flext Deferred Self Reference Detector"
    tool_url: ClassVar[str] = "internal://flext-infra/deferred-self-reference"

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Check."""
        started = time.monotonic()
        files_result = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(project_dir,))
        )
        if files_result.failure:
            issue = m.Infra.Issue(
                file=c.Infra.PYPROJECT_FILENAME,
                line=1,
                column=1,
                code=self.gate_id,
                message=files_result.error or "deferred-self-reference scan failed",
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
                for issue in FlextInfraDeferredSelfReferenceDetector.detect_file(
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
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Build check command."""
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse check output."""
        _ = result, project_dir, ctx
        return True, ()


__all__: list[str] = ["FlextInfraDeferredSelfReferenceGate"]
