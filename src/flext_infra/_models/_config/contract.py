"""Shared config contract base and inherited toolchain declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models.mise_toolchain import FlextInfraModelsMiseToolchain
from flext_infra._models.mise_toolchain_base import FlextInfraModelsMiseToolchainBase


class FlextInfraConfigModelsContract(FlextInfraModelsMiseToolchain):
    """Shared config contract base and inherited toolchain declarations."""

    class ConfigContract(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Public declarative base for schema-loaded codegen records."""

    class DocsAuditOverridesSpec(ConfigContract):
        """Repository-specific exceptions and stale-symbol declarations."""

        stale_symbols: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Public symbols retired from current documentation"),
        ] = ()
        stale_symbol_exempt_paths: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Exact generated API paths retaining live symbols"),
        ] = ()
        forbidden_terms: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Literal retired-surface names forbidden in current "
                    "documentation, each superseded by a declared canonical "
                    "owner"
                ),
            ),
        ] = ()
        container_home_identities: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Container/CI identities whose /home|/Users home is part "
                    "of the declared image contract, never an operator "
                    "machine path"
                ),
            ),
        ] = ()
        historical_evidence_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(
                description="Exact dated Markdown records preserving observed paths",
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_evidence_files(self) -> Self:
            files = self.historical_evidence_files
            if len(set(files)) != len(files):
                msg = "historical evidence files must be unique"
                raise ValueError(msg)
            for path in files:
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or not path.parts
                    or path.parts[0] != c.Infra.DIR_DOCS
                    or path.suffix != ".md"
                ):
                    msg = (
                        "historical evidence must be "
                        f"an exact docs Markdown file: {path}"
                    )
                    raise ValueError(msg)
            return self

    class DocsAuditPolicySpec(DocsAuditOverridesSpec):
        """Complete rendered documentation policy accepted by the auditor."""

        placeholder_patterns: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Regexes recognizing unfinished document markers"),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_patterns(self) -> Self:
            for pattern in self.placeholder_patterns:
                re.compile(pattern)
            return self


__all__: list[str] = ["FlextInfraConfigModelsContract"]
