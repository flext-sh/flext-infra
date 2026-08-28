# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.github package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .main_cli_tests import (
        test_main_returns_nonzero_on_unknown,
        test_main_returns_one_without_subcommand,
        test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options,
    )
    from .main_dispatch_tests import (
        test_pull_request_dispatch_accepts_only_repository_alias,
        test_pull_request_dispatch_processes_only_supplied_repository,
    )
    from .main_integration_tests import (
        test_lint_subcommand_writes_report,
        test_pr_subcommand_rejects_removed_lifecycle_action,
        test_pr_subcommand_returns_nonzero_for_minimal_repo,
        test_workflows_subcommand_applies_templates,
    )
    from .main_tests import TestsInfraGithub
__all__: tuple[str, ...] = (
    "TestsInfraGithub",
    "test_lint_subcommand_writes_report",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_one_without_subcommand",
    "test_main_returns_zero_on_help",
    "test_pr_subcommand_rejects_removed_lifecycle_action",
    "test_pr_subcommand_returns_nonzero_for_minimal_repo",
    "test_pr_workspace_accepts_repeated_project_options",
    "test_pull_request_dispatch_accepts_only_repository_alias",
    "test_pull_request_dispatch_processes_only_supplied_repository",
    "test_workflows_subcommand_applies_templates",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".main_cli_tests": (
                "test_main_returns_nonzero_on_unknown",
                "test_main_returns_one_without_subcommand",
                "test_main_returns_zero_on_help",
                "test_pr_workspace_accepts_repeated_project_options",
            ),
            ".main_dispatch_tests": (
                "test_pull_request_dispatch_accepts_only_repository_alias",
                "test_pull_request_dispatch_processes_only_supplied_repository",
            ),
            ".main_integration_tests": (
                "test_lint_subcommand_writes_report",
                "test_pr_subcommand_rejects_removed_lifecycle_action",
                "test_pr_subcommand_returns_nonzero_for_minimal_repo",
                "test_workflows_subcommand_applies_templates",
            ),
            ".main_tests": ("TestsInfraGithub",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
