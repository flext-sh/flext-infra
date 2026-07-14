"""Centralized constants for the check subpackage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final

from flext_infra import t


class FlextInfraConstantsCheck:
    """Check infrastructure constants."""

    @unique
    class GateSeverity(StrEnum):
        """Severity levels accepted by gate output parsers."""

        ERROR = "error"
        WARNING = "warning"
        NOTE = "note"

    @unique
    class GateMode(StrEnum):
        """Gate enforcement posture — WARN reports without failing; STRICT fails."""

        WARN = "warn"
        STRICT = "strict"

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
        "markdown": ("MarkdownLint", "https://github.com/DavidAnson/markdownlint"),
        "loc-cap": ("Tokei", "https://github.com/XAMPPRocky/tokei"),
        "boundary": (
            "Flext Abstraction Boundary Auditor",
            "internal://flext-infra/abstraction-boundary",
        ),
        "runtime-census": (
            "Flext Runtime Enforcement Census",
            "internal://flext-infra/runtime-census",
        ),
        "namespace": ("Flext Namespace Rule Gate", "internal://flext-infra/namespace"),
        "tier-whitelist": (
            "Flext Tier Whitelist Gate",
            "internal://flext-infra/tier-whitelist",
        ),
        "smells": ("Flext Code Smell Detector", "internal://flext-infra/smells"),
        "canonical-alias": (
            "Flext Canonical Alias Detector",
            "internal://flext-infra/canonical-alias",
        ),
    })
    ALLOWED_GATES: Final[frozenset[str]] = frozenset(SARIF_TOOL_INFO)
    "Gate identifiers — derived from SARIF_TOOL_INFO keys (single SSOT)."
    RUFF_FORMAT_FILE_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*-->\s*(.+?):\d+:\d+\s*$"
    )
    MARKDOWN_RE: Final[t.RegexPattern] = re.compile(
        r"^(?P<file>.*?):(?P<line>\d+)(?::(?P<col>\d+))?\s+error\s+(?P<code>MD\d+)(?:/[^\s]+)?\s+(?P<msg>.*)$"
    )
    VALID_GATE_SEVERITIES: Final[frozenset[str]] = frozenset(GateSeverity)
    "Severity levels accepted by gate output parsers — derived from GateSeverity."

    PYRIGHT_DIAGNOSTICS_KEY: Final[str] = "generalDiagnostics"
    PYRIGHT_PROJECT_ARG: Final[str] = "--project"
    PYRIGHT_PROJECT_CONFIG_TARGET: Final[str] = "."
    BANDIT_RESULTS_KEY: Final[str] = "results"
    PYREFLY_ERRORS_KEY: Final[str] = "errors"

    # --- Abstraction-boundary gate (§2.7) detection SSOT ---
    BOUNDARY_SKIP_PROJECTS: Final[frozenset[str]] = frozenset({
        "flext-cli",
        "flext-core",
    })
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
        "click": "flext_cli.cli application, registration, execution, and invocation methods",
        "argparse": "cli.register_result_command + Pydantic model",
        "rich": "cli.print / cli.display_message / cli.render_panel / cli.render_table",
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
            re.compile(
                rf"^\s*(import|from)\s+{'sub' + 'process'}(\s|$|\.)", re.MULTILINE
            ),
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
        (
            re.compile(r"^\s*sys\.exit\(", re.MULTILINE),
            "uses sys.exit() — use cli.exit()",
        ),
    )
    # The boundary gate's own rule-definition source files legitimately contain the
    # forbidden-pattern strings as DETECTION RULES (not as usage); exempt them from
    # self-scanning so the detector does not flag its own catalog.
    BOUNDARY_SELF_FILES: Final[frozenset[str]] = frozenset({
        "flext_infra/_constants/check.py",
        "flext_infra/gates/abstraction_boundary.py",
    })
    BOUNDARY_TOML_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*(import|from)\s+(tomllib|tomlkit)(\s|$|\.)", re.MULTILINE
    )
    BOUNDARY_CONCRETE_IMPORT_RE: Final[t.RegexPattern] = re.compile(
        r"^from\s+flext_cli\s+import\s+(?P<imports>.+?)$", re.MULTILINE
    )
    BOUNDARY_FLEXT_CLI_CONCRETE_RE: Final[t.RegexPattern] = re.compile(
        r"\bFlextCli[A-Z]\w*"
    )

    # --- 200-LOC SUPREME LAW (§3.1) gate SSOT ---
    LOC_CAP_MAX: Final[int] = 200
    "Per-module logical-LOC ceiling (AGENTS.md §3.1 SUPREME LAW)."
    TOKEI_BINARY: Final[str] = "tokei"
    TOKEI_TOTAL_KEY: Final[str] = "Total"
    TOKEI_PYTHON_LANG: Final[str] = "Python"
    "tokei language key the 200-LOC cap enforces — §3.1 is a Python-module law; "
    "templates (.j2/.mk), schemas (.json), and config (.yml/.toml) are not modules."

    # --- qlty smells gate (code-smell architecture violations) SSOT ---
    SMELLS_GATE_MODE: Final[GateMode] = GateMode.WARN
    "Report-only posture. FLIP-TO-FAIL = change this one line to GateMode.STRICT."
    QLTY_BINARY: Final[str] = "qlty"
    QLTY_BINARY_FALLBACK_SUFFIX: Final[str] = ".qlty/bin/qlty"
    "Joined to Path.home() when the binary is absent from PATH."
    SMELLS_QLTY_ARGS: Final[t.StrSequence] = (
        "smells",
        "--all",
        "--sarif",
        "--include-tests",
        "--no-snippets",
        "--quiet",
        "--no-upgrade-check",
    )
    "Full-workspace scan: default qlty scope is changed-files-only; --all overrides."
    SMELLS_RULE_PREFIX: Final[str] = "qlty:"
    SMELLS_RULE_TAGS: Final[t.MappingKV[str, str]] = MappingProxyType({
        "boolean-logic": "smell_boolean_logic",
        "file-complexity": "smell_file_complexity",
        "function-complexity": "smell_function_complexity",
        "function-parameters": "smell_function_parameters",
        "identical-code": "smell_identical_code",
        "nested-control-flow": "smell_nested_control_flow",
        "return-statements": "smell_return_statements",
        "similar-code": "smell_similar_code",
    })
    "qlty ruleId suffix -> flext-core enforcement tag (texts SSOT: core ENFORCEMENT_RULES_TEXT)."

    # --- Manual-command blocker (§5 Make Contract) SSOT ---
    MANUAL_CMD_BLOCKED_TOOLS: Final[frozenset[str]] = frozenset({
        "ruff",
        "pytest",
        "pyrefly",
        "mypy",
        "pyright",
    })
    MANUAL_CMD_BLOCKED_GIT: Final[frozenset[str]] = frozenset({
        "commit",
        "add",
        "push",
        "tag",
    })
    MANUAL_CMD_REWRITE_TOOLS: Final[frozenset[str]] = frozenset({"ast-grep", "sg"})
    MANUAL_CMD_RUNNERS: Final[frozenset[str]] = frozenset({"python", "python3"})
    MANUAL_CMD_UV_RUN_VALUE_OPTIONS: Final[frozenset[str]] = frozenset({
        "--default-index",
        "--directory",
        "--env-file",
        "--extra",
        "--find-links",
        "--from",
        "--group",
        "--index",
        "--index-url",
        "--index-strategy",
        "--keyring-provider",
        "--link-mode",
        "--no-extra",
        "--no-group",
        "--only-group",
        "--package",
        "--prerelease",
        "--project",
        "--python",
        "--python-platform",
        "--resolution",
        "--with",
        "--with-editable",
        "--with-requirements",
    })
    "``uv run`` options that consume the following token before the real command."
    MANUAL_CMD_WRAPPERS: Final[frozenset[str]] = frozenset({
        "env",
        "time",
        "nohup",
        "xargs",
        "sudo",
        "command",
        "nice",
        "ionice",
        "stdbuf",
    })
    MANUAL_CMD_REWRITE_FLAGS: Final[frozenset[str]] = frozenset({
        "--rewrite",
        "-U",
        "--update-all",
    })
    MANUAL_CMD_SEGMENT_RE: Final[t.RegexPattern] = re.compile(r"&&|\|\||;|\||\n|`|\$\(")

    # --- Net-LOC-delta validator (§3.5) SSOT ---
    REFACTOR_COMMIT_LABELS: Final[frozenset[str]] = frozenset({
        "refactor",
        "deduplicate",
        "cleanup",
        "yagni",
        "simplify",
    })

    # Canonical .pre-commit-config.yaml (SSOT; was templates/pre_commit_config.yaml.j2).
    # Static — no Jinja vars; hooks route through the workspace uv environment.
    PRE_COMMIT_CONFIG: Final[str] = """\
