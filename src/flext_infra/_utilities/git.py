"""Public Git utilities facet for ``u.Infra`` (composed into utilities FLEXT).

Private GitPython parts live under ``_utilities/_git/``. Consumers use
``from flext_infra import u`` only — never import this module or ``_git``.

The composing owner imports its bases from their declaring lazy package.
It does not resolve them through the aggregate utilities facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitAttestation,
    FlextInfraUtilitiesGitLaneHygiene,
    FlextInfraUtilitiesGitMutationScope,
    FlextInfraUtilitiesGitRequirementSource,
    FlextInfraUtilitiesGitScope,
    FlextInfraUtilitiesGitSemanticIdentity,
    FlextInfraUtilitiesGitSemanticIndex,
    FlextInfraUtilitiesGitSemanticLane,
    FlextInfraUtilitiesGitSemanticPaths,
    FlextInfraUtilitiesGitSemanticPublish,
    FlextInfraUtilitiesGitSemanticRefs,
    FlextInfraUtilitiesGitSemanticSubmodule,
    FlextInfraUtilitiesGitSemanticWorktree,
    FlextInfraUtilitiesGitStateCapture,
    FlextInfraUtilitiesGitWorktree,
)


class FlextInfraUtilitiesGit(
    FlextInfraUtilitiesGitRequirementSource,
    FlextInfraUtilitiesGitMutationScope,
    FlextInfraUtilitiesGitWorktree,
    FlextInfraUtilitiesGitAttestation,
    FlextInfraUtilitiesGitScope,
    FlextInfraUtilitiesGitSemanticSubmodule,
    FlextInfraUtilitiesGitLaneHygiene,
    FlextInfraUtilitiesGitStateCapture,
    FlextInfraUtilitiesGitSemanticIdentity,
    FlextInfraUtilitiesGitSemanticIndex,
    FlextInfraUtilitiesGitSemanticLane,
    FlextInfraUtilitiesGitSemanticPaths,
    FlextInfraUtilitiesGitSemanticPublish,
    FlextInfraUtilitiesGitSemanticRefs,
    FlextInfraUtilitiesGitSemanticWorktree,
):
    """Canonical Git owner for flext-infra: every Git part composed flat.

    A part inherits only the parts whose protected helpers it calls and reaches
    another part's public operation through that owner (removal calls
    ``FlextInfraUtilitiesGitSemanticRefs.git_verify_lane``), so the parts stay
    shallow and only this owner composes them all.
    """

    @staticmethod
    def git_attribute_pattern(path: str) -> str:
        """Encode one literal path with Git's glob escaping and C quoting.

        Returns:
            The resulting ``str``.

        """
        literal = (
            path
            .replace("\\", "\\\\")
            .replace("*", "\\*")
            .replace("?", "\\?")
            .replace("[", "\\[")
        )
        quoted = "".join(
            chr(byte)
            if chr(byte).isascii()
            and chr(byte).isprintable()
            and chr(byte) not in {'"', "\\"}
            else f"\\{byte:03o}"
            for byte in literal.encode("utf-8")
        )
        return f'"{quoted}"'


__all__: list[str] = ["FlextInfraUtilitiesGit"]
