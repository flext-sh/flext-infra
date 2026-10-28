# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Git package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._git.attestation import (
        FlextInfraUtilitiesGitAttestation,
    )
    from flext_infra._utilities._git.attestation_evidence import (
        FlextInfraUtilitiesGitAttestationEvidence,
    )
    from flext_infra._utilities._git.gitignore import FlextInfraUtilitiesGitignore
    from flext_infra._utilities._git.lane_hygiene import (
        FlextInfraUtilitiesGitLaneHygiene,
    )
    from flext_infra._utilities._git.mutation_scope import (
        FlextInfraUtilitiesGitMutationScope,
    )
    from flext_infra._utilities._git.remote import FlextInfraUtilitiesGitRemote
    from flext_infra._utilities._git.repo import FlextInfraUtilitiesGitRepo
    from flext_infra._utilities._git.requirement_source import (
        FlextInfraUtilitiesGitRequirementSource,
    )
    from flext_infra._utilities._git.scope import FlextInfraUtilitiesGitScope
    from flext_infra._utilities._git.semantic_identity import (
        FlextInfraUtilitiesGitSemanticIdentity,
    )
    from flext_infra._utilities._git.semantic_index import (
        FlextInfraUtilitiesGitSemanticIndex,
    )
    from flext_infra._utilities._git.semantic_lane import (
        FlextInfraUtilitiesGitSemanticLane,
    )
    from flext_infra._utilities._git.semantic_paths import (
        FlextInfraUtilitiesGitSemanticPaths,
    )
    from flext_infra._utilities._git.semantic_publish import (
        FlextInfraUtilitiesGitSemanticPublish,
    )
    from flext_infra._utilities._git.semantic_refs import (
        FlextInfraUtilitiesGitSemanticRefs,
    )
    from flext_infra._utilities._git.semantic_submodule import (
        FlextInfraUtilitiesGitSemanticSubmodule,
    )
    from flext_infra._utilities._git.semantic_worktree import (
        FlextInfraUtilitiesGitSemanticWorktree,
    )
    from flext_infra._utilities._git.state_capture import (
        FlextInfraUtilitiesGitStateCapture,
    )
    from flext_infra._utilities._git.state_checkpoint import (
        FlextInfraUtilitiesGitStateCheckpoint,
    )
    from flext_infra._utilities._git.state_files import FlextInfraUtilitiesGitStateFiles
    from flext_infra._utilities._git.state_publication import (
        FlextInfraUtilitiesGitStatePublication,
    )
    from flext_infra._utilities._git.state_snapshot import (
        FlextInfraUtilitiesGitStateSnapshot,
    )
    from flext_infra._utilities._git.state_transition import (
        FlextInfraUtilitiesGitStateTransition,
    )
    from flext_infra._utilities._git.state_trees import FlextInfraUtilitiesGitStateTrees
    from flext_infra._utilities._git.worktree import FlextInfraUtilitiesGitWorktree
    from flext_infra._utilities._git.worktree_checkpoint import (
        FlextInfraUtilitiesGitWorktreeCheckpoint,
    )
    from flext_infra._utilities._git.worktree_discovery import (
        FlextInfraUtilitiesGitWorktreeDiscovery,
    )
    from flext_infra._utilities._git.worktree_facts import (
        FlextInfraUtilitiesGitWorktreeFacts,
    )
    from flext_infra._utilities._git.worktree_io import FlextInfraUtilitiesGitWorktreeIO
    from flext_infra._utilities._git.worktree_materialization import (
        FlextInfraUtilitiesGitWorktreeMaterialization,
    )
    from flext_infra._utilities._git.worktree_measure import (
        FlextInfraUtilitiesGitWorktreeMeasure,
    )
    from flext_infra._utilities._git.worktree_patch import (
        FlextInfraUtilitiesGitWorktreePatch,
    )
    from flext_infra._utilities._git.worktree_removal import (
        FlextInfraUtilitiesGitWorktreeRemoval,
    )
    from flext_infra._utilities._git.worktree_roots import (
        FlextInfraUtilitiesGitWorktreeRoots,
    )
    from flext_infra._utilities._git.worktree_status import (
        FlextInfraUtilitiesGitWorktreeStatus,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesGitAttestation",
    "FlextInfraUtilitiesGitAttestationEvidence",
    "FlextInfraUtilitiesGitLaneHygiene",
    "FlextInfraUtilitiesGitMutationScope",
    "FlextInfraUtilitiesGitRemote",
    "FlextInfraUtilitiesGitRepo",
    "FlextInfraUtilitiesGitRequirementSource",
    "FlextInfraUtilitiesGitScope",
    "FlextInfraUtilitiesGitSemanticIdentity",
    "FlextInfraUtilitiesGitSemanticIndex",
    "FlextInfraUtilitiesGitSemanticLane",
    "FlextInfraUtilitiesGitSemanticPaths",
    "FlextInfraUtilitiesGitSemanticPublish",
    "FlextInfraUtilitiesGitSemanticRefs",
    "FlextInfraUtilitiesGitSemanticSubmodule",
    "FlextInfraUtilitiesGitSemanticWorktree",
    "FlextInfraUtilitiesGitStateCapture",
    "FlextInfraUtilitiesGitStateCheckpoint",
    "FlextInfraUtilitiesGitStateFiles",
    "FlextInfraUtilitiesGitStatePublication",
    "FlextInfraUtilitiesGitStateSnapshot",
    "FlextInfraUtilitiesGitStateTransition",
    "FlextInfraUtilitiesGitStateTrees",
    "FlextInfraUtilitiesGitWorktree",
    "FlextInfraUtilitiesGitWorktreeCheckpoint",
    "FlextInfraUtilitiesGitWorktreeDiscovery",
    "FlextInfraUtilitiesGitWorktreeFacts",
    "FlextInfraUtilitiesGitWorktreeIO",
    "FlextInfraUtilitiesGitWorktreeMaterialization",
    "FlextInfraUtilitiesGitWorktreeMeasure",
    "FlextInfraUtilitiesGitWorktreePatch",
    "FlextInfraUtilitiesGitWorktreeRemoval",
    "FlextInfraUtilitiesGitWorktreeRoots",
    "FlextInfraUtilitiesGitWorktreeStatus",
    "FlextInfraUtilitiesGitignore",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesGitAttestationEvidence": ".attestation_evidence",
        "FlextInfraUtilitiesGitAttestation": ".attestation",
        "FlextInfraUtilitiesGitLaneHygiene": ".lane_hygiene",
        "FlextInfraUtilitiesGitMutationScope": ".mutation_scope",
        "FlextInfraUtilitiesGitRemote": ".remote",
        "FlextInfraUtilitiesGitRepo": ".repo",
        "FlextInfraUtilitiesGitRequirementSource": ".requirement_source",
        "FlextInfraUtilitiesGitScope": ".scope",
        "FlextInfraUtilitiesGitSemanticIdentity": ".semantic_identity",
        "FlextInfraUtilitiesGitSemanticIndex": ".semantic_index",
        "FlextInfraUtilitiesGitSemanticLane": ".semantic_lane",
        "FlextInfraUtilitiesGitSemanticPaths": ".semantic_paths",
        "FlextInfraUtilitiesGitSemanticPublish": ".semantic_publish",
        "FlextInfraUtilitiesGitSemanticRefs": ".semantic_refs",
        "FlextInfraUtilitiesGitSemanticSubmodule": ".semantic_submodule",
        "FlextInfraUtilitiesGitSemanticWorktree": ".semantic_worktree",
        "FlextInfraUtilitiesGitStateCapture": ".state_capture",
        "FlextInfraUtilitiesGitStateCheckpoint": ".state_checkpoint",
        "FlextInfraUtilitiesGitStateFiles": ".state_files",
        "FlextInfraUtilitiesGitStatePublication": ".state_publication",
        "FlextInfraUtilitiesGitStateSnapshot": ".state_snapshot",
        "FlextInfraUtilitiesGitStateTransition": ".state_transition",
        "FlextInfraUtilitiesGitStateTrees": ".state_trees",
        "FlextInfraUtilitiesGitWorktreeCheckpoint": ".worktree_checkpoint",
        "FlextInfraUtilitiesGitWorktreeDiscovery": ".worktree_discovery",
        "FlextInfraUtilitiesGitWorktreeFacts": ".worktree_facts",
        "FlextInfraUtilitiesGitWorktreeIO": ".worktree_io",
        "FlextInfraUtilitiesGitWorktreeMaterialization": (".worktree_materialization"),
        "FlextInfraUtilitiesGitWorktreeMeasure": ".worktree_measure",
        "FlextInfraUtilitiesGitWorktree": ".worktree",
        "FlextInfraUtilitiesGitWorktreePatch": ".worktree_patch",
        "FlextInfraUtilitiesGitWorktreeRemoval": ".worktree_removal",
        "FlextInfraUtilitiesGitWorktreeRoots": ".worktree_roots",
        "FlextInfraUtilitiesGitWorktreeStatus": ".worktree_status",
        "FlextInfraUtilitiesGitignore": ".gitignore",
    }),
    public_exports=__all__,
)
