"""Deptry dependency-declaration gate over the project's import surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, t, u
from flext_infra.gates.base_gate import FlextInfraGate


class FlextInfraDepsGate(FlextInfraGate):
    """Fail every import the project's declared dependencies never declare.

    Why (aihub-l42it.11): undeclared runtime imports surface today only deep
    inside the generation pipeline's rope pass, minutes into a failing run;
    this gate states the same fact in seconds at check time, so a racing
    consolidation can never land an orphan import unnoticed.
    """

    gate_id: ClassVar[str] = c.Infra.DEPS
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = False

    @override
    def selected_for(self, project_dir: Path) -> bool:
        """Select projects that declare dependencies (a pyproject exists).

        Returns:
            The resulting ``bool``.
        """
        return (project_dir / c.PYPROJECT_FILENAME).is_file()

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run deptry over the checkout and fail on any declared-surface gap.

        Returns:
            The complete scan receipt with every dependency issue.

        Raises:
            FileNotFoundError: If the runtime environment carries no deptry.
        """
        _ = ctx
        started = time.monotonic()
        venv_bin = Path(sys.executable).parent
        deptry_bin = venv_bin / c.Infra.DEPTRY
        if not deptry_bin.exists():
            message = (
                "deps gate requires deptry in the runtime environment: "
                f"{deptry_bin} is absent; add deptry to the workspace root "
                "dev group and run make setup"
            )
            raise FileNotFoundError(message)
        settings = project_dir / c.PYPROJECT_FILENAME
        out_file = project_dir / ".reports" / "deptry-check.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        command: t.MutableSequenceOf[str] = [
            str(deptry_bin),
            ".",
            "--config",
            str(settings),
            "--json-output",
            str(out_file),
            "--no-ansi",
        ]
        run = u.Cli.run_raw(
            command,
            cwd=project_dir,
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        # deptry exits nonzero on findings and on misuse alike: the receipt
        # content decides the verdict, so a failed run with a report still
        # states its issues; a failed run with no report is a gate error and
        # the raw failure escapes unchanged (law 14).
        issues: list[m.Infra.Issue] = []
        if out_file.exists():
            loaded = json.loads(out_file.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                for item in loaded:
                    if not isinstance(item, dict):
                        continue
                    location = item.get("location")
                    location = location if isinstance(location, dict) else {}
                    line_value = location.get("line")
                    issues.append(
                        m.Infra.Issue(
                            file=str(
                                location.get("file")
                                or item.get("module")
                                or project_dir,
                            ),
                            line=int(line_value) if line_value else 1,
                            column=1,
                            code=f"{self.gate_id}-{item.get('kind', 'issue')}",
                            message=str(item.get("message", item))[:400],
                            severity=c.Infra.GateSeverity.ERROR.value,
                        ),
                    )
            out_file.unlink(missing_ok=True)
        if run.failure and not issues:
            return self._build_check_gate_execution(
                project_dir,
                passed=False,
                issues=(),
                raw_output=str(run.error),
                started=started,
            )
        raw = f"checked={project_dir} findings={len(issues)}"
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=tuple(issues),
            raw_output="\n".join((raw, *(issue.formatted for issue in issues))),
            started=started,
        )


__all__: list[str] = ["FlextInfraDepsGate"]
