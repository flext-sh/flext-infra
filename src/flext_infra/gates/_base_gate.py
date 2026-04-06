from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, m, t, u


class FlextInfraGate(ABC):
    gate_id: ClassVar[str] = ""
    gate_name: ClassVar[str] = ""
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = ""
    tool_url: ClassVar[str] = ""

    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    # ------------------------------------------------------------------
    # Template method: check
    # ------------------------------------------------------------------

    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
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
            project=project_dir.name,
            passed=passed,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )

    def check_files(
        self,
        files: Sequence[Path],
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Check specific files instead of whole directory.

        Passes file paths directly to the tool CLI for scoped validation.
        Falls back to directory check if no files provided.
        """
        if not files:
            return self.check(project_dir, ctx)
        started = time.monotonic()
        file_strs = [str(f.relative_to(project_dir)) for f in files if f.exists()]
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
            project=project_dir.name,
            passed=passed,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )

    # ------------------------------------------------------------------
    # Template hooks — subclasses override these
    # ------------------------------------------------------------------

    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Return directories to check. Default: discover + filter for .py files."""
        _ = ctx
        return self._dirs_with_py(project_dir, self._existing_check_dirs(project_dir))

    @abstractmethod
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Build the tool CLI command."""
        ...

    @abstractmethod
    def _parse_check_output(
        self,
        result: m.Infra.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        """Parse tool output into (passed, issues)."""
        ...

    def _check_timeout(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> int:
        """Timeout for the check command. Override for long-running tools."""
        _ = project_dir, ctx
        return c.Infra.Timeouts.DEFAULT

    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrMapping | None:
        """Custom environment for the check command. Default: None (inherit)."""
        _ = project_dir, ctx
        return None

    # ------------------------------------------------------------------
    # Template method: fix
    # ------------------------------------------------------------------

    def fix(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Template method: timing + targets + skip + run fix + result."""
        if not self.can_fix:
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=0.0,
                raw_output=f"Gate {self.gate_id} does not support fix",
            )
        started = time.monotonic()
        targets = self._get_fix_targets(project_dir, ctx)
        if not targets:
            return self._skip_result(project_dir, started)
        cmd = self._build_fix_command(project_dir, ctx, targets)
        result = self._run(cmd, project_dir)
        return self._build_gate_result(
            project=project_dir.name,
            passed=result.exit_code == 0,
            issues=[],
            duration=time.monotonic() - started,
            raw_output=self._fix_raw_output(result),
        )

    # ------------------------------------------------------------------
    # Fix hooks — subclasses override these
    # ------------------------------------------------------------------

    def _get_fix_targets(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Targets for fix. Default: same as check dirs."""
        return self._get_check_dirs(project_dir, ctx)

    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
    ) -> t.StrSequence:
        """Build the fix CLI command. Must override if can_fix is True."""
        _ = project_dir, ctx, targets
        msg = f"Gate {self.gate_id} set can_fix=True but did not implement _build_fix_command"
        raise NotImplementedError(msg)

    def _fix_raw_output(self, result: m.Infra.CommandOutput) -> str:
        """Assemble raw output from fix result. Default: stderr only."""
        return result.stderr

    def _run(
        self,
        cmd: t.StrSequence,
        cwd: Path,
        timeout: int = c.Infra.Timeouts.DEFAULT,
        env: t.StrMapping | None = None,
    ) -> m.Infra.CommandOutput:
        result = u.Infra.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
        if result.is_failure:
            return m.Infra.CommandOutput(
                stdout="",
                stderr=result.error or "command execution failed",
                exit_code=1,
            )
        return result.value

    def _build_gate_result(
        self,
        *,
        project: str,
        passed: bool,
        issues: Sequence[m.Infra.Issue],
        duration: float,
        raw_output: str = "",
    ) -> m.Infra.GateExecution:
        model = m.Infra.GateResult(
            gate=self.gate_id,
            project=project,
            passed=passed,
            errors=[issue.formatted for issue in issues],
            duration=round(duration, 3),
        )
        return m.Infra.GateExecution(
            result=model,
            issues=tuple(issues),
            raw_output=raw_output,
        )

    def _existing_check_dirs(self, project_dir: Path) -> t.StrSequence:
        has_root_python = any(project_dir.glob(c.Infra.Extensions.PYTHON_GLOB)) or any(
            project_dir.glob("*.pyi"),
        )
        discovered_dirs = u.Infra.discover_python_dirs(project_dir)
        if has_root_python or discovered_dirs:
            return ["."]
        return []

    @staticmethod
    def _dirs_with_py(project_dir: Path, dirs: t.StrSequence) -> t.StrSequence:
        out: MutableSequence[str] = []
        for directory in dirs:
            path = project_dir / directory
            if not path.is_dir():
                continue
            if next(path.rglob(c.Infra.Extensions.PYTHON_GLOB), None) or next(
                path.rglob("*.pyi"),
                None,
            ):
                out.append(directory)
        return out

    def _skip_result(
        self,
        project_dir: Path,
        started: float,
    ) -> m.Infra.GateExecution:
        return self._build_gate_result(
            project=project_dir.name,
            passed=True,
            issues=[],
            duration=time.monotonic() - started,
            raw_output="",
        )


__all__ = ["FlextInfraGate"]
