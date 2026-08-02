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
        "markdown": ("rumdl", "https://rumdl.dev/"),
        "actionlint": ("Actionlint", "https://github.com/rhysd/actionlint"),
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
        "layout": ("Flext Project Layout Gate", "internal://flext-infra/layout"),
        "canonical-alias": (
            "Flext Canonical Alias Detector",
            "internal://flext-infra/canonical-alias",
        ),
    })
    RUFF_FORMAT_FILE_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*-->\s*(.+?):\d+:\d+\s*$"
    )
    MARKDOWN_RE: Final[t.RegexPattern] = re.compile(
        r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+):\s+\[(?P<code>MD\d+)\]\s+(?P<msg>.*)$"
    )
    VALID_GATE_SEVERITIES: Final[frozenset[str]] = frozenset(GateSeverity)
    "Severity levels accepted by gate output parsers — derived from GateSeverity."
    GATE_ERROR_OUTPUT_LIMIT: Final[int] = 20
    "Maximum parsed gate diagnostics emitted inline before the canonical report."

    PYRIGHT_DIAGNOSTICS_KEY: Final[str] = "generalDiagnostics"
    PYRIGHT_PROJECT_ARG: Final[str] = "--project"
    PYRIGHT_PROJECT_CONFIG_TARGET: Final[str] = "."
    BANDIT_RESULTS_KEY: Final[str] = "results"
    PYREFLY_ERRORS_KEY: Final[str] = "errors"

    # --- Net-LOC-delta validator (§3.5) SSOT ---
    REFACTOR_COMMIT_LABELS: Final[frozenset[str]] = frozenset({
        "refactor",
        "deduplicate",
        "cleanup",
        "yagni",
        "simplify",
    })


__all__: list[str] = ["FlextInfraConstantsCheck"]