# @generated by flext_infra — DO NOT EDIT. Run `make gen` / `make sync` to regenerate.
#
# Every hook routes through the canonical `uv run --all-packages python -m flext_infra`
# workspace monopoly; no standalone scripts and no bare tool invocations
# (AGENTS.md §5 Make Contract).
# Enable locally with `pre-commit install` from the workspace root.
repos:
  - repo: local
    hooks:
      - id: beads-issue-discipline
        name: Beads issue tracking (bd hooks run pre-commit)
        entry: bd hooks run pre-commit
        language: system
        pass_filenames: false
        always_run: true
      - id: flext-abstraction-boundary
        name: Abstraction boundary (§2.7) — CLI-domain libs + concrete FlextCli imports
        entry: uv run --all-packages python scripts/hooks/check_changed_projects.py boundary
        language: system
        pass_filenames: true
        always_run: false
        types: [python]
      - id: flext-loc-cap
        name: 200-LOC SUPREME LAW (§3.1) — module cap via tokei
        entry: uv run --all-packages python scripts/hooks/check_changed_projects.py loc-cap
        language: system
        pass_filenames: true
        always_run: false
        types: [python]
      - id: flext-manual-command
        name: Manual-command blocker (§5) — no bare tool calls in automation
        entry: uv run --all-packages python -m flext_infra validate --what manual-cmd
        language: system
        pass_filenames: false
        always_run: true
        types: [python]
"""


__all__: list[str] = ["FlextInfraConstantsCheck"]
