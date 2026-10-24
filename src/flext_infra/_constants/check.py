"""Centralized constants for the check subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from flext_core import c

from flext_infra._constants.config import FlextInfraConstantsConfig
from flext_infra._pytest_profile_child import FlextInfraPytestProfileChild

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCheck(FlextInfraConstantsConfig):
    """Check infrastructure constants."""

    AST_GREP_DOCS_URL: ClassVar[str] = "https://ast-grep.github.io/"
    LINT: ClassVar[str] = "lint"
    FORMAT: ClassVar[str] = "format"
    MARKDOWN: ClassVar[str] = "markdown"
    MARKDOWN_FORMAT: ClassVar[str] = "markdown-format"
    MARKDOWN_CODE: ClassVar[str] = "markdown-code"
    SMELLS: ClassVar[str] = "smells"
    FRESH_IMPORT: ClassVar[str] = "fresh-import"
    CONFLICT_MARKERS: ClassVar[str] = "conflict-markers"
    DEPS: ClassVar[str] = "deps"
    RUNTIME_INTEGRITY: ClassVar[str] = "runtime-integrity"
    ENFORCEMENT_CATALOG: ClassVar[str] = "enforcement-catalog"

    GATE_TOOLS_BY_KIND: ClassVar[
        t.MappingKV[
            FlextInfraConstantsConfig.GateKind,
            t.MappingKV[str, t.Quad[str, str, bool, bool]],
        ]
    ] = MappingProxyType({
        FlextInfraConstantsConfig.GateKind.EXTERNAL: MappingProxyType({
            "lint": ("Ruff Linter", "https://docs.astral.sh/ruff/", True, True),
            "format": (
                "Ruff Formatter",
                "https://docs.astral.sh/ruff/formatter/",
                False,
                True,
            ),
            "security": ("Bandit", "https://bandit.readthedocs.io/", False, False),
            "markdown": ("rumdl", "https://rumdl.dev/", True, False),
            "markdown-format": ("rumdl", "https://rumdl.dev/", False, False),
            "markdown-code": ("Ruff", "https://docs.astral.sh/ruff/", True, False),
            "duplication": (
                "jscpd",
                "https://github.com/kucherenko/jscpd",
                False,
                False,
            ),
        }),
        FlextInfraConstantsConfig.GateKind.TYPE_CHECKER: MappingProxyType({
            "pyrefly": ("Pyrefly", "https://github.com/facebook/pyrefly", False, True),
            "mypy": ("Mypy", "https://mypy.readthedocs.io/", False, True),
            "pyright": ("Pyright", "https://github.com/microsoft/pyright", False, True),
        }),
        FlextInfraConstantsConfig.GateKind.INFRA: MappingProxyType({
            RUNTIME_INTEGRITY: (
                "Flext Runtime Integrity",
                "internal://flext-infra/runtime-integrity",
                False,
                False,
            ),
            CONFLICT_MARKERS: (
                "Git Conflict Markers",
                "internal://flext-infra/conflict-markers",
                False,
                False,
            ),
            "loc-cap": ("scc", "https://github.com/boyter/scc", False, False),
            ENFORCEMENT_CATALOG: (
                "Flext Static Enforcement Catalog",
                "internal://flext-infra/enforcement-catalog",
                False,
                False,
            ),
            FRESH_IMPORT: (
                "Flext Fresh-Process Import Gate",
                "internal://flext-infra/fresh-import",
                False,
                False,
            ),
            DEPS: (
                "Flext Dependency Declaration Gate",
                "internal://flext-infra/deps",
                True,
                False,
            ),
            "index-declarations": (
                "Flext Index Declarations Gate",
                "internal://flext-infra/index-declarations",
                False,
                False,
            ),
            SMELLS: (
                "Flext Code Smell Detector",
                "internal://flext-infra/smells",
                False,
                False,
            ),
            "codemod": ("ast-grep", AST_GREP_DOCS_URL, False, True),
            "layout": (
                "Flext Project Layout Gate",
                "internal://flext-infra/layout",
                False,
                False,
            ),
            "direnv": (
                "Flext Direnv Environment Contract Gate",
                "internal://flext-infra/direnv",
                False,
                False,
            ),
        }),
    })
    """Sole gate registry; each gate is declared once under its catalog owner.

    Each row carries the gate's SARIF tool identity (name, URL), its
    ``make fix`` repair policy, and whether the checker accepts one
    declared file via the file-gate verbs.
    """
    GATE_KINDS: ClassVar[t.MappingKV[str, FlextInfraConstantsConfig.GateKind]] = (
        MappingProxyType({
            gate: kind for kind, tools in GATE_TOOLS_BY_KIND.items() for gate in tools
        })
    )
    TYPE_CHECKER_GATES: ClassVar[frozenset[str]] = frozenset(
        GATE_TOOLS_BY_KIND[FlextInfraConstantsConfig.GateKind.TYPE_CHECKER],
    )
    SARIF_TOOL_INFO: ClassVar[t.MappingKV[str, t.StrPair]] = MappingProxyType({
        gate: (tool[0], tool[1])
        for tools in GATE_TOOLS_BY_KIND.values()
        for gate, tool in tools.items()
    })
    ALLOWED_GATES: ClassVar[frozenset[str]] = frozenset(SARIF_TOOL_INFO)
    CANONICAL_GATE_IDS: ClassVar[t.VariadicTuple[str]] = tuple(SARIF_TOOL_INFO)
    CANONICAL_FIXABLE_GATE_IDS: ClassVar[t.VariadicTuple[str]] = tuple(
        gate
        for tools in GATE_TOOLS_BY_KIND.values()
        for gate, tool in tools.items()
        if tool[2]
    )
    """Independent repair policy; formatting remains owned by Make fmt."""
    CANONICAL_FILE_GATE_IDS: ClassVar[t.VariadicTuple[str]] = tuple(
        gate
        for tools in GATE_TOOLS_BY_KIND.values()
        for gate, tool in tools.items()
        if tool[3]
    )
    """Gates whose checker accepts one declared file via ``make <verb>-file``."""

    CHECK_FAIL_FAST_DEFAULT: ClassVar[bool] = False
    """Run every independent quality gate unless fail-fast is requested."""
    SERVICE_FAIL_FAST: ClassVar[bool] = True
    """Stop mutating service workflows at the first failed project or rule."""
    NATIVE_CODE_WITNESS_MARSHAL_VERSION: ClassVar[int] = 2
    """Complete CPython code encoding without reference or interning flags."""
    NATIVE_TUPLE_REPEAT_LIMIT: ClassVar[int] = 255
    """Largest literal repeat count read as closed tuple constructor data."""

    PYTEST_SELECTED_COLLECTION_OPTION: ClassVar[str] = "--flext-selected-collection"
    PYTEST_SUITE_STOP_OPTION: ClassVar[str] = "--flext-suite-stop-monotonic"
    PYTEST_CASE_TIMEOUT_DISABLED_SECONDS: ClassVar[int] = 0
    """Native pytest-timeout sentinel disabling per-item deadlines."""
    PYTEST_WORKER_RESTARTS_DISABLED: ClassVar[int] = 0
    """Native xdist sentinel prohibiting replacement of crashed workers."""
    PYTEST_COLLECTION_MANIFEST_OPTION: ClassVar[str] = "--flext-collection-manifest"
    PYTEST_WORKER_COLLECTION_KEY: ClassVar[str] = "flext_collection_manifest"
    """Native xdist worker-output key carrying the observed manifest as JSON."""
    PYTEST_PROFILE_PROCESS_DIRECTORY_ENV: ClassVar[str] = (
        "FLEXT_PYTEST_PROFILE_PROCESS_DIRECTORY"
    )
    PYTEST_PROFILE_CHILD_ROOT_ENV: ClassVar[str] = "FLEXT_PYTEST_PROFILE_CHILD_ROOT"
    PYTEST_SELECTION_PROFILE_FILENAME: ClassVar[str] = "testmon-selection.pstats"
    PYTEST_INVENTORY_PROFILE_FILENAME: ClassVar[str] = "testmon-inventory.pstats"
    PYTEST_PROFILE_CLOCK_MODULE: ClassVar[str] = "flext_infra._pytest_clock"
    PYTEST_PROFILE_BOOTSTRAP: ClassVar[str] = (
        FlextInfraPytestProfileChild.bootstrap_stub(PYTEST_PROFILE_CLOCK_MODULE)
    )
    PYTEST_PROFILE_LAUNCHER: ClassVar[str] = FlextInfraPytestProfileChild.launcher_stub(
        PYTEST_PROFILE_CLOCK_MODULE,
        PYTEST_PROFILE_CHILD_ROOT_ENV,
        PYTEST_PROFILE_PROCESS_DIRECTORY_ENV,
    )
    """Parent-free ``python -c`` payloads projected from their real owner.

    ``FlextInfraPytestProfileChild`` owns the child transport and renders
    these stubs from its live module, class and method identities, so the
    embedded transport logic has exactly one authored source. The launcher
    accepts ``<output.pstats> <pytest args...>`` and enables run-owned
    startup instrumentation for descendants, including pytester children,
    while still executing the existing site customization. The stdlib
    loader resolves the clock without importing the parent package.
    Pytest installs assertion rewriting before any plugin package is
    imported; its ``SystemExit`` still sets the native exit status.
    """

    @unique
    class SarifSchema(StrEnum):
        """Supported SARIF schema identities."""

        V2_1_0 = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/Schemata/sarif-schema-2.1.0.json"

    @unique
    class SarifVersion(StrEnum):
        """Supported SARIF format versions."""

        V2_1_0 = "2.1.0"

    @unique
    class GateSeverity(StrEnum):
        """Severity levels accepted by gate output parsers."""

        ERROR = "error"
        WARNING = "warning"
        NOTE = "note"

    @unique
    class EnforcementEngine(StrEnum):
        """Owner engine named by a static enforcement catalog rule reference."""

        AST_GREP = "ast-grep"
        RUFF = "ruff"
        GATE = "gate"
        CODEGEN = "codegen"

    @unique
    class EnforcementSeverity(StrEnum):
        """Severity declared by a static enforcement catalog row."""

        CRITICAL = "CRITICAL"
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"

    ENFORCEMENT_RULE_ID_PATTERN: ClassVar[str] = r"^ENFORCE-\d{3}$"
    ACCESSOR_PREFIX_UTIL_ID: ClassVar[str] = "accessor-forbidden-prefix"
    "Generated ast-grep util projecting tooling accessor-policy prefixes."
    RUFF_SELECT_ALL: ClassVar[str] = "ALL"

    @unique
    class ToolOutcome(StrEnum):
        """How a completed tool run ended, read from its exit and its report.

        ``CLEAN`` and ``FINDINGS`` are runs the tool completed; only ``ERROR``
        (a status the tool does not declare, a timeout, a signal, or a findings
        status with nothing reported) breaks a repair verb. Findings stay
        reported and are enforced by ``make check``
        (operator-rulings-2026-10-01-lint-automation, ruling d).
        """

        CLEAN = "clean"
        FINDINGS = "findings"
        ERROR = "error"

    @unique
    class LintFixRecipe(StrEnum):
        """Repair the lint gate applies to a finding Ruff reports without a fix.

        The tooling owner maps each Ruff rule name to one recipe; ``make fix``
        applies Ruff's own fixes first and then the recipe of every finding
        left, so no rule code or repair text lives in the gate.
        """

        RETURNS_SECTION = "returns-section"
        YIELDS_SECTION = "yields-section"
        RAISES_SECTION = "raises-section"
        EXTRANEOUS_RAISES = "extraneous-raises"
        SUMMARY_DOCSTRING = "summary-docstring"
        COPYRIGHT_NOTICE = "copyright-notice"
        STATIC_METHOD = "static-method"
        NORMALIZE_IMPORTS = "normalize-imports"
        WRAP_LONG_LINE = "wrap-long-line"

    SERVICE_BASE_ROOTS: ClassVar[frozenset[str]] = frozenset({"FlextService", "s"})
    """Roots whose service operations remain public instance methods (ADR-019).

    Core discovery excludes static methods, class methods and properties.
    """

    CHECK_REPORT_MARKDOWN_FILENAME: ClassVar[str] = "check-report.md"
    "Human-readable check report written beside the SARIF report."
    CHECK_REPORT_SARIF_FILENAME: ClassVar[str] = "check-report.sarif"
    "SARIF 2.1.0 check report: the machine-readable findings owner of ``check run``."
    CHECK_PROFILE_FILENAME: ClassVar[str] = "check.pstats"
    "Optional native profile of the captured checker in its invocation directory."
    RUFF_FORMAT_FILE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*-->\s*(.+?):\d+:\d+\s*$",
    )
    MARKDOWN_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+):\s+\[(?P<code>MD\d+)\]\s+(?P<msg>.*)$",
    )
    MARKDOWN_FIXED_SUFFIX: ClassVar[str] = "[fixed]"
    "rumdl text-output suffix marking a finding its mutating pass repaired."
    MARKDOWN_FORMAT_DIFF_HEADERS: ClassVar[t.StrPair] = ("--- ", "+++ ")
    MARKDOWN_FORMAT_RE: ClassVar[t.RegexPattern] = re.compile(
        # Prettier applies terminal SGR styling to the warning label in CI.
        r"^\[(?:\x1b\[[0-9;]*m)*warn(?:\x1b\[[0-9;]*m)*\]"
        r"\s+(?P<file>\S+\.md)\s*$",
        re.MULTILINE,
    )
    (
        "``rumdl fmt --check`` unified-diff header pair naming one file the "
        "formatter would rewrite; consecutive lines carry the same path."
    )
    MARKDOWN_CODE_LANGUAGE: ClassVar[str] = "python"
    "Fence language prefix (``python``, ``python3``) the embedded-code gates own."
    MARKDOWN_CODE_SOURCE_FORMAT: ClassVar[str] = "{}_b{}.py"
    "Temp-file name for one extracted block: sanitized doc path plus block index."
    MARKDOWN_CODE_SKIP_MARKER: ClassVar[str] = "notest"
    (
        "Existing fence marker (pytest-markdown-docs) "
        "opting a block out of code validation."
    )
    MARKDOWN_CODE_SOURCE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"(?P<file>[^\s/:]+_b\d+\.py)(?::(?P<line>\d+))?",
    )
    "Extracted-source name (``MARKDOWN_CODE_SOURCE_FORMAT``) inside any ruff line."
    VALID_GATE_SEVERITIES: ClassVar[frozenset[str]] = frozenset(GateSeverity)
    "Severity levels accepted by gate output parsers — derived from GateSeverity."
    PYRIGHT_DIAGNOSTICS_KEY: ClassVar[str] = "generalDiagnostics"
    PYRIGHT_PROJECT_ARG: ClassVar[str] = "--project"
    PYRIGHT_PROJECT_CONFIG_TARGET: ClassVar[str] = "."
    BANDIT_RESULTS_KEY: ClassVar[str] = "results"
    PYREFLY_ERRORS_KEY: ClassVar[str] = "errors"
    PYREFLY_ZERO_ERRORS_RECEIPT: ClassVar[str] = "INFO 0 errors"
    "Exact successful stderr receipt emitted by Pyrefly's per-file check."

    SCC_BINARY: ClassVar[str] = "scc"
    CLI_DIRENV: ClassVar[str] = "direnv"
    SCC_PYTHON_LANG: ClassVar[str] = "Python"
    "scc language key the 200-LOC cap enforces; "
    "templates (.j2/.mk), schemas (.json), and config (.yml/.toml) are not modules."

    # --- qlty smells gate (code-smell architecture violations) SSOT ---
    QLTY_BINARY: ClassVar[str] = "qlty"
    QLTY_CONFIG_DIRNAME: ClassVar[str] = ".qlty"
    QLTY_CONFIG_FILENAME: ClassVar[str] = "qlty.toml"
    SMELLS_QLTY_ARGS: ClassVar[t.StrSequence] = (
        "smells",
        "--sarif",
        "--include-tests",
        "--no-snippets",
        "--quiet",
        "--no-upgrade-check",
    )
    "Smells scan arguments; the gate appends explicit targets, scanned in full."
    SMELLS_RULE_PREFIX: ClassVar[str] = "qlty:"
    # --- jscpd duplication gate SSOT (flext-infra owns the
    # jscpd plugin behind one centralized `make check` verb; its config is
    # rendered from this typed SSOT at scan time, never a hand-maintained file).
    JSCPD_BINARY: ClassVar[str] = "jscpd"
    (
        "Provisioned by mise from codegen.toolchain.tools entry 'jscpd'; "
        "never a runner or a version here."
    )

    JSCPD_MODE: ClassVar[str] = "strict"
    JSCPD_MIN_LINES: ClassVar[int] = 10
    "Minimum lines for a clone (R2: 10 lines = 62 tokens per consumption-law.md)."
    JSCPD_MIN_TOKENS: ClassVar[int] = 62
    "Minimum tokens for a clone (R2: 10 lines ≈ 62 tokens)."
    JSCPD_THRESHOLD_PERCENT: ClassVar[int] = 0
    "Zero tolerance — every owned clone is an error."
    JSCPD_SCOPE_DIRNAMES: ClassVar[t.StrSequence] = (
        "src",
        "tests",
        "scripts",
        "examples",
        "templates",
        "config",
    )
    (
        "Canonical scope: source, tests, scripts, examples, "
        "templates, config (R2 consumer+family)."
    )
    JSCPD_REPORT_DIRNAME: ClassVar[str] = ".reports/jscpd"
    JSCPD_CONFIG_FILENAME: ClassVar[str] = ".jscpd.generated.json"
    JSCPD_REPORT_FILENAME: ClassVar[str] = "jscpd-report.json"
    JSCPD_FORMAT_EXTENSIONS: ClassVar[t.MappingKV[str, t.StrSequence]] = (
        MappingProxyType({"django": ("j2",)})
    )
    "Parse Jinja projections in place; never duplicate templates into a scan tree."
    # NOTE: JSCPD_IGNORE_PATTERNS was removed: the duplication gate derives
    # its ignore list from the declared sgconfig fixture topology, the
    # generated-surface and snapshot declarations, the artifact
    # resolver_owned emission type, and the declared exclusion registry
    # (parameterized case fixtures, part containers, helper modules).
    # No hand-maintained pattern list remains.

    # --- Extended duplication gate (R2 consumer+family scope) ---
    JSCPD_CONSUMER_FAMILY_SCOPE: ClassVar[bool] = True
    "When true, extend scan scope to consumer+family via [tool.flext.project] keys."
    JSCPD_STRUCTURAL_BAN_FORMS: ClassVar[bool] = True
    (
        "When true, ban structural forms only for mechanisms "
        "with published canonical owner."
    )

    # --- Manual-command blocker (AGENTS.md `Build & Test`) SSOT ---
    MANUAL_CMD_BLOCKED_TOOLS: ClassVar[frozenset[str]] = frozenset({
        "ruff",
        "pytest",
        "pyrefly",
        "mypy",
        "pyright",
    })
    MANUAL_CMD_BLOCKED_GIT: ClassVar[frozenset[str]] = frozenset({
        "commit",
        "add",
        "push",
        "tag",
    })
    MANUAL_CMD_REWRITE_TOOLS: ClassVar[frozenset[str]] = frozenset({"ast-grep"})
    MANUAL_CMD_RUNNERS: ClassVar[frozenset[str]] = frozenset({"python", "python3"})
    MANUAL_CMD_UV_RUN_VALUE_OPTIONS: ClassVar[frozenset[str]] = frozenset({
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
    MANUAL_CMD_WRAPPERS: ClassVar[frozenset[str]] = frozenset({
        "env",
        "time",
        "nohup",
        "xargs",
        "sudo",
        c.HandlerType.COMMAND,
        "nice",
        "ionice",
        "stdbuf",
    })
    MANUAL_CMD_REWRITE_FLAGS: ClassVar[frozenset[str]] = frozenset({
        "--rewrite",
        "-U",
        "--update-all",
    })
    MANUAL_CMD_SEGMENT_RE: ClassVar[t.RegexPattern] = re.compile(
        r"&&|\|\||;|\||\n|`|\$\(",
    )

    # --- Net-LOC-delta validator (§3.5) SSOT ---
    REFACTOR_COMMIT_LABELS: ClassVar[frozenset[str]] = frozenset({
        "refactor",
        "deduplicate",
        "cleanup",
        "yagni",
        "simplify",
    })


__all__: list[str] = ["FlextInfraConstantsCheck"]
