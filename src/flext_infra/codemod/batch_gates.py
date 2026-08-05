"""Gate measurement and ast-grep batch execution for the mod safety circuit."""  # ruff:ignore[implicit-namespace-package]

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, ClassVar, Final

from flext_infra import c, m, p, r, t, u

_TOOL_TIMEOUT_SECONDS: Final[int] = 900


class FlextInfraModGateSnapshot(m.ArbitraryTypesModel):
    """Error-count snapshot of the two mod circuit gates."""

    model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

    ruff_errors: Annotated[
        t.NonNegativeInt, m.Field(description="ruff check error count")
    ]
    pyrefly_errors: Annotated[
        t.NonNegativeInt, m.Field(description="pyrefly error count")
    ]


class FlextInfraModGateEngine:
    """Measure ruff/pyrefly counts and execute the sgconfig rule batch."""

    @staticmethod
    def circuit_broken(
        baseline: FlextInfraModGateSnapshot, final: FlextInfraModGateSnapshot
    ) -> bool:
        """Return True when either gate error count increased after the apply."""
        return (
            final.ruff_errors > baseline.ruff_errors
            or final.pyrefly_errors > baseline.pyrefly_errors
        )

    @staticmethod
    def _run_tool(root: Path, command: t.StrSequence) -> p.Result[p.Cli.CommandOutput]:
        """Run one circuit tool and tolerate its findings exit codes."""
        run = u.Cli.run_raw(command, cwd=root, timeout=_TOOL_TIMEOUT_SECONDS)
        if run.failure:
            return r[p.Cli.CommandOutput].fail(
                run.error or f"tool execution failed: {command[0]}"
            )
        output = run.value
        if output.exit_code not in {0, 1}:
            detail = (output.stderr or output.stdout).strip()
            return r[p.Cli.CommandOutput].fail(
                detail or f"{command[0]} exited with code {output.exit_code}"
            )
        return r[p.Cli.CommandOutput].ok(output)

    @staticmethod
    def _count_json_lines(stdout: str) -> int:
        """Count JSON-per-line findings (ast-grep ``--json=stream`` output)."""
        count = 0
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if line and u.Cli.json_parse(line).success:
                count += 1
        return count

    @classmethod
    def _count_tool_errors(cls, stdout: str) -> int:
        """Count error items from array, object-with-errors, or JSONL output."""
        parsed = u.Cli.json_parse(stdout.strip()) if stdout.strip() else None
        if parsed is not None and parsed.success:
            value = parsed.value
            if isinstance(value, list):
                return len(value)
            if isinstance(value, Mapping):
                errors = value.get("errors")
                return len(errors) if isinstance(errors, list) else 0
        return cls._count_json_lines(stdout)

    @classmethod
    def measure(cls, root: Path) -> p.Result[FlextInfraModGateSnapshot]:
        """Capture the ruff + pyrefly error counts for one project root."""
        ruff_run = cls._run_tool(
            root,
            (
                c.Infra.RUFF,
                c.Infra.VERB_CHECK,
                ".",
                "--no-fix",
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--quiet",
            ),
        )
        if ruff_run.failure:
            return r[FlextInfraModGateSnapshot].from_failure(ruff_run)
        pyrefly_run = cls._run_tool(
            root,
            (
                c.Infra.PYREFLY,
                c.Infra.CHECK,
                ".",
                "--config",
                c.Infra.PYPROJECT_FILENAME,
                "--python-interpreter-path",
                sys.executable,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--summary=none",
            ),
        )
        if pyrefly_run.failure:
            return r[FlextInfraModGateSnapshot].from_failure(pyrefly_run)
        return r[FlextInfraModGateSnapshot].ok(
            FlextInfraModGateSnapshot(
                ruff_errors=cls._count_tool_errors(ruff_run.value.stdout or ""),
                pyrefly_errors=cls._count_tool_errors(pyrefly_run.value.stdout or ""),
            )
        )

    @classmethod
    def scan(cls, root: Path, config: Path, *, fix: bool) -> p.Result[int]:
        """Scan with every sgconfig rule; fix mode applies all rewrites."""
        command: list[str] = [c.Infra.SG, c.Infra.SCAN, "--config", str(config)]
        command.extend(("--update-all" if fix else "--json=stream", "."))
        run = cls._run_tool(root, tuple(command))
        if run.failure:
            return r[int].from_failure(run)
        if fix:
            return r[int].ok(0)
        return r[int].ok(cls._count_json_lines(run.value.stdout or ""))


__all__: list[str] = ["FlextInfraModGateEngine", "FlextInfraModGateSnapshot"]
