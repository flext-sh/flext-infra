"""FLEXT infrastructure check services."""

from __future__ import annotations

from flext_infra import m
from flext_infra.check.fix_pyrefly_config import FlextInfraConfigFixer
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker, run_cli

type CheckIssue = m.Infra.Check.Issue
type GateExecution = m.Infra.Check.GateExecution
type ProjectResult = m.Infra.Check.ProjectResult

__all__ = [
    "CheckIssue",
    "FlextInfraConfigFixer",
    "FlextInfraWorkspaceChecker",
    "GateExecution",
    "ProjectResult",
    "run_cli",
]
