"""FLEXT markdown formatting gate: prettier, owned by ``make fmt``.

Prettier is the fleet's markdown FORMATTER and rumdl stays the linter. The
read-only side (``prettier --check``) validates inside ``make check``; the
mutating side (``prettier --write``) is reached only through the gate's fix
contract from ``make fmt`` — the gate deliberately never appears in
``CANONICAL_FIXABLE_GATE_IDS``, so every tool runs exactly one operation per
verb and no verb repeats another's work.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u

from .base_gate import FlextInfraGate
from .markdown_support import collect_markdown_files

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraMarkdownFormatGate(FlextInfraGate):
    """Markdown formatting gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN_FORMAT
    gate_name: ClassVar[str] = "Markdown Format"
    scanner_binary: ClassVar[str] = c.Infra.PRETTIER_BINARY
    can_fix: ClassVar[bool] = True

    def _resolve_config_args(self, project_dir: Path) -> t.StrSequence:
        """Resolve only the repository-local prettier settings owner."""
        config_path = project_dir / c.Infra.PRETTIER_CONFIG_FILENAME
        if not config_path.is_file():
            return ()
        return ["--config", str(config_path.resolve())]

    def _resolve_ignore_args(self, project_dir: Path) -> t.StrSequence:
        """Point ``--ignore-path`` at the generated ignore projection, when present."""
        ignore_path = project_dir / c.Infra.PRETTIER_IGNORE_FILENAME
        if not ignore_path.is_file():
            return ()
        return ["--ignore-path", str(ignore_path.resolve())]

    def _binary_args(self) -> t.StrSequence:
        """Anchor the invocation to the mise-provisioned binary on PATH."""
        return (self._resolve_binary() or c.Infra.PRETTIER_BINARY,)

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run prettier --check only when markdown files exist."""
        started = time.monotonic()
        if self._resolve_binary() is None:
            return self._binary_missing_result(project_dir, started, ctx)
        check_dirs = self._get_check_dirs(project_dir, ctx)
        if not check_dirs:
            return self._neutral_skip_result(
                project_dir,
                started,
                message=f"{self.gate_id}: no markdown files to check",
            )
        return self._execute_check_command(project_dir, ctx, check_dirs, started)

    def _binary_missing_result(
        self, project_dir: Path, started: float, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """A missing provisioned binary is a tool error, never a clean pass."""
        return self._build_single_issue_result(
            project_dir,
            Path(c.Infra.PYPROJECT_FILENAME),
            (
                f"{c.Infra.PRETTIER_BINARY} not found on PATH; `make setup` "
                "provisions it from codegen.toolchain.prettier_version"
            ),
            passed=False,
            started=started,
            ctx=ctx,
        )

    @override
    def _get_check_dirs(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> t.StrSequence:
        """Return relative markdown file paths (doubles as fix targets)."""
        _ = ctx
        return [
            str(path.relative_to(project_dir))
            for path in collect_markdown_files(project_dir)
        ]

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Build the read-only ``prettier --check`` pass."""
        _ = ctx
        return (
            *self._binary_args(),
            "--check",
            *self._resolve_config_args(project_dir),
            *self._resolve_ignore_args(project_dir),
            *check_dirs,
        )

    @override
    def _build_fix_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, targets: t.StrSequence
    ) -> t.StrSequence:
        """Build the single mutating pass: ``prettier --write``."""
        _ = ctx
        return (
            *self._binary_args(),
            "--write",
            *self._resolve_config_args(project_dir),
            *self._resolve_ignore_args(project_dir),
            *targets,
        )

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> t.Pair[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse prettier output: one repairable finding per unformatted file."""
        _ = project_dir, ctx
        issues: t.MutableSequenceOf[m.Infra.Issue] = [
            m.Infra.Issue(
                file=match.group("file"),
                line=1,
                column=1,
                code=self.gate_id,
                message="file is not prettier-formatted (repair belongs to `make fmt`)",
            )
            for line in (result.stdout + "\n" + result.stderr).splitlines()
            if (match := c.Infra.MARKDOWN_FORMAT_RE.match(line.strip()))
        ]
        if not u.Cli.process_succeeded(result.outcome) and not issues:
            issues.append(
                self._command_error_issue(
                    result,
                    tool=c.Infra.PRETTIER_BINARY,
                    file=str(project_dir),
                    line=1,
                    column=1,
                )
            )
        return u.Cli.process_succeeded(result.outcome), issues


__all__: list[str] = ["FlextInfraMarkdownFormatGate"]
