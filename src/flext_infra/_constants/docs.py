"""Centralized constants for the docs subpackage."""

from __future__ import annotations

import re
from typing import Final


class FlextInfraConstantsDocs:
    """Docs infrastructure constants."""

    DEFAULT_DOCS_OUTPUT_DIR: Final[str] = ".reports/docs"
    DOCS_CONFIG_FILENAME: Final[str] = "docs_config.json"
    PYTHON_FENCE_RE: Final[re.Pattern[str]] = re.compile(
        r"^```python\s*\n(?P<body>.*?)^```\s*$",
        re.MULTILINE | re.DOTALL,
    )
    """Regex matching ``python`` fenced blocks; ``body`` group yields contents."""


__all__: list[str] = ["FlextInfraConstantsDocs"]
