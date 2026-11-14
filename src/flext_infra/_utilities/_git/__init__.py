# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Git package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._git.attestation import (
        FlextInfraUtilitiesGitAttestation,
    )
    from flext_infra._utilities._git.attestation_evidence import (
        FlextInfraUtilitiesGitAttestationEvidence,
    )
    from flext_infra._utilities._git.ignore import FlextInfraUtilitiesGitignore
    from flext_infra._utilities._git.lane_hygiene import (
        FlextInfraUtilitiesGitLaneHygiene,
    )
    from flext_infra._utilities._git.mutation_scope import (
        FlextInfraUtilitiesGitMutationScope,
    )
    from flext_infra._utilities._git.physical_scope import (
        FlextInfraUtilitiesGitPhysicalScope,
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
    "FlextInfraUtilitiesGitPhysicalScope",
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
    {
        "FlextInfraUtilitiesGitAttestation": ".attestation",
        "FlextInfraUtilitiesGitAttestationEvidence": ".attestation_evidence",
        "FlextInfraUtilitiesGitLaneHygiene": ".lane_hygiene",
        "FlextInfraUtilitiesGitMutationScope": ".mutation_scope",
        "FlextInfraUtilitiesGitPhysicalScope": ".physical_scope",
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
        "FlextInfraUtilitiesGitWorktree": ".worktree",
        "FlextInfraUtilitiesGitWorktreeCheckpoint": ".worktree_checkpoint",
        "FlextInfraUtilitiesGitWorktreeDiscovery": ".worktree_discovery",
        "FlextInfraUtilitiesGitWorktreeFacts": ".worktree_facts",
        "FlextInfraUtilitiesGitWorktreeIO": ".worktree_io",
        "FlextInfraUtilitiesGitWorktreeMaterialization": ".worktree_materialization",
        "FlextInfraUtilitiesGitWorktreeMeasure": ".worktree_measure",
        "FlextInfraUtilitiesGitWorktreePatch": ".worktree_patch",
        "FlextInfraUtilitiesGitWorktreeRemoval": ".worktree_removal",
        "FlextInfraUtilitiesGitWorktreeRoots": ".worktree_roots",
        "FlextInfraUtilitiesGitWorktreeStatus": ".worktree_status",
        "FlextInfraUtilitiesGitignore": ".ignore",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesGitAttestation": (
            "_TAG_PREFIX",
            "_SSH_SIGNATURE_MARKER",
            "git_signing_identity",
            "_validate_inline_ssh_key",
            "_signing_config_observation",
            "git_capture_gate",
            "git_begin_gate_capture",
            "_gate_capture_context_digest",
            "git_finish_gate_capture",
            "git_capture_report_bindings",
            "_captured_gate_evidence",
            "_attestation_tag",
            "_attestation_paths",
            "_attestation_predicate",
            "_toolchain_digest",
            "git_create_gate_attestation",
            "_create_gate_tag",
            "_publish_gate_tag",
            "git_verify_gate_attestation",
            "git_admit_gate_candidate",
            "_admission_report",
            "_check_identity_match",
            "_check_merge_constraints",
            "_check_clean_requirement",
            "_check_ttl",
            "_check_dirty_workspace",
            "_verified_gate_predicate",
            "_verify_predicate_evidence",
            "_verified_original_receipt",
            "_published_attestation_report",
            "_predicate_from_tag",
            "_attestation_predicate_from_value",
            "_attestation_report",
        ),
        "FlextInfraUtilitiesGitAttestationEvidence": (
            "_original_gate_evidence",
            "_accepted_gate_evidence",
            "_original_report_outcome",
            "_producer_report_outcome",
            "_original_check_outcome",
            "_original_test_outcome",
            "_check_report_outcome",
            "_pytest_report_outcome",
            "_report_contract_bytes",
            "_report_bytes",
            "_verified_report_evidence",
        ),
        "FlextInfraUtilitiesGitLaneHygiene": ("git_lane_facts",),
        "FlextInfraUtilitiesGitMutationScope": (
            "git_mutation_scope",
            "mutation_lock_path",
        ),
        "FlextInfraUtilitiesGitRepo": (
            "_publication_index",
            "_git_index_path",
            "_registered_worktree_entries",
            "_worktree_registry",
            "_primary_storage_facts_disagree",
            "_primary_binding_disagrees",
            "refresh_binary",
            "_open_repo",
            "_repo",
            "_primary_from_config",
            "_primary_from_registry",
            "_validated_primary_root",
            "_git_primary_worktree_root_path",
        ),
        "FlextInfraUtilitiesGitRequirementSource": (
            "_canonical_https_url",
            "ref_is_commit",
            "declared_git_source",
        ),
        "FlextInfraUtilitiesGitScope": (
            "ScopeFacts",
            "git_repo_root",
            "git_tracked_repo_relative_paths",
            "scope_relative_paths",
            "_git_tracked_scope_relative_paths",
            "git_source_scope_paths",
            "git_tracked_scope_paths",
            "git_tracked_top_level_dir_names",
            "project_descriptor_is_tracked",
        ),
        "FlextInfraUtilitiesGitSemanticIdentity": (
            "git_identity",
            "repository_cache_namespace",
            "_git_head_is_unborn",
            "exact_worktree_root",
            "exact_worktree_git_dir",
            "_exact_worktree_control",
            "git_is_inside_work_tree",
            "_redacted_remotes",
            "_superproject_root",
            "_has_gitlink_stages",
            "_collect_identity_facts",
        ),
        "FlextInfraUtilitiesGitSemanticIndex": (
            "git_committed_directory_blobs",
            "git_head_numstat",
            "git_fingerprint_inputs",
            "_git_capture_fingerprint",
            "git_update_index_gitlink",
            "git_staged_gitlink_oid",
            "git_index_gitlink_paths",
        ),
        "FlextInfraUtilitiesGitSemanticLane": (
            "_verified_lane_base",
            "_git_produce_lane",
            "git_publish_lane",
            "_git_discard_empty_lane",
            "_git_enter_lane",
            "_git_take_base_projections",
            "_git_commit_produced",
            "_git_open_pull_request",
        ),
        "FlextInfraUtilitiesGitSemanticPaths": (
            "git_capture_index_file",
            "_capture_index_state",
            "git_retire_index_file",
            "_retire_index_locked",
            "_retirable_relative_path",
            "_write_index_replacement",
            "git_init",
            "git_checkout_restore",
            "git_mv_path",
            "git_rm_cached",
            "git_rm_path",
            "git_is_tracked",
            "git_path_has_history",
            "git_add_paths",
            "git_restore_paths",
            "git_commit",
        ),
        "FlextInfraUtilitiesGitSemanticPublish": (
            "git_merge_no_edit",
            "git_delete_ref",
            "git_fetch_origin",
            "git_push_upstream",
            "git_remote_url",
            "git_fetch_remote",
            "git_delete_remote_branch",
            "git_merge_ff_only",
            "git_create_branch",
            "git_switch_branch",
            "git_stash_drop",
        ),
        "FlextInfraUtilitiesGitSemanticRefs": (
            "git_verify_lane",
            "_git_lane_ownership",
            "_git_lane_retained_ownership",
            "_git_lane_checkpoint_receipt",
            "git_lane_ownership",
            "_git_lane_clean_owned_branch",
            "_git_lane_no_stash",
            "_git_lane_tip",
            "_git_lane_declared_remote",
            "_git_lane_cached_tip",
            "_git_lane_ancestry",
            "_git_lane_retirement_clean",
            "git_list_worktrees",
            "git_check_branch_format",
            "git_ref_exists",
            "git_superproject_working_tree",
            "git_show_toplevel",
            "git_current_branch",
            "git_resolve_commit",
            "git_is_ancestor",
            "git_rev_parse",
            "git_ref_heads",
            "git_stash_oids",
            "git_remote_branch_oid",
            "git_remote_default_branch",
            "git_unique_patch_oids",
            "git_merge_is_noop",
            "git_last_activity",
            "git_ref_last_activity",
        ),
        "FlextInfraUtilitiesGitSemanticSubmodule": (
            "git_submodule_init",
            "recorded_member_sources",
            "flext_back_edges",
            "_member_manifests",
            "_requirement_names",
            "_runtime_closure",
            "_unordered_members",
        ),
        "FlextInfraUtilitiesGitSemanticWorktree": (
            "git_add_lane_worktree",
            "_git_add_worktree_args",
            "git_attach_branch_at_head",
            "_force_attach_branch_at_head",
        ),
        "FlextInfraUtilitiesGitStateCapture": (
            "_state_apply",
            "git_apply_worktree_checkpoint",
            "_state_cleanup",
            "git_cleanup_worktree_state",
        ),
        "FlextInfraUtilitiesGitStateCheckpoint": (
            "state_leases",
            "_state_require_original",
            "_state_checkpoint",
            "git_checkpoint_worktree_state",
            "_state_verify_saved",
            "git_verify_worktree_checkpoint_commit",
        ),
        "FlextInfraUtilitiesGitStateFiles": (
            "_state_blob_payload",
            "_state_require_directory_scope",
            "_state_blob_oid",
            "_state_require_payload",
            "_state_write_symlink",
            "_state_effect_file",
            "_state_remove_empty_tree",
        ),
        "FlextInfraUtilitiesGitStatePublication": (
            "_state_remote_url",
            "_state_advertised",
            "_state_verify_publication",
            "_state_publish",
            "git_publish_worktree_checkpoint",
            "git_verify_worktree_checkpoint_publication",
            "_state_checkpoint_branch_ref",
            "git_create_checkpoint_branch",
            "_state_push_checkpoint_branch",
            "git_publish_checkpoint_branch",
            "_state_delete_checkpoint_branch",
            "git_delete_checkpoint_branch",
        ),
        "FlextInfraUtilitiesGitStateSnapshot": (
            "_state_pathspecs",
            "_state_file_bytes",
            "_state_file",
            "_state_files",
            "state_snapshot_index",
            "_state_head_entries",
            "_state_snapshot_files",
            "_state_snapshot",
            "git_snapshot_worktree_state",
            "git_verify_worktree_state",
        ),
        "FlextInfraUtilitiesGitStateTransition": (
            "_state_baseline_file",
            "_state_baseline_at",
            "_state_obstruction",
            "_state_allowed_files",
            "_state_require_encodable_symlinks",
            "_state_realized_current",
            "_state_require_path_content",
            "_state_verify_transition",
            "_state_preflight_transition",
            "_state_materialize",
        ),
        "FlextInfraUtilitiesGitStateTrees": (
            "_state_tree_entries",
            "state_index_update",
            "state_publication_index",
            "_state_tree",
            "_state_working_entries",
            "_state_validate_checkpoint",
        ),
        "FlextInfraUtilitiesGitWorktree": (),
        "FlextInfraUtilitiesGitWorktreeCheckpoint": (
            "_transaction_exclusion_pathspecs",
            "git_repository_delta",
        ),
        "FlextInfraUtilitiesGitWorktreeDiscovery": (
            "git_remote_identity",
            "git_submodule_paths",
        ),
        "FlextInfraUtilitiesGitWorktreeFacts": (
            "git_registered_worktrees_fs",
            "collect_worktree_facts",
            "worktrees_report",
            "_worktree_fact",
            "_worktree_gitdir_pointer",
            "_worktree_registry_branch",
            "_worktree_kind",
            "_worktree_bead_index",
            "_worktree_correlate",
        ),
        "FlextInfraUtilitiesGitWorktreeMaterialization": (
            "git_add_detached_worktree",
            "_git_path_is_excluded",
            "_git_copy_untracked_file",
            "_git_copy_untracked",
            "git_copy_worktree_state",
            "_verified_worktree_pair",
            "_worktree_pair_conflict",
            "_worktree_layer_patches",
            "_unsafe_untracked_parent",
            "_verify_untracked_destinations",
            "_apply_layer_patches",
            "_preserve_source_modes",
            "_git_copy_worktree_layers",
        ),
        "FlextInfraUtilitiesGitWorktreeMeasure": (
            "_worktree_measure",
            "_worktree_scan_dir",
            "_worktree_entry_metrics",
            "_worktree_entry_is_dir",
            "_worktree_entry_file_metrics",
        ),
        "FlextInfraUtilitiesGitWorktreePatch": (
            "_git_check_patch_at",
            "git_check_patch",
            "git_check_isolated_patch",
            "_git_source_has_patch",
            "_git_patch_added_paths",
            "_git_apply_gitlinks",
            "_git_apply_with_ignored_additions",
            "git_apply_patch",
        ),
        "FlextInfraUtilitiesGitWorktreeRemoval": (
            "_nested_submodule_changes",
            "_preflight_clean_worktree",
            "_verify_worktree_clean",
            "git_remove_clean_worktree",
        ),
        "FlextInfraUtilitiesGitWorktreeRoots": (
            "git_repository_root",
            "git_primary_worktree_root",
            "_git_repository_root_path",
            "git_submodule_declarations",
            "_gitmodules_sections",
            "_gitmodules_config",
            "git_submodule_declaration",
            "git_require_submodule_contract",
        ),
        "FlextInfraUtilitiesGitWorktreeStatus": (
            "_lifecycle_porcelain",
            "git_status",
            "git_repository_head",
            "git_changed_paths",
            "_git_head_oid",
            "git_has_staged_changes",
        ),
        "FlextInfraUtilitiesGitignore": (
            "codegen_templates_root",
            "codegen_artifact_source",
            "codegen_template_sources",
            "render_project_gitignore",
            "preserve_project_gitignore_blocks",
            "_apply_runtime_suffix",
            "gitignore_runtime_suffix",
            "_locate_block_markers",
            "_block_sections",
            "_compose_preserved_blocks",
            "gitignore_sections",
            "_runtime_gitignore_sections",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesGitAttestation": (
            (".", "FlextInfraUtilitiesGitAttestationEvidence"),
        ),
        "FlextInfraUtilitiesGitAttestationEvidence": (
            (".", "FlextInfraUtilitiesGitRepo"),
        ),
        "FlextInfraUtilitiesGitScope": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitSemanticIdentity": (
            (".", "FlextInfraUtilitiesGitRepo"),
        ),
        "FlextInfraUtilitiesGitSemanticIndex": (
            (".", "FlextInfraUtilitiesGitStateFiles"),
        ),
        "FlextInfraUtilitiesGitSemanticPaths": (
            (".", "FlextInfraUtilitiesGitStateFiles"),
        ),
        "FlextInfraUtilitiesGitSemanticPublish": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitSemanticRefs": (
            (".", "FlextInfraUtilitiesGitStatePublication"),
            (".", "FlextInfraUtilitiesGitWorktreeRoots"),
        ),
        "FlextInfraUtilitiesGitSemanticSubmodule": (
            (".", "FlextInfraUtilitiesGitRepo"),
        ),
        "FlextInfraUtilitiesGitSemanticWorktree": (
            (".", "FlextInfraUtilitiesGitRepo"),
        ),
        "FlextInfraUtilitiesGitStateCapture": (
            (".", "FlextInfraUtilitiesGitStatePublication"),
            (".", "FlextInfraUtilitiesGitStateTransition"),
        ),
        "FlextInfraUtilitiesGitStateCheckpoint": (
            (".", "FlextInfraUtilitiesGitStateTrees"),
        ),
        "FlextInfraUtilitiesGitStateFiles": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitStatePublication": (
            (".", "FlextInfraUtilitiesGitStateCheckpoint"),
        ),
        "FlextInfraUtilitiesGitStateSnapshot": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitStateTransition": (
            (".", "FlextInfraUtilitiesGitStateFiles"),
            (".", "FlextInfraUtilitiesGitStateTrees"),
        ),
        "FlextInfraUtilitiesGitStateTrees": (
            (".", "FlextInfraUtilitiesGitStateSnapshot"),
        ),
        "FlextInfraUtilitiesGitWorktree": (
            (".", "FlextInfraUtilitiesGitWorktreeCheckpoint"),
            (".", "FlextInfraUtilitiesGitWorktreeDiscovery"),
            (".", "FlextInfraUtilitiesGitWorktreeFacts"),
            (".", "FlextInfraUtilitiesGitWorktreeMaterialization"),
            (".", "FlextInfraUtilitiesGitWorktreePatch"),
            (".", "FlextInfraUtilitiesGitWorktreeRemoval"),
            (".", "FlextInfraUtilitiesGitWorktreeRoots"),
        ),
        "FlextInfraUtilitiesGitWorktreeCheckpoint": (
            (".", "FlextInfraUtilitiesGitWorktreeStatus"),
        ),
        "FlextInfraUtilitiesGitWorktreeDiscovery": (
            (".", "FlextInfraUtilitiesGitRepo"),
        ),
        "FlextInfraUtilitiesGitWorktreeFacts": (
            (".", "FlextInfraUtilitiesGitWorktreeMeasure"),
        ),
        "FlextInfraUtilitiesGitWorktreeMaterialization": (
            (".", "FlextInfraUtilitiesGitWorktreeStatus"),
        ),
        "FlextInfraUtilitiesGitWorktreePatch": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitWorktreeRemoval": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitWorktreeRoots": ((".", "FlextInfraUtilitiesGitRepo"),),
        "FlextInfraUtilitiesGitWorktreeStatus": ((".", "FlextInfraUtilitiesGitRepo"),),
    },
)
