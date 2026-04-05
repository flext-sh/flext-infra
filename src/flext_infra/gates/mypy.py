"""FLEXT mypy quality gate."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraMypyGate(FlextInfraGate):
    """Gate for Mypy type checking."""

    gate_id: ClassVar[str] = c.Infra.MYPY
    gate_name: ClassVar[str] = "Mypy"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MYPY][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.MYPY][1]

    def _resolve_config(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Path:
        """Resolve mypy config: project-local if it has [tool.mypy], else workspace."""
        proj_py = project_dir / c.Infra.Files.PYPROJECT_FILENAME
        if proj_py.exists() and "[tool.mypy]" in proj_py.read_text(
            encoding=c.Infra.Encoding.DEFAULT
        ):
            return proj_py
        return ctx.workspace_root / c.Infra.Files.PYPROJECT_FILENAME

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
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
    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrMapping | None:
        _ = project_dir
        typings_generated = (
            ctx.workspace_root / c.Infra.Directories.TYPINGS / "generated"
        )
        mypy_env = os.environ.copy()
        if typings_generated.is_dir():
            existing = mypy_env.get("MYPYPATH", "")
            mypy_env["MYPYPATH"] = str(typings_generated) + (
                f":{existing}" if existing else ""
            )
        return mypy_env

    @override
    def _parse_check_output(
        self,
        result: m.Infra.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        _ = project_dir, ctx
        issues: MutableSequence[m.Infra.Issue] = []
        for raw_line in (result.stdout or "").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                line_data: Mapping[str, t.Infra.InfraValue] = (
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_json(stripped)
                )
            except ValidationError:
                continue
            try:
                severity = u.Infra.pick_str(line_data, "severity", c.Infra.ERROR)
                if severity in c.Infra.VALID_GATE_SEVERITIES:
                    issues.append(
                        m.Infra.Issue(
                            file=u.Infra.pick_str(line_data, "file", "?"),
                            line=u.Infra.pick_int(line_data, "line"),
                            column=u.Infra.pick_int(line_data, "column"),
                            code=u.Infra.pick_str(line_data, "code"),
                            message=u.Infra.pick_str(line_data, "message"),
                            severity=severity,
                        ),
                    )
            except ValidationError:
                continue
        return result.exit_code == 0, issues


__all__ = ["FlextInfraMypyGate"]
