"""Centralized constants for the check subpackage."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCheck:
    """Check infrastructure constants."""

    ALLOWED_GATES: Final[frozenset[str]] = frozenset({
        "lint",
        "format",
        "pyrefly",
        "mypy",
        "pyright",
        "silent-failure",
        "security",
        "markdown",
        "go",
    })
    SARIF_TOOL_INFO: Final[Mapping[str, t.Infra.StrPair]] = MappingProxyType({
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
    REQUIRED_EXCLUDES: Final[t.StrSequence] = ["**/*_pb2*.py", "**/*_pb2_grpc*.py"]
    RUFF_FORMAT_FILE_RE: Final[re.Pattern[str]] = re.compile(
        r"^\s*-->\s*(.+?):\d+:\d+\s*$",
    )
    MARKDOWN_RE: Final[re.Pattern[str]] = re.compile(
        r"^(?P<file>.*?):(?P<line>\d+)(?::(?P<col>\d+))?\s+error\s+(?P<code>MD\d+)(?:/[^\s]+)?\s+(?P<msg>.*)$",
    )
    GO_VET_RE: Final[re.Pattern[str]] = re.compile(
        r"^(?P<file>[^:\n]+\.go):(?P<line>\d+)(?::(?P<col>\d+))?:\s*(?P<msg>.*)$",
    )
    MAX_DISPLAY_ISSUES: Final[int] = 50

    VALID_GATE_SEVERITIES: Final[frozenset[str]] = frozenset({
        "error",
        "warning",
        "note",
    })
    "Severity levels accepted by gate output parsers."

    PYRIGHT_DIAGNOSTICS_KEY: Final[str] = "generalDiagnostics"
    BANDIT_RESULTS_KEY: Final[str] = "results"
    PYREFLY_ERRORS_KEY: Final[str] = "errors"


__all__: list[str] = ["FlextInfraConstantsCheck"]
