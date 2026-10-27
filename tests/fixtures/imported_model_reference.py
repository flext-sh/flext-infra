"""Executable imported-class references for native campaign regression.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.models import FlextInfraModels as ImportedModels


class TestsImportedModelReference:
    """Keep real imported reads distinct from local names and payloads."""

    @staticmethod
    def entity_name() -> str:
        """Read a real member through the imported class.

        Returns:
            The canonical entity class name.
        """
        return ImportedModels.Infra.WorkspaceTestsRequest.__name__

    @staticmethod
    def shadowed() -> str:
        """Preserve a local declaration that shadows the imported class.

        Returns:
            The local class name.
        """
        class ImportedModels:
            """Independent local declaration, not an imported model."""

        return ImportedModels.__name__


__all__ = ["TestsImportedModelReference"]
