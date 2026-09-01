# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.github package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .gate_attestation_tests import (
        close_git_repositories,
        test_gate_attestation_normalizes_network_remote_git_suffix,
        test_gate_attestation_rejects_duplicate_gate_coverage,
        test_gate_attestation_rejects_incomplete_coverage,
        test_gate_attestation_rejects_source_without_no_ff_merge,
        test_gate_attestation_removes_local_tag_when_atomic_push_fails,
        test_gate_attestation_requires_committed_promotion_manifest,
        test_gate_attestation_verifies_selected_promoted_parent,
        test_signed_gate_attestation_round_trip,
    )
    from .main_cli_tests import (
        test_main_returns_nonzero_on_unknown,
        test_main_returns_one_without_subcommand,
        test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options,
    )
    from .main_dispatch_tests import (
        test_run_github_workspace_pull_requests_continues_without_fail_fast,
        test_run_github_workspace_pull_requests_honors_fail_fast,
        test_run_github_workspace_pull_requests_respects_project_selection,
        test_run_github_workspace_pull_requests_stops_on_first_failure,
    )
    from .main_integration_tests import (
        test_lint_subcommand_writes_report,
        test_pr_status_rejects_directory_without_repository_identity,
        test_pr_subcommand_rejects_removed_lifecycle_action,
        test_workflows_subcommand_applies_templates,
    )
    from .main_tests import TestsInfraGithub
__all__: tuple[str, ...] = (
    "TestsInfraGithub",
    "c",
    "close_git_repositories",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "t",
    "td",
    "test_gate_attestation_normalizes_network_remote_git_suffix",
    "test_gate_attestation_rejects_duplicate_gate_coverage",
    "test_gate_attestation_rejects_incomplete_coverage",
    "test_gate_attestation_rejects_source_without_no_ff_merge",
    "test_gate_attestation_removes_local_tag_when_atomic_push_fails",
    "test_gate_attestation_requires_committed_promotion_manifest",
    "test_gate_attestation_verifies_selected_promoted_parent",
    "test_lint_subcommand_writes_report",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_one_without_subcommand",
    "test_main_returns_zero_on_help",
    "test_pr_status_rejects_directory_without_repository_identity",
    "test_pr_subcommand_rejects_removed_lifecycle_action",
    "test_pr_workspace_accepts_repeated_project_options",
    "test_run_github_workspace_pull_requests_continues_without_fail_fast",
    "test_run_github_workspace_pull_requests_honors_fail_fast",
    "test_run_github_workspace_pull_requests_respects_project_selection",
    "test_run_github_workspace_pull_requests_stops_on_first_failure",
    "test_signed_gate_attestation_round_trip",
    "test_workflows_subcommand_applies_templates",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".gate_attestation_tests": (
                "close_git_repositories",
                "test_gate_attestation_normalizes_network_remote_git_suffix",
                "test_gate_attestation_rejects_duplicate_gate_coverage",
                "test_gate_attestation_rejects_incomplete_coverage",
                "test_gate_attestation_rejects_source_without_no_ff_merge",
                "test_gate_attestation_removes_local_tag_when_atomic_push_fails",
                "test_gate_attestation_requires_committed_promotion_manifest",
                "test_gate_attestation_verifies_selected_promoted_parent",
                "test_signed_gate_attestation_round_trip",
            ),
            ".main_cli_tests": (
                "test_main_returns_nonzero_on_unknown",
                "test_main_returns_one_without_subcommand",
                "test_main_returns_zero_on_help",
                "test_pr_workspace_accepts_repeated_project_options",
            ),
            ".main_dispatch_tests": (
                "test_run_github_workspace_pull_requests_continues_without_fail_fast",
                "test_run_github_workspace_pull_requests_honors_fail_fast",
                "test_run_github_workspace_pull_requests_respects_project_selection",
                "test_run_github_workspace_pull_requests_stops_on_first_failure",
            ),
            ".main_integration_tests": (
                "test_lint_subcommand_writes_report",
                "test_pr_status_rejects_directory_without_repository_identity",
                "test_pr_subcommand_rejects_removed_lifecycle_action",
                "test_workflows_subcommand_applies_templates",
            ),
            ".main_tests": ("TestsInfraGithub",),
            "flext_tests": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "u",
                "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
