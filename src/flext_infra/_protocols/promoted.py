"""Promoted-command protocol contracts for flext-infra.

Structural contracts for the frozen models in ``p.Infra.Promoted*`` — leaf
code annotates with these protocols, never with the concrete models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols


class FlextInfraProtocolsPromoted:
    """Promoted-command protocol definitions."""

    """flext-command registry protocol namespace."""

    @runtime_checkable
    class PromotedParam(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Parameter name."""
            ...

        @property
        def help(self) -> str:
            """Parameter help text."""
            ...

        @property
        def required(self) -> bool:
            """Whether the parameter must be supplied."""
            ...

        @property
        def default(self) -> str:
            """Default value applied when omitted."""
            ...

        @property
        def choices(self) -> tuple[str, ...]:
            """Accepted values; empty accepts any value."""
            ...

    @runtime_checkable
    class PromotedCommand(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def verb(self) -> str:
            """Command verb."""
            ...

        @property
        def what(self) -> str:
            """Command subject the verb acts on."""
            ...

        @property
        def domain(self) -> str:
            """Command domain grouping."""
            ...

        @property
        def summary(self) -> str:
            """One-line command summary."""
            ...

        @property
        def description(self) -> str:
            """Long command description."""
            ...

        @property
        def example(self) -> str:
            """Example invocation."""
            ...

        @property
        def path(self) -> Path:
            """Script that implements it."""
            ...

        @property
        def mutates(self) -> bool:
            """Whether the command mutates files."""
            ...

        @property
        def aliases(self) -> tuple[str, ...]:
            """Alternate command names."""
            ...

        @property
        def params(self) -> tuple[FlextInfraProtocolsPromoted.PromotedParam, ...]:
            """Declared command parameters."""
            ...

        @property
        def rules(self) -> tuple[str, ...]:
            """Rules the command applies."""
            ...

    @runtime_checkable
    class PromotedAliasTarget(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def verb(self) -> str:
            """Target command verb."""
            ...

        @property
        def what(self) -> str:
            """Target command subject."""
            ...

    @runtime_checkable
    class PromotedWorkspaceSpec(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Repository root."""
            ...

        @property
        def scripts(self) -> Path:
            """Repository scripts root."""
            ...

        @property
        def local_python(self) -> Path:
            """Interpreter of the repository environment."""
            ...

        @property
        def submodule_script_roots(self) -> tuple[Path, ...]:
            """Scripts roots of the composed submodules."""
            ...

        @property
        def consumer_scripts_root(self) -> Path | None:
            """Scripts root of the consuming repository."""
            ...

    @runtime_checkable
    class PromotedRegistry(Protocol):
        """In-memory promoted command registry discovered from script headers."""

        def add(self, command: FlextInfraProtocolsPromoted.PromotedCommand) -> None: ...

        def validate(self) -> None: ...

        def resolve_verb(self, verb: str) -> str: ...

        def alias_target(
            self,
            verb: str,
        ) -> FlextInfraProtocolsPromoted.PromotedAliasTarget | None: ...

        def commands(
            self,
            verb: str,
        ) -> Mapping[str, FlextInfraProtocolsPromoted.PromotedCommand]: ...

        def command(
            self,
            verb: str,
            what: str,
        ) -> FlextInfraProtocolsPromoted.PromotedCommand: ...

        def verbs(self) -> Sequence[str]: ...

        def aliases_for(self, verb: str) -> Sequence[str]: ...

        def has(self, verb: str, what: str) -> bool: ...


__all__: list[str] = ["FlextInfraProtocolsPromoted"]
