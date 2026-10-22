"""Workspace provenance for canonicalizing internal requirement lines.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m, t

from flext_infra._models.deps_typings import FlextInfraModelsDepsTypings


class FlextInfraUtilitiesPyprojectRequirementsProvenance(m.ImmutableValueModel):
    """Workspace provenance consulted while canonicalizing requirement lines."""

    declared_sources: t.StrMapping = m.Field(description="Declared member Git origins")
    candidate_sources: t.StrMapping = m.Field(
        description="Selected candidate Git origins"
    )
    family_line: str | None = m.Field(description="Detected integration branch")
    generated_local: t.VariadicTuple[
        FlextInfraModelsDepsTypings.GeneratedTypingPackage
    ] = m.Field(default=(), description="Authenticated generated-local typing origins")


__all__: list[str] = []
