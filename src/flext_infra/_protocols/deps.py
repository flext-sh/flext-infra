"""Structural contracts for dependency-analysis collaborators.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t
from flext_infra._protocols._config import FlextInfraProtocolsConfigArtifact
from flext_infra._protocols.mixins import FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra._protocols import (
        FlextInfraProtocolsGates,
        FlextInfraProtocolsWorkspace,
    )


class FlextInfraProtocolsDeps:
    """Dependency-analysis protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class RuntimeDependencyCollector(Protocol):
        """Collect explicit target suppliers for one completed native scan."""

        def __call__(
            self,
            project_root: Path,
            scan: FlextInfraProtocolsGates.DeptryScan,
            /,
        ) -> p.Result[FlextInfraProtocolsDeps.RuntimeDependencyInputs]:
            """Return the elected lock, supplier metadata and own applicability."""
            ...

    @runtime_checkable
    class TypeCheckerPathRules(Protocol):
        """Path-rule fields every type-checker configuration declares."""

        @property
        def source_dir(self) -> str:
            """Import root the generated search paths order first."""
            ...

        @property
        def project_root(self) -> str:
            """Project-root entry the generated search paths order last."""
            ...

    @runtime_checkable
    class DetectCommand(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository root."""
            ...

        @property
        def projects(self) -> Sequence[str] | None:
            """Projects to process; repeat --projects NAME as needed."""
            ...

        @property
        def verbose(self) -> bool:
            """Verbose output."""
            ...

        @property
        def apply(self) -> bool:
            """Apply changes instead of running in dry-run mode."""
            ...

        @property
        def gates(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Gate names for post-transform validation; empty resolves the requested
            gate set from the typed Make spec at runtime.
            """
            ...

        @property
        def dry_run(self) -> bool:
            """Whether writes are disabled (inverse of apply)."""
            ...

        @property
        def output_format(self) -> str:
            """Output format for dependency report."""
            ...

        @property
        def output(self) -> str | None:
            """Optional output report path."""
            ...

        @property
        def quiet(self) -> bool:
            """Reduce command output."""
            ...

        @property
        def no_fail(self) -> bool:
            """Exit successfully even when issues are found."""
            ...

        @property
        def no_pip_check(self) -> bool:
            """Skip workspace pip check."""
            ...

        @property
        def output_path(self) -> Path | None:
            """Resolved explicit output path when provided."""
            ...

    @runtime_checkable
    class GitSourceReferenceMigration(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def url_prefix(self) -> t.NonEmptyStr:
            """Canonical Git URL directory prefix selecting dependency sources."""
            ...

        @property
        def source_ref(self) -> t.NonEmptyStr:
            """Only this existing explicit Git reference may change."""
            ...

        @property
        def target_ref(self) -> t.NonEmptyStr:
            """Operator-declared replacement Git reference."""
            ...

    @runtime_checkable
    class PackagedDataSelection(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def files(self) -> t.StrTuple:
            """Explicit data files included individually."""
            ...

        @property
        def directories(self) -> t.StrTuple:
            """Data directories selected with VCS filters."""
            ...

    @runtime_checkable
    class RuffProjectFacts(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def first_party(self) -> Sequence[str]:
            """Detected first-party namespaces."""
            ...

        @property
        def analysis_exclusions(self) -> Sequence[str] | None:
            """Declared analysis exclusions; None derives workspace globs."""
            ...

        @property
        def generated_python_roots(self) -> Sequence[str]:
            """Generated python roots to exclude."""
            ...

        @property
        def repository_namespace_packages(self) -> t.StrTuple:
            """Declared repository-root namespace packages."""
            ...

    @runtime_checkable
    class PyprojectDeclaredTopology(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root_modules(self) -> t.StrTuple:
            """Top-level single-file modules the package ships."""
            ...

        @property
        def root_packages(self) -> t.StrTuple:
            """Top-level packages shipped beyond the primary one."""
            ...

        @property
        def repository_namespace_packages(self) -> t.StrTuple:
            """Implicit namespace directories shipped from the repository root."""
            ...

        @property
        def packaged_data_paths(self) -> t.StrTuple:
            """Repository-declared relative data paths to ship."""
            ...

        @property
        def packaged_data_excludes(self) -> t.StrTuple:
            """Repository-relative files omitted from declared data directories."""
            ...

        @property
        def hatch_build_hook_path(self) -> Path | None:
            """Declared project-relative Hatch build hook module."""
            ...

        @property
        def planned_data_files(self) -> t.StrTuple:
            """Exact scaffold file destinations planned before publication."""
            ...

        @property
        def declared_python_dirs(self) -> t.StrTuple:
            """Python roots declared for the project."""
            ...

        @property
        def declared_python_dirs_are_complete(self) -> bool:
            """Declared roots are the full set; discovery must not widen it."""
            ...

        @property
        def project_kind(self) -> str | None:
            """Declared project kind; absent classifies on demand."""
            ...

        @property
        def analysis_exclusions(self) -> t.StrTuple | None:
            """Structural member projected from the owning model.

            Workspace-relative paths excluded from analysis; absent derives them
            from the workspace.
            """
            ...

    @runtime_checkable
    class PyprojectAnalyzerContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def is_root(self) -> bool:
            """Whether the pyproject is the repository root."""
            ...

        @property
        def repository_root(self) -> Path | None:
            """Repository root on disk."""
            ...

        @property
        def project_dir(self) -> Path | None:
            """Project directory on disk."""
            ...

        @property
        def declared_python_dirs(self) -> t.StrTuple:
            """Python roots declared for the project."""
            ...

        @property
        def declared_python_dirs_are_complete(self) -> bool:
            """Declared roots are the full set; discovery must not widen it."""
            ...

    @runtime_checkable
    class RequirementsProvenance(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def declared_sources(self) -> Mapping[str, str]:
            """Declared member Git origins."""
            ...

        @property
        def candidate_sources(self) -> Mapping[str, str]:
            """Selected candidate Git origins."""
            ...

        @property
        def native_sources(self) -> Sequence[str]:
            """Names with explicit native UV source declarations."""
            ...

        @property
        def override_references(self) -> Mapping[str, str]:
            """Structural member projected from the owning model.

            Direct reference each declared UV override elects, by canonical name;
            every requirement line of that name carries exactly it.
            """
            ...

    @runtime_checkable
    class ProjectPackagingDeclaration(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def uv_package(self) -> bool | None:
            """Explicit native UV package participation declaration."""
            ...

        @property
        def build_backend(self) -> t.NonEmptyStr | None:
            """Declared native Python build backend."""
            ...

    @runtime_checkable
    class ProjectMetadataState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> p.Cli.AtomicFileState:
            """Original TOML observation parsed here."""
            ...

        metadata: p.ProjectMetadata

        @property
        def packaging(self) -> FlextInfraProtocolsDeps.ProjectPackagingDeclaration:
            """Packaging facts from the same parsed document."""
            ...

    @runtime_checkable
    class RuntimeDependencyProvider(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def modules(self) -> t.StrTuple:
            """Native import identities supplied by metadata."""
            ...

        @property
        def package(self) -> FlextInfraProtocolsWorkspace.LockedPackage:
            """Exact package selected by the target's native lock."""
            ...

        @property
        def requirement(self) -> t.NonEmptyStr:
            """Target-qualified PEP 508 requirement retaining its source."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Authenticated distribution metadata states."""
            ...

    @runtime_checkable
    class RuntimeDependencyInputs(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target_root(self) -> Path:
            """Selected repository root."""
            ...

        @property
        def python(self) -> Path:
            """Elected consumer interpreter."""
            ...

        @property
        def lock(self) -> p.Cli.AtomicFileState:
            """Captured native UV lock of the selected runtime."""
            ...

        @property
        def providers(
            self,
        ) -> tuple[FlextInfraProtocolsDeps.RuntimeDependencyProvider, ...]:
            """All matching suppliers; ambiguity is preserved."""
            ...

        @property
        def development_only(self) -> t.StrTuple:
            """Contract-owned requirements forbidden in runtime."""
            ...

        @property
        def invoked_executables(self) -> t.StrTuple:
            """Structural member projected from the owning model.

            Canonical unimported requirements whose installed console scripts the
            project's own files invoke.
            """
            ...

        @property
        def loaded_plugins(self) -> t.StrTuple:
            """Structural member projected from the owning model.

            Canonical unimported requirements whose installed distribution registers
            a pytest plugin entry point, which pytest autoloads.
            """
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Native lock and production-source input states."""
            ...

    @runtime_checkable
    class RuntimeDependencyPlan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> tuple[p.Cli.AtomicPhysicalTreeManifest, ...]:
            """Production trees establishing applicability."""
            ...

        @property
        def before(self) -> p.Cli.AtomicFileState:
            """Authenticated pyproject state consumed by native deptry."""
            ...

        @property
        def dependencies(self) -> t.StrTuple:
            """Calculated runtime requirements, including marker variants."""
            ...

        @property
        def unresolved_modules(self) -> t.StrTuple:
            """Missing or ambiguous import suppliers remaining red."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Every metadata, lock and source state backing this plan."""
            ...

    @runtime_checkable
    class DependencyMarkerEnvironment(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def prefix(self) -> Path:
            """Consumer interpreter environment prefix."""
            ...

        @property
        def implementation_name(self) -> str:
            """PEP 508 implementation name."""
            ...

        @property
        def implementation_version(self) -> str:
            """PEP 508 implementation version."""
            ...

        @property
        def os_name(self) -> str:
            """PEP 508 operating system name."""
            ...

        @property
        def platform_machine(self) -> str:
            """PEP 508 machine architecture."""
            ...

        @property
        def platform_release(self) -> str:
            """PEP 508 platform release."""
            ...

        @property
        def platform_system(self) -> str:
            """PEP 508 platform system."""
            ...

        @property
        def platform_version(self) -> str:
            """PEP 508 platform version."""
            ...

        @property
        def platform_python_implementation(self) -> str:
            """PEP 508 Python implementation."""
            ...

        @property
        def python_full_version(self) -> str:
            """PEP 508 complete Python version."""
            ...

        @property
        def python_version(self) -> str:
            """PEP 508 Python major and minor version."""
            ...

        @property
        def sys_platform(self) -> str:
            """PEP 508 interpreter platform."""
            ...

    @runtime_checkable
    class PyprojectDocumentState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        pyproject_path: Path

        @property
        def before(self) -> p.Cli.AtomicFileState | None:
            """Original physical read; absent for pure source rendering."""
            ...

        original_rendered: str
        rendered: str
        payload: t.MutableJsonMapping
        document: t.Cli.TomlDocument | None

    @runtime_checkable
    class PipCheckReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        ok: bool
        lines: Sequence[str]

    @runtime_checkable
    class DeptryIssueGroups(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        dep001: MutableSequence[Mapping[str, t.Primitives | None]]
        dep002: MutableSequence[Mapping[str, t.Primitives | None]]
        dep003: MutableSequence[Mapping[str, t.Primitives | None]]
        dep004: MutableSequence[Mapping[str, t.Primitives | None]]

    @runtime_checkable
    class DeptryReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        missing: Sequence[str]
        unused: Sequence[str]
        transitive: Sequence[str]
        dev_in_runtime: Sequence[str]
        raw_count: t.NonNegativeInt

    @runtime_checkable
    class ProjectDependencyReport(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def deptry(self) -> FlextInfraProtocolsDeps.DeptryReport:
            """Deptry report."""
            ...

    @runtime_checkable
    class WorkspaceDependencyReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        workspace: str

        @property
        def projects(
            self,
        ) -> Mapping[str, FlextInfraProtocolsDeps.ProjectDependencyReport]:
            """Per-project reports."""
            ...

        @property
        def pip_check(self) -> FlextInfraProtocolsDeps.PipCheckReport | None:
            """Pip check report."""
            ...

    @runtime_checkable
    class ToolingContextRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        environment_dir: Path
        planned_sources: Mapping[Path, str]
        project_name: t.NonEmptyStr
        package_name: t.NonEmptyStr | None
        path: Path

        @property
        def topology(self) -> FlextInfraProtocolsDeps.PyprojectDeclaredTopology:
            """Declared repository topology."""
            ...

        @property
        def codegen(self) -> FlextInfraProtocolsConfigArtifact.CodegenConfigSpec:
            """Elected effective target codegen policy."""
            ...

        runtime_dependency_overlay: Sequence[str]
        declared_project_dependencies: Sequence[str]

    @runtime_checkable
    class UpgBounds(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def floors(self) -> Sequence[t.NonEmptyStr]:
            """Distributions whose >= floor upg writes."""
            ...

        @property
        def pins(self) -> Sequence[t.NonEmptyStr]:
            """Distributions whose == pin upg writes."""
            ...


__all__: list[str] = ["FlextInfraProtocolsDeps"]
