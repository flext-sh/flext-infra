"""Centralized constants for the docs subpackage."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsDocs:
    """Docs infrastructure constants."""

    DEFAULT_DOCS_OUTPUT_DIR: Final[str] = ".reports/docs"
    DOCS_CONFIG_FILENAME: Final[str] = "docs_config.json"
    PYTHON_FENCE_RUFF_EXTEND_IGNORE: Final[t.StrSequence] = (
        "D100",
        "D101",
        "D102",
        "D103",
        "PLR2004",
        "S101",
        "INP001",
        "T201",
        "T203",
        "ANN001",
        "ANN002",
        "ANN003",
        "ANN201",
        "ANN202",
        "ANN204",
        "ANN205",
        "PLC0415",
    )
    """Rules ignored for executable docs snippets that are not full modules/tests."""
    PYTHON_FENCE_RE: Final[t.RegexPattern] = re.compile(
        r"^```python\s*\n(?P<body>.*?)^```\s*$", re.MULTILINE | re.DOTALL
    )
    """Regex matching ``python`` fenced blocks; ``body`` group yields contents."""

    PYTHON_FENCE_FIX_RE: Final[t.RegexPattern] = re.compile(
        r"^(?P<open>```python\s*\n)(?P<body>.*?)^```\s*$", re.MULTILINE | re.DOTALL
    )
    """Regex matching ``python`` fenced blocks for fix-in-place replacement."""

    FENCE_NOTEST_RE: Final[t.RegexPattern] = re.compile(
        r"^```(\S+)\s+notest\s*$", re.MULTILINE
    )
    """Regex matching fenced code blocks with a ``notest`` info qualifier."""

    MANUAL_TOC_RE: Final[t.RegexPattern] = re.compile(
        r"<!--\s*TOC\s+START\s*-->.*?<!--\s*TOC\s+END\s*-->", re.DOTALL
    )
    """Regex matching a manually inserted table-of-contents block."""

    FENCED_BLOCK_RE: Final[t.RegexPattern] = re.compile(
        r"^(?P<fence>```+|~~~+)[^\n]*\n.*?^(?P=fence)[ \t]*$\n?",
        re.MULTILINE | re.DOTALL,
    )
    """Match a whole fenced code block, backtick or tilde, with its info string."""

    # --- Markdown link/heading patterns ---
    MARKDOWN_LINK_RE: Final[t.RegexPattern] = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    """Match markdown links capturing text (group 1) and URL (group 2)."""
    MARKDOWN_LINK_URL_RE: Final[t.RegexPattern] = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    """Match markdown links capturing only the URL (group 1)."""
    HEADING_RE: Final[t.RegexPattern] = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
    """Match any markdown heading (h1-h6), capturing the text."""
    HEADING_H2_H3_RE: Final[t.RegexPattern] = re.compile(
        r"^(##|###)\s+(.+?)\s*$", re.MULTILINE
    )
    """Match h2/h3 headings, capturing level (group 1) and text (group 2)."""
    ANCHOR_LINK_RE: Final[t.RegexPattern] = re.compile(r"\[([^\]]+)\]\(#([^)]+)\)")
    """Match internal anchor links, capturing text and anchor."""
    INLINE_CODE_RE: Final[t.RegexPattern] = re.compile(r"`[^`]*`")
    """Match inline code spans for stripping before analysis."""
    STRING_LITERAL_RE: Final[t.RegexPattern] = re.compile(
        r"""["']([a-zA-Z0-9_\.]+)["']"""
    )
    """Match quoted string literals, capturing the content."""

    DOCS_MAKE_COMMAND_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*(?:\$\s*)?make\s+(?P<verb>[a-z][a-z0-9_-]*)(?P<args>.*)$", re.IGNORECASE
    )
    """Match an executable Make command and capture its verb and arguments."""
    DOCS_SHELL_FENCE_LANGUAGES: Final[frozenset[str]] = frozenset({
        "",
        "bash",
        "console",
        "fish",
        "sh",
        "shell",
        "zsh",
    })
    """Markdown fence languages whose lines are executable shell commands."""
    DOCS_FORBIDDEN_MAKE_SELECTOR_RE: Final[t.RegexPattern] = re.compile(
        r"\b(?:PROJECTS?|MATCH|WHAT|FILES?|FIX|CHANGED_ONLY|CHECK_GATES|"
        r"DOCS_PHASE|VALIDATE_SCOPE)\s*=",
        re.IGNORECASE,
    )
    """Match selectors outside the canonical root Make grammar."""
    DOCS_APPLY_RE: Final[t.RegexPattern] = re.compile(r"\bAPPLY=Y\b")
    """Match the sole canonical mutation flag in documented commands."""
    DOCS_COMMAND_CONTRACT_DIRNAMES: Final[frozenset[str]] = frozenset({
        "guides",
        "standards",
    })
    """Live documentation trees governed by the command contract."""
    DOCS_RAW_PYTEST_COMMAND_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*(?:\$\s*)?(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S+)\s+)*"
        r"(?:(?:uv|poetry|pdm)\s+run\s+|"
        r"python(?:3(?:\.\d+)?)?\s+-m\s+)?pytest(?:\s|$)",
        re.IGNORECASE,
    )
    """Match direct pytest execution that bypasses the root Testmon verb."""
    DOCS_RAW_TOOL_COMMAND_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*(?:\$\s*)?(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S+)\s+)*"
        r"(?:ruff|pyrefly|mypy|pyright|mkdocs|uv|poetry|pdm|tox|nox|pre-commit|"
        r"python(?:3(?:\.\d+)?)?(?:\s+-m|\s+[^\s]+\.py\b))",
        re.IGNORECASE,
    )
    """Match tool and script commands that bypass the root Make dispatcher."""
    DOCS_TEST_DOUBLE_CODE_RE: Final[t.RegexPattern] = re.compile(
        r"(?:from\s+unittest(?:\.mock)?\s+import|import\s+unittest\.mock|"
        r"(?:^|\W)(?:MagicMock|Mock|patch)\s*\(|mock\.patch\s*\(|"
        r"monkeypatch\.[A-Za-z_]|class\s+(?:Fake|Stub)[A-Za-z0-9_]*|"
        r"(?:^|\W)(?:fake|stub)_[A-Za-z0-9_]+)",
        re.IGNORECASE,
    )
    """Match test-double construction inside executable Python examples."""
    DOCS_TEST_DOUBLE_HEADING_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*#{1,6}\s+.*\b(?:mock(?:ing|s)?|fake(?:s)?|stub(?:bing|s)?|"
        r"patch(?:ing)?)\b",
        re.IGNORECASE,
    )
    """Match headings that introduce test-double guidance."""


__all__: list[str] = ["FlextInfraConstantsDocs"]
