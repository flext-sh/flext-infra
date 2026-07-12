"""Project-scaffold manifest (data) for ``flext-infra codegen new``.

Per ADR-005 this is the single source of truth describing *which* templates make
up a new project and *where* each lands. The engine (``u.Cli.template_render_dir``,
flext-cli) is policy-free; this manifest + the rope-derived context carry all the
FLEXT naming policy. Adding a file or a kind is a data edit here + a ``.j2`` drop
in ``templates/``.

Output paths use ``{token}`` placeholders (resolved by the service from rope) so
the engine never sees FLEXT naming. NOTE: the large-row form migrates to
``config/codegen/project_manifest.yaml`` in the ``conform`` slice (ADR-005 SSOT).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Final


class FlextInfraConstantsCodegenProject:
    """Manifest + naming constants for project creation (flat in ``c.Infra.*``)."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these enums define the
    # one public conform contract shared by new and existing repositories. The
    # declarative values live in config/codegen.yaml; constants only type the
    # closed vocabulary used by models and CLI dispatch.

    @unique
    class CodegenConformScope(StrEnum):
        """Repository selection accepted by ``codegen conform``."""

        SELF = "self"
        MEMBERS = "members"
        ALL = "all"

    @unique
    class CodegenConformMode(StrEnum):
        """Read-only or write mode accepted by ``codegen conform``."""

        CHECK = "check"
        APPLY = "apply"

    @unique
    class MakeProfile(StrEnum):
        """Generated Makefile profile for one repository."""

        WORKSPACE_ROOT = "workspace-root"
        WORKSPACE_MEMBER = "workspace-member"
        STANDALONE = "standalone"

    @unique
    class RepositoryRole(StrEnum):
        """Repository role in a declared workspace topology."""

        WORKSPACE_ROOT = "workspace-root"
        WORKSPACE_MEMBER = "workspace-member"
        STANDALONE = "standalone"
        CONTENT_ONLY = "content-only"
        EXCLUDED = "excluded"

    @unique
    class RepositoryState(StrEnum):
        """Lifecycle state used by repository selection."""

        ACTIVE = "active"
        CONTENT_ONLY = "content-only"
        EXCLUDED = "excluded"

    @unique
    class ProjectKind(StrEnum):
        """New-project kind; drives deps, Makefile mode, and registration."""

        INTERNAL = "internal"
        EXTERNAL = "external"

    WORKSPACE_MANIFEST_FILENAME: Final[str] = "workspace.yaml"
    WORKSPACE_SCHEMA_FILENAME: Final[str] = "workspace.schema.json"
    UV_LOCK_FILENAME: Final[str] = "uv.lock"
    CUSTOM_MAKE_FILENAME: Final[str] = "custom.mk"
    CUSTOM_HANDLER_PREFIX: Final[str] = "_custom_"
    PUBLIC_MAKE_VERBS: Final[tuple[str, ...]] = (
        "help",
        "setup",
        "deps",
        "build",
        "check",
        "test",
        "format",
        "run",
        "status",
        "docs",
        "clean",
        "release",
        "codegen",
    )

    TEMPLATE_MODULE_SKELETON: Final[str] = "module_skeleton.py.j2"
    "Scaffold module-skeleton template (replaces the legacy f-string)."

    # Each row: (relpath_template, output_relpath, kinds, delegate, overwrite).
    # kinds: tuple of ProjectKind the row applies to (BOTH = internal+external).
    # delegate: "render" (cli engine) today; lazy_init/version_file/basemk later.
    # NOTE (multi-agent, mro-wkii.17): one base catalog serves both profiles;
    # workspace topology is owned only by config/workspace.yaml.


__all__: list[str] = ["FlextInfraConstantsCodegenProject"]
