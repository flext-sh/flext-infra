"""Structural contracts for validated base.mk configuration models.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

from flext_cli import p

if TYPE_CHECKING:
    from flext_infra import t


@runtime_checkable
class FlextInfraProtocolsBasemk(Protocol):
    """Protocol-of-model contracts published under ``p.Infra``."""

    @runtime_checkable
    class BaseMkConfig(p.BaseModel, Protocol):
        """Validated settings consumed by the base.mk renderer."""

        @property
        def project_name(self) -> str: ...

        @property
        def python_version(self) -> str: ...

        @property
        def package_manager(self) -> str: ...

        @property
        def source_dir(self) -> str: ...

        @property
        def tests_dir(self) -> str: ...

        @property
        def lint_gates(self) -> t.StrSequence: ...

        @property
        def test_command(self) -> str: ...

        def model_copy(
            self, *, update: t.JsonMapping | None = None, deep: bool = False
        ) -> Self: ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsBasemk",)
