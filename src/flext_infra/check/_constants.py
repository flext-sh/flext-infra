"""Centralized constants for the check subpackage."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraCheckConstants:
    """Check infrastructure constants."""

    ALLOWED_GATES: Final[frozenset[str]] = frozenset({
        "lint",
        "format",
        "pyrefly",
        "mypy",
        "pyright",
        "security",
        "markdown",
        "go",
    })
    SARIF_TOOL_INFO: Final[Mapping[str, tuple[str, str]]] = {
        "lint": ("Ruff Linter", "https://docs.astral.sh/ruff/"),
        "format": ("Ruff Formatter", "https://docs.astral.sh/ruff/formatter/"),
        "pyrefly": ("Pyrefly", "https://github.com/facebook/pyrefly"),
        "mypy": ("Mypy", "https://mypy.readthedocs.io/"),
        "pyright": ("Pyright", "https://github.com/microsoft/pyright"),
        "security": ("Bandit", "https://bandit.readthedocs.io/"),
        "markdown": (
            "MarkdownLint",
            "https://github.com/DavidAnson/markdownlint",
        ),
        "go": ("Go Vet", "https://pkg.go.dev/cmd/vet"),
    }
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


__all__ = ["FlextInfraCheckConstants"]
