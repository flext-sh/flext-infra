"""Structural contracts for dependency-analysis collaborators.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableSequence
    from pathlib import Path

    from flext_infra import p, t


@runtime_checkable
class FlextInfraProtocolsDeps(Protocol):
    """Dependency-analysis protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class RuntimeDependencyCollector(Protocol):
        """Collect explicit target suppliers for one completed native scan."""

        def __call__(
            self,
            project_root: Path,
            scan: p.Infra.DeptryScan,
            /,
        ) -> p.Result[p.Infra.RuntimeDependencyInputs]:
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
    class DetectCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def projects(self) -> Sequence[str] | None: ...
        @property
        def verbose(self) -> bool: ...
        @property
        def apply(self) -> bool: ...
        @property
        def gates(self) -> Sequence[str]: ...
        @property
        def dry_run(self) -> bool: ...
        @property
        def output_format(self) -> str: ...
        @property
        def output(self) -> str | None: ...
        @property
        def quiet(self) -> bool: ...
        @property
        def no_fail(self) -> bool: ...
        @property
        def no_pip_check(self) -> bool: ...

    @runtime_checkable
    class GitSourceReferenceMigration(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def url_prefix(self) -> t.NonEmptyStr: ...
        @property
        def source_ref(self) -> t.NonEmptyStr: ...
        @property
        def target_ref(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class PackagedDataSelection(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def files(self) -> t.StrTuple: ...
        @property
        def directories(self) -> t.StrTuple: ...

    @runtime_checkable
    class RuffProjectFacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def first_party(self) -> Sequence[str]: ...
        @property
        def analysis_exclusions(self) -> Sequence[str] | None: ...
        @property
        def generated_python_roots(self) -> Sequence[str]: ...
        @property
        def repository_namespace_packages(self) -> t.StrTuple: ...

    @runtime_checkable
    class PyprojectDeclaredTopology(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root_modules(self) -> t.StrTuple: ...
        @property
        def root_packages(self) -> t.StrTuple: ...
        @property
        def repository_namespace_packages(self) -> t.StrTuple: ...
        @property
        def packaged_data_paths(self) -> t.StrTuple: ...
        @property
        def packaged_data_excludes(self) -> t.StrTuple: ...
        @property
        def hatch_build_hook_path(self) -> Path | None: ...
        @property
        def planned_data_files(self) -> t.StrTuple: ...
        @property
        def declared_python_dirs(self) -> t.StrTuple: ...
        @property
        def declared_python_dirs_are_complete(self) -> bool: ...
        @property
        def project_kind(self) -> str | None: ...
        @property
        def analysis_exclusions(self) -> t.StrTuple | None: ...

    @runtime_checkable
    class PyprojectAnalyzerContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def is_root(self) -> bool: ...
        @property
        def repository_root(self) -> Path | None: ...
        @property
        def project_dir(self) -> Path | None: ...
        @property
        def declared_python_dirs(self) -> t.StrTuple: ...
        @property
        def declared_python_dirs_are_complete(self) -> bool: ...

    @runtime_checkable
    class RequirementsProvenance(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def declared_sources(self) -> Mapping[str, str]: ...
        @property
        def candidate_sources(self) -> Mapping[str, str]: ...
        @property
        def native_sources(self) -> Sequence[str]: ...
        @property
        def override_references(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class ProjectPackagingDeclaration(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def uv_package(self) -> bool | None: ...
        @property
        def build_backend(self) -> t.NonEmptyStr | None: ...

    @runtime_checkable
    class ProjectMetadataState(Protocol):
        """Structural data contract projected from the owning model."""

        source: p.Cli.AtomicFileState
        metadata: p.ProjectMetadata
        packaging: p.Infra.ProjectPackagingDeclaration

    @runtime_checkable
    class RuntimeDependencyProvider(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def modules(self) -> t.StrTuple: ...
        @property
        def package(self) -> p.Infra.LockedPackage: ...
        @property
        def requirement(self) -> t.NonEmptyStr: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class RuntimeDependencyInputs(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target_root(self) -> Path: ...
        @property
        def python(self) -> Path: ...
        @property
        def lock(self) -> p.Cli.AtomicFileState: ...
        @property
        def providers(self) -> tuple[p.Infra.RuntimeDependencyProvider, ...]: ...
        @property
        def development_only(self) -> t.StrTuple: ...
        @property
        def invoked_executables(self) -> t.StrTuple: ...
        @property
        def loaded_plugins(self) -> t.StrTuple: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class RuntimeDependencyPlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> tuple[p.Cli.AtomicPhysicalTreeManifest, ...]: ...
        @property
        def before(self) -> p.Cli.AtomicFileState: ...
        @property
        def dependencies(self) -> t.StrTuple: ...
        @property
        def unresolved_modules(self) -> t.StrTuple: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class DependencyMarkerEnvironment(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def prefix(self) -> Path: ...
        @property
        def implementation_name(self) -> str: ...
        @property
        def implementation_version(self) -> str: ...
        @property
        def os_name(self) -> str: ...
        @property
        def platform_machine(self) -> str: ...
        @property
        def platform_release(self) -> str: ...
        @property
        def platform_system(self) -> str: ...
        @property
        def platform_version(self) -> str: ...
        @property
        def platform_python_implementation(self) -> str: ...
        @property
        def python_full_version(self) -> str: ...
        @property
        def python_version(self) -> str: ...
        @property
        def sys_platform(self) -> str: ...

    @runtime_checkable
    class PyprojectDocumentState(Protocol):
        """Structural data contract projected from the owning model."""

        pyproject_path: Path
        before: p.Cli.AtomicFileState | None
        original_rendered: str
        rendered: str
        payload: t.MutableJsonMapping
        document: t.Cli.TomlDocument | None

    @runtime_checkable
    class PipCheckReport(Protocol):
        """Structural data contract projected from the owning model."""

        ok: bool
        lines: Sequence[str]

    @runtime_checkable
    class DeptryIssueGroups(Protocol):
        """Structural data contract projected from the owning model."""

        dep001: MutableSequence[Mapping[str, t.Primitives | None]]
        dep002: MutableSequence[Mapping[str, t.Primitives | None]]
        dep003: MutableSequence[Mapping[str, t.Primitives | None]]
        dep004: MutableSequence[Mapping[str, t.Primitives | None]]

    @runtime_checkable
    class DeptryReport(Protocol):
        """Structural data contract projected from the owning model."""

        missing: Sequence[str]
        unused: Sequence[str]
        transitive: Sequence[str]
        dev_in_runtime: Sequence[str]
        raw_count: t.NonNegativeInt

    @runtime_checkable
    class ProjectDependencyReport(Protocol):
        """Structural data contract projected from the owning model."""

        project: t.NonEmptyStr
        deptry: p.Infra.DeptryReport

    @runtime_checkable
    class WorkspaceDependencyReport(Protocol):
        """Structural data contract projected from the owning model."""

        workspace: str
        projects: MutableMapping[str, p.Infra.ProjectDependencyReport]
        pip_check: p.Infra.PipCheckReport | None

    @runtime_checkable
    class ToolingContextRequest(Protocol):
        """Structural data contract projected from the owning model."""

        environment_dir: Path
        planned_sources: Mapping[Path, str]
        project_name: t.NonEmptyStr
        package_name: t.NonEmptyStr
        path: Path
        topology: p.Infra.PyprojectDeclaredTopology
        codegen: p.Infra.CodegenConfigSpec
        runtime_dependency_overlay: Sequence[str]
        declared_project_dependencies: Sequence[str]


__all__: list[str] = ["FlextInfraProtocolsDeps"]
