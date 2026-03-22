"""Protocol definitions for flext-infra utilities and services.

Defines structural contracts (runtime-checkable Protocols) for orchestration,
command execution, validation, and reporting services used across the
infrastructure layer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import JsonValue

from flext_core import FlextProtocols, r

if TYPE_CHECKING:
    from flext_infra import m, t, u


class FlextInfraProtocols(FlextProtocols):
    """Structural contracts for flext-infra utilities and services.

    All parent protocols (Result, Config, DI, Service, etc.) are inherited
    transparently from ``FlextProtocols`` via MRO. Infra-specific utility
    protocols live as nested classes below.
    """

    class Infra:
        """Infra-specific structural protocol definitions."""

        @runtime_checkable
        class ProjectInfo(Protocol):
            """Minimal project descriptor used by orchestration services."""

            @property
            def name(self) -> str:
                """Return the project name."""
                ...

            @property
            def path(self) -> Path:
                """Return the project path."""
                ...

        @runtime_checkable
        class CommandOutput(Protocol):
            """Minimal command execution output contract."""

            @property
            def exit_code(self) -> int:
                """Return the command exit code."""
                ...

            @property
            def stderr(self) -> str:
                """Return the command standard error."""
                ...

            @property
            def stdout(self) -> str:
                """Return the command standard output."""
                ...

        @runtime_checkable
        class Discovery(Protocol):
            """Contract for project discovery services."""

            def discover_projects(
                self,
                workspace_root: Path,
            ) -> r[list[m.Infra.ProjectInfo]]:
                """Discover projects in a workspace root."""
                ...

        @runtime_checkable
        class TomlReader(Protocol):
            """Contract for TOML file readers used by dependency services."""

            def read_plain(self, path: Path) -> r[t.Infra.TomlConfig]:
                """Read and parse a TOML file as a plain dict with r error handling."""
                ...

        @runtime_checkable
        class CommandRunner(Protocol):
            """Contract for command execution services."""

            def run(
                self,
                cmd: Sequence[str],
                cwd: Path | None = None,
                timeout: int | None = None,
                env: Mapping[str, str] | None = None,
            ) -> r[m.Infra.CommandOutput]:
                """Execute a command and return output."""
                ...

            def capture(
                self,
                cmd: Sequence[str],
                cwd: Path | None = None,
                timeout: int | None = None,
                env: Mapping[str, str] | None = None,
            ) -> r[str]:
                """Execute a command and return captured stdout."""
                ...

            def run_raw(
                self,
                cmd: Sequence[str],
                cwd: Path | None = None,
                timeout: int | None = None,
                env: Mapping[str, str] | None = None,
            ) -> r[m.Infra.CommandOutput]:
                """Execute a command and return raw output, including non-zero exit codes."""
                ...

            def run_checked(
                self,
                cmd: Sequence[str],
                cwd: Path | None = None,
                timeout: int | None = None,
                env: Mapping[str, str] | None = None,
            ) -> r[bool]:
                """Execute a command and return success/failure status."""
                ...

            def run_to_file(
                self,
                cmd: Sequence[str],
                output_file: Path,
                cwd: Path | None = None,
                timeout: int | None = None,
                env: Mapping[str, str] | None = None,
            ) -> r[int]:
                """Execute a command and write combined output to file."""
                ...

        @runtime_checkable
        class SafetyRunner(Protocol):
            """Protocol for command execution backends used by the safety manager."""

            def capture(
                self,
                cmd: list[str],
                cwd: Path | None = None,
                timeout: int | None = None,
            ) -> r[str]:
                """Run a command and capture its stdout."""
                ...

            def run_checked(
                self,
                cmd: list[str],
                cwd: Path | None = None,
                timeout: int | None = None,
            ) -> r[bool]:
                """Run a command and return success/failure."""
                ...

        @runtime_checkable
        class Scanner(Protocol):
            """Protocol for file scanners that detect violations."""

            def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
                """Scan a single file and return scan result."""
                ...

        class WorkspaceReport(Protocol):
            """Protocol for workspace dependency report model contract."""

            pip_check: m.Infra.PipCheckReport | None
            dependency_limits: m.Infra.DependencyLimitsInfo | None

            def model_dump(self) -> dict[str, t.Infra.InfraValue]:
                """Serialize report model payload."""
                ...

        @runtime_checkable
        class ReportingService(Protocol):
            """Service for reporting directory resolution."""

            def get_report_dir(
                self, workspace_root: Path, scope: str, verb: str
            ) -> Path:
                """Resolve report output directory for given scope and verb."""
                ...

        @runtime_checkable
        class JsonService(Protocol):
            """Service for JSON serialization and persistence."""

            def write_json(
                self,
                path: Path,
                payload: dict[str, t.Infra.InfraValue],
            ) -> r[bool]:
                """Write payload to JSON file."""
                ...

        class ProjectReportLike(Protocol):
            """Protocol for project-level dependency report contracts."""

            def model_dump(self) -> dict[str, t.Infra.InfraValue]:
                """Serialize project report payload."""
                ...

        @runtime_checkable
        class DepsService(Protocol):
            """Service for dependency detection across projects."""

            def discover_project_paths(
                self,
                workspace_root: Path,
                *,
                projects_filter: list[str] | None = None,
            ) -> r[list[Path]]:
                """Discover project paths in workspace root."""
                ...

            def run_deptry(
                self,
                project_path: Path,
                venv_bin: Path,
            ) -> r[tuple[list[t.Infra.IssueMap], int]]:
                """Run deptry on a project and return issues."""
                ...

            def build_project_report(
                self,
                project_name: str,
                deptry_issues: list[t.Infra.IssueMap],
            ) -> p.Infra.ProjectReportLike:
                """Build project report from deptry issues."""
                ...

        @runtime_checkable
        class TypingsDepsService(Protocol):
            """Service for typing-related dependency detection."""

            def load_dependency_limits(
                self,
                limits_path: Path | None = None,
            ) -> Mapping[str, t.Infra.TomlValue]:
                """Load dependency limits from TOML file."""
                ...

            def get_required_typings(
                self,
                project_path: Path,
                venv_bin: Path,
                limits_path: Path | None = None,
                *,
                include_mypy: bool = True,
            ) -> r[m.Infra.TypingsReport]:
                """Get required typing libraries for a project."""
                ...

        @runtime_checkable
        class PipCheckDepsService(Protocol):
            """Service for pip-based dependency checking."""

            def run_pip_check(
                self,
                workspace_root: Path,
                venv_bin: Path,
            ) -> r[tuple[list[str], int]]:
                """Run pip check on workspace and return results."""
                ...

        @runtime_checkable
        class RunnerService(Protocol):
            """Service for running arbitrary commands."""

            def run_raw(
                self,
                cmd: list[str],
                cwd: Path | None = None,
                timeout: int | None = None,
                env: dict[str, str] | None = None,
            ) -> r[m.Infra.CommandOutput]:
                """Run command and return raw output."""
                ...

        class DetectorRuntime(Protocol):
            """Protocol for detector runtime service dependencies."""

            reporting: p.Infra.ReportingService
            json: p.Infra.JsonService
            deps: p.Infra.DepsService
            runner: p.Infra.RunnerService
            log: p.Logger

            @staticmethod
            def parser(default_limits_path: Path) -> argparse.ArgumentParser:
                """Create argument parser for detector CLI."""
                ...

            @staticmethod
            def project_filter(cli: u.Infra.CliArgs) -> list[str] | None:
                """Resolve project filter list from parsed args."""
                ...

        class TemplateRenderer(Protocol):
            """Protocol for template rendering engines."""

            def render_all(
                self,
                config: m.Infra.BaseMkConfig | None = None,
            ) -> r[str]:
                """Render all templates with given configuration."""
                ...

        @runtime_checkable
        class RunnableDetector(Protocol):
            """Contract for detectors that can be invoked via CLI."""

            def run(self, argv: list[str] | None = None) -> r[int]:
                """Execute the detector and return an exit code."""
                ...

        @runtime_checkable
        class ImportNormalizerTransformerLike(Protocol):
            """Protocol for import normalizer transformer compatibility checking."""

            @staticmethod
            def detect_file(
                *,
                file_path: Path,
                project_package: str,
                alias_map: dict[str, tuple[str, ...]] | None = None,
            ) -> list[object]:
                """Detect import violations in a file.

                Args:
                    file_path: Path to the Python file to analyze.
                    project_package: The project package name.
                    alias_map: Optional mapping of packages to their public aliases.

                Returns:
                    List of violation objects found.

                """
                ...

        class ViolationWithLine(Protocol):
            """Protocol for violations that have a line number."""

            def model_dump(self) -> dict[str, JsonValue]:
                """Dump violation data to a dictionary."""
                ...


p = FlextInfraProtocols
__all__ = ["FlextInfraProtocols", "p"]
