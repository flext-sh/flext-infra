# AUTO-GENERATED FILE — Regenerate with: make gen
"""Unit package.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from .fixtures import (
    deptry_report_payload,
    models_resource,
    modernizer_workspace,
    modernizer_workspace_with_projects,
    real_docs_project,
    real_makefile_project,
    real_python_package,
    real_toml_project,
    real_workspace,
    rope_workspace,
    services_resource,
    tool_config_document,
)
from .fixtures_git import real_git_repo
from .runner_service import RealSubprocessRunner
from .workspace_factory import TestsFlextInfraWorkspaceFactory

__all__: tuple[str, ...] = (
    "RealSubprocessRunner",
    "TestsFlextInfraWorkspaceFactory",
    "deptry_report_payload",
    "models_resource",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "rope_workspace",
    "services_resource",
    "tool_config_document",
)
