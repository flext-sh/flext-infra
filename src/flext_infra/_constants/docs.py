"""Centralized constants for the docs subpackage."""

from __future__ import annotations

from typing import Final


class FlextInfraDocsConstants:
    """Docs infrastructure constants."""

    DEFAULT_DOCS_OUTPUT_DIR: Final[str] = ".reports/docs"
    DOCS_CONFIG_FILENAME: Final[str] = "docs_config.json"


__all__ = ["FlextInfraDocsConstants"]
