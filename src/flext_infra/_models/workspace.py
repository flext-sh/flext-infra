"""Domain models for the workspace subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u
from typing_extensions import TypeForm

from flext_infra import c, p, t
from flext_infra._models import (
    FlextInfraModelsBase,
    FlextInfraModelsCheck,
    FlextInfraModelsMixins,
    FlextInfraModelsRope,
)
from flext_infra._models._config import (
    FlextInfraConfigModels,
    FlextInfraConfigModelsContexts,
)
from flext_infra._models._git import FlextInfraModelsGitIdentity


class FlextInfraModelsWorkspace:
    """Models for workspace discovery and orchestration.

    Canonical base policy:
    - ``ArbitraryTypesModel`` for mutable discovery payloads.
    - ``ContractModel`` reserved for immutable workspace settings contracts.
    """

    class CodegenSourceAuthority(m.Value):
        """Cold reference authority has no project publication capability."""

        runtime: Path = m.Field(description="Authenticated native interpreter")
        optimize: int = m.Field(ge=0, le=2, description="Native compiler optimization")
        inputs: t.VariadicTuple[m.Cli.AtomicFileReceipt] = m.Field(
            description="Pinned source/resource/distribution/runtime byte identities"
        )
        bootstrap_sources: t.VariadicTuple[m.Cli.AtomicFileState] = m.Field(
            default=(),
            description=(
                "Original buffered source candidates for atomic-reader bootstrap; "
                "only consumed candidates enter the sealed native reference"
            ),
        )
        _source_birth: t.Pair[int, str] | None = m.PrivateAttr(default=None)
        generator_trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest] = m.Field(
            description="Authenticated physical producer membership"
        )
        generator_modules: t.VariadicTuple[t.Pair[str, Path]] = m.Field(
            description="Cold-elected physical producer namespaces"
        )
        selections: t.VariadicTuple[FlextInfraModelsRope.SourceClassReference] = (
            m.Field(
                min_length=1,
                description="Portable entrypoint, receiver and explicitly "
                "wired port roots",
            )
        )
        generator_reference: FlextInfraModelsWorkspace.NativeImportReference | None = (
            m.Field(
                default=None,
                description="Shared native epoch; cold authority carries none",
            )
        )

    class NativeCodeEvidence(m.Value):
        """Complete compiler bytes or an explicit nonportable-constant refusal."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            strict=True,
            ser_json_bytes="base64",
            val_json_bytes="base64",
        )

        filename: str = m.Field(description="Actual relocated compiler filename")
        name: str = m.Field(description="Native code-unit name")
        firstlineno: int = m.Field(description="Actual compiler starting line")
        witness: Annotated[bytes, m.Field(min_length=1)] | None = m.Field(
            description="Complete native compiler witness, never deserialized"
        )
        locations: t.VariadicTuple[t.JsonValue] | None = m.Field(
            description="Flat root and nested compiler locations"
        )
        nonportable_constants: t.VariadicTuple[t.Pair[t.VariadicTuple[int], str]] = (
            m.Field(
                description="Constant paths and native types requiring identity "
                "or containing NaN"
            )
        )

        @m.model_validator(mode="after")
        def _require_complete_witness_or_refusal(self) -> Self:
            """Require either complete compiler evidence or explicit rejection.

            Returns:
                The coherent compiler observation.

            Raises:
                ValueError: Witness bytes and constant eligibility disagree.

            """
            if bool(self.nonportable_constants) != (self.witness is None):
                message = "native code witness and constant eligibility disagree"
                raise ValueError(message)
            if (self.locations is None) != (self.witness is None):
                message = "native code witness requires complete compiler locations"
                raise ValueError(message)
            return self

    class NativeBindingEvidence(m.Value):
        """Static binding and strict native executable transport."""

        binding: str = m.Field(
            description="Root anchors, identity nodes and labeled native edges"
        )
        kind: str = m.Field(description="Observed native descriptor category")
        supplier: str = m.Field(description="Actual defining module")
        name: str = m.Field(description="Advertised native name")
        qualname: str = m.Field(description="Advertised qualified name")
        code: str | None = m.Field(
            default=None,
            description="Validated JSON compiler witness or explicit "
            "nonportable-constant refusal",
        )
        operands: t.VariadicTuple[t.Pair[str, str]] = m.Field(
            default=(),
            description="Static executable links and native declaration inputs",
        )
        operational: t.VariadicTuple[t.Pair[str, str]] = m.Field(
            default=(),
            description="Observable native cache state kept separate from "
            "executable links",
        )

    class NativeObservationContext(m.ArbitraryTypesModel):
        """Mutable native observations owned by one source-capture invocation."""

        paths: t.VariadicTuple[t.Pair[Path, Path]] = m.Field(
            description="Physical source relocation pairs for this observation",
        )
        origins: t.MutableMappingKV[str, Path] = m.Field(
            default_factory=u.empty(TypeForm(t.MutableMappingKV[str, Path])),
            description="Native module source elections observed during this capture",
        )
        module_anchors: t.MutableMappingKV[str, t.Infra.NativeOperand] = m.Field(
            default_factory=u.empty(
                TypeForm(t.MutableMappingKV[str, t.Infra.NativeOperand])
            ),
            description="Strong native identities of elected module anchors",
        )
        sources: t.Infra.MutableSetOf[t.Triple[str, str, str]] = m.Field(
            default_factory=u.empty(
                TypeForm(t.Infra.MutableSetOf[t.Triple[str, str, str]])
            ),
            description="Observed suppliers and physical declaration sources",
        )
        evidence: t.MutableSequenceOf[
            FlextInfraModelsWorkspace.NativeBindingEvidence
        ] = m.Field(
            default_factory=list,
            validate_default=True,
            description="Ordered native binding and executable observations",
        )
        generated_owners: t.MutableMappingKV[
            int, t.Triple[str, str, p.AttributeProbe | None]
        ] = m.Field(
            default_factory=u.empty(
                TypeForm(
                    t.MutableMappingKV[int, t.Triple[str, str, p.AttributeProbe | None]]
                )
            ),
            description="Strongly retained generated function source receivers",
        )
        references: t.MutableSequenceOf[t.Pair[str, t.Infra.NativeOperand]] = m.Field(
            default_factory=u.empty(
                TypeForm(t.MutableSequenceOf[t.Pair[str, t.Infra.NativeOperand]])
            ),
            description="Native operand registrations awaiting graph traversal",
        )
        pending: t.MutableSequenceOf[
            t.Quint[
                str,
                t.Infra.NativeOperand,
                str,
                str,
                Literal["execution", "storage_type"],
            ]
        ] = m.Field(
            default_factory=u.empty(
                TypeForm(
                    t.MutableSequenceOf[
                        t.Quint[
                            str,
                            t.Infra.NativeOperand,
                            str,
                            str,
                            Literal["execution", "storage_type"],
                        ]
                    ]
                )
            ),
            description="Ordered native graph work awaiting first-identity admission",
        )
        expanded_classes: t.Infra.MutableSetOf[int] = m.Field(
            default_factory=u.empty(TypeForm(t.Infra.MutableSetOf[int])),
            description="Strongly retained classes whose executable "
            "children were queued",
        )
        role: Literal["execution", "storage_type"] = m.Field(
            default="execution",
            description="The current edge consumes execution "
            "or existing instance storage",
        )
        compiled: t.MutableMappingKV[Path, t.Infra.NativeClassDeclarations] = m.Field(
            default_factory=u.empty(
                TypeForm(t.MutableMappingKV[Path, t.Infra.NativeClassDeclarations])
            ),
            description="Immutable class compiler facts within this observation",
        )
        lexical: bool = m.Field(
            default=False,
            description="Whether the validated nominations select lexical bindings",
        )
        binding_context: str = m.Field(
            default="",
            description="Current native edge and identity labels for diagnostics",
        )
        incoming: str = m.Field(
            default="",
            description="Actual labeled native edge currently being observed",
        )
        binding: str = m.Field(
            default="",
            description="Actual first-visited identity node currently being observed",
        )
        supplier: str = m.Field(
            default="",
            description="Supplier carried by the actual pending native edge",
        )
        owner_source: str = m.Field(
            default="",
            description="Physical owner source carried by the actual pending edge",
        )
        visited: t.MutableMappingKV[int, t.Pair[t.Infra.NativeOperand, str]] = m.Field(
            default_factory=u.empty(
                TypeForm(t.MutableMappingKV[int, t.Pair[t.Infra.NativeOperand, str]])
            ),
            description="Strong exact identities in original first-visit order",
        )
        edges: t.MutableMappingKV[str, str] = m.Field(
            default_factory=u.empty(TypeForm(t.MutableMappingKV[str, str])),
            description="Already observed edge-to-native-node identities",
        )
        absent_edges: t.Infra.MutableSetOf[str] = m.Field(
            default_factory=u.empty(TypeForm(t.Infra.MutableSetOf[str])),
            description="Actual lexical bindings observed as absent",
        )

    class NativeFunctionObservationContext(m.ArbitraryTypesModel):
        """Source-elected function facts within one native graph observation."""

        value: tuple[t.Infra.NativeFunction] = m.Field(
            description="One exact native function retained without model binding",
        )
        code: t.Infra.NativeCode = m.Field(
            description="Native executable code after the declared source relocation",
        )
        supplier: str = m.Field(description="The actual defining native module")
        origin: Path = m.Field(description="The elected physical supplier source")
        generated: bool = m.Field(
            description="Whether code was emitted during the real native import",
        )
        generated_operands: t.VariadicTuple[t.Pair[str, str]] = m.Field(
            description="Actual generated binding and receiver identities",
        )
        nonlocals: t.MutableMappingKV[str, t.Infra.NativeOperand] = m.Field(
            default_factory=u.empty(
                TypeForm(t.MutableMappingKV[str, t.Infra.NativeOperand])
            ),
            description="Actual closure cell values in native free-variable order",
        )
        global_bindings: t.MutableMappingKV[str, t.Infra.NativeOperand] = m.Field(
            default_factory=u.empty(
                TypeForm(t.MutableMappingKV[str, t.Infra.NativeOperand])
            ),
            description="Actual globals selected by native LOAD_GLOBAL instructions",
        )
        operational_globals: frozenset[str] = m.Field(
            default_factory=u.empty(TypeForm(frozenset[str])),
            description="Global names written by the authenticated native code units",
        )

    class NativeImportObservation(m.Value):
        """Static physical and executable observations without publication authority."""

        runtime: Path = m.Field(description="Exact observed native interpreter")
        runtime_prefix: Path = m.Field(description="Physical interpreter environment")
        modules: t.VariadicTuple[FlextInfraModelsRope.SourceClassReference] = m.Field(
            min_length=1,
            description="Selected modules and native lexical binding paths",
        )
        sources: t.VariadicTuple[t.Triple[str, str, str]] = m.Field(
            description="Physical supplier and generated declaration origins",
        )
        bindings: t.VariadicTuple[FlextInfraModelsWorkspace.NativeBindingEvidence] = (
            m.Field(description="Complete static native binding observations")
        )
        executed_sources: t.VariadicTuple[m.Cli.AtomicFileReceipt] = m.Field(
            default=(),
            description="Sources authenticated before compilation in the cold import",
        )
        _import_birth: t.Pair[int, str] | None = m.PrivateAttr(default=None)

    class NativeImportReference(NativeImportObservation):
        """One loaded epoch authenticated against its cold physical source."""

        source_authority: FlextInfraModelsWorkspace.CodegenSourceAuthority = m.Field(
            description="Cold authority pinned by the capture call",
        )
        _native_birth: t.Pair[int, str] | None = m.PrivateAttr(default=None)

    class NativeImportRequest(
        FlextInfraModelsBase.FrozenArbitrary, strict=True, validate_default=True
    ):
        """Loaded producer identities and pinned inputs for source authentication."""

        repository_root: Path = m.Field(
            description="Declared workspace whose unchanged source view is consumed",
        )
        runtime_root: Path = m.Field(
            description="Declared resolution owner of the elected physical runtime",
        )
        modules: t.VariadicTuple[FlextInfraModelsRope.SourceClassReference] = m.Field(
            min_length=1,
            description="Source-owned module/binding selections for this epoch",
        )
        import_roots: t.VariadicTuple[Path] = m.Field(
            description="Physical import roots carrying the elected producer sources",
        )
        source_authority: FlextInfraModelsWorkspace.CodegenSourceAuthority = m.Field(
            description="Cold authority for reference consumption, not publication",
        )
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = m.Field(
            description="Pinned source inputs checked before and after authentication",
            exclude=True,
        )

    class WorkspaceRequest(
        FlextInfraModelsMixins.RepositoryRootPathMixin, m.ContractModel
    ):
        """One explicit repository target for read-only workspace operations."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(populate_by_name=True)

    class LifecycleFileObservation(m.ContractModel):
        """Bounded physical file evidence without retaining source contents."""

        path: Annotated[Path, m.Field(description="Observed physical leaf")]
        sha256: Annotated[
            str | None,
            m.Field(description="Byte digest; absent for an absent leaf"),
        ]
        mode: Annotated[int | None, m.Field(description="Observed permission mode")]
        size: Annotated[int, m.Field(ge=0, description="Observed byte count")]

    class LifecycleReceipt(m.ContractModel):
        """One public Make invocation; an absent outcome is never a green receipt."""

        command: Annotated[
            t.VariadicTuple[str], m.Field(description="Public Make argv")
        ]
        cwd: Annotated[Path, m.Field(description="Repository execution directory")]
        output_file: Annotated[
            Path,
            m.Field(description="Durable combined stdout/stderr for reached steps"),
        ]
        outcome: Annotated[
            m.Cli.ProcessOutcome | None,
            m.Field(
                description=(
                    "Original reaped process outcome; absent when unreached or "
                    "launch failed"
                )
            ),
        ] = None
        error: Annotated[
            str | None, m.Field(description="First execution failure, if observed")
        ] = None
        repository_root: Annotated[
            Path | None, m.Field(description="Repository whose public Makefile ran")
        ] = None
        environment_root: Annotated[
            Path | None,
            m.Field(description="Target environment resolved by canonical ownership"),
        ] = None
        before_files: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.LifecycleFileObservation],
            m.Field(description="Config-declared file observations before execution"),
        ] = ()
        after_files: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.LifecycleFileObservation],
            m.Field(description="Same bounded file observations after execution"),
        ] = ()
        elapsed_seconds: Annotated[
            float | None, m.Field(ge=0, description="Measured invocation wall time")
        ] = None
        applicable: Annotated[
            bool | None,
            m.Field(
                description="Observed applicability; absent for unreached commands"
            ),
        ] = None
        applicability_reason: Annotated[
            str | None,
            m.Field(description="Observed reason a dependency stays a library"),
        ] = None
        execution_context: Annotated[
            t.Infra.LifecycleContext | None,
            m.Field(
                description="Declared lifecycle context, absent for other receipts"
            ),
        ] = None

    class LifecycleReport(m.ContractModel):
        """Complete declared scope and ordered reached/unreached lifecycle receipts."""

        workspace_root: Annotated[Path, m.Field(description="Invoking workspace root")]
        scope: Annotated[t.VariadicTuple[Path], m.Field(description="Governed roots")]
        observed_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Root-effective declared file observation scope"),
        ] = ()
        receipts: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.LifecycleReceipt],
            m.Field(description="Ordered public command receipts for the entire scope"),
        ]

        @m.computed_field
        @property
        def executed_commands(self) -> int:
            """Count only commands with a reaped native process outcome."""
            return sum(receipt.outcome is not None for receipt in self.receipts)

        @m.computed_field
        @property
        def failed_commands(self) -> int:
            """Count causal execution or precondition failures."""
            return sum(receipt.error is not None for receipt in self.receipts)

        @m.computed_field
        @property
        def inapplicable_commands(self) -> int:
            """Count explicit applicability decisions, never inferred passes."""
            return sum(receipt.applicable is False for receipt in self.receipts)

        @m.computed_field
        @property
        def unreached_commands(self) -> int:
            """Count required commands whose execution has not been reached."""
            return sum(
                receipt.outcome is None
                and receipt.error is None
                and receipt.applicable is not False
                for receipt in self.receipts
            )

    class WorkspaceRuntimeContext(m.ContractModel):
        """Physical runtime ownership and its selected native resolution input."""

        project_root: Annotated[
            Path, m.Field(description="Submitted Git worktree root")
        ]
        runtime_root: Annotated[Path, m.Field(description="Physical runtime owner")]
        resolution_root: Annotated[
            Path, m.Field(description="Selected native UV project")
        ]
        pyproject_path: Annotated[
            Path, m.Field(description="Selected resolution document")
        ]
        lock_path: Annotated[Path, m.Field(description="Selected immutable UV lock")]
        environment_path: Annotated[
            Path, m.Field(description="Physical shared environment")
        ]
        standalone: Annotated[
            bool,
            m.Field(
                description="Installed native resolution view; independent of "
                "later CI flags"
            ),
        ]
        installation_inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                description="Native lock and physical environment states "
                "captured after installation"
            ),
        ] = ()
        native_install_exit_code: Annotated[
            int | None,
            m.Field(
                description="Original frozen sync status; absent before installation",
                ge=0,
                le=255,
            ),
        ] = None

    class WorkspaceOperationReceipt(m.ContractModel):
        """Original in-process repository operation, with its observed effects."""

        native_tool_qualifications: Annotated[
            t.VariadicTuple[m.Cli.ProcessNativeToolEvidence],
            m.Field(description="Shared native qualification evidence."),
        ] = ()
        runtime_context: Annotated[
            FlextInfraModelsWorkspace.WorkspaceRuntimeContext | None,
            m.Field(description="Authenticated installed runtime association."),
        ] = None
        root: Annotated[Path, m.Field(description="Repository actually attempted.")]
        executed: Annotated[
            bool, m.Field(description="Original operation was invoked.")
        ]
        outcome: Annotated[
            c.Infra.ToolOutcome | None,
            m.Field(description="Native outcome, independent of report transport."),
        ]
        native_exit_code: Annotated[
            int | None,
            m.Field(ge=0, le=255, description="Observed original shell exit status."),
        ] = None
        stage: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Original bootstrap stage reached."),
        ] = None
        completed: Annotated[
            bool | None,
            m.Field(description="Whether bootstrap reached its final stage."),
        ] = None
        applicability: Annotated[
            str,
            m.Field(description="Declared reason preventing execution."),
        ] = ""
        files: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Paths returned by the original operation owner."),
        ] = ()
        issues: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
            m.Field(description="Native findings at their actual repository."),
        ] = ()

    class WorkspaceOperationTarget(m.ContractModel):
        """One discovered root and its original Git management declaration."""

        root: Annotated[Path, m.Field(description="Actual declared repository root")]
        managed: Annotated[
            bool | None,
            m.Field(
                description="Explicit Git management policy; absent when undeclared",
            ),
        ] = None

    class WorkspaceOperationApplicability(m.ContractModel):
        """Repository-owned policy applied before an operation's real effects."""

        applicable: Annotated[bool, m.Field(description="Original owner may execute")]
        reason: Annotated[
            str,
            m.Field(description="Declared reason when inapplicable"),
        ] = ""

    class WorkspaceOperationReport(m.ContractModel):
        """Declared repository scope and original serial operation receipts."""

        root: Annotated[Path, m.Field(description="Invoking repository root.")]
        operation: Annotated[
            t.NonEmptyStr,
            m.Field(description="Public operation name."),
        ]
        scope: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Roots discovered before the batch."),
        ]
        receipts: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.WorkspaceOperationReceipt],
            m.Field(description="Original receipts in discovered order."),
        ]
        candidate_read_exit_code: Annotated[
            int | None,
            m.Field(description="Original Git metadata read status."),
        ] = None
        candidate_sha: Annotated[
            str | None,
            m.Field(
                pattern=c.Infra.GIT_COMMIT_OID_RE.pattern,
                description="Observed Git candidate; absent when no candidate could be "
                "read",
            ),
        ] = None

    class SubprojectLoadContext(m.ContractModel):
        """Workspace governance scope shared by every declared subproject entry."""

        integration_branch: Annotated[
            str | None,
            m.Field(
                description=(
                    "Resolved workspace integration line; absent defers to the "
                    "provider's conventional branch fallback"
                ),
            ),
        ] = None
        workspace_beads: Annotated[
            FlextInfraConfigModels.BeadsProjectSpec | None,
            m.Field(description="Workspace Beads ledger spec; absent disables routing"),
        ] = None
        allow_unprovisioned_members: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether declared Python members may stay unprovisioned "
                    "checkouts while CI omits them deliberately"
                ),
            ),
        ] = False

        declared_member: Annotated[
            FlextInfraConfigModelsContexts.RepositoryRef | None,
            m.Field(
                description="Catalog-declared member reference for this entry",
            ),
        ] = None

    class EnvironmentContractViolation(
        FlextInfraModelsMixins.PositiveLineMixin,
        m.ContractModel,
    ):
        """One static ``.envrc``/``.envrc.local`` contract violation.

        The line is carried as a typed field; the consuming gate renders the
        canonical ``line N: <message>`` text, so the textual projection stays at
        the reporting boundary and never in the declaration layer.
        """

        message: Annotated[
            str,
            m.Field(description="Violation description without the line prefix"),
        ]
        token: Annotated[
            str,
            m.Field(description="Offending token when the contract is token-based"),
        ] = ""

    class WorkspaceProjectContext(m.ContractModel):
        """Canonical context derived from one runtime working directory."""

        cwd: Annotated[Path, m.Field(description="Resolved submitted directory")]
        identity: Annotated[
            FlextInfraModelsGitIdentity.GitIdentityReport | None,
            m.Field(description="Observed Git identity, absent outside a repository"),
        ] = None
        workspace: Annotated[
            FlextInfraConfigModels.WorkspaceSpec | None,
            m.Field(description="Governed workspace contract when declared"),
        ] = None
        target: Annotated[
            FlextInfraConfigModels.RepositoryConformTarget | None,
            m.Field(description="Effective governed project properties"),
        ] = None
        governed: Annotated[
            bool,
            m.Field(description="Whether repository-local FLEXT governance exists"),
        ] = False
        runtime: Annotated[
            FlextInfraModelsWorkspace.WorkspaceRuntimeContext | None,
            m.Field(description="Physical environment and native resolver ownership"),
        ] = None

    class FlextBindingRequest(m.ContractModel):
        """Session request binding one consumer onto a flext worktree."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(populate_by_name=True)

        repository_root: Annotated[Path, m.Field(description="Consumer project root")]
        flext_root: Annotated[
            Path,
            m.Field(description="Flext worktree supplying the packages"),
        ]
        python: Annotated[
            Path,
            m.Field(description="Interpreter of the environment to rebind"),
        ]

    class DirectUrlDirectoryInfo(m.ContractModel):
        """PEP 610 directory metadata for one installed distribution."""

        editable: Annotated[
            bool,
            m.Field(description="Distribution is installed as editable"),
        ] = False

    class DirectUrlVcsInfo(m.ContractModel):
        """Native PEP 610 VCS identity, independent of a moving requested ref."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="ignore",
            frozen=True,
        )
        vcs: Annotated[str, m.Field(description="Native VCS kind")]
        commit_id: Annotated[str, m.Field(description="Installed full commit identity")]

    class PythonEnvironmentObservation(m.Value):
        """Native metadata and package resolution from one elected interpreter."""

        prefix: Annotated[Path, m.Field(description="Observed native sys.prefix")]
        metadata_paths: Annotated[
            t.VariadicTuple[Path],
            m.Field(
                description="Native physical purelib and platlib install directories"
            ),
        ]
        import_paths: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Native sys.path used for package resolution"),
        ]
        package_directories: Annotated[
            t.MappingKV[str, t.VariadicTuple[Path]],
            m.Field(description="Native package search locations by declared package"),
        ]

    class DirectUrlReceipt(m.ContractModel):
        """Any installed distribution's PEP 610 receipt, read for its kind only.

        VCS and archive receipts carry other keys; only the directory metadata
        decides whether the receipt names a checkout path.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore", frozen=True)

        dir_info: Annotated[
            FlextInfraModelsWorkspace.DirectUrlDirectoryInfo | None,
            m.Field(description="Directory metadata of a local install"),
        ] = None
        url: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required PEP 610 origin URL"),
        ]
        vcs_info: FlextInfraModelsWorkspace.DirectUrlVcsInfo | None = m.Field(
            default=None,
            description="Installed immutable VCS identity",
        )

    class LockedPackageSource(m.ContractModel):
        """Only the lock's immutable installation source fields cross this boundary."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore", frozen=True)
        git: str | None = m.Field(default=None, description="Locked VCS URL and SHA")
        registry: str | None = m.Field(
            default=None,
            description="Locked registry artifact",
        )
        editable: str | None = m.Field(default=None, description="Local root source")
        directory: str | None = m.Field(
            default=None,
            description="Noneditable directory",
        )
        virtual: str | None = m.Field(default=None, description="Virtual local project")
        url: str | None = m.Field(default=None, description="Locked archive URL")

    class LockedDependency(m.ContractModel):
        """A native UV resolved edge, including its fork and requested extras."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore", frozen=True)
        name: Annotated[t.NonEmptyStr, m.Field(description="Required distribution")]
        version: Annotated[
            str | None,
            m.Field(description="Locked edge version when needed to disambiguate"),
        ] = None
        source: Annotated[
            FlextInfraModelsWorkspace.LockedPackageSource | None,
            m.Field(description="Locked edge source when needed to disambiguate"),
        ] = None
        marker: Annotated[
            str | None, m.Field(description="Environment condition for this edge")
        ] = None
        extra: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Requested extras; absent means none"),
        ] = ()

    class LockedPackage(m.ContractModel):
        """Installed identity selected from the committed uv lock."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore", frozen=True)
        name: Annotated[t.NonEmptyStr, m.Field(description="Locked distribution name")]
        version: Annotated[
            t.NonEmptyStr, m.Field(description="Locked distribution version")
        ]
        source: Annotated[
            FlextInfraModelsWorkspace.LockedPackageSource,
            m.Field(description="Locked source identity"),
        ]
        dependencies: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.LockedDependency],
            m.Field(description="Resolved package edges; absent for a leaf package"),
        ] = ()
        optional_dependencies: Annotated[
            t.MappingKV[
                str, t.VariadicTuple[FlextInfraModelsWorkspace.LockedDependency]
            ],
            m.Field(
                alias="optional-dependencies",
                description="Resolved edges by extra; absent when no extras exist",
            ),
        ] = m.Field(
            default_factory=lambda: MappingProxyType[
                str, tuple[FlextInfraModelsWorkspace.LockedDependency, ...]
            ]({}),
            validate_default=True,
        )
        dev_dependencies: Annotated[
            t.MappingKV[
                str, t.VariadicTuple[FlextInfraModelsWorkspace.LockedDependency]
            ],
            m.Field(
                alias="dev-dependencies",
                description="Resolved edges by development group; absent means none",
            ),
        ] = m.Field(
            default_factory=lambda: MappingProxyType[
                str, tuple[FlextInfraModelsWorkspace.LockedDependency, ...]
            ]({}),
            validate_default=True,
        )
        resolution_markers: Annotated[
            t.VariadicTuple[str],
            m.Field(
                alias="resolution-markers",
                description="Package fork conditions; absent means no fork restriction",
            ),
        ] = ()

    class LockedEnvironment(m.ContractModel):
        """Typed installation identities, never a dependency resolver."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore", frozen=True)
        package: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.LockedPackage],
            m.Field(min_length=1, description="Nonempty lock-owned package inventory"),
        ]
        members: Annotated[
            t.VariadicTuple[str],
            m.Field(
                validation_alias=m.AliasPath("manifest", "members"),
                description="Native workspace members; absent outside a workspace",
            ),
        ] = ()

    class EditableDirectUrl(m.ContractModel):
        """Validated PEP 610 editable provenance payload."""

        url: Annotated[t.NonEmptyStr, m.Field(description="Editable source URL")]
        dir_info: Annotated[
            FlextInfraModelsWorkspace.DirectUrlDirectoryInfo,
            m.Field(description="Editable directory metadata"),
        ]

    class FleetPullRequest(m.ContractModel):
        """One open pull request observed in a member repository."""

        number: Annotated[
            int,
            m.Field(description="Provider pull-request number"),
        ]
        head: Annotated[
            str,
            m.Field(description="Branch the pull request proposes"),
        ]
        title: Annotated[str, m.Field(description="Pull-request title")]
        url: Annotated[str, m.Field(description="Pull-request web address")]

    class FleetRepoGaps(m.ContractModel):
        """One repository's row of the workspace fleet-gaps report.

        Quality counts come only from explicitly selected, project-bound check
        invocations. None means unknown/not executed, never PASS. Other hygiene
        probes retain their independent presence and empty-value contracts.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        name: Annotated[str, m.Field(description="Repository name")]
        root: Annotated[Path, m.Field(description="Repository checkout root")]
        present: Annotated[
            bool,
            m.Field(description="Whether the declared checkout exists on disk"),
        ]
        dirty_paths: Annotated[
            t.StrSequence,
            m.Field(description="Porcelain status paths of the checkout"),
        ]
        open_pull_requests: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.FleetPullRequest],
            m.Field(description="Open pull requests; empty when the query fails"),
        ]
        unmerged_branches: Annotated[
            int,
            m.Field(description="Local branches not merged into the integration line"),
        ]
        lint_findings: Annotated[
            t.NonNegativeInt | None,
            m.Field(
                description="Executed eligible lint findings; null is unknown/not "
                "executed",
            ),
        ]
        pyrefly_findings: Annotated[
            t.NonNegativeInt | None,
            m.Field(
                description="Executed eligible Pyrefly findings; null is unknown/not "
                "executed",
            ),
        ]
        codemod_findings: Annotated[
            int,
            m.Field(
                description="Mod scan findings from the checkout's receipt; 0 absent",
            ),
        ]
        agents_doc_present: Annotated[
            bool,
            m.Field(description="Whether the checkout declares its AGENTS.md"),
        ]
        skills_stamp_present: Annotated[
            bool,
            m.Field(description="Whether the skills provisioning stamp exists"),
        ]
        skills_stamp_distribution_version: Annotated[
            str,
            m.Field(
                description=(
                    "Stamp's distribution_version; empty when the stamp is absent"
                ),
            ),
        ]
        beads_config_present: Annotated[
            bool,
            m.Field(description="Whether the Beads runtime identity exists"),
        ]

    class FleetGapsReport(m.ContractModel):
        """Typed receipt of one workspace fleet-gaps run.

        The report carries no wall-clock field: an unchanged tree produces a
        byte-identical receipt, so a rerun is its own idempotence proof.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        schema_version: Annotated[
            int,
            m.Field(description="Report schema version"),
        ]
        workspace_root: Annotated[
            Path,
            m.Field(description="Invoking workspace root"),
        ]
        workspace_name: Annotated[str, m.Field(description="Workspace identity name")]
        repos: Annotated[
            t.VariadicTuple[FlextInfraModelsWorkspace.FleetRepoGaps],
            m.Field(description="One row per declared member and external consumer"),
        ]

    class ProjectInfo(
        FlextInfraModelsMixins.ProjectEntryNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Discovered project metadata for workspace operations."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            validate_default=False,
        )

        path: Annotated[Path, m.Field(description="Absolute or relative project path")]
        stack: Annotated[t.NonEmptyStr, m.Field(description="Primary technology stack")]
        has_tests: Annotated[bool, m.Field(description="Project has test suite")] = (
            False
        )
        has_src: Annotated[
            bool,
            m.Field(description="Project has source directory"),
        ] = True
        project_class: Annotated[
            t.NonEmptyStr,
            m.Field(description="Docs/governance project classification"),
        ] = "platform"
        package_name: Annotated[
            str,
            m.Field(description="Primary Python package name"),
        ] = ""
        make_profile: Annotated[
            c.Infra.MakeProfile,
            m.Field(description="Topology proven by this checkout's .gitmodules"),
        ] = c.Infra.MakeProfile.STANDALONE
        declared_subproject: Annotated[
            bool,
            m.Field(description="Whether the aggregate workspace declares this path"),
        ] = False

    class ProjectPyprojectState(m.ArbitraryTypesModel):
        """Centralized parsed pyproject state reused across discovery services.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            validate_default=False,
        )

        project_root: Annotated[Path, m.Field(description="Project root path")]
        pyproject_path: Annotated[Path, m.Field(description="Resolved pyproject path")]
        payload: Annotated[
            t.JsonMapping,
            m.Field(description="Parsed pyproject payload"),
        ]
        docs_meta: Annotated[
            t.JsonMapping,
            m.Field(description="Parsed tool.flext.docs payload"),
        ]
        project_name: Annotated[str, m.Field(description="Declared project name")] = ""
        package_name: Annotated[str, m.Field(description="Primary package name")] = ""
        dependency_names: Annotated[
            t.StrSequence,
            m.Field(description="Declared dependency names"),
        ] = m.Field(default_factory=tuple)


__all__: list[str] = ["FlextInfraModelsWorkspace"]
