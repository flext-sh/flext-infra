"""Package version and metadata information.

Provides version information and package metadata for the flext-infra package
using standard library metadata extraction.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageMetadata, PackageNotFoundError, metadata
from typing import Final

_MAJOR_INDEX: Final[int] = 0
_MINOR_INDEX: Final[int] = 1
_PATCH_INDEX: Final[int] = 2


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
        """Return the version as a string."""
        return cls.__version__

    @classmethod
    def get_version_info(cls) -> tuple[int | str, ...]:
        """Return the version as a tuple of integers and strings."""
        return cls.__version_info__

    @classmethod
    def is_version_at_least(cls, major: int, minor: int = 0, patch: int = 0) -> bool:
        """Return True if the package version is at least major.minor.patch."""
        info = cls.__version_info__
        cur_major = (
            info[_MAJOR_INDEX] if info and isinstance(info[_MAJOR_INDEX], int) else 0
        )
        cur_minor = (
            info[_MINOR_INDEX]
            if len(info) > _MINOR_INDEX and isinstance(info[_MINOR_INDEX], int)
            else 0
        )
        cur_patch = (
            info[_PATCH_INDEX]
            if len(info) > _PATCH_INDEX and isinstance(info[_PATCH_INDEX], int)
            else 0
        )
        return (cur_major, cur_minor, cur_patch) >= (major, minor, patch)

    @classmethod
    def get_package_info(cls) -> dict[str, str]:
        """Return package metadata as a string-keyed dict of strings."""
        return {
            "name": cls.__title__,
            "version": cls.__version__,
            "description": cls.__description__,
            "author": cls.__author__,
            "author_email": cls.__author_email__,
            "license": cls.__license__,
            "url": cls.__url__,
        }


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
