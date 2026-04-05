"""Package version and metadata information.

Provides version information and package metadata for the flext-infra package
using standard library metadata extraction.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from importlib.metadata import PackageMetadata, PackageNotFoundError, metadata
from pathlib import Path

from flext_core import FlextVersion


def _pyproject_metadata() -> Mapping[str, str]:
    """Load fallback package metadata directly from the local pyproject."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        payload = tomllib.load(handle)
    project = payload.get("project", {})
    authors = project.get("authors", [])
    first_author = authors[0] if authors and isinstance(authors[0], dict) else {}
    urls = project.get("urls", {})
    home_page = (
        urls.get("Homepage")
        or urls.get("Repository")
        or urls.get("Documentation")
        or ""
    )
    return {
        "Name": str(project.get("name", "flext-infra")),
        "Version": str(project.get("version", "0.0.0")),
        "Summary": str(project.get("description", "")),
        "Author": str(first_author.get("name", "")),
        "Author-Email": str(first_author.get("email", "")),
        "License": str(project.get("license", "")),
        "Home-Page": str(home_page),
    }


def _load_metadata() -> PackageMetadata | Mapping[str, str]:
    """Load installed metadata when available, otherwise fall back to pyproject."""
    try:
        return metadata("flext-infra")
    except PackageNotFoundError:
        return _pyproject_metadata()


class FlextInfraVersion(FlextVersion):
    """Package version and metadata for flext-infra — inherits FlextVersion."""

    _metadata: PackageMetadata | Mapping[str, str] = _load_metadata()
    __version__ = _metadata["Version"]
    __version_info__ = tuple(
        int(part) if part.isdigit() else part for part in __version__.split(".")
    )
    __title__ = _metadata["Name"]
    __description__ = _metadata.get("Summary", "")
    __author__ = _metadata.get("Author", "")
    __author_email__ = _metadata.get("Author-Email", "")
    __license__ = _metadata.get("License", "")
    __url__ = _metadata.get("Home-Page", "")


__version__ = FlextInfraVersion.__version__
__version_info__ = FlextInfraVersion.__version_info__
__title__ = FlextInfraVersion.__title__
__description__ = FlextInfraVersion.__description__
__author__ = FlextInfraVersion.__author__
__author_email__ = FlextInfraVersion.__author_email__
__license__ = FlextInfraVersion.__license__
__url__ = FlextInfraVersion.__url__
__all__ = [
    "FlextInfraVersion",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
]
