"""Cohesive external-tool-runner mixin for dependency detection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraDependencyDetectionRunnersMixin:
    """Mixin holding raw-run contract plus external analysis-tool runners."""

    if TYPE_CHECKING:
        # Conversion helper provided by the concrete analyzer; declared for static
        # resolution only (runtime impl lives on the concrete via MRO).
        def _to_toml_config(
            self, payload: t.MappingKV[str, t.Infra.InfraValue]
        ) -> t.JsonMapping: ...

    def _run_raw(
        self,
        cmd: t.StrSequence,
        *,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run raw command; concrete analyzer supplies the real runner."""
        _ = cmd, cwd, timeout, env
        msg = "_run_raw must be implemented by the concrete analyzer"
        raise NotImplementedError(msg)

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
        *,
        config_path: Path | None = None,
        json_output_path: Path | None = None,
        extend_exclude: t.StrSequence | None = None,
    ) -> p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]:
        """Run deptry analysis on a project and parse JSON output."""
        settings = config_path or project_path / c.Infra.PYPROJECT_FILENAME
        if not settings.exists():
            return r[t.Pair[t.SequenceOf[t.JsonMapping], int]].ok(([], 0))
        out_file = json_output_path or project_path / ".deptry-report.json"
        cmd: t.MutableSequenceOf[str] = [
            str(venv_bin / c.Infra.DEPTRY),
            ".",
            "--config",
            str(settings),
            "--json-output",
            str(out_file),
            "--no-ansi",
        ]
        if extend_exclude:
            for excluded in extend_exclude:
                cmd.extend(["--extend-exclude", excluded])
        result = self._run_raw(cmd, cwd=project_path, timeout=c.Infra.TIMEOUT_MEDIUM)
        if result.failure:
            return r[t.Pair[t.SequenceOf[t.JsonMapping], int]].fail(
                result.error or "deptry execution failed"
            )
        issues: t.SequenceOf[t.JsonMapping] = []
        if out_file.exists():
            loaded_result = u.Cli.files_read_json(out_file)
            if loaded_result.failure:
                return r[t.Pair[t.SequenceOf[t.JsonMapping], int]].fail(
                    loaded_result.error or "deptry JSON output unreadable/invalid"
                )
            if isinstance(loaded_result.value, list):
                normalized_issues: t.MutableSequenceOf[t.JsonMapping] = []
                for item in loaded_result.value:
                    if not isinstance(item, Mapping):
                        continue
                    try:
                        typed_item = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item)
                    except c.ValidationError:
                        continue
                    converted_issue = self._to_toml_config(typed_item)
                    if len(converted_issue) == len(typed_item):
                        normalized_issues.append(converted_issue)
                issues = normalized_issues
            if json_output_path is None:
                try:
                    out_file.unlink()
                except OSError as exc:
                    return r[t.Pair[t.SequenceOf[t.JsonMapping], int]].fail(
                        f"failed to cleanup deptry temp output: {exc}"
                    )
        cmd_result: p.Cli.CommandOutput = result.value
        return r[t.Pair[t.SequenceOf[t.JsonMapping], int]].ok((
            issues,
            cmd_result.exit_code,
        ))

    def run_pip_check(
        self, workspace_root: Path, venv_bin: Path
    ) -> p.Result[t.Pair[t.StrSequence, int]]:
        """Run pip check to detect dependency conflicts in workspace."""
        pip = venv_bin / "pip"
        if not pip.exists():
            return r[t.Pair[t.StrSequence, int]].ok(([], 0))
        env = {"VIRTUAL_ENV": str(venv_bin.parent)}
        result = self._run_raw(
            [str(pip), c.Infra.VERB_CHECK],
            cwd=workspace_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            env=env,
        )
        if result.failure:
            return r[t.Pair[t.StrSequence, int]].fail(
                result.error or "pip check failed"
            )
        cmd_result: p.Cli.CommandOutput = result.value
        output = cmd_result.stdout
        lines = output.strip().splitlines() if output else []
        return r[t.Pair[t.StrSequence, int]].ok((lines, cmd_result.exit_code))


__all__: list[str] = ["FlextInfraDependencyDetectionRunnersMixin"]
