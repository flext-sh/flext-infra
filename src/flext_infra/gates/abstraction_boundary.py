"""Abstraction-boundary quality gate (AGENTS.md §2.7).

Single SSOT replacing the two standalone scripts ``audit_banned_cli_libs.py``
and ``audit_flext_cli_concrete_imports.py``. For every project except
``flext-cli``/``flext-core`` it flags CLI-domain lib imports (``click`` exempt
in Singer-SDK boundary files), ``subprocess``, ``tomllib``/``tomlkit`` outside
``flext-infra``, direct ``json.``/``yaml.``/``csv.`` use, top-level ``print(``/
``sys.exit(``, and concrete ``FlextCli<X>`` imports outside src extension files.
Core-abstracted libs (pydantic, structlog, …) are NOT yet banned here — that
extension needs an owner catalogue + workspace cleanup first (plan §F).
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar, override

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraAbstractionBoundaryGate(FlextInfraGate):
    """Block CLI-domain library leakage and concrete FlextCli imports in consumers."""

    gate_id: ClassVar[str] = "boundary"
    gate_name: ClassVar[str] = "Abstraction Boundary"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["boundary"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["boundary"][1]

    _SKIP_PROJECTS: ClassVar[frozenset[str]] = frozenset({"flext-cli", "flext-core"})
    _TOML_ALLOWED: ClassVar[frozenset[str]] = frozenset({"flext-infra"})
    _CLICK_BOUNDARY: ClassVar[tuple[str, ...]] = (
        "/flext-tap-",
        "/flext-target-",
        "/flext-meltano/src/flext_meltano/services/executor_base.py",
        "/flext-meltano/src/flext_meltano/_protocols/singer.py",
        "/flext-meltano/tests/unit/test_singer_sdk_adapter.py",
    )
    _EXTENSION_FILES: ClassVar[frozenset[str]] = frozenset({
        "constants.py",
        "models.py",
        "protocols.py",
        "typings.py",
        "utilities.py",
        "settings.py",
    })
    _BANNED_LIBS: ClassVar[MappingProxyType[str, str]] = MappingProxyType({
        "typer": "cli.create_app_with_common_params / cli.register_command",
        "click": "flext_cli (cli, c.Cli.CliAbortError, c.Cli.CliCommandError)",
        "argparse": "cli.register_result_command + Pydantic model",
        "rich": "cli.print / cli.display_message / cli.render_panel / cli.create_tree",
        "tabulate": "cli.format_table / cli.show_table",
        "colorama": "cli.print with c.Cli.MessageStyles",
        "prompt_toolkit": "cli.prompt / cli.confirm / cli.prompt_password",
        "tqdm": "cli.display_progress",
        "getpass": "cli.prompt_password",
        "orjson": "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps",
        "ujson": "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps",
        "simplejson": "cli.read_json_file / cli.write_json_file / u.Cli.json_dumps",
    })
    _PROC_RE: ClassVar[re.Pattern[str]] = re.compile(
        rf"^\s*(import|from)\s+{'sub' + 'process'}(\s|$|\.)", re.MULTILINE
    )
    _TOML_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^\s*(import|from)\s+(tomllib|tomlkit)(\s|$|\.)", re.MULTILINE
    )
    _JSON_RE: ClassVar[re.Pattern[str]] = re.compile(r"\bjson\.(load|dump|loads|dumps)\b")
    _YAML_RE: ClassVar[re.Pattern[str]] = re.compile(r"\byaml\.(safe_load|dump|load)\b")
    _CSV_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"\bcsv\.(reader|writer|DictReader|DictWriter)\b"
    )
    _PRINT_RE: ClassVar[re.Pattern[str]] = re.compile(r"^\s*print\(", re.MULTILINE)
    _SYSEXIT_RE: ClassVar[re.Pattern[str]] = re.compile(r"^\s*sys\.exit\(", re.MULTILINE)
    _CONCRETE_IMPORT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^from\s+flext_cli\s+import\s+(?P<imports>.+?)$", re.MULTILINE
    )
    _FLEXT_CLI_CONCRETE_RE: ClassVar[re.Pattern[str]] = re.compile(r"\bFlextCli[A-Z]\w*")

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Scan one project's Python sources for abstraction-boundary breaches."""
        _ = ctx
        started = time.monotonic()
        if project_dir.name in self._SKIP_PROJECTS:
            return self._skip_result(project_dir, started)
        files_result = u.Infra.iter_python_files(
            project_dir,
            project_roots=[project_dir],
            include_tests=True,
        )
        if files_result.failure:
            issue = m.Infra.Issue(
                file=project_dir.name,
                line=1,
                column=1,
                code=self.gate_id,
                message=files_result.error or "abstraction-boundary scan failed",
            )
            return self._result(project_dir, started, [issue])
        issues = [
            issue
            for file_path in files_result.value
            for issue in self._scan_file(file_path, project_dir.name)
        ]
        return self._result(project_dir, started, issues)

    def _result(
        self,
        project_dir: Path,
        started: float,
        issues: t.SequenceOf[m.Infra.Issue],
    ) -> m.Infra.GateExecution:
        """Assemble the gate execution from collected issues."""
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=len(issues) == 0,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output="\n".join(issue.formatted for issue in issues),
        )

    def _scan_file(self, path: Path, project: str) -> t.SequenceOf[m.Infra.Issue]:
        """Return boundary violations for a single Python file."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        posix = str(path).replace("\\", "/")
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        click_ok = any(fragment in posix for fragment in self._CLICK_BOUNDARY)
        for lib, replacement in self._BANNED_LIBS.items():
            if lib == "click" and click_ok:
                continue
            if re.search(rf"^\s*(import|from)\s+{lib}(\s|$|\.)", text, re.MULTILINE):
                issues.append(self._issue(path, f"imports `{lib}` — use {replacement}"))
        if self._PROC_RE.search(text):
            issues.append(self._issue(path, "imports subprocess — use cli.run / cli.capture"))
        if self._TOML_RE.search(text) and project not in self._TOML_ALLOWED:
            issues.append(self._issue(path, "imports tomllib/tomlkit — use cli.read_toml_file"))
        if self._JSON_RE.search(text):
            issues.append(self._issue(path, "uses json.load/dump — use cli.*_json_file"))
        if self._YAML_RE.search(text):
            issues.append(self._issue(path, "uses yaml.safe_load/dump — use cli.*_yaml_file"))
        if self._CSV_RE.search(text):
            issues.append(self._issue(path, "uses csv.reader/writer — use cli.*_csv_file"))
        if self._PRINT_RE.search(text):
            issues.append(self._issue(path, "uses print() — use cli.print / cli.display_message"))
        if self._SYSEXIT_RE.search(text):
            issues.append(self._issue(path, "uses sys.exit() — use cli.exit()"))
        issues.extend(self._concrete_cli_issues(path, text, posix))
        return issues

    def _concrete_cli_issues(
        self, path: Path, text: str, posix: str
    ) -> t.SequenceOf[m.Infra.Issue]:
        """Flag concrete FlextCli<X> imports outside src extension files."""
        extension_ok = "/src/" in posix and path.name in self._EXTENSION_FILES
        if extension_ok:
            return ()
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        for match in self._CONCRETE_IMPORT_RE.finditer(text):
            for name in self._FLEXT_CLI_CONCRETE_RE.findall(match.group("imports")):
                issues.append(
                    self._issue(path, f"imports concrete `{name}` (use cli/c/m/p/t/u/s)")
                )
        return issues

    def _issue(self, path: Path, message: str) -> m.Infra.Issue:
        """Build a boundary Issue anchored at the file head."""
        return m.Infra.Issue(
            file=str(path),
            line=1,
            column=1,
            code=self.gate_id,
            message=message,
            severity="ERROR",
        )

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """No external tool — scanning happens in `check`."""
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Unused — `check` is overridden directly."""
        _ = result, project_dir, ctx
        return True, ()


__all__: list[str] = ["FlextInfraAbstractionBoundaryGate"]
