"""FLEXT mypy quality gate."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, t, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraMypyGate(FlextInfraGate):
    """Gate for Mypy type checking."""

    gate_id: ClassVar[str] = c.Infra.MYPY
    gate_name: ClassVar[str] = "Mypy"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MYPY][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MYPY][1]

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Check local Python roots directly instead of recursively scanning ``.``."""
        _ = ctx
        discovered_dirs = self._dirs_with_py(
            project_dir,
            c.Infra.CHECK_DIRS_SUBPROJECT,
        )
        root_files = [
            path.name
            for path in sorted(project_dir.iterdir())
            if path.is_file() and path.suffix in {".py", ".pyi"}
        ]
        if discovered_dirs or root_files:
            return [*discovered_dirs, *root_files]
        return []

    def _resolve_config(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Path:
        """Resolve mypy settings: project-local if it has [tool.mypy], else workspace."""
        pyproject_name: str = c.Infra.PYPROJECT_FILENAME
        proj_py = project_dir / pyproject_name
        doc = u.Cli.toml_read(proj_py)
        if doc is not None:
            tool_table = u.Cli.toml_table_child(doc, c.Infra.TOOL)
            if (
                tool_table is not None
                and u.Cli.toml_table_child(tool_table, c.Infra.MYPY) is not None
            ):
                return proj_py
        workspace_root: Path = ctx.workspace_root
        return workspace_root / pyproject_name

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Build check command."""
        cfg = self._resolve_config(project_dir, ctx)
        return [
            sys.executable,
            "-m",
            c.Infra.MYPY,
            *check_dirs,
            "--config-file",
            str(cfg),
            "--output",
            c.Infra.OUTPUT_JSON,
        ]

    @override
    def _check_timeout(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> int:
        """Allow large projects enough time for a full mypy graph walk."""
        _ = project_dir, ctx
        timeout: int = c.Infra.TIMEOUT_LONG
        return timeout

    @override
    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrMapping | None:
        """Check env."""
        _ = project_dir
        typings_generated = ctx.workspace_root / c.Infra.DIR_TYPINGS / "generated"
        if not typings_generated.is_dir():
            return None
        base_env = u.Cli.process_env()
        existing = base_env.get("MYPYPATH", "")
        mypy_path = str(typings_generated) + (f":{existing}" if existing else "")
        return u.Cli.process_env(overrides={"MYPYPATH": mypy_path})

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse check output."""
        _ = project_dir, ctx
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        for raw_line in (result.stdout or "").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                line_data: t.MappingKV[str, t.Infra.InfraValue] = (
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_json(stripped)
                )
            except c.ValidationError:
                continue
            try:
                severity = u.Cli.json_pick_str(line_data, "severity", c.Infra.ERROR)
                if severity in c.Infra.VALID_GATE_SEVERITIES:
                    issues.append(
                        m.Infra.Issue(
                            file=u.Cli.json_pick_str(line_data, "file", "?"),
                            line=u.Cli.json_pick_int(line_data, "line"),
                            column=u.Cli.json_pick_int(line_data, "column"),
                            code=u.Cli.json_pick_str(line_data, "code"),
                            message=u.Cli.json_pick_str(line_data, "message"),
                            severity=severity,
                        ),
                    )
            except c.ValidationError:
                continue
        if (not issues) and result.exit_code != 0:
            message = (result.stderr or result.stdout).strip()
            if not message:
                message = (
                    f"mypy exited with code {result.exit_code} without JSON diagnostics"
                )
            issues.append(
                m.Infra.Issue(
                    file=c.Infra.PYPROJECT_FILENAME,
                    line=1,
                    column=1,
                    code="mypy-exec",
                    message=message,
                    severity=c.Infra.ERROR,
                ),
            )
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraMypyGate"]
