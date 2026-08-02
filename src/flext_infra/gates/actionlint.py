"""GitHub Actions workflow validation gate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraActionlintGate(FlextInfraGate):
    """Validate every GitHub Actions workflow through one Actionlint execution."""

    gate_id: ClassVar[str] = c.Infra.ACTIONLINT
    gate_name: ClassVar[str] = "Actionlint"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.ACTIONLINT][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.ACTIONLINT][1]

    @override
    def _get_check_dirs(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> t.StrSequence:
        """Discover all workflows from the GitHub Actions protocol directory."""
        _ = ctx
        workflows_dir = project_dir / c.Infra.GITHUB_WORKFLOWS_DIR
        if not workflows_dir.is_dir():
            return ()
        return tuple(
            path.relative_to(project_dir).as_posix()
            for pattern in c.Infra.GITHUB_WORKFLOW_GLOBS
            for path in sorted(workflows_dir.glob(pattern))
            if path.is_file()
        )

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Build one uv-managed Actionlint command for the discovered workflows."""
        _ = project_dir, ctx
        return self._python_console_script_command(
            c.Infra.ACTIONLINT,
            "-format",
            c.Infra.ACTIONLINT_JSON_FORMAT,
            "-shellcheck=",
            "-pyflakes=",
            *check_dirs,
        )

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse Actionlint's documented JSON error objects."""
        _ = ctx
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        parsed_result = u.Cli.json_parse(result.stdout or "[]")
        parsed_value = parsed_result.unwrap() if parsed_result.success else None
        raw_items = (
            u.Cli.json_as_mapping_list(parsed_value)
            if isinstance(parsed_value, list)
            else ()
        )
        if (
            parsed_result.failure
            or not isinstance(parsed_value, list)
            or (len(raw_items) != len(parsed_value))
        ):
            issues.append(
                m.Infra.Issue(
                    file="<actionlint-output>",
                    line=1,
                    column=1,
                    code="PARSE_ERROR",
                    message=parsed_result.error
                    or "actionlint JSON output does not match its error-object contract",
                    severity="ERROR",
                )
            )
            return False, issues
        issues.extend(
            m.Infra.Issue(
                file=u.Cli.json_pick_str(item, "filepath", "?"),
                line=u.Cli.json_pick_int(item, "line"),
                column=u.Cli.json_pick_int(item, "column"),
                code=u.Cli.json_pick_str(item, "kind", c.Infra.ACTIONLINT),
                message=u.Cli.json_pick_str(item, "message"),
            )
            for item in raw_items
        )
        if result.exit_code != 0 and not issues:
            output = "\n".join(
                part for part in (result.stdout, result.stderr) if part
            ).strip()
            issues.append(
                m.Infra.Issue(
                    file=str(project_dir / c.Infra.GITHUB_WORKFLOWS_DIR),
                    line=1,
                    column=1,
                    code="TOOL_ERROR",
                    message=output or f"actionlint exited with code {result.exit_code}",
                    severity="ERROR",
                )
            )
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraActionlintGate"]
