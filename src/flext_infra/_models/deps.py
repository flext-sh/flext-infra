"""Domain models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import p, t
from flext_infra._models import (
    FlextInfraModelsDepsToml,
    FlextInfraModelsDepsToolConfig,
    FlextInfraModelsMixins,
    FlextInfraModelsWorkspace,
)
from flext_infra._models._config import (
    FlextInfraConfigModelsRepository,
    FlextInfraConfigModelsScaffold,
)

GitSourceUrlPrefixField = Annotated[
    t.NonEmptyStr | None,
    m.Field(
        alias="git-source-url-prefix",
        description="Explicit Git source URL scope",
    ),
]
GitSourceRefFromField = Annotated[
    t.NonEmptyStr | None,
    m.Field(alias="git-source-ref-from", description="Explicit reference to migrate"),
]
GitSourceRefToField = Annotated[
    t.NonEmptyStr | None,
    m.Field(alias="git-source-ref-to", description="Replacement Git reference"),
]


class FlextInfraModelsDeps(
    FlextInfraModelsDepsToolConfig,
    FlextInfraModelsDepsToml,
):
    """Models for dependency detection and modernization reporting."""

    class RequirementsProvenance(m.ImmutableValueModel):
        """Workspace provenance consulted while canonicalizing requirement lines."""

        declared_sources: t.StrMapping = m.Field(
            description="Declared member Git origins"
        )
        candidate_sources: t.StrMapping = m.Field(
            description="Selected candidate Git origins"
        )
        native_sources: t.StrSequence = m.Field(
            default=(), description="Names with explicit native UV source declarations"
        )

    class ProjectPackagingDeclaration(m.ContractModel):
        """Native packaging facts retained independently of Python export health."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="ignore",
            frozen=True,
            populate_by_name=True,
        )
        uv_package: Annotated[
            bool | None,
            m.Field(
                validation_alias=m.AliasPath("tool", "uv", "package"),
                description="Explicit native UV package participation declaration",
            ),
        ] = None
        build_backend: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                validation_alias=m.AliasPath("build-system", "build-backend"),
                description="Declared native Python build backend",
            ),
        ] = None

    class ProjectMetadataState(m.ArbitraryTypesModel):
        """One TOML ingress retaining metadata and its native packaging declaration."""

        metadata: Annotated[
            p.ProjectMetadata,
            m.Field(description="Original canonical PEP 621 and FLEXT metadata"),
        ]
        packaging: Annotated[
            FlextInfraModelsDeps.ProjectPackagingDeclaration,
            m.Field(description="Packaging facts from the same parsed document"),
        ]

    class RuntimeDependencyProvider(m.Value):
        """One imported package associated with an authenticated locked supplier."""

        modules: Annotated[
            t.StrTuple,
            m.Field(
                min_length=1,
                description="Native import identities supplied by metadata",
            ),
        ]
        package: Annotated[
            FlextInfraModelsWorkspace.LockedPackage,
            m.Field(description="Exact package selected by the target's native lock"),
        ]
        requirement: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Target-qualified PEP 508 requirement retaining its source"
            ),
        ]
        inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                min_length=1, description="Authenticated distribution metadata states"
            ),
        ]

    class RuntimeDependencyInputs(m.Value):
        """Interpreter, lock and import-provider proof injected by the owner."""

        target_root: Annotated[Path, m.Field(description="Selected repository root")]
        python: Annotated[Path, m.Field(description="Elected consumer interpreter")]
        lock: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Captured native UV lock of the selected runtime"),
        ]
        providers: Annotated[
            t.VariadicTuple[FlextInfraModelsDeps.RuntimeDependencyProvider],
            m.Field(description="All matching suppliers; ambiguity is preserved"),
        ]
        development_only: Annotated[
            t.StrTuple,
            m.Field(description="Contract-owned requirements forbidden in runtime"),
        ]
        invoked_executables: Annotated[
            t.StrTuple,
            m.Field(
                description=(
                    "Canonical unimported requirements whose installed console "
                    "scripts the project's own files invoke"
                ),
            ),
        ]
        inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                min_length=1,
                description="Native lock and production-source input states",
            ),
        ]

    class RuntimeDependencyPlan(m.Value):
        """Calculated target requirements and unchanged diagnostic identities."""

        source: Annotated[
            t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
            m.Field(
                min_length=1,
                description="Production trees establishing applicability",
            ),
        ]
        before: Annotated[
            m.Cli.AtomicFileState,
            m.Field(
                description="Authenticated pyproject state consumed by native deptry"
            ),
        ]
        dependencies: Annotated[
            t.StrTuple,
            m.Field(
                description="Calculated runtime requirements, including marker variants"
            ),
        ]
        unresolved_modules: Annotated[
            t.StrTuple,
            m.Field(description="Missing or ambiguous import suppliers remaining red"),
        ]
        inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                description="Every metadata, lock and source state backing this plan"
            ),
        ]

    class DependencyMarkerEnvironment(m.Value):
        """Complete PEP 508 facts reported by the consumer interpreter."""

        prefix: Annotated[
            Path,
            m.Field(
                exclude=True,
                description="Consumer interpreter environment prefix",
            ),
        ]
        implementation_name: Annotated[
            str,
            m.Field(description="PEP 508 implementation name"),
        ]
        implementation_version: Annotated[
            str,
            m.Field(description="PEP 508 implementation version"),
        ]
        os_name: Annotated[str, m.Field(description="PEP 508 operating system name")]
        platform_machine: Annotated[
            str,
            m.Field(description="PEP 508 machine architecture"),
        ]
        platform_release: Annotated[
            str,
            m.Field(description="PEP 508 platform release"),
        ]
        platform_system: Annotated[str, m.Field(description="PEP 508 platform system")]
        platform_version: Annotated[
            str,
            m.Field(description="PEP 508 platform version"),
        ]
        platform_python_implementation: Annotated[
            str,
            m.Field(description="PEP 508 Python implementation"),
        ]
        python_full_version: Annotated[
            str,
            m.Field(description="PEP 508 complete Python version"),
        ]
        python_version: Annotated[
            str,
            m.Field(description="PEP 508 Python major and minor version"),
        ]
        sys_platform: Annotated[
            str,
            m.Field(description="PEP 508 interpreter platform"),
        ]

    class DetectCommand(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra deps detect``.

        Inherits ``apply``/``dry_run``, ``repository_root``, ``projects``,
        ``verbose`` from ``WriteMixin``.
        """

        output_format: Annotated[
            str,
            m.Field(alias="format", description="Output format for dependency report"),
        ] = "text"
        output: Annotated[
            str | None,
            m.Field(None, description="Optional output report path"),
        ] = None
        quiet: Annotated[
            bool,
            m.Field(default=False, description="Reduce command output"),
        ] = False
        no_fail: Annotated[
            bool,
            m.Field(
                alias="no-fail",
                description="Exit successfully even when issues are found",
            ),
        ] = False
        no_pip_check: Annotated[
            bool,
            m.Field(alias="no-pip-check", description="Skip workspace pip check"),
        ] = False

        @property
        def output_path(self) -> Path | None:
            """Resolved explicit output path when provided."""
            if self.output is None:
                return None
            return Path(self.output).expanduser().resolve()

    class GitSourceReferenceMigration(m.ContractModel):
        """Explicit source scope and reference transition; no source conversion."""

        url_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^https://[^/?#]+/[^?#]+/$",
                description=(
                    "Canonical Git URL directory prefix selecting dependency sources"
                ),
            ),
        ]
        source_ref: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[^\s@#;]+$",
                description="Only this existing explicit Git reference may change",
            ),
        ]
        target_ref: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[^\s@#;]+$",
                description="Operator-declared replacement Git reference",
            ),
        ]

    class PyprojectDocumentState(m.ArbitraryTypesModel):
        """Centralized normalized TOML state reused across deps workflows.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(validate_default=False)

        pyproject_path: Annotated[Path, m.Field(description="Resolved pyproject path")]
        original_rendered: Annotated[
            str,
            m.Field(description="Original TOML source text"),
        ] = ""
        rendered: Annotated[
            str,
            m.Field(description="Canonical rendered TOML source text"),
        ] = ""
        payload: Annotated[
            t.MutableJsonMapping,
            m.Field(description="Validated plain TOML payload"),
        ] = m.Field(default_factory=dict[str, t.JsonValue])
        document: Annotated[
            t.Cli.TomlDocument | None,
            m.Field(
                default=None,
                exclude=True,
                description=(
                    "Original parsed TOML tree retaining authored layout and comments"
                ),
            ),
        ] = None

    class PackagedDataSelection(m.ContractModel):
        """Validated data inputs separated by Hatch selection semantics."""

        files: Annotated[
            t.StrTuple,
            m.Field(description="Explicit data files included individually"),
        ] = ()
        directories: Annotated[
            t.StrTuple,
            m.Field(description="Data directories selected with VCS filters"),
        ] = ()

    class RuffProjectFacts(m.ContractModel):
        """Measured per-project facts the canonical Ruff phase derives from."""

        first_party: Annotated[
            t.StrSequence,
            m.Field(description="Detected first-party namespaces"),
        ]
        analysis_exclusions: Annotated[
            t.StrSequence | None,
            m.Field(
                description=(
                    "Declared analysis exclusions; None derives workspace globs"
                ),
            ),
        ] = None
        generated_python_roots: Annotated[
            t.StrSequence,
            m.Field(description="Generated python roots to exclude"),
        ]
        repository_namespace_packages: Annotated[
            t.StrTuple,
            m.Field(description="Declared repository-root namespace packages"),
        ] = ()

    class PyprojectDeclaredTopology(m.ContractModel):
        """Project topology a caller declares instead of discovering it on disk.

        An atomic scaffold knows its shipped roots and analyzer roots before
        they exist; an empty declaration keeps filesystem discovery.
        """

        root_modules: Annotated[
            t.StrTuple,
            m.Field(description="Top-level single-file modules the package ships"),
        ] = ()
        root_packages: Annotated[
            t.StrTuple,
            m.Field(description="Top-level packages shipped beyond the primary one"),
        ] = ()
        repository_namespace_packages: Annotated[
            t.StrTuple,
            m.Field(
                description=(
                    "Implicit namespace directories shipped from the repository root"
                ),
            ),
        ] = ()
        packaged_data_paths: Annotated[
            t.StrTuple,
            m.Field(description="Repository-declared relative data paths to ship"),
        ] = ()
        packaged_data_excludes: Annotated[
            t.StrTuple,
            m.Field(
                description=(
                    "Repository-relative files omitted from declared data directories"
                ),
            ),
        ] = ()
        project_declaration_resource: Annotated[
            t.Pair[t.NonEmptyStr, t.NonEmptyStr] | None,
            m.Field(
                description=(
                    "Declared producer metadata source and wheel extra-metadata "
                    "destination"
                ),
            ),
        ] = None
        hatch_build_hook_path: Annotated[
            Path | None,
            m.Field(description="Declared project-relative Hatch build hook module"),
        ] = None
        planned_data_files: Annotated[
            t.StrTuple,
            m.Field(
                description=(
                    "Exact scaffold file destinations planned before publication"
                ),
            ),
        ] = ()
        declared_python_dirs: Annotated[
            t.StrTuple,
            m.Field(description="Python roots declared for the project"),
        ] = ()
        declared_python_dirs_are_complete: Annotated[
            bool,
            m.Field(
                description=(
                    "Declared roots are the full set; discovery must not widen it"
                ),
            ),
        ] = False
        project_kind: Annotated[
            str | None,
            m.Field(description="Declared project kind; absent classifies on demand"),
        ] = None
        analysis_exclusions: Annotated[
            t.StrTuple | None,
            m.Field(
                description=(
                    "Workspace-relative paths excluded from analysis; absent "
                    "derives them from the workspace"
                ),
            ),
        ] = None

        @m.field_validator("hatch_build_hook_path")
        @classmethod
        def _validate_hatch_build_hook_path(cls, value: Path | None) -> Path | None:
            """Validate the hook with the project declaration's canonical owner.

            Returns:
                The validated project-relative hook path.

            """
            return FlextInfraConfigModelsRepository.validated_hatch_build_hook_path(
                value
            )

    class PyprojectAnalyzerContext(m.ContractModel):
        """Placement and Python roots of one pyproject the analyzer phases conform.

        Paths are absent while an atomic scaffold renders a project that is not
        on disk yet; the declared roots then stand in for discovery.
        """

        is_root: Annotated[
            bool,
            m.Field(description="Whether the pyproject is the repository root"),
        ]
        repository_root: Annotated[
            Path | None,
            m.Field(description="Repository root on disk"),
        ] = None
        project_dir: Annotated[
            Path | None,
            m.Field(description="Project directory on disk"),
        ] = None
        declared_python_dirs: Annotated[
            t.StrTuple,
            m.Field(description="Python roots declared for the project"),
        ] = ()
        declared_python_dirs_are_complete: Annotated[
            bool,
            m.Field(
                description=(
                    "Declared roots are the full set; discovery must not widen it"
                ),
            ),
        ] = False

    class PipCheckReport(m.ArbitraryTypesModel):
        """Pip check execution report with status and output lines."""

        ok: Annotated[
            bool,
            m.Field(default=True, description="Whether pip check passed"),
        ] = True
        lines: Annotated[
            t.StrSequence,
            m.Field(description="Pip check output lines"),
        ] = ()

    class DeptryIssueGroups(m.ArbitraryTypesModel):
        """Deptry issue grouping model by error code (DEP001-DEP004)."""

        dep001: Annotated[
            t.MutableSequenceOf[t.MappingKV[str, t.Primitives | None]],
            m.Field(description="DEP001 issues"),
        ] = m.Field(default_factory=list[t.MappingKV[str, t.Primitives | None]])
        dep002: Annotated[
            t.MutableSequenceOf[t.MappingKV[str, t.Primitives | None]],
            m.Field(description="DEP002 issues"),
        ] = m.Field(default_factory=list[t.MappingKV[str, t.Primitives | None]])
        dep003: Annotated[
            t.MutableSequenceOf[t.MappingKV[str, t.Primitives | None]],
            m.Field(description="DEP003 issues"),
        ] = m.Field(default_factory=list[t.MappingKV[str, t.Primitives | None]])
        dep004: Annotated[
            t.MutableSequenceOf[t.MappingKV[str, t.Primitives | None]],
            m.Field(description="DEP004 issues"),
        ] = m.Field(default_factory=list[t.MappingKV[str, t.Primitives | None]])

    class DeptryReport(m.ArbitraryTypesModel):
        """Deptry analysis report with categorized issue modules."""

        missing: Annotated[
            t.StrSequence,
            m.Field(description="Missing dependencies"),
        ] = m.Field(default_factory=tuple)
        unused: Annotated[t.StrSequence, m.Field(description="Unused dependencies")] = (
            m.Field(default_factory=tuple)
        )
        transitive: Annotated[
            t.StrSequence,
            m.Field(description="Transitive dependencies"),
        ] = m.Field(default_factory=tuple)
        dev_in_runtime: Annotated[
            t.StrSequence,
            m.Field(description="Dev dependencies in runtime"),
        ] = m.Field(default_factory=tuple)
        raw_count: Annotated[
            t.NonNegativeInt,
            m.Field(0, description="Raw issue count"),
        ] = 0

    class ProjectDependencyReport(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Project-level dependency report combining deptry results."""

        deptry: FlextInfraModelsDeps.DeptryReport = m.Field(description="Deptry report")

    class WorkspaceDependencyReport(m.ArbitraryTypesModel):
        """Workspace-level dependency analysis report aggregating all projects.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        workspace: Annotated[str, m.Field(description="Workspace name")]
        projects: t.MutableMappingKV[
            str, FlextInfraModelsDeps.ProjectDependencyReport
        ] = m.Field(description="Per-project reports")
        pip_check: FlextInfraModelsDeps.PipCheckReport | None = m.Field(
            None,
            description="Pip check report",
            validate_default=True,
        )

    class ToolingContextRequest(m.ArbitraryTypesModel):
        """Declared inputs the modernizer resolves into a runtime context."""

        environment_dir: Annotated[
            Path,
            m.Field(
                description="Declared environment directory owned by project runtime"
            ),
        ]

        planned_sources: Annotated[
            t.MappingKV[Path, str],
            m.Field(
                exclude=True,
                description="Captured Python candidate bytes overriding disk",
            ),
        ]

        project_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Distribution name of the project"),
        ]
        package_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Importable package name of the project"),
        ]
        path: Annotated[
            Path,
            m.Field(description="Absolute path of the project's pyproject file"),
        ]
        topology: Annotated[
            FlextInfraModelsDeps.PyprojectDeclaredTopology,
            m.Field(description="Declared repository topology"),
        ]
        scaffold_project: Annotated[
            FlextInfraConfigModelsScaffold.ScaffoldProjectSpec,
            m.Field(description="Scaffold project specification"),
        ]
        runtime_dependency_overlay: Annotated[
            t.StrSequence,
            m.Field(description="Runtime dependency overlay requirement lines"),
        ]
        declared_project_dependencies: Annotated[
            t.StrSequence,
            m.Field(description="Declared project dependency requirement lines"),
        ]

        @m.field_validator("environment_dir")
        @classmethod
        def _validate_environment_dir(cls, value: Path) -> Path:
            """Require an absolute, project-owned environment directory.

            Returns:
                The validated absolute environment directory.

            Raises:
                ValueError: If the path is not absolute.

            """
            if not value.is_absolute():
                msg = "environment_dir must be an absolute path"
                raise ValueError(msg)
            return value.resolve()


__all__: list[str] = ["FlextInfraModelsDeps"]
