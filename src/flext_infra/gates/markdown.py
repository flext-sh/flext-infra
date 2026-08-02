"""FLEXT markdown quality gate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraMarkdownGate(FlextInfraGate):
    """Markdown quality gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN
    gate_name: ClassVar[str] = "Markdown"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MARKDOWN][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MARKDOWN][1]

    def _collect_markdown_files(self, project_dir: Path) -> t.SequenceOf[Path]:
        """Collect markdown files."""
        return [
            path
            for path in u.Infra.iter_matching_files(project_dir, includes=["*.md"])
            if not any(part in c.Infra.CHECK_EXCLUDED_DIRS for part in path.parts)
        ]

    def _resolve_config_args(self, project_dir: Path) -> t.StrSequence:
        """Resolve markdownlint settings file args."""
        root_config = self._workspace_root / ".markdownlint.json"
        local_config = project_dir / ".markdownlint.json"
        if root_config.exists():
            return ["--config", str(root_config)]
        if local_config.exists():
            return ["--config", str(local_config)]
        return []

    @override
    def _get_check_dirs(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> t.StrSequence:
        """Return relative markdown file paths (doubles as check_dirs for _build_check_command)."""
        _ = ctx
        return [
            str(path.relative_to(project_dir))
            for path in self._collect_markdown_files(project_dir)
        ]

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Build check command."""
        _ = ctx
        return self._python_console_script_command(
            c.Infra.RUMDL,
            "check",
            "--no-cache",
            "--color",
            "never",
            "--output-format",
            "text",
            "--deny-config-warnings",
            *self._resolve_config_args(project_dir),
            *check_dirs,
        )

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse check output."""
        _ = ctx
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
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
                )
            )
        if result.exit_code != 0 and not issues:
            detail = (result.stderr or result.stdout).strip() or "no diagnostics"
            issues.append(
                m.Infra.Issue(
                    file=str(project_dir),
                    line=1,
                    column=1,
                    code="TOOL_ERROR",
                    message=f"rumdl exited with code {result.exit_code}: {detail}",
                    severity="ERROR",
                )
            )
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraMarkdownGate"]
