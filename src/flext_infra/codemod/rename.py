"""Extracted facade class for rename.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra.codemod._rename import (
    FlextInfraCodemodRenameSources,
    FlextInfraCodemodRenameSymbols,
)


class FlextInfraCodemodRename(
    FlextInfraCodemodRenameSources,
    FlextInfraCodemodRenameSymbols,
):
    """Facade for rename."""


__all__: list[str] = ["FlextInfraCodemodRename"]
