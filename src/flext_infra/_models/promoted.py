"""Promoted-command domain models for flext-infra.

``Param``/``Command``/``AliasTarget`` mirror the frozen promoted-command
contract consumed across the fleet; ``WorkspaceSpec`` is the one typed
projection of repository facts the framework consumes. Construction is
keyword-only; leaf code annotates with the ``p.Infra.Promoted.*`` protocols
(a model is never a type).
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import m

from .base import FlextInfraModelsBase


class FlextInfraModelsPromoted(FlextInfraModelsBase):
    """Promoted-command models mixed into ``m.Infra``."""

    class Promoted:
        """cosmos-command registry models (promoted script headers)."""

        class Param(m.BaseModel):
            """One promoted command parameter declared in the script header."""

            model_config = m.ConfigDict(extra="forbid", frozen=True)

            name: str
            help: str
            required: bool = False
            default: str = ""
            choices: tuple[str, ...] = ()

        class Command(m.BaseModel):
            """One promoted command discovered from a cosmos-command header."""

            model_config = m.ConfigDict(extra="forbid", frozen=True)

            verb: str
            what: str
            domain: str
            summary: str
            description: str
            example: str
            path: Path
            mutates: bool
            aliases: tuple[str, ...]
            params: tuple[FlextInfraModelsPromoted.Promoted.Param, ...]
            rules: tuple[str, ...]

        class AliasTarget(m.BaseModel):
            """Resolved command alias target."""

            model_config = m.ConfigDict(extra="forbid", frozen=True)

            verb: str
            what: str

        class WorkspaceSpec(m.BaseModel):
            """Repository facts the promoted framework consumes, resolved once."""

            model_config = m.ConfigDict(extra="forbid", frozen=True)

            root: Path
            scripts: Path
            local_python: Path
            submodule_script_roots: tuple[Path, ...] = ()
            consumer_scripts_root: Path | None = None


__all__: list[str] = ["FlextInfraModelsPromoted"]
