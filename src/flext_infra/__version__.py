"""Package version and metadata information.

Provides version information and package metadata for the flext-infra package
using standard library metadata extraction.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from importlib.metadata import PackageMetadata, PackageNotFoundError, metadata
from pathlib import Path
from typing import TypeIs

from flext_core import FlextVersion


def _is_object_mapping(value: object) -> TypeIs[Mapping[object, object]]:
    """Return whether one payload is a generic runtime mapping."""
    return isinstance(value, Mapping)


def _is_object_sequence(value: object) -> TypeIs[Sequence[object]]:
    """Return whether one payload is a non-string runtime sequence."""
    return isinstance(value, Sequence) and not isinstance(
        value,
        str | bytes | bytearray,
    )


def _object_mapping(value: object) -> Mapping[str, object]:
    """Normalize one runtime payload to a string-key mapping."""
    if not _is_object_mapping(value):
        return {}
    normalized: dict[str, object] = {}
    for key, entry in value.items():
        normalized[str(key)] = entry
    return normalized


def _object_sequence(value: object) -> Sequence[object]:
    """Normalize one runtime payload to a generic object sequence."""
    if not _is_object_sequence(value):
        return ()
    return tuple(value)


def _pyproject_metadata() -> dict[str, str]:
    """Load fallback package metadata directly from the local pyproject."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        payload = _object_mapping(tomllib.load(handle))
    project = _object_mapping(payload.get("project", {}))
    authors = _object_sequence(project.get("authors", ()))
    first_author = _object_mapping(authors[0] if authors else {})
    urls = _object_mapping(project.get("urls", {}))
    home_page_obj: object = (
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
        "Home-Page": str(home_page_obj),
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
