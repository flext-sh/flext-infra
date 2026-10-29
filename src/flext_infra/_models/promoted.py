"""Promoted-command domain models for flext-infra.

``PromotedParam``/``PromotedCommand``/``PromotedAliasTarget`` mirror the frozen
promoted-command contract; ``PromotedWorkspaceSpec`` is the typed
projection of repository facts the framework consumes. Construction is
keyword-only; leaf code annotates with the ``p.Infra.Promoted*`` protocols
(a model is never a type).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_cli import m

from flext_infra._models import FlextInfraModelsBase


class FlextInfraModelsPromoted(FlextInfraModelsBase):
    """Promoted-command models mixed into ``m.Infra``."""

    """flext-command registry models (promoted script headers)."""

    class PromotedParam(m.BaseModel):
        """One promoted command parameter declared in the script header."""

        model_config = m.ConfigDict(extra="forbid", frozen=True)

        name: Annotated[str, m.Field(description="Parameter name")]
        help: Annotated[str, m.Field(description="Parameter help text")]
        required: Annotated[
            bool, m.Field(description="Whether the parameter must be supplied")
        ] = False
        default: Annotated[
            str, m.Field(description="Default value applied when omitted")
        ] = ""
        choices: Annotated[
            tuple[str, ...],
            m.Field(description="Accepted values; empty accepts any value"),
        ] = ()

    class PromotedCommand(m.BaseModel):
        """One promoted command discovered from a flext-command header."""

        model_config = m.ConfigDict(extra="forbid", frozen=True)

        verb: Annotated[str, m.Field(description="Command verb")]
        what: Annotated[str, m.Field(description="Command subject the verb acts on")]
        domain: Annotated[str, m.Field(description="Command domain grouping")]
        summary: Annotated[str, m.Field(description="One-line command summary")]
        description: Annotated[str, m.Field(description="Long command description")]
        example: Annotated[str, m.Field(description="Example invocation")]
        path: Annotated[Path, m.Field(description="Script that implements it")]
        mutates: Annotated[
            bool, m.Field(description="Whether the command mutates files")
        ]
        aliases: Annotated[
            tuple[str, ...], m.Field(description="Alternate command names")
        ]
        params: Annotated[
            tuple[FlextInfraModelsPromoted.PromotedParam, ...],
            m.Field(description="Declared command parameters"),
        ]
        rules: Annotated[
            tuple[str, ...], m.Field(description="Rules the command applies")
        ]

    class PromotedAliasTarget(m.BaseModel):
        """Resolved command alias target."""

        model_config = m.ConfigDict(extra="forbid", frozen=True)

        verb: Annotated[str, m.Field(description="Target command verb")]
        what: Annotated[str, m.Field(description="Target command subject")]

    class PromotedWorkspaceSpec(m.BaseModel):
        """Repository facts the promoted framework consumes, resolved once."""

        model_config = m.ConfigDict(extra="forbid", frozen=True)

        root: Annotated[Path, m.Field(description="Repository root")]
        scripts: Annotated[Path, m.Field(description="Repository scripts root")]
        local_python: Annotated[
            Path, m.Field(description="Interpreter of the repository environment")
        ]
        submodule_script_roots: Annotated[
            tuple[Path, ...],
            m.Field(description="Scripts roots of the composed submodules"),
        ] = ()
        consumer_scripts_root: Annotated[
            Path | None,
            m.Field(description="Scripts root of the consuming repository"),
        ] = None


__all__: list[str] = ["FlextInfraModelsPromoted"]
