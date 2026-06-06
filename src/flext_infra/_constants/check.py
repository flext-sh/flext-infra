"""Centralized constants for the check subpackage."""

from __future__ import annotations

import re
from enum import StrEnum, unique
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCheck:
    """Check infrastructure constants."""

    @unique
    class GateSeverity(StrEnum):
        """Severity levels accepted by gate output parsers."""

        ERROR = "error"
        WARNING = "warning"
        NOTE = "note"

    SARIF_TOOL_INFO: Final[t.MappingKV[str, t.StrPair]] = MappingProxyType({
        "lint": ("Ruff Linter", "https://docs.astral.sh/ruff/"),
        "format": ("Ruff Formatter", "https://docs.astral.sh/ruff/formatter/"),
        "pyrefly": ("Pyrefly", "https://github.com/facebook/pyrefly"),
        "mypy": ("Mypy", "https://mypy.readthedocs.io/"),
        "pyright": ("Pyright", "https://github.com/microsoft/pyright"),
        "silent-failure": (
            "Flext Silent Failure Detector",
            "internal://flext-infra/silent-failure",
        ),
        "security": ("Bandit", "https://bandit.readthedocs.io/"),
        "markdown": (
            "MarkdownLint",
            "https://github.com/DavidAnson/markdownlint",
        ),
        "go": ("Go Vet", "https://pkg.go.dev/cmd/vet"),
        "loc-cap": ("Tokei", "https://github.com/XAMPPRocky/tokei"),
        "boundary": (
            "Flext Abstraction Boundary Auditor",
            "internal://flext-infra/abstraction-boundary",
        ),
    })
    ALLOWED_GATES: Final[frozenset[str]] = frozenset(SARIF_TOOL_INFO)
    "Gate identifiers — derived from SARIF_TOOL_INFO keys (single SSOT)."
    REQUIRED_EXCLUDES: Final[t.StrSequence] = (
        "**/*_pb2*.py",
        "**/*_pb2_grpc*.py",
    )
    RUFF_FORMAT_FILE_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*-->\s*(.+?):\d+:\d+\s*$",
    )
    MARKDOWN_RE: Final[t.RegexPattern] = re.compile(
        r"^(?P<file>.*?):(?P<line>\d+)(?::(?P<col>\d+))?\s+error\s+(?P<code>MD\d+)(?:/[^\s]+)?\s+(?P<msg>.*)$",
    )
    GO_VET_RE: Final[t.RegexPattern] = re.compile(
        r"^(?P<file>[^:\n]+\.go):(?P<line>\d+)(?::(?P<col>\d+))?:\s*(?P<msg>.*)$",
    )
    MAX_DISPLAY_ISSUES: Final[int] = 50

    VALID_GATE_SEVERITIES: Final[frozenset[str]] = frozenset(GateSeverity)
    "Severity levels accepted by gate output parsers — derived from GateSeverity."

    PYRIGHT_DIAGNOSTICS_KEY: Final[str] = "generalDiagnostics"
    BANDIT_RESULTS_KEY: Final[str] = "results"
    PYREFLY_ERRORS_KEY: Final[str] = "errors"

    # --- Abstraction-boundary gate (§2.7) detection SSOT ---
    BOUNDARY_SKIP_PROJECTS: Final[frozenset[str]] = frozenset({"flext-cli", "flext-core"})
    BOUNDARY_TOML_ALLOWED: Final[frozenset[str]] = frozenset({"flext-infra"})
    BOUNDARY_CLICK_FILES: Final[t.StrSequence] = (
        "/flext-tap-",
        "/flext-target-",
        "/flext-meltano/src/flext_meltano/services/executor_base.py",
        "/flext-meltano/src/flext_meltano/_protocols/singer.py",
        "/flext-meltano/tests/unit/test_singer_sdk_adapter.py",
    )
    BOUNDARY_EXTENSION_FILES: Final[frozenset[str]] = frozenset({
        "constants.py",
        "models.py",
        "protocols.py",
        "typings.py",
        "utilities.py",
        "settings.py",
    })
    BOUNDARY_BANNED_LIBS: Final[t.MappingKV[str, str]] = MappingProxyType({
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
    # Precompiled (lib, regex, replacement) rows — click is exempted at the call
    # site for Singer-SDK boundary files.
    BOUNDARY_BANNED_RULES: Final[tuple[tuple[str, t.RegexPattern, str], ...]] = tuple(
        (lib, re.compile(rf"^\s*(import|from)\s+{lib}(\s|$|\.)", re.MULTILINE), repl)
        for lib, repl in BOUNDARY_BANNED_LIBS.items()
    )
    # Unconditional (regex, message) catalog — one data-driven loop in the gate.
    BOUNDARY_SIMPLE_RULES: Final[tuple[tuple[t.RegexPattern, str], ...]] = (
        (
            re.compile(rf"^\s*(import|from)\s+{'sub' + 'process'}(\s|$|\.)", re.MULTILINE),
            "imports subprocess — use cli.run / cli.capture",
        ),
        (
            re.compile(r"\bjson\.(load|dump|loads|dumps)\b"),
            "uses json.load/dump — use cli.*_json_file",
        ),
        (
            re.compile(r"\byaml\.(safe_load|dump|load)\b"),
            "uses yaml.safe_load/dump — use cli.*_yaml_file",
        ),
        (
            re.compile(r"\bcsv\.(reader|writer|DictReader|DictWriter)\b"),
            "uses csv.reader/writer — use cli.*_csv_file",
        ),
        (re.compile(r"^\s*print\(", re.MULTILINE), "uses print() — use cli.print"),
        (re.compile(r"^\s*sys\.exit\(", re.MULTILINE), "uses sys.exit() — use cli.exit()"),
    )
    BOUNDARY_TOML_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*(import|from)\s+(tomllib|tomlkit)(\s|$|\.)",
        re.MULTILINE,
    )
    BOUNDARY_CONCRETE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
        r"^from\s+flext_cli\s+import\s+(?P<imports>.+?)$",
        re.MULTILINE,
    )
    BOUNDARY_FLEXT_CLI_CONCRETE_RE: Final[t.RegexPattern] = re.compile(r"\bFlextCli[A-Z]\w*")

    # --- 200-LOC SUPREME LAW (§3.1) gate SSOT ---
    LOC_CAP_MAX: Final[int] = 200
    "Per-module logical-LOC ceiling (AGENTS.md §3.1 SUPREME LAW)."
    TOKEI_BINARY: Final[str] = "tokei"
    TOKEI_TOTAL_KEY: Final[str] = "Total"


__all__: list[str] = ["FlextInfraConstantsCheck"]
