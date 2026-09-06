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

    # These enums define the
    # one public conform contract shared by new and existing repositories. The
    # declarative values live in config/codegen.yaml; constants only type the
    # closed vocabulary used by models and CLI dispatch.

    @unique
    class CodegenConformScope(StrEnum):
        """Repository selection accepted by ``codegen conform``."""

        SELF = "self"
        SUBPROJECTS = "subprojects"
        ALL = "all"

    @unique
    class CodegenConformSurface(StrEnum):
        """Managed file selection accepted by ``codegen conform``."""

        ALL = "all"
        DEPENDENCIES = "dependencies"
        MAKEFILE = "makefile"
        PYPROJECT = "pyproject"

    @unique
    class CodegenConformMode(StrEnum):
        """Read-only or write mode accepted by ``codegen conform``."""

        CHECK = "check"
        APPLY = "apply"

    @unique
    class MiseResolutionMode(StrEnum):
        """How an apply-mode ``codegen conform`` resolves the Mise toolchain.

        ``AUTO`` probes the declared release endpoint once in preflight and
        becomes ``ONLINE`` (the newest Mise release and every moving tool
        selector are resolved and published) or ``OFFLINE`` (the published
        launchers and lock are kept byte-identical). The explicit values pin
        one path; none of them is a fallback taken after a failed effect.
        """

        AUTO = "auto"
        ONLINE = "online"
        OFFLINE = "offline"

    @unique
    class MakeProfile(StrEnum):
        """Generated Makefile profile for one repository.

        Topology is proven by the repository itself: a checkout that declares
        ``.gitmodules`` is a workspace, and one that does not is standalone.
        This mirrors ``MakeProfile``, which the detector returns, so the two
        vocabularies cannot drift.
        """

        WORKSPACE = "workspace"
        STANDALONE = "standalone"

    @unique
    class RepositoryState(StrEnum):
        """Lifecycle state used by repository selection."""

        ACTIVE = "active"
        EXCLUDED = "excluded"

    @unique
    class CodegenKind(StrEnum):
        """Code-generation policy applied to one repository."""

        CONFORM = "conform"
        PYTHON = "python"
        NONE = "none"

    @unique
    class ProjectKind(StrEnum):
        """Governance kind of one repository; decides who may rewrite it.

        Generation applies to ``INTERNAL_FLEXT`` alone. An ``INTERNAL`` project
        is owned but not built on FLEXT, so FLEXT layout, facade chain, and
        typing policy do not apply to it. A ``THIRD_PARTY_FORK`` follows its
        upstream in everything, and standardizing it would destroy the contract
        the fork exists to track.
        """

        INTERNAL_FLEXT = "internal_flext"
        INTERNAL = "internal"
        THIRD_PARTY_FORK = "third_party_fork"

    BEADS_CONFIG_FILENAME: Final[str] = "beads.yaml"
    BEADS_DIRNAME: Final[str] = ".beads"
    BEADS_LOCAL_VERSION_FILENAME: Final[str] = ".local_version"
    BEADS_CONFIG_VERSION: Final = 1
    WORKSPACE_MANIFEST_FILENAME: Final[str] = "workspace.yaml"
    WORKSPACE_MANIFEST_VERSION: Final[int] = 3
    UV_LOCK_FILENAME: Final[str] = "uv.lock"
    GIT_URL_SUFFIX: Final[str] = ".git"
    "Canonical clone-URL suffix every governed RepositoryRef URL carries."
    CUSTOM_MAKE_FILENAME: Final[str] = "custom.mk"
    CUSTOM_CI_STEPS_FILENAME: Final[str] = ".github/ci-custom-steps.yml"
    """Project-owned steps injected into generated CI, symmetric to custom.mk.

    It sits beside the workflows rather than inside them: GitHub parses every
    file under ``.github/workflows`` as a workflow, and a bare step list is not
    one, so a file placed there would surface as a permanent syntax error.
    """
    CUSTOM_HANDLER_PREFIX: Final[str] = "_custom_"
    TEMPLATE_MODULE_SKELETON: Final[str] = "module_skeleton.py.j2"
    "Scaffold module-skeleton template (replaces the legacy f-string)."

    # One base catalog serves both profiles;
    # workspace topology is read only from each repository's own .gitmodules.


__all__: list[str] = ["FlextInfraConstantsCodegenProject"]
