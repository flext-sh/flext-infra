"""Import insertion helpers for LibCST module rewrites.

Method moved to FlextInfraUtilitiesParsing -- use u.Infra.* instead.
"""

from __future__ import annotations

from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing


class FlextInfraTransformerImportInsertion(FlextInfraUtilitiesParsing):
    """Backwards-compatible alias -- use u.Infra.* instead."""


__all__ = ["FlextInfraTransformerImportInsertion"]
