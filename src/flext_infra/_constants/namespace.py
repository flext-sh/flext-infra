"""Bootstrap-safe namespace constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar


class FlextInfraConstantsNamespace:
    """Namespace constants shared by bootstrap-sensitive utilities."""

    NAMESPACE_SETTINGS_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
    })
    NAMESPACE_CONFIG_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "config.py",
        "_config.py",
    })
    NAMESPACE_DEFAULT_OWNER_FILE_NAMES: ClassVar[frozenset[str]] = (
        NAMESPACE_SETTINGS_FILE_NAMES | NAMESPACE_CONFIG_FILE_NAMES
    )
    NAMESPACE_PROTECTED_FILES: ClassVar[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
        "typings.py",
        "_typings.py",
        "__init__.py",
        "__main__.py",
        "__version__.py",
        "conftest.py",
        "py.typed",
    })


__all__: list[str] = ["FlextInfraConstantsNamespace"]
