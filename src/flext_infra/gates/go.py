"""FLEXT go quality gate."""

from __future__ import annotations

import time
from collections.abc import MutableSequence
from pathlib import Path
from typing import override

from flext_infra import FlextInfraGate, c, m


class FlextInfraGoGate(FlextInfraGate):
    """Go quality gate."""

    gate_id = c.Infra.GO
    gate_name = "Go"
    can_fix = False
    tool_name = c.Infra.SARIF_TOOL_INFO[c.Infra.GO][0]
    tool_url = c.Infra.SARIF_TOOL_INFO[c.Infra.GO][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        _ = ctx
        started = time.monotonic()
        if not (project_dir / c.Infra.Files.GO_MOD).exists():
            return self._skip_result(project_dir, started)
        issues: MutableSequence[m.Infra.Issue] = []
        raw_output = ""
        vet_result = self._run(
            [c.Infra.GOVET, "vet", "./..."],
            project_dir,
            timeout=c.Infra.Timeouts.CI,
        )
        raw_output = "\n".join(
            part for part in (vet_result.stdout, vet_result.stderr) if part
        )
        for line in (vet_result.stdout + "\n" + vet_result.stderr).splitlines():
            match = c.Infra.GO_VET_RE.match(line.strip())
            if not match:
                continue
            issues.append(
                m.Infra.Issue(
                    file=match.group("file"),
                    line=int(match.group("line")),
                    column=int(match.group("col") or 1),
                    code=c.Infra.GOVET,
                    message=match.group("msg"),
                ),
            )
        if vet_result.exit_code != 0 and (not issues):
            issues.append(
                m.Infra.Issue(
                    file=".",
                    line=1,
                    column=1,
                    code=c.Infra.GOVET,
                    message=(
                        vet_result.stdout or vet_result.stderr or "go vet failed"
                    ).strip(),
                ),
            )
        go_files = list(project_dir.rglob("*.go"))
        if go_files:
            fmt_result = self._run(
                [
                    c.Infra.GOFMT,
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
                    m.Infra.Issue(
                        file=cleaned,
                        line=1,
                        column=1,
                        code=c.Infra.GOFMT,
                        message="File is not gofmt-formatted",
                    ),
                )
        return self._build_gate_result(
            project=project_dir.name,
            passed=not issues,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=raw_output,
        )


__all__ = ["FlextInfraGoGate"]
