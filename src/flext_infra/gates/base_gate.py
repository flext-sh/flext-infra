"""Shared gate template abstraction for workspace quality checks.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m, p, t, u

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraGate(ABC):
    """Abstract template implementing common check/fix execution flow for gates."""

    gate_id: ClassVar[str] = ""
    gate_name: ClassVar[str] = ""
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = ""
    tool_url: ClassVar[str] = ""

    def __init__(
        self, workspace_root: Path, *, runner: p.Cli.CommandRunner | None = None
    ) -> None:
        """Bind workspace root and optional command runner override."""
        self._workspace_root = workspace_root
        self._runner = runner

    # ------------------------------------------------------------------
    # Template method: check
    # ------------------------------------------------------------------

    def check(
        self, project_dir: Path, ctx: p.Infra.GateContext
    ) -> p.Infra.GateExecution:
        """Template method: timing + dirs + skip + run + parse + result."""
        started = time.monotonic()
        check_dirs = self._get_check_dirs(project_dir, ctx)
        if not check_dirs:
            return self._skip_result(project_dir, started)
        cmd = self._build_check_command(project_dir, ctx, check_dirs)
        result = self._run(
            cmd,
            project_dir,
            timeout=self._check_timeout(project_dir, ctx),
            env=self._check_env(project_dir, ctx),
        )
        passed, issues = self._parse_check_output(result, project_dir, ctx)
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=passed,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output=result.stderr,
        )

    def check_files(
        self, files: t.SequenceOf[Path], project_dir: Path, ctx: p.Infra.GateContext
    ) -> p.Infra.GateExecution:
        """Check specific files instead of whole directory.

        Passes file paths directly to the tool CLI for scoped validation.
        Falls back to directory check if no files provided.

        Returns:
            The scoped gate execution result.
        """
        if not files:
            return self.check(project_dir, ctx)
        started = time.monotonic()
        file_strs = self._file_targets(files, project_dir, ctx)
        if not file_strs:
            return self._skip_result(project_dir, started)
        cmd = self._build_check_command(project_dir, ctx, file_strs)
        result = self._run(
            cmd,
            project_dir,
            timeout=self._check_timeout(project_dir, ctx),
            env=self._check_env(project_dir, ctx),
        )
        passed, issues = self._parse_check_output(result, project_dir, ctx)
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=passed,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output=result.stderr,
        )

    def _filter_check_files(
        self, files: t.SequenceOf[Path], project_dir: Path, ctx: p.Infra.GateContext
    ) -> t.SequenceOf[Path]:
        """Keep existing files owned by the selected project."""
        _ = ctx
        project_root = project_dir.resolve()
        selected: list[Path] = []
        for file_path in files:
            resolved = file_path.resolve()
            if resolved.is_file() and resolved.is_relative_to(project_root):
                selected.append(resolved)
        return tuple(selected)

    def _file_targets(
        self, files: t.SequenceOf[Path], project_dir: Path, ctx: p.Infra.GateContext
    ) -> t.StrSequence:
        """Return project-relative tool targets after gate-specific filtering."""
        project_root = project_dir.resolve()
        return tuple(
            file_path.relative_to(project_root).as_posix()
            for file_path in self._filter_check_files(files, project_root, ctx)
        )

    # ------------------------------------------------------------------
    # Template hooks — subclasses override these
    # ------------------------------------------------------------------

    def _get_check_dirs(
        self, project_dir: Path, ctx: p.Infra.GateContext
    ) -> t.StrSequence:
        """Return directories to check. Default: discover + filter for .py files."""
        _ = ctx
        return self._dirs_with_py(project_dir, self._existing_check_dirs(project_dir))

    @abstractmethod
    def _build_check_command(
        self, project_dir: Path, ctx: p.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Build the tool CLI command."""
        ...

    @abstractmethod
    # mro-r3r8: every gate override consumes the structural p.Cli process contract.
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: p.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[p.Infra.Issue]]:
        """Parse tool output into (passed, issues)."""
        ...

    def _check_timeout(self, project_dir: Path, ctx: p.Infra.GateContext) -> int:
        """Timeout for the check command. Override for long-running tools."""
        _ = project_dir, ctx
        timeout: int = c.Infra.TIMEOUT_DEFAULT
        return timeout

    def _check_env(
        self, project_dir: Path, ctx: p.Infra.GateContext
    ) -> t.StrMapping | None:
        """Return a custom environment for the check command. Default: None (inherit)."""
        _ = project_dir, ctx
        return None

    # ------------------------------------------------------------------
    # Template method: fix
    # ------------------------------------------------------------------

    def fix(self, project_dir: Path, ctx: p.Infra.GateContext) -> p.Infra.GateExecution:
        """Template method: timing + targets + skip + run fix + result."""
        if ctx.check_only or not ctx.apply_fixes:
            return self._check_only_fix_result(project_dir)
        if not self.can_fix:
            return self._build_gate_result(
                result=m.Infra.GateResult(
                    gate=self.gate_id,
                    project=project_dir.name,
                    passed=True,
                    errors=[],
                    duration=0.0,
                ),
                issues=[],
                raw_output=f"Gate {self.gate_id} does not support fix",
            )
        started = time.monotonic()
        targets = self._get_fix_targets(project_dir, ctx)
        if not targets:
            return self._skip_result(project_dir, started)
        cmd = self._build_fix_command(project_dir, ctx, targets)
        result = self._run(cmd, project_dir)
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=result.exit_code == 0,
                errors=[],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=[],
            raw_output=self._fix_raw_output(result),
        )

    def fix_files(
        self, files: t.SequenceOf[Path], project_dir: Path, ctx: p.Infra.GateContext
    ) -> p.Infra.GateExecution:
        """Apply a supported fix only to explicitly selected files."""
        if ctx.check_only or not ctx.apply_fixes:
            return self._check_only_fix_result(project_dir)
        if not self.can_fix:
            return self._build_gate_result(
                result=m.Infra.GateResult(
                    gate=self.gate_id,
                    project=project_dir.name,
                    passed=True,
                    errors=[],
                    duration=0.0,
                ),
                issues=[],
                raw_output=f"Gate {self.gate_id} does not support fix",
            )
        started = time.monotonic()
        targets = self._file_targets(files, project_dir, ctx)
        if not targets:
            return self._skip_result(project_dir, started)
        result = self._run(
            self._build_fix_command(project_dir, ctx, targets), project_dir
        )
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=result.exit_code == 0,
                errors=[],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=[],
            raw_output=self._fix_raw_output(result),
        )

    def _check_only_fix_result(self, project_dir: Path) -> p.Infra.GateExecution:
        """Return a non-mutating fix preview for check-only gate contexts."""
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=True,
                errors=[],
                duration=0.0,
            ),
            issues=[],
            raw_output=f"Gate {self.gate_id} fix preview only; no files written",
        )

    # ------------------------------------------------------------------
    # Fix hooks — subclasses override these
    # ------------------------------------------------------------------

    def _get_fix_targets(
        self, project_dir: Path, ctx: p.Infra.GateContext
    ) -> t.StrSequence:
        """Targets for fix. Default: same as check dirs."""
        return self._get_check_dirs(project_dir, ctx)

    def _build_fix_command(
        self, project_dir: Path, ctx: p.Infra.GateContext, targets: t.StrSequence
    ) -> t.StrSequence:
        """Build the fix CLI command. Must override if can_fix is True."""
        _ = project_dir, ctx, targets
        msg = f"Gate {self.gate_id} set can_fix=True but did not implement _build_fix_command"
        raise NotImplementedError(msg)

    def _fix_raw_output(self, result: p.Cli.CommandOutput) -> str:
        """Assemble raw output from fix result. Default: stderr only."""
        stderr: str = result.stderr
        return stderr

    def _run(
        self,
        cmd: t.StrSequence,
        cwd: Path,
        timeout: int = c.Infra.TIMEOUT_DEFAULT,
        env: t.StrMapping | None = None,
    ) -> p.Cli.CommandOutput:
        """Run."""
        runner = self._runner or u.Cli
        result = runner.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
        if result.failure:
            return m.Cli.CommandOutput(
                stdout="",
                stderr=result.error or "command execution failed",
                exit_code=1,
            )
        return result.value

    def _build_gate_result(
        self,
        *,
        result: p.Infra.GateResult,
        issues: t.SequenceOf[p.Infra.Issue],
        raw_output: str = "",
        ctx: p.Infra.GateContext | None = None,
    ) -> p.Infra.GateExecution:
        """Build gate result.

        When ``ctx.gate_mode == "warn"`` the gate reports issues but is
        marked passed so advisory enforcement gates do not fail the check
        pipeline.

        Returns:
            The normalized gate execution result.
        """
        if (
            ctx is not None
            and getattr(ctx, "gate_mode", None) == "warn"
            and not result.passed
        ):
            warn_issues = [
                issue.model_copy(update={"severity": "WARNING"})
                if hasattr(issue, "model_copy")
                else issue
                for issue in issues
            ]
            return m.Infra.GateExecution(
                result=m.Infra.GateResult(
                    gate=result.gate,
                    project=result.project,
                    passed=True,
                    errors=[],
                    duration=result.duration,
                ),
                issues=tuple(warn_issues),
                raw_output=raw_output,
            )
        return m.Infra.GateExecution(
            result=result, issues=tuple(issues), raw_output=raw_output
        )

    def _existing_check_dirs(self, project_dir: Path) -> t.StrSequence:
        """Existing check dirs."""
        has_root_python = any(project_dir.glob(c.Infra.EXT_PYTHON_GLOB)) or any(
            project_dir.glob("*.pyi")
        )
        discovered_dirs = u.Infra.discover_python_dirs(project_dir)
        if has_root_python or discovered_dirs:
            return ["."]
        return []

    @staticmethod
    def _dirs_with_py(project_dir: Path, dirs: t.StrSequence) -> t.StrSequence:
        """Dirs with py."""
        out: t.MutableSequenceOf[str] = []
        for directory in dirs:
            path = project_dir / directory
            if not path.is_dir():
                continue
            if next(path.rglob(c.Infra.EXT_PYTHON_GLOB), None) or next(
                path.rglob("*.pyi"), None
            ):
                out.append(directory)
        return out

    def _skip_result(self, project_dir: Path, started: float) -> p.Infra.GateExecution:
        """Skip result."""
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=True,
                errors=[],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=[],
            raw_output="",
        )


__all__: list[str] = ["FlextInfraGate"]
