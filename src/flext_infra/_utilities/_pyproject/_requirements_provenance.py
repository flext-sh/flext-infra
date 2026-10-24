"""Workspace provenance for canonicalizing internal requirement lines.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m, t


class FlextInfraUtilitiesPyprojectRequirementsProvenance(m.ImmutableValueModel):
    """Workspace provenance consulted while canonicalizing requirement lines."""

    declared_sources: t.StrMapping = m.Field(description="Declared member Git origins")
    candidate_sources: t.StrMapping = m.Field(
        description="Selected candidate Git origins"
    )
    native_sources: t.StrSequence = m.Field(
        default=(), description="Names with explicit native UV source declarations"
    )


__all__: list[str] = []
