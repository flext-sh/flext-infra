# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.github package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .gate_attestation_tests import (
        test_gate_attestation_rejects_incomplete_coverage,
        test_gate_attestation_removes_local_tag_when_atomic_push_fails,
        test_signed_gate_attestation_round_trip,
    )
    from .main_cli_tests import (
        test_main_returns_nonzero_on_unknown,
        test_main_returns_one_without_subcommand,
        test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options,
    )
    from .main_dispatch_tests import (
        test_run_github_workspace_pull_requests_aggregates_results,
        test_run_github_workspace_pull_requests_honors_fail_fast,
        test_run_github_workspace_pull_requests_respects_project_selection,
    )
    from .main_integration_tests import (
        test_lint_subcommand_writes_report,
        test_pr_status_succeeds_for_minimal_repo_without_open_pull_request,
        test_pr_subcommand_rejects_removed_lifecycle_action,
        test_workflows_subcommand_applies_templates,
    )
    from .main_tests import TestsInfraGithub
__all__: tuple[str, ...] = (
    "TestsInfraGithub",
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
    "test_gate_attestation_rejects_incomplete_coverage",
    "test_gate_attestation_removes_local_tag_when_atomic_push_fails",
    "test_lint_subcommand_writes_report",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_one_without_subcommand",
    "test_main_returns_zero_on_help",
    "test_pr_status_succeeds_for_minimal_repo_without_open_pull_request",
    "test_pr_subcommand_rejects_removed_lifecycle_action",
    "test_pr_workspace_accepts_repeated_project_options",
    "test_run_github_workspace_pull_requests_aggregates_results",
    "test_run_github_workspace_pull_requests_honors_fail_fast",
    "test_run_github_workspace_pull_requests_respects_project_selection",
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
                "test_gate_attestation_rejects_incomplete_coverage",
                "test_gate_attestation_removes_local_tag_when_atomic_push_fails",
                "test_signed_gate_attestation_round_trip",
            ),
            ".main_cli_tests": (
                "test_main_returns_nonzero_on_unknown",
                "test_main_returns_one_without_subcommand",
                "test_main_returns_zero_on_help",
                "test_pr_workspace_accepts_repeated_project_options",
            ),
            ".main_dispatch_tests": (
                "test_run_github_workspace_pull_requests_aggregates_results",
                "test_run_github_workspace_pull_requests_honors_fail_fast",
                "test_run_github_workspace_pull_requests_respects_project_selection",
            ),
            ".main_integration_tests": (
                "test_lint_subcommand_writes_report",
                "test_pr_status_succeeds_for_minimal_repo_without_open_pull_request",
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
