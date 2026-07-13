"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r

from flext_infra import config
from flext_infra._models.deps_tool_config import (
    FlextInfraModelsDepsToolSettings as mdts,
)
from flext_infra.constants import c
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    @staticmethod
    def load_tool_config() -> p.Result[mdts.ToolConfigDocument]:
        """Return the already validated config singleton tooling domain."""
        return r[mdts.ToolConfigDocument].ok(config.Infra.tooling)

    @staticmethod
    def resolve_workspace_root_or_cwd(workspace_root: Path | None = None) -> Path:
        """Resolve workspace root from explicit value or current working directory."""
        target = workspace_root or Path.cwd()
        if target.is_file():
            target = target.parent
        return target.resolve()

    @staticmethod
    def normalize_optional_path(value: str | Path | None) -> Path | None:
        """Resolve one optional path-like value when present."""
        if value is None:
            return None
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    @staticmethod
    def normalize_cli_values(*values: str | None) -> t.StrSequence:
        """Normalize comma-separated or whitespace-separated CLI selectors."""
        return tuple(
            item.strip()
            for value in values
            for group in (value or "").split(",")
            for item in group.split()
            if item.strip()
        )

    @staticmethod
    def normalize_sequence_values(values: t.StrSequence | None) -> t.StrSequence | None:
        """Normalize repeated CLI sequence fields into a compact selector list."""
        names = FlextInfraUtilitiesBase.normalize_cli_values(*(values or ()))
        return names or None

    @staticmethod
    def normalize_make_args(values: t.StrSequence) -> t.StrSequence:
        """Return trimmed make arguments without blank entries."""
        return tuple(item.strip() for item in values if item.strip())

    @staticmethod
    def resolve_what(verb: str, phase: str) -> p.Result[t.StrSequence]:
        """Resolve a ``WHAT=`` phase against ``c.Infra.WHAT_PHASES`` (single SSOT).

        Empty ``phase`` expands to every phase of ``verb`` (sorted); a non-empty
        unknown phase is a usage failure listing the valid phases. Shared by the
        orchestrator, check and validate groups so WHAT resolution lives in one
        place.
        """
        phases = c.Infra.WHAT_PHASES.get(verb, frozenset())
        if not phase:
            return r[t.StrSequence].ok(tuple(sorted(phases)))
        if phase not in phases:
            valid = ", ".join(sorted(phases)) or "(none)"
            return r[t.StrSequence].fail(
                f"unknown WHAT '{phase}' for verb '{verb}' (valid: {valid})",
            )
        return r[t.StrSequence].ok((phase,))


__all__: list[str] = ["FlextInfraUtilitiesBase"]
