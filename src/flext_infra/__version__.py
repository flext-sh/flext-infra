"""Package version and metadata information.

Provides version information and package metadata for the flext-infra package
using standard library metadata extraction.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageMetadata, PackageNotFoundError, metadata


class FlextInfraVersion:
    """Package version and metadata information.

    Provides version information and package metadata using standard library
    metadata extraction.
    """

    _metadata: PackageMetadata | Mapping[str, str]
    try:
        _metadata = metadata("flext-infra")
    except PackageNotFoundError:
        _metadata = {
            "Version": "0.12.0-dev",
            "Name": "flext-infra",
            "Summary": "FLEXT infrastructure",
            "Author": "",
            "Author-Email": "",
            "License": "",
            "Home-Page": "",
        }
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

    @classmethod
    def get_version_string(cls) -> str:
        """Return the package version as a string."""
        return cls.__version__

    @classmethod
    def get_version_info(cls) -> tuple[int | str, ...]:
        """Return the package version as a tuple of ints and strings."""
        return cls.__version_info__

    @classmethod
    def get_package_info(cls) -> dict[str, str]:
        """Return package metadata as a dictionary."""
        return {
            "name": str(cls.__title__),
            "version": str(cls.__version__),
            "description": str(cls.__description__),
            "author": str(cls.__author__),
            "author_email": str(cls.__author_email__),
            "license": str(cls.__license__),
            "url": str(cls.__url__),
        }

    @classmethod
    def is_version_at_least(
        cls,
        major: int,
        minor: int = 0,
        patch: int = 0,
    ) -> bool:
        """Check whether the current version is at least (major, minor, patch)."""
        info = cls.__version_info__
        idx_major = 0
        idx_minor = 1
        idx_patch = 2
        current_major = info[idx_major] if len(info) > idx_major else 0
        current_minor = info[idx_minor] if len(info) > idx_minor else 0
        current_patch = info[idx_patch] if len(info) > idx_patch else 0
        if not isinstance(current_major, int):
            return False
        if not isinstance(current_minor, int):
            current_minor = 0
        if not isinstance(current_patch, int):
            current_patch = 0
        return (current_major, current_minor, current_patch) >= (major, minor, patch)


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
