# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import c, p, t


class FlextInfraProtocolsWorkspace:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class NativeImportRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path = ...
        runtime_root: Path = ...
        modules: tuple[p.Infra.SourceClassReference, ...] = ...
        import_roots: tuple[Path, ...] = ...
        source_authority: FlextInfraProtocolsWorkspace.CodegenSourceAuthority = ...
        inputs: tuple[p.Cli.AtomicFileState, ...] = ...

    @runtime_checkable
    class WorkspaceRequest(Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class WorkspaceTestsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        scope: Literal[
            c.Infra.CodegenConformScope.ALL, c.Infra.CodegenConformScope.SELF
        ] = ...

    @runtime_checkable
    class FlextEditableRequest(Protocol):
        """Structural data contract projected from the owning model."""

        flext_root: Path | None = ...
        candidate_environment: Path | None = ...

    @runtime_checkable
    class FlextEditableSelection(Protocol):
        """Structural data contract projected from the owning model."""

        flext_root: Path
        distributions: Mapping[str, Path]

    @runtime_checkable
    class WorkspaceRuntimeContext(Protocol):
        """Structural data contract projected from the owning model."""

        project_root: Path
        runtime_root: Path
        resolution_root: Path
        pyproject_path: Path
        lock_path: Path
        environment_path: Path
        standalone: bool
        installation_inputs: tuple[p.Cli.AtomicFileState, ...] = ...
        native_install_exit_code: int | None = ...

    @runtime_checkable
    class WorkspaceOperationReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        native_tool_qualifications: tuple[p.Cli.ProcessNativeToolEvidence, ...] = ...
        runtime_context: (
            FlextInfraProtocolsWorkspace.WorkspaceRuntimeContext | None
        ) = ...
        root: Path
        executed: bool
        outcome: c.Infra.ToolOutcome | None
        native_exit_code: int | None = ...
        stage: t.NonEmptyStr | None = ...
        completed: bool | None = ...
        applicability: str = ...
        files: tuple[Path, ...] = ...
        issues: tuple[p.Infra.Issue, ...] = ...

    @runtime_checkable
    class WorkspaceOperationTarget(Protocol):
        """Structural data contract projected from the owning model."""

        root: Path
        managed: bool | None = ...

    @runtime_checkable
    class WorkspaceOperationApplicability(Protocol):
        """Structural data contract projected from the owning model."""

        applicable: bool
        reason: str = ...

    @runtime_checkable
    class WorkspaceOperationReport(Protocol):
        """Structural data contract projected from the owning model."""

        root: Path
        operation: t.NonEmptyStr
        scope: tuple[Path, ...]
        receipts: tuple[FlextInfraProtocolsWorkspace.WorkspaceOperationReceipt, ...]
        candidate_read_exit_code: int | None = ...
        candidate_sha: str | None = ...

    @runtime_checkable
    class SubprojectLoadContext(Protocol):
        """Structural data contract projected from the owning model."""

        integration_branch: str
        workspace_beads: p.Infra.BeadsProjectSpec | None = ...
        allow_unprovisioned_members: bool = ...
        declared_member: p.Infra.RepositoryRef | None = ...

    @runtime_checkable
    class EnvironmentContractViolation(Protocol):
        """Structural data contract projected from the owning model."""

        message: str
        token: str = ...

    @runtime_checkable
    class WorkspaceProjectContext(Protocol):
        """Structural data contract projected from the owning model."""

        cwd: Path
        identity: p.Infra.GitIdentityReport | None = ...
        workspace: p.Infra.WorkspaceSpec | None = ...
        target: p.Infra.RepositoryConformTarget | None = ...
        governed: bool = ...
        runtime: FlextInfraProtocolsWorkspace.WorkspaceRuntimeContext | None = ...

    @runtime_checkable
    class DirectUrlDirectoryInfo(Protocol):
        """Structural data contract projected from the owning model."""

        editable: bool = ...

    @runtime_checkable
    class EditableDirectUrl(Protocol):
        """Structural data contract projected from the owning model."""

        url: t.NonEmptyStr
        dir_info: FlextInfraProtocolsWorkspace.DirectUrlDirectoryInfo

    @runtime_checkable
    class FleetPullRequest(Protocol):
        """Structural data contract projected from the owning model."""

        number: int
        head: str
        title: str
        url: str

    @runtime_checkable
    class FleetRepoGaps(Protocol):
        """Structural data contract projected from the owning model."""

        name: str
        root: Path
        present: bool
        dirty_paths: Sequence[str]
        open_pull_requests: tuple[FlextInfraProtocolsWorkspace.FleetPullRequest, ...]
        unmerged_branches: int
        lint_findings: t.NonNegativeInt | None
        pyrefly_findings: t.NonNegativeInt | None
        codemod_findings: int
        agents_doc_present: bool
        skills_stamp_present: bool
        skills_stamp_distribution_version: str
        beads_config_present: bool

    @runtime_checkable
    class FleetGapsReport(Protocol):
        """Structural data contract projected from the owning model."""

        schema_version: int
        workspace_root: Path
        workspace_name: str
        repos: tuple[FlextInfraProtocolsWorkspace.FleetRepoGaps, ...]


__all__: list[str] = [
    "FlextInfraProtocolsWorkspace",
]
