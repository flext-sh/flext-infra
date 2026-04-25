"""Scope resolution models for flext-infra (Lane A-CH Phase 0 Task 0.4).

``m.Infra.ScopeResolution`` is the structured outcome of resolving a target
selector (``--module``, ``--namespace``, ``--project``, ``--projects``,
``--files``, or workspace default) against the workspace tree. Consumed by
refactor verbs and the catalog dispatcher.

Per AGENT_COORDINATION.md §2.2 + §4.2 (C2), A-CH owns this model. A-TS
consumes it read-only via the bridge it ships in Phase 2.0a; A-HD and A-PT
also consume it.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum, unique
from pathlib import Path
from typing import Annotated

from flext_cli import m


class FlextInfraModelsScope:
    """Scope resolution models exposed at ``m.Infra.ScopeResolution``."""

    @unique
    class ScopeLevel(StrEnum):
        """The granularity at which a selector resolved."""

        MODULE = "module"
        NAMESPACE = "namespace"
        PROJECT = "project"
        PROJECTS = "projects"
        FILES = "files"
        WORKSPACE = "workspace"

    class ScopeResolution(m.ContractModel):
        """Resolved scope returned by ``u.Infra.scope_resolve``.

        ``files`` is sorted, deduplicated, and contains only paths inside
        ``workspace_root``. ``namespace_alias`` and ``namespace_path`` are
        populated only when ``level == NAMESPACE``.
        """

        level: Annotated[
            FlextInfraModelsScope.ScopeLevel,
            m.Field(description="Granularity: module, namespace, project, …"),
        ]
        workspace_root: Annotated[
            Path,
            m.Field(description="Resolved workspace root for this resolution."),
        ]
        files: Annotated[
            tuple[Path, ...],
            m.Field(
                default_factory=tuple,
                description=(
                    "Sorted, deduplicated absolute paths inside workspace_root. "
                    "Empty when the level does not constrain to specific files."
                ),
            ),
        ]
        projects: Annotated[
            tuple[str, ...],
            m.Field(
                default_factory=tuple,
                description=(
                    "Project names selected (level=PROJECT or PROJECTS). "
                    "Empty otherwise."
                ),
            ),
        ]
        module: Annotated[
            str | None,
            m.Field(
                default=None,
                description=(
                    "Dotted module path (level=MODULE). e.g. "
                    "'flext_core._models.enforcement'."
                ),
            ),
        ]
        namespace_alias: Annotated[
            str | None,
            m.Field(
                default=None,
                description=(
                    "Alias root when level=NAMESPACE — one of c|m|p|t|u|r|e|h|s|x|d."
                ),
            ),
        ]
        namespace_path: Annotated[
            Sequence[str],
            m.Field(
                default_factory=tuple,
                description=(
                    "Path segments under the alias when level=NAMESPACE. "
                    "e.g. ('Cli',) for 'm.Cli'."
                ),
            ),
        ]


__all__: list[str] = ["FlextInfraModelsScope"]
