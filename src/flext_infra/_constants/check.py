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

    SARIF_TOOL_INFO: Final[t.MappingKV[str, t.Infra.StrPair]] = MappingProxyType({
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


__all__: list[str] = ["FlextInfraConstantsCheck"]
