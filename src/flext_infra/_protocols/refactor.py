"""Protocol for refactor change tracking.

Defines the structural contract for objects that track applied
refactoring transformations via a mutable changes sequence.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Mapping,
    MutableSequence,
)
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraProtocolsRefactor(Protocol):
    @runtime_checkable
    class ChangeTracker(Protocol):
        """Protocol for objects that track applied changes."""

        changes: MutableSequence[str]

    @runtime_checkable
    class Rule(Protocol):
        """Structural contract for one flext-infra rule implementation."""

        rule_id: str
        name: str
        description: str
        enabled: bool
        severity: str

        def apply(
            self,
            source: str,
            _file_path: Path | None = None,
        ) -> t.Infra.TransformResult:
            """Apply the rule to source text and return transformed source + changes."""
            ...

    @runtime_checkable
    class FileRule(Protocol):
        """Structural contract for Rope-backed file rules."""

        def apply(
            self,
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
            *,
            dry_run: bool = False,
        ) -> m.Infra.Result:
            """Apply one file rule to the Rope resource."""
            ...

    @runtime_checkable
    class RuleDefinitionValidator(Protocol):
        """Structural validator contract for declarative flext-infra rules."""

        def validate_rule_definition(
            self,
            rule_def: Mapping[str, t.Infra.InfraValue],
        ) -> str | None:
            """Return an error string or ``None`` when the rule definition is valid."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsRefactor",
]
