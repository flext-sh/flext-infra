"""FLEXT go quality gate."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraGate, c, m, t


class FlextInfraGoGate(FlextInfraGate):
    """Go quality gate — runs go vet + gofmt."""

    gate_id: ClassVar[str] = c.Infra.GO
    gate_name: ClassVar[str] = "Go"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.GO][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.GO][1]

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        _ = ctx
        if not (project_dir / c.Infra.GO_MOD).exists():
            return []
        return ["."]

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        _ = project_dir, ctx, check_dirs
        return [c.Infra.GOVET, "vet", "./..."]

    @override
    def _check_timeout(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> int:
        _ = project_dir, ctx
        timeout: int = c.Infra.TIMEOUT_CI
        return timeout

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        _ = ctx
        issues: MutableSequence[m.Infra.Issue] = []
        passed = result.exit_code == 0
        for line in (result.stdout + "\n" + result.stderr).splitlines():
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
        go_files = list(project_dir.rglob("*.go"))
        if go_files:
            fmt_result = self._run(
                [
                    c.Infra.GOFMT,
                    "-l",
                    *[str(path.relative_to(project_dir)) for path in go_files],
                ],
                project_dir,
                timeout=c.Infra.TIMEOUT_CI,
            )
            passed = passed and fmt_result.exit_code == 0
            for file_name in fmt_result.stdout.splitlines():
                cleaned = file_name.strip()
                if cleaned:
                    issues.append(
                        m.Infra.Issue(
                            file=cleaned,
                            line=1,
                            column=1,
                            code=c.Infra.GOFMT,
                            message="File is not gofmt-formatted",
                        ),
                    )
        return passed and not issues, issues


__all__: list[str] = ["FlextInfraGoGate"]
