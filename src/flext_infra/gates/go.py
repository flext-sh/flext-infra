"""FLEXT go quality gate."""

from __future__ import annotations

import time
from pathlib import Path
from typing import override

from flext_infra import c, m
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext
from flext_infra.check._constants import FlextInfraCheckConstants


class FlextInfraGoGate(FlextInfraGate):
    """Gate for Go quality checks."""

    """Go quality gate."""

    gate_id = c.Infra.Gates.GO
    gate_name = "Go"
    can_fix = False
    tool_name = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.GO][0]
    tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.GO][1]

    @override
    @override
    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.Check.GateExecution:
        _ = ctx
        started = time.monotonic()
        if not (project_dir / c.Infra.Files.GO_MOD).exists():
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=time.monotonic() - started,
                raw_output="",
            )
        issues: list[m.Infra.Check.Issue] = []
        raw_output = ""
        vet_result = self._run(
            [c.Infra.Cli.GOVET, "vet", "./..."],
            project_dir,
            timeout=c.Infra.Timeouts.CI,
        )
        raw_output = "\n".join(
            part for part in (vet_result.stdout, vet_result.stderr) if part
        )
        for line in (vet_result.stdout + "\n" + vet_result.stderr).splitlines():
            match = FlextInfraCheckConstants.GO_VET_RE.match(line.strip())
            if not match:
                continue
            issues.append(
                m.Infra.Check.Issue(
                    file=match.group("file"),
                    line=int(match.group("line")),
                    column=int(match.group("col") or 1),
                    code=c.Infra.Gates.GOVET,
                    message=match.group("msg"),
                ),
            )
        if self._result_exit_code(vet_result) != 0 and (not issues):
            issues.append(
                m.Infra.Check.Issue(
                    file=".",
                    line=1,
                    column=1,
                    code=c.Infra.Gates.GOVET,
                    message=(
                        vet_result.stdout or vet_result.stderr or "go vet failed"
                    ).strip(),
                ),
            )
        go_files = list(project_dir.rglob("*.go"))
        if go_files:
            fmt_result = self._run(
                [
                    c.Infra.Cli.GOFMT,
                    "-l",
                    *[str(path.relative_to(project_dir)) for path in go_files],
                ],
                project_dir,
                timeout=c.Infra.Timeouts.CI,
            )
            fmt_raw_output = "\n".join(
                part for part in (fmt_result.stdout, fmt_result.stderr) if part
            )
            raw_output = "\n".join(
                part for part in (raw_output, fmt_raw_output) if part
            )
            for file_name in fmt_result.stdout.splitlines():
                cleaned = file_name.strip()
                if not cleaned:
                    continue
                issues.append(
                    m.Infra.Check.Issue(
                        file=cleaned,
                        line=1,
                        column=1,
                        code=c.Infra.Gates.GOFMT,
                        message="File is not gofmt-formatted",
                    ),
                )
        return self._build_gate_result(
            project=project_dir.name,
            passed=len(issues) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=raw_output,
        )


__all__ = ["FlextInfraGoGate"]
