"""Project-owned Mise configuration models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models import FlextInfraModelsMiseToolchain


class FlextInfraModelsDepsToolConfigProjectMise:
    """Project-local Mise tools extending fleet tool declarations."""

    class ProjectMiseTool(m.ArbitraryTypesModel):
        """One project-owned Mise tool with one exact version."""

        version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact version written to the generated .mise.toml."),
        ]

    class ProjectMiseConfig(m.ArbitraryTypesModel):
        """Exact project-owned Mise selectors and their tool declarations."""

        tools: Annotated[
            t.MappingKV[
                t.NonEmptyStr,
                FlextInfraModelsDepsToolConfigProjectMise.ProjectMiseTool,
            ],
            m.Field(description="Project-local Mise tools added to generated config."),
        ]

    class MiseRoleDeclaration(m.ContractModel):
        """An immutable consumer role, separate from fleet and host selectors."""

        role: Annotated[
            str,
            m.Field(
                pattern=r"^[a-z][a-z0-9_-]*$",
                description="Consumer role owning these exact tool declarations",
            ),
        ]
        source_inputs: Annotated[
            tuple[m.Cli.AtomicFileReceipt, ...],
            m.Field(
                min_length=1,
                description="Authenticated inputs consumed by the role producer",
            ),
        ]
        tools: Annotated[
            tuple[FlextInfraModelsMiseToolchain.MiseToolEntry, ...],
            m.Field(
                min_length=1,
                description="Exact native tools and unchanged version/integrity probes",
            ),
        ]

        @m.model_validator(mode="after")
        def _exact_native_role(self) -> Self:
            names = tuple(entry.name for entry in self.tools)
            if len(set(names)) != len(names):
                msg = "role tools must have unique native names"
                raise ValueError(msg)
            for entry in self.tools:
                if (
                    not re.fullmatch(r"[a-z][a-z0-9_-]*", entry.name)
                    or not re.fullmatch(
                        r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", entry.version
                    )
                    or entry.selector not in {None, entry.name}
                    or not entry.lock_checksum
                    or entry.http is not None
                    or entry.bin is not None
                    or entry.postinstall is not None
                    or entry.depends
                    or entry.install_env
                    or entry.version_prefix is not None
                ):
                    msg = (
                        f"role requires an exact checksummed native tool: {entry.name}"
                    )
                    raise ValueError(msg)
            return self

    class MiseRoleRequest(m.ContractModel):
        """Pinned declaration/reader inputs and an explicitly isolated target."""

        declaration: Annotated[
            m.Cli.AtomicFileReceipt,
            m.Field(description="Authenticated typed role declaration bytes"),
        ]
        reader: Annotated[
            m.Cli.AtomicFileReceipt,
            m.Field(description="Captured physical native Mise reader"),
        ]
        reader_manifest: Annotated[
            m.Cli.AtomicFileReceipt,
            m.Field(description="Reader owner's self-management declaration"),
        ]
        reader_lock: Annotated[
            m.Cli.AtomicFileReceipt,
            m.Field(description="Reader owner's checksum-locked self identity"),
        ]
        scope_root: Annotated[
            Path,
            m.Field(
                description="Explicit physical root owning isolated installation state"
            ),
        ]
        target_root: Annotated[
            Path,
            m.Field(
                description="New role directory strictly contained by the owned scope"
            ),
        ]

    class MiseRolePlan(m.ContractModel):
        """Native projection and lock authenticated before installation."""

        request: Annotated[
            FlextInfraModelsDepsToolConfigProjectMise.MiseRoleRequest,
            m.Field(description="Accepted reader, source and target authority"),
        ]
        manifest: Annotated[
            m.Cli.AtomicFileReceipt,
            m.Field(description="Authenticated role-local native Mise projection"),
        ]
        lock: Annotated[
            m.Cli.AtomicFileReceipt,
            m.Field(
                description="Authenticated exact version and platform checksum lock"
            ),
        ]

    class MiseRoleInstallation(m.ContractModel):
        """Exact installed binaries bound to the source and locked projection."""

        plan: Annotated[
            FlextInfraModelsDepsToolConfigProjectMise.MiseRolePlan,
            m.Field(
                description="Unchanged declaration and locked projection used for acquisition"
            ),
        ]
        executables: Annotated[
            t.MappingKV[str, m.Cli.AtomicFileReceipt],
            m.Field(description="Proven physical binaries with exact content digests"),
        ]


__all__: list[str] = ["FlextInfraModelsDepsToolConfigProjectMise"]
