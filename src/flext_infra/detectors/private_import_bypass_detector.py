"""Detect private-module imports that should route through canonical facades.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import config, m, t, u


class FlextInfraPrivateImportBypassDetector:
    """Detect config/settings private-root imports from validated rule data."""

    @classmethod
    def detect_file(
        cls, ctx: m.Infra.DetectorContext
    ) -> t.SequenceOf[p.Infra.PrivateImportBypassViolation]:
        """Return private-import bypass violations for one file."""
        rules = tuple(
            rule
            for rule in config.Infra.enforcement.rules
            if isinstance(rule, m.Infra.StaticPrivateRootImportRule)
        )
        return u.Infra.detect_private_root_imports(ctx, rules)


__all__: list[str] = ["FlextInfraPrivateImportBypassDetector"]
