"""Guard 5 — tier / abstraction-boundary enforcer.

Enforces AGENTS.md §2.7 abstraction-boundary rules: each external library
listed in ``c.ENFORCEMENT_LIBRARY_OWNERS`` (flext-core SSOT) has exactly
one owning FLEXT project. Bare runtime imports of those libs outside the
canonical wrapper sites are violations.

Uses rope's semantic import resolution so ``if TYPE_CHECKING:`` imports
are automatically exempt (they live in conditional blocks that rope
skips when collecting runtime imports).

Mandate: 100% ROPE-based per the flext-infra detector mandate — no raw
``ast``/``libcst`` source analysis. Uses
``u.Infra`` Rope boundary helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, t
from flext_infra.validate._rope_import_boundary import _RopeImportBoundaryBase


class FlextInfraValidateTierWhitelist(_RopeImportBoundaryBase):
    """Enforce the §2.7 abstraction boundary at runtime-import level.

    Banned-lib set is derived from ``c.ENFORCEMENT_LIBRARY_OWNERS`` keys
    (flext-core SSOT). Canonical wrapper paths come from
    ``c.Infra.TIER_WHITELIST_ALLOWLIST_MARKERS``. No parallel lists.
    """

    _BANNED: ClassVar[frozenset[str]] = frozenset(c.ENFORCEMENT_LIBRARY_OWNERS)
    _OK_SUMMARY: ClassVar[str] = (
        "abstraction boundary respected (flext-core-only libs not imported elsewhere)"
    )
    _VIOLATION_KIND: ClassVar[str] = "abstraction-boundary"
    _SCAN_KIND: ClassVar[str] = "tier-whitelist"

    NON_RUNTIME_DIR_PARTS: ClassVar[frozenset[str]] = frozenset({
        c.Infra.DIR_TESTS,
        c.Infra.DIR_EXAMPLES,
        c.Infra.DIR_SCRIPTS,
    })

    @override
    def _is_allowlisted(self, file_path: Path) -> bool:
        """Return True iff ``file_path`` is a canonical wrapper or non-runtime surface.

        Sources the canonical-wrapper marker list from
        ``c.Infra.TIER_WHITELIST_ALLOWLIST_MARKERS`` (SSOT). Also exempts
        ``tests/``, ``examples/``, and ``scripts/`` directories — only
        runtime ``src/`` modules are gated by the abstraction boundary.
        """
        posix = file_path.as_posix()
        if any(marker in posix for marker in c.Infra.TIER_WHITELIST_ALLOWLIST_MARKERS):
            return True
        return any(part in self.NON_RUNTIME_DIR_PARTS for part in file_path.parts)

    @override
    def _format_violation(self, file_path: Path, module_name: str) -> str:
        """Format the abstraction-boundary violation message."""
        return (
            f"{file_path}: bare import of {module_name!r} "
            "— use flext_core facades (c/m/p/t/u)"
        )


__all__: t.StrSequence = ["FlextInfraValidateTierWhitelist"]
