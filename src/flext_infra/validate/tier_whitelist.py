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

from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, u
from flext_infra.validate._rope_import_boundary import _RopeImportBoundaryBase

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraValidateTierWhitelist(_RopeImportBoundaryBase):
    """Enforce the §2.7 abstraction boundary at runtime-import level.

    Banned-lib set + per-library ownership are both derived from
    ``c.ENFORCEMENT_LIBRARY_OWNERS`` (flext-core SSOT): each banned library's
    owning project tree is the only place that library may be imported.
    """

    _BANNED: ClassVar[frozenset[str]] = frozenset(c.ENFORCEMENT_LIBRARY_OWNERS)
    _OK_SUMMARY: ClassVar[str] = (
        "abstraction boundary respected (owned libraries stay in their projects)"
    )
    _VIOLATION_KIND: ClassVar[str] = "abstraction-boundary"
    _SCAN_KIND: ClassVar[str] = "tier-whitelist"

    @override
    def _is_allowlisted(self, _file_path: Path, _module_name: str) -> bool:
        """Return True iff ``file_path`` owns ``module_name`` per OWNERS SSOT.

        Ownership comes directly from ``c.ENFORCEMENT_LIBRARY_OWNERS``
        (flext-core SSOT): each banned library has exactly one owning project,
        and the project identified by its typed ``pyproject.toml`` metadata is
        allowed to import that library. ``tests/``, ``examples/``, ``scripts/``
        are runtime-exempt globally.
        """
        if any(
            part in c.Infra.TIER_WHITELIST_NON_RUNTIME_DIR_PARTS
            for part in _file_path.parts
        ):
            return True
        top = self._top_module(_module_name)
        owner = c.ENFORCEMENT_LIBRARY_OWNERS.get(top)
        if owner is None:
            return False
        project_root = u.Infra.project_root(_file_path)
        if project_root is None:
            return False
        metadata = u.read_project_metadata(project_root)
        return metadata.success and metadata.value.project.name == owner

    @override
    def _format_violation(self, file_path: Path, module_name: str) -> str:
        """Format the abstraction-boundary violation message."""
        owner = c.ENFORCEMENT_LIBRARY_OWNERS[self._top_module(module_name)]
        return (
            f"{file_path}: bare import of {module_name!r} "
            f"— use {owner} public facades"
        )


__all__: t.StrSequence = ("FlextInfraValidateTierWhitelist",)
