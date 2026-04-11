"""FLEXT markdown quality gate."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraGate, c, m, t


class FlextInfraMarkdownGate(FlextInfraGate):
    """Markdown quality gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN
    gate_name: ClassVar[str] = "Markdown"
    can_fix: ClassVar[bool] = True
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MARKDOWN][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MARKDOWN][1]

    def _collect_markdown_files(self, project_dir: Path) -> Sequence[Path]:
        return [
            path
            for path in project_dir.rglob("*.md")
            if not any(part in c.Infra.CHECK_EXCLUDED_DIRS for part in path.parts)
        ]

    def _resolve_config_args(self, project_dir: Path) -> t.StrSequence:
        """Resolve markdownlint config file args."""
        root_config = self._workspace_root / ".markdownlint.json"
        local_config = project_dir / ".markdownlint.json"
        if root_config.exists():
            return ["--config", str(root_config)]
        if local_config.exists():
            return ["--config", str(local_config)]
        return []

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Return relative markdown file paths (doubles as check_dirs for _build_check_command)."""
        _ = ctx
        return [
            str(path.relative_to(project_dir))
            for path in self._collect_markdown_files(project_dir)
        ]

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        _ = ctx
        return [
            c.Infra.MARKDOWNLINT,
            *self._resolve_config_args(project_dir),
            *check_dirs,
        ]

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        _ = project_dir, ctx
        issues: MutableSequence[m.Infra.Issue] = []
        for line in (result.stdout + "\n" + result.stderr).splitlines():
            match = c.Infra.MARKDOWN_RE.match(line.strip())
            if not match:
                continue
            issues.append(
                m.Infra.Issue(
                    file=match.group("file"),
                    line=int(match.group("line")),
                    column=int(match.group("col") or 1),
                    code=match.group("code"),
                    message=match.group("msg"),
                ),
            )
        return result.exit_code == 0, issues

    @override
    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
    ) -> t.StrSequence:
        _ = ctx
        return [
            c.Infra.MARKDOWNLINT,
            "--fix",
            *self._resolve_config_args(project_dir),
            *targets,
        ]

    @override
    def _fix_raw_output(self, result: m.Cli.CommandOutput) -> str:
        return "\n".join(part for part in (result.stdout, result.stderr) if part)


__all__ = ["FlextInfraMarkdownGate"]
