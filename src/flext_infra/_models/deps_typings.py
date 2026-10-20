"""Typed inputs for generated third-party PEP 561 distributions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_cli import m

from flext_infra import t
from flext_infra._models._config.scaffold import FlextInfraConfigModelsScaffold


class FlextInfraModelsDepsTypings:
    """Typing-package policy and native packaging context."""

    class TypingGenerationPolicy(m.ContractModel):
        """Declared destination and distribution identity for generated stubs."""

        directory: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project-relative package root"),
        ]
        distribution_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Distribution prefix reserved for generated stubs"),
        ]

        @m.field_validator("directory")
        @classmethod
        def validate_directory(cls, value: str) -> str:
            """Require a confined, non-root generation destination.

            Returns:
                The validated relative directory.

            Raises:
                ValueError: If the destination leaves its owning project.

            """
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or path == Path():
                msg = "typing package directory must be a confined relative path"
                raise ValueError(msg)
            return value

    class TypingPackageRenderContext(m.ContractModel):
        """PEP 561 metadata from the installed implementation and packaging policy."""

        distribution: Annotated[
            t.NonEmptyStr,
            m.Field(description="PEP 561 distribution name for generated stubs."),
        ]
        version: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Installed implementation version of the stub package."
            ),
        ]
        module: Annotated[
            t.NonEmptyStr,
            m.Field(description="Implementation import module published by the stubs."),
        ]
        runtime_requirement: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Installed implementation identity retained as provenance."
            ),
        ]
        python_required: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python requirement inherited from the toolchain."),
        ]
        build: Annotated[
            FlextInfraConfigModelsScaffold.ScaffoldBuildSpec,
            m.Field(description="Canonical build policy passed by reference."),
        ]


__all__: list[str] = ["FlextInfraModelsDepsTypings"]
