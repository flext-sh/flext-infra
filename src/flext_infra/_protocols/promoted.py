"""Promoted-command protocol contracts for flext-infra.

Structural contracts for the frozen models in ``m.Infra.Promoted.*`` — leaf
code annotates with these protocols, never with the concrete models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class FlextInfraProtocolsPromoted(Protocol):
    """Promoted-command protocol definitions."""

    class Promoted:
        """cosmos-command registry protocol namespace."""

        class Param(Protocol):
            """Promoted command parameter contract."""

            @property
            def name(self) -> str:
                """Name."""

            @property
            def help(self) -> str:
                """Help."""

            @property
            def required(self) -> bool:
                """Required."""

            @property
            def default(self) -> str:
                """Default."""

            @property
            def choices(self) -> tuple[str, ...]:
                """Choices."""

        class Command(Protocol):
            """Promoted command contract discovered from a script header."""

            @property
            def verb(self) -> str:
                """Verb."""

            @property
            def what(self) -> str:
                """What."""

            @property
            def domain(self) -> str:
                """Domain."""

            @property
            def summary(self) -> str:
                """Summary."""

            @property
            def description(self) -> str:
                """Description."""

            @property
            def example(self) -> str:
                """Example."""

            @property
            def path(self) -> Path:
                """Path."""

            @property
            def mutates(self) -> bool:
                """Mutates."""

            @property
            def aliases(self) -> tuple[str, ...]:
                """Aliases."""

            @property
            def params(self) -> tuple[FlextInfraProtocolsPromoted.Promoted.Param, ...]:
                """Params."""

            @property
            def rules(self) -> tuple[str, ...]:
                """Rules."""

        class AliasTarget(Protocol):
            """Resolved command alias target contract."""

            @property
            def verb(self) -> str:
                """Verb."""

            @property
            def what(self) -> str:
                """What."""

        class WorkspaceSpec(Protocol):
            """Repository facts contract the promoted framework consumes."""

            @property
            def root(self) -> Path:
                """Repository root."""

            @property
            def scripts(self) -> Path:
                """Scripts directory."""

            @property
            def local_python(self) -> Path:
                """Declared local ``.venv`` interpreter."""

            @property
            def submodule_script_roots(self) -> tuple[Path, ...]:
                """Submodule script roots in first-wins order."""

            @property
            def consumer_scripts_root(self) -> Path | None:
                """Consuming workspace scripts root when vendored as a submodule."""


__all__: list[str] = ["FlextInfraProtocolsPromoted"]
