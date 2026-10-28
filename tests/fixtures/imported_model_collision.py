"""Executable lexical receiver collision for native campaign regression.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from flext_infra.models import FlextInfraModels as ImportedModels


class TestsImportedModelCollision:
    """A local receiver must never be captured by a public import."""

    @staticmethod
    def entity_name() -> str:
        """Retain a locally bound receiver beside the imported model.

        Returns:
            The existing local text and canonical class name.
        """
        m = "occupied"
        return m + ImportedModels.Infra.WorkspaceTestsRequest.__name__


__all__ = ["TestsImportedModelCollision"]
