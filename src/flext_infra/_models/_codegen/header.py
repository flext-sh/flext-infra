"""Canonical namespace import header facts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import t
from flext_infra._models._codegen import FlextInfraModelsCodegenFixModels


class FlextInfraModelsCodegenHeaderModels:
    """Facts the generated namespace import header rules are rendered from."""

    class NamespaceImportHeader(m.ContractModel):
        """Facts of the canonical namespace import header of one project."""

        package: Annotated[
            t.NonEmptyStr,
            m.Field(description="Import package of the project"),
        ]
        aliases: Annotated[
            t.StrSequence,
            m.Field(description="Public aliases the package root exports"),
        ]
        namespace: Annotated[
            t.StrMapping,
            m.Field(description="Namespace object of each required library"),
        ]
        families: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenFixModels.FacadeFamily],
            m.Field(description="Facade families declared by the core package"),
        ]
        upstreams: Annotated[
            t.StrMapping,
            m.Field(description="Package each facade letter of the project extends"),
        ]
        layers: Annotated[
            t.StrSequence,
            m.Field(description="Canonical import-layer order"),
        ]


__all__: list[str] = ["FlextInfraModelsCodegenHeaderModels"]
