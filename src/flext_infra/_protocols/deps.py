"""Structural contracts for dependency-analysis collaborators.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p


@runtime_checkable
class FlextInfraProtocolsDeps(Protocol):
    """Dependency-analysis protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class RuntimeDependencyCollector(Protocol):
        """Collect explicit target suppliers for one completed native scan."""

        def __call__(
            self,
            project_root: Path,
            scan: m.Infra.DeptryScan,
            /,
        ) -> p.Result[m.Infra.RuntimeDependencyInputs]:
            """Return the elected lock, supplier metadata and own applicability."""
            ...

    @runtime_checkable
    class TypeCheckerPathRules(Protocol):
        """Path-rule fields every type-checker configuration declares."""

        @property
        def source_dir(self) -> str:
            """Import root the generated search paths order first."""
            ...

        @property
        def project_root(self) -> str:
            """Project-root entry the generated search paths order last."""
            ...


__all__: list[str] = ["FlextInfraProtocolsDeps"]
