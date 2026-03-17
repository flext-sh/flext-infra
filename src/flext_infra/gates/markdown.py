"""FLEXT markdown quality gate."""

from __future__ import annotations

import time
from pathlib import Path
from typing import override

from flext_infra import c, m
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext
from flext_infra.check._constants import FlextInfraCheckConstants


class FlextInfraMarkdownGate(FlextInfraGate):
    """Gate for markdown lint checks and fixes."""

    """Markdown quality gate."""

    gate_id = c.Infra.Gates.MARKDOWN
    gate_name = "Markdown"
    can_fix = True
    tool_name = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.MARKDOWN][0]
    tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.MARKDOWN][1]

    def _collect_markdown_files(self, project_dir: Path) -> list[Path]:
        files: list[Path] = []
        for path in project_dir.rglob("*.md"):
            if any(part in c.Infra.Excluded.CHECK_EXCLUDED_DIRS for part in path.parts):
                continue
            files.append(path)
        return files

    def _run_markdown(
        self, project_dir: Path, *, fix: bool
    ) -> m.Infra.Check.GateExecution:
        started = time.monotonic()
        md_files = self._collect_markdown_files(project_dir)
        if not md_files:
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=time.monotonic() - started,
                raw_output="",
            )
        cmd = [c.Infra.Cli.MARKDOWNLINT]
        if fix:
            cmd.append("--fix")
        root_config = self._workspace_root / ".markdownlint.json"
        local_config = project_dir / ".markdownlint.json"
        if root_config.exists():
            cmd.extend(["--config", str(root_config)])
        elif local_config.exists():
            cmd.extend(["--config", str(local_config)])
        cmd.extend(str(path.relative_to(project_dir)) for path in md_files)
        result = self._run(cmd, project_dir)
        issues: list[m.Infra.Check.Issue] = []
        if not fix:
            for line in (result.stdout + "\n" + result.stderr).splitlines():
                match = FlextInfraCheckConstants.MARKDOWN_RE.match(line.strip())
                if not match:
                    continue
                issues.append(
                    m.Infra.Check.Issue(
                        file=match.group("file"),
                        line=int(match.group("line")),
                        column=int(match.group("col") or 1),
                        code=match.group("code"),
                        message=match.group("msg"),
                    ),
                )
            if self._result_exit_code(result) != 0 and (not issues):
                issues.append(
                    m.Infra.Check.Issue(
                        file=".",
                        line=1,
                        column=1,
                        code=c.Infra.Gates.MARKDOWNLINT,
                        message=(
                            result.stdout or result.stderr or "markdownlint failed"
                        ).strip(),
                    ),
                )
        raw_output = (
            result.stderr
            if not fix
            else "\n".join(part for part in (result.stdout, result.stderr) if part)
        )
        return self._build_gate_result(
            project=project_dir.name,
            passed=self._result_exit_code(result) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=raw_output,
        )

    @override
    @override
    def check(
        self, project_dir: Path, ctx: FlextInfraGateContext
    ) -> m.Infra.Check.GateExecution:
        _ = ctx
        return self._run_markdown(project_dir, fix=False)

    @override
    @override
    def fix(
        self, project_dir: Path, ctx: FlextInfraGateContext
    ) -> m.Infra.Check.GateExecution:
        _ = ctx
        return self._run_markdown(project_dir, fix=True)


__all__ = ["FlextInfraMarkdownGate"]
