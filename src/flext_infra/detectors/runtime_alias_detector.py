"""Detect missing or duplicate runtime alias assignments via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import c, m, u


class FlextInfraRuntimeAliasDetector:
    """Detect missing/duplicate runtime aliases (e.g. m = FlextFooModels) via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.RuntimeAliasViolation]:
        """Detect missing/duplicate runtime alias assignments in a facade file."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            return []
        source = resource.read()
        matches = [
            hit.group(2)
            for hit in c.Infra.FACADE_ALIAS_RE.finditer(source)
            if hit.group(1) == family
        ]
        if not matches:
            return [
                m.Infra.RuntimeAliasViolation(
                    file=str(file_path),
                    kind="missing",
                    alias=family,
                    detail=f"No '{family} = ...' assignment found",
                )
            ]
        if len(matches) > 1:
            return [
                m.Infra.RuntimeAliasViolation(
                    file=str(file_path),
                    kind="duplicate",
                    alias=family,
                    detail=f"Found {len(matches)} '{family} = ...' assignments",
                )
            ]
        return []


__all__: list[str] = ["FlextInfraRuntimeAliasDetector"]
