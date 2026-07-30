"""Pure Pydantic config and codegen contracts for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u
from flext_infra import t
from flext_infra._constants.codegen_project import FlextInfraConstantsCodegenProject
from flext_infra._constants.make import FlextInfraConstantsMake
from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolSettings
from flext_infra._models.layout import FlextInfraModelsLayout


class _ConfigContract(m.ContractModel):
    """Private declarative base for schema-loaded codegen records."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): rendered file payloads are
    # byte contracts; Pydantic must never trim their final newline.
    model_config = m.ConfigDict(
        strict=False, frozen=True, extra="forbid", str_strip_whitespace=False
    )


class FlextInfraConfigModels:
    """Field-only models for config loading and codegen plans."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these models replace the
    # former model-less workspace/make dictionaries. YAML is accepted only at
    # the flext-cli loading boundary and is immediately model-validated here.

    class MiseToolSpec(_ConfigContract):
        """One exact mise backend selector and immutable version."""

        selector: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical mise backend selector")
        ]
        version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact tool version installed by mise")
        ]

    class ToolchainSpec(_ConfigContract):
        """Language-runtime and native-tool versions shared by generated projects.

        Only the Python minor line ``python_version`` (e.g. ``3.13``) is
        declared for the language runtime. The environment resolves its newest
        compatible patch. The PEP 440 family requirement is derived, so a
        version-line bump touches exactly one value. uv is supplied by the caller
        environment. Python linters/type-checkers are NOT here: their floors live
        in pyproject and uv.lock owns the resolved versions. Native executables
        required by canonical Make gates are declared here for reproducible
        provisioning through mise.
        """

        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[0-9]+\.[0-9]+$",
                description="Python major.minor line, e.g. '3.13'",
            ),
        ]
        uv_link_mode: Annotated[
            t.NonEmptyStr, m.Field(description="Portable uv installation link mode")
        ]
        kubectl_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kubectl version, e.g. '1.32.0'")
        ]
        helm_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Helm version, e.g. '3.19.4'")
        ]
        kind_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kind version, e.g. '0.31.0'")
        ]
        environment_path_prepends: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Extra directories the generated shell activation prepends "
                    "to PATH when they exist. Installation data expressed as "
                    "shell-expandable paths; empty by default so the engine "
                    "never names a specific tool installation."
                ),
            ),
        ] = ()
        taplo_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Taplo formatter version")
        ]
        ast_grep_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact ast-grep analyzer version")
        ]
        gitleaks_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Gitleaks scanner version")
        ]
        tokei_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Tokei analyzer version")
        ]
        mise_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact mise binary version")
        ]
        beads: Annotated[
            FlextInfraConfigModels.MiseToolSpec,
            m.Field(description="Official Beads CLI installed through mise"),
        ]

        @m.computed_field()
        @property
        def python_required_version(self) -> str:
            """PEP 440 requirement spanning the configured Python minor line."""
            major, _, minor = self.python_version.partition(".")
            next_minor = int(minor) + 1
            return f">={self.python_version},<{major}.{next_minor}"

        @m.computed_field()
        @property
        def python_selector(self) -> str:
            """Mise/pyenv-style selector for the configured Python minor line."""
            return self.python_version

    class ProviderSpec(_ConfigContract):
        """One GitHub organization and its mandatory branch policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Provider key")]
        organization: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub organization")
        ]
        base_url: Annotated[t.NonEmptyStr, m.Field(description="GitHub HTTPS base URL")]
        branch: Annotated[t.NonEmptyStr, m.Field(description="Provider branch")]

    class BranchPolicySpec(_ConfigContract):
        """Global ancestry policy shared by every governed provider."""

        REQUIRED_TECHNICAL_PATTERNS: ClassVar[tuple[str, ...]] = (
            "__dolt_remote_info__",
            "dolt/*",
            "gh-readonly-queue/*",
        )
        technical_branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "GitHub/Dolt technical branches excluded from ancestry validation"
                )
            ),
        ]
        governed_branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Development lines whose descent from the baseline is enforced. "
                    "Refs outside this allowlist are inventoried but never gated: "
                    "parked releases, snapshots and lane branches must not block."
                ),
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_technical_patterns(self) -> Self:
            """Keep the global exclusion set exact and non-extensible."""
            if self.technical_branch_patterns != self.REQUIRED_TECHNICAL_PATTERNS:
                msg = (
                    "technical branch patterns must equal the canonical GitHub/Dolt "
                    f"set: {', '.join(self.REQUIRED_TECHNICAL_PATTERNS)}"
                )
                raise ValueError(msg)
            return self

    class GithubActionPinSpec(_ConfigContract):
        """One immutable GitHub Action reference from the codegen catalog."""

        repository: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub owner/repository action name")
        ]
        version: Annotated[
            t.NonEmptyStr, m.Field(description="Human-readable upstream release tag")
        ]
        sha: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[0-9a-f]{40}$",
                description="Immutable upstream action commit",
            ),
        ]

    class GithubWorkflowRenderSpec(_ConfigContract):
        """Typed input consumed by generated GitHub workflow templates."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        repository_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Repository integration branch")
        ]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor line")
        ]
        github_actions: Annotated[
            Mapping[str, FlextInfraConfigModels.GithubActionPinSpec],
            m.Field(description="Immutable GitHub Action catalog"),
        ]

    class DistroDockerRenderSpec(_ConfigContract):
        """Typed input consumed by generated distro Dockerfiles."""

        package_name: Annotated[
            t.NonEmptyStr, m.Field(description="Python import package name")
        ]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor line")
        ]

    class UvPackageSelectorSpec(_ConfigContract):
        """Package selector for one official uv scoped dependency exclusion."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Selected package name")]
        version: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional selected package version expression"),
        ] = None

    class UvScopedDependencyExclusionSpec(_ConfigContract):
        """Project-routed official uv scoped dependency exclusion."""

        project: Annotated[
            t.NonEmptyStr,
            m.Field(exclude=True, description="Owning project distribution route"),
        ]
        package: Annotated[
            FlextInfraConfigModels.UvPackageSelectorSpec,
            m.Field(description="Package whose transitive edge is scoped"),
        ]
        dependencies: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Excluded transitive dependency names"),
        ]

    class ProfileSpec(_ConfigContract):
        """Execution semantics for one generated Make profile."""

        name: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Closed Make profile name"),
        ]
        environment_scope: Annotated[
            t.NonEmptyStr, m.Field(description="uv environment ownership")
        ]
        setup_scope: Annotated[
            t.NonEmptyStr, m.Field(description="setup orchestration scope")
        ]
        execution_scope: Annotated[
            t.NonEmptyStr, m.Field(description="check/test runtime scope")
        ]
        discovery_scope: Annotated[
            t.NonEmptyStr, m.Field(description="repository discovery policy")
        ]

    class MakeVerbSpec(_ConfigContract):
        """One public Make verb and its single default selector."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Public Make verb")]
        default_what: Annotated[
            t.NonEmptyStr, m.Field(description="Default WHAT selector")
        ]
        apply_guarded: Annotated[
            bool, m.Field(description="Whether mutation requires APPLY=Y")
        ] = False

    class ScriptDispatchSpec(_ConfigContract):
        """Opt-in routing of non-builtin verbs to a script command framework."""

        dispatcher: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Repository-relative dispatcher entrypoint that resolves "
                    "scripts/<verb>/<what>.{py,sh} commands"
                )
            ),
        ]
        roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Repository-relative script roots scanned for a matching "
                    "<verb>/<what> command before falling back to a builtin"
                ),
            ),
        ]

    class CustomHandlerPolicy(_ConfigContract):
        """Strict schema for the only handwritten Make extension file."""

        filename: Annotated[
            t.NonEmptyStr, m.Field(description="Versioned custom handler filename")
        ]
        target_pattern: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required private target regular expression"),
        ]
        allow_public_targets: bool = m.Field(description="Permit public targets")
        allow_toolchain_declarations: bool = m.Field(
            description="Permit toolchain declarations"
        )

    class CustomHandlerPolicyOverride(_ConfigContract):
        """Per-profile relaxation of the strict custom-handler contract.

        Every field is optional: a profile declares ONLY what it relaxes, so a
        new permission added to the base policy propagates automatically
        instead of having to be repeated in each profile.
        """

        allow_public_targets: bool | None = m.Field(
            default=None, description="Permit public targets"
        )
        allow_toolchain_declarations: bool | None = m.Field(
            default=None, description="Permit toolchain declarations"
        )

    class MakeSerializationSpec(_ConfigContract):
        """Portable per-checkout serialization for state-sensitive Make verbs."""

        lock_path: Annotated[
            Path, m.Field(description="Repository-relative native process-lock path")
        ]
        single_flight_lock_path: Annotated[
            Path,
            m.Field(
                description=(
                    "Repository-relative lock around one complete Make operation"
                )
            ),
        ]
        mutation_fixed_points: Annotated[
            Mapping[t.NonEmptyStr, Mapping[t.NonEmptyStr, t.NonEmptyStr]],
            m.Field(
                default_factory=lambda: MappingProxyType({}),
                description=(
                    "Authorized mutating WHATs and the validation WHAT each must "
                    "run afterward under the same lock"
                ),
            ),
        ]
        snapshot_excludes: Annotated[
            tuple[Path, ...],
            m.Field(
                description=(
                    "Repository-relative lock and report artifacts omitted "
                    "from gate-integrity fingerprints"
                )
            ),
        ]
        timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                description="Maximum seconds to wait for the checkout validation lock",
            ),
        ]
        verbs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1, description="Public Make verbs serialized per checkout"
            ),
        ]

        @m.field_validator("lock_path", "single_flight_lock_path")
        @classmethod
        def _validate_lock_path(cls, value: Path) -> Path:
            """Keep every validation lock within its owning checkout."""
            if value.is_absolute() or not value.parts or ".." in value.parts:
                msg = "make serialization lock paths must be repository-relative"
                raise ValueError(msg)
            return value

        @m.field_validator("snapshot_excludes")
        @classmethod
        def _validate_snapshot_excludes(
            cls, values: tuple[Path, ...]
        ) -> tuple[Path, ...]:
            """Keep explicit snapshot exclusions within their owning checkout."""
            for value in values:
                if value.is_absolute() or not value.parts or ".." in value.parts:
                    msg = (
                        "make serialization snapshot_excludes must be "
                        "repository-relative"
                    )
                    raise ValueError(msg)
            return values

        @u.model_validator(mode="after")
        def _validate_lock_excluded_from_snapshot(self) -> Self:
            """Require the native lock artifact to remain outside fingerprints."""
            lock_paths = (self.single_flight_lock_path, self.lock_path)
            if len(set(lock_paths)) != len(lock_paths):
                msg = "make serialization lock paths must be distinct"
                raise ValueError(msg)
            missing_excludes = set(lock_paths) - set(self.snapshot_excludes)
            if missing_excludes:
                msg = (
                    "make serialization lock paths must be snapshot-excluded: "
                    f"{', '.join(sorted(path.as_posix() for path in missing_excludes))}"
                )
                raise ValueError(msg)
            invalid = set(self.mutation_fixed_points) - set(self.verbs)
            if invalid:
                msg = (
                    "make serialization mutation verbs are not serialized: "
                    f"{', '.join(sorted(invalid))}"
                )
                raise ValueError(msg)
            empty = [
                verb
                for verb, fixed_points in self.mutation_fixed_points.items()
                if not fixed_points
            ]
            if empty:
                msg = (
                    "make serialization mutation verbs require fixed points: "
                    f"{', '.join(sorted(empty))}"
                )
                raise ValueError(msg)
            return self

    class MakeDocsSpec(_ConfigContract):
        """Generated Makefile docs verb lifecycle and audit policy."""

        actions: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Ordered public docs actions"),
        ]
        default_action: Annotated[
            t.NonEmptyStr, m.Field(description="Default docs action")
        ]
        mutable_actions: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Docs actions guarded by APPLY=Y"),
        ]
        reports_dir: Annotated[
            Path, m.Field(description="Repository-relative docs reports directory")
        ]
        cross_project_relative_link_pattern: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Regex rejecting cross-project relative Markdown links"
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_docs_actions(self) -> Self:
            """Require the default action and every mutable action to be declared."""
            declared = set(self.actions)
            if self.default_action not in declared:
                msg = (
                    f"docs default action must be one of {', '.join(sorted(declared))}"
                )
                raise ValueError(msg)
            unknown = set(self.mutable_actions) - declared
            if unknown:
                msg = (
                    "docs mutable actions must be declared actions: "
                    f"{', '.join(sorted(unknown))}"
                )
                raise ValueError(msg)
            if not any(action == "all" for action in self.actions):
                msg = "docs actions must include the 'all' aggregate action"
                raise ValueError(msg)
            return self

    class MakeSpec(_ConfigContract):
        """Complete generated Makefile public and extension contract."""

        selector: Annotated[
            t.NonEmptyStr, m.Field(description="Single selector variable name")
        ]
        apply_variable: Annotated[
            t.NonEmptyStr, m.Field(description="Write-enable variable name")
        ]
        apply_value: Annotated[
            t.NonEmptyStr, m.Field(description="Only accepted write-enable value")
        ]
        serialization: Annotated[
            FlextInfraConfigModels.MakeSerializationSpec,
            m.Field(description="Per-checkout Make validation serialization"),
        ]
        verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Ordered canonical public verbs"),
        ]
        docs: Annotated[
            FlextInfraConfigModels.MakeDocsSpec,
            m.Field(description="Public documentation lifecycle policy"),
        ]
        custom_handler_policy: Annotated[
            FlextInfraConfigModels.CustomHandlerPolicy,
            m.Field(description="Private custom target policy"),
        ]
        custom_handler_profile_overrides: Annotated[
            Mapping[t.NonEmptyStr, FlextInfraConfigModels.CustomHandlerPolicyOverride],
            m.Field(
                default_factory=lambda: MappingProxyType({}),
                description="Per-profile overrides of the custom handler policy",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_serialized_verbs(self) -> Self:
            """Require serialization to target declared non-bootstrap verbs."""
            declared = {verb.name for verb in self.verbs}
            serialized = set(self.serialization.verbs)
            invalid = serialized - declared
            if invalid:
                msg = (
                    "make serialization verbs are not declared public verbs: "
                    f"{', '.join(sorted(invalid))}"
                )
                raise ValueError(msg)
            if "setup" in serialized:
                msg = "make setup cannot require the managed validation environment"
                raise ValueError(msg)
            docs_actions = set(self.docs.actions)
            if self.docs.default_action not in docs_actions:
                msg = "make docs default_action must be declared in actions"
                raise ValueError(msg)
            invalid_mutable = set(self.docs.mutable_actions) - docs_actions
            if invalid_mutable:
                msg = "make docs mutable_actions must be declared in actions"
                raise ValueError(msg)
            if (
                self.docs.reports_dir.is_absolute()
                or ".." in self.docs.reports_dir.parts
            ):
                msg = "make docs reports_dir must be repository-relative"
                raise ValueError(msg)
            return self

        @m.computed_field()
        @property
        def check_gates_allowed(self) -> tuple[str, ...]:
            """Canonical generated Make check-gate vocabulary."""
            return FlextInfraConstantsMake.PROJECT_CHECK_GATES_ALLOWED_VALUES

        @m.computed_field()
        @property
        def check_gates_default(self) -> tuple[str, ...]:
            """Canonical generated Make default check gates."""
            return FlextInfraConstantsMake.PROJECT_CHECK_GATES_DEFAULT_VALUES

        @m.computed_field()
        @property
        def custom_handler_policies(
            self,
        ) -> Mapping[str, FlextInfraConfigModels.CustomHandlerPolicy]:
            """Effective custom-handler policy for every Make profile.

            The base policy states the strictest contract (private handlers
            only). A profile whose custom surface legitimately owns more --
            a workspace root orchestrating its members -- declares only the
            fields it relaxes, so the engine never has to know which project
            it is conforming.
            """
            base = self.custom_handler_policy
            overrides = self.custom_handler_profile_overrides
            # Keys are normalised to the profile's string value: MakeProfile is a
            # StrEnum, so a raw YAML key and its enum member must land on the SAME
            # entry. Mixing both would make a lookup silently miss and fall back to
            # the strict base policy.
            return {
                str(profile): (
                    base.model_copy(update=override.model_dump(exclude_none=True))
                    if (override := overrides.get(str(profile)))
                    else base
                )
                for profile in (
                    *overrides,
                    *FlextInfraConstantsCodegenProject.MakeProfile,
                )
            }

    class ManagedFileSpec(_ConfigContract):
        """One versioned file governed by codegen lifecycle policy."""

        path: Annotated[Path, m.Field(description="Repository-relative file path")]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical owner")]
        policy: Annotated[
            Literal["full", "merge", "create-only", "delegated", "manual"],
            m.Field(
                description=(
                    "Conform ownership and mutation policy; create-only files are "
                    "emitted during creation, preserved when present, and never "
                    "backfilled into existing trees"
                )
            ),
        ]

    class TemplateEntrySpec(_ConfigContract):
        """One scaffold-only template mapping consumed by ``codegen new``."""

        source: Annotated[Path, m.Field(description="Template-root-relative source")]
        destination: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
        ]
        profiles: Annotated[
            tuple[FlextInfraConstantsCodegenProject.MakeProfile, ...],
            m.Field(description="Profiles that consume the template"),
        ]
        delegate: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical rendering delegate")
        ]
        overwrite: Annotated[
            bool, m.Field(description="Whether the template owns existing content")
        ] = False

    class TemplatesSpec(_ConfigContract):
        """New-project scaffold root and its complete ordered manifest."""

        root: Annotated[Path, m.Field(description="Package-relative template root")]
        entries: Annotated[
            tuple[FlextInfraConfigModels.TemplateEntrySpec, ...],
            m.Field(description="Complete ordered template manifest"),
        ]

    class ScaffoldBuildSpec(_ConfigContract):
        """Configured Python build backend for newly scaffolded projects."""

        backend: Annotated[t.NonEmptyStr, m.Field(description="PEP 517 backend")]
        requirements: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Build-system requirements"),
        ]

    class ScaffoldDependencyProfileSpec(_ConfigContract):
        """Dependencies selected by the declared upstream FLEXT facade."""

        upstream: Annotated[
            t.NonEmptyStr, m.Field(description="Supported upstream facade package")
        ]
        runtime: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Runtime requirements"),
        ]
        codegen: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Code-generation requirements"),
        ] = ()

    class ScaffoldProjectSpec(_ConfigContract):
        """Project metadata policy for newly scaffolded distributions."""

        readme: Annotated[t.NonEmptyStr, m.Field(description="PEP 621 readme path")]
        supported_licenses: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Licenses with complete templates"),
        ]
        classifiers: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Default PyPI classifiers"),
        ]
        keywords: Annotated[
            tuple[t.NonEmptyStr, ...], m.Field(description="Default project keywords")
        ] = ()
        dev: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Canonical development and validation requirements",
            ),
        ]
        dependency_profiles: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldDependencyProfileSpec, ...],
            m.Field(min_length=1, description="Upstream dependency profiles"),
        ]

    class ScaffoldPingExampleSpec(_ConfigContract):
        """Values for the functional ping example created only by codegen new."""

        command_name: Annotated[
            t.NonEmptyStr, m.Field(description="Public CLI command")
        ]
        help_text: Annotated[
            t.NonEmptyStr, m.Field(description="Public CLI command help")
        ]
        success_message: Annotated[
            t.NonEmptyStr, m.Field(description="CLI success message")
        ]
        enabled_default: Annotated[
            bool, m.Field(description="Default runtime enablement")
        ]
        reply: Annotated[t.NonEmptyStr, m.Field(description="Enabled ping response")]
        disabled_reply: Annotated[
            t.NonEmptyStr, m.Field(description="Disabled ping response")
        ]

    class ScaffoldGitignoreSectionSpec(_ConfigContract):
        """One configured section of the generated Git ignore policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Section heading")]
        patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Ignored path patterns"),
        ]
        profiles: Annotated[
            tuple[FlextInfraConstantsCodegenProject.MakeProfile, ...],
            m.Field(
                description=(
                    "Make profiles this section applies to; empty means every "
                    "profile (universal). Sections that only make sense at the "
                    "superproject root (member-directory allowlists, workspace "
                    "manifest, submodule/Beads coordination) declare "
                    "[workspace-root] so members and standalone projects never "
                    "receive the phantom entries."
                )
            ),
        ] = ()

    class ScaffoldSpec(_ConfigContract):
        """Complete typed policy consumed only by new-project templates."""

        build: Annotated[
            FlextInfraConfigModels.ScaffoldBuildSpec,
            m.Field(description="Build-system policy"),
        ]
        project: Annotated[
            FlextInfraConfigModels.ScaffoldProjectSpec,
            m.Field(description="Project metadata and dependency policy"),
        ]
        ping_example: Annotated[
            FlextInfraConfigModels.ScaffoldPingExampleSpec,
            m.Field(description="Functional scaffold example"),
        ]
        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(min_length=1, description="Generated Git ignore sections"),
        ]

    class GitignoreRenderContext(_ConfigContract):
        """Profile-filtered input consumed by the Git ignore template."""

        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(min_length=1, description="Applicable Git ignore sections"),
        ]

    class RepositoryRef(_ConfigContract):
        """One declared repository and its immutable Git origin contract."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        name: Annotated[t.NonEmptyStr, m.Field(description="Catalog key")]
        distribution: Annotated[
            t.NonEmptyStr, m.Field(description="Python distribution or repository name")
        ]
        url: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical GitHub clone URL ending in .git"),
        ]
        path: Annotated[
            Path, m.Field(description="POSIX path relative to its workspace root")
        ]
        role: Annotated[
            FlextInfraConstantsCodegenProject.RepositoryRole,
            m.Field(description="Repository role in the declared topology"),
        ]
        state: Annotated[
            FlextInfraConstantsCodegenProject.RepositoryState,
            m.Field(description="Repository lifecycle state"),
        ] = FlextInfraConstantsCodegenProject.RepositoryState.ACTIVE
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key from the codegen configuration"),
        ]
        checkout: Annotated[
            FlextInfraConstantsCodegenProject.CheckoutKind,
            m.Field(description="Physical checkout topology"),
        ]
        codegen: Annotated[
            FlextInfraConstantsCodegenProject.CodegenKind,
            m.Field(description="Repository code-generation policy"),
        ]
        package: Annotated[
            bool, m.Field(description="Repository publishes a Python package")
        ]
        editable: Annotated[
            bool, m.Field(description="Overlay repository as an editable dependency")
        ]
        read_only: Annotated[
            bool, m.Field(description="Repository rejects generated mutations")
        ]
        extra_verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(
                description=(
                    "Additional public Make verbs this repository dispatches "
                    "beyond the canonical set (e.g. a script command framework)"
                )
            ),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraConfigModels.ScriptDispatchSpec | None,
            m.Field(
                description=(
                    "Opt-in script command-framework routing for non-builtin "
                    "verbs and WHAT selectors; None keeps builtin-only dispatch"
                )
            ),
        ] = None

    class RepositoryPolicyOverlaySpec(_ConfigContract):
        """Bounded per-project exceptions to inferred repository policy."""

        project: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical PEP 621 project name")
        ]
        beads_enabled: Annotated[
            bool,
            m.Field(description="Opt an independent standalone project into Beads"),
        ] = False
        ci_enabled: Annotated[
            bool,
            m.Field(description="Whether conform generates the governed CI surface"),
        ] = True

    class RepositoryConformTarget(_ConfigContract):
        """Runtime-derived conformance identity for one repository."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Declared immutable repository identity"),
        ]
        root: Annotated[
            Path, m.Field(description="Resolved repository root receiving conformance")
        ]
        make_profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Make profile inferred from live Git topology"),
        ]
        beads_enabled: Annotated[
            bool, m.Field(description="Whether this repository owns a Beads tracker")
        ]
        canonical_project_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical PEP 621 project name and Beads namespace"),
        ]
        baseline_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider-owned integration ancestry baseline"),
        ]
        ci_enabled: Annotated[
            bool, m.Field(description="Whether conform owns the CI projection")
        ]
        external_dependency_paths: Annotated[
            tuple[Path, ...],
            m.Field(description="Observed external or fork Git submodule paths"),
        ] = ()
        technical_branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Technical branches excluded from ancestry policy"),
        ] = ()
        governed_branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Development lines gated by ancestry policy; required because "
                    "an empty tuple would match no ref and silently disable the "
                    "gate instead of failing closed"
                ),
            ),
        ]

    class ManagedGitlinkSpec(_ConfigContract):
        """One governed submodule with its provider-owned baseline branch."""

        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Governed repository identity"),
        ]
        branch: Annotated[
            t.NonEmptyStr, m.Field(description="Provider-owned integration branch")
        ]

    class MakeCommandContext(_ConfigContract):
        """Shared command identity required by every generated Make surface."""

        infra_cli: Annotated[
            t.NonEmptyStr, m.Field(description="Installed infrastructure CLI command")
        ]

    class MakefileRenderSpec(MakeCommandContext):
        """Field-only render input for an existing repository Makefile."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="PEP 621 project name")]
        infra_repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(
                description="Canonical bootstrap source for the infrastructure CLI"
            ),
        ]
        infra_repository_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider-owned infrastructure baseline branch"),
        ]
        infra_source_root_rel: Annotated[
            str | None,
            m.Field(
                description=(
                    "Repository-relative local infrastructure source, or None "
                    "when bootstrap must use the configured Git source"
                )
            ),
        ] = None
        make_profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Selected repository Make profile"),
        ]
        workspace_root_rel: Annotated[
            t.NonEmptyStr, m.Field(description="Relative workspace root path")
        ]
        workspace_members: Annotated[
            tuple[str, ...], m.Field(description="Declared workspace member paths")
        ] = ()
        workspace_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Repositories editable from the selected workspace"),
        ] = ()
        workspace_gitlinks: Annotated[
            tuple[FlextInfraConfigModels.ManagedGitlinkSpec, ...],
            m.Field(description="Provider-resolved governed Git submodules"),
        ] = ()
        uv_link_mode: Annotated[
            t.NonEmptyStr, m.Field(description="Configured uv installation link mode")
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Generated Make command contract"),
        ]
        extra_verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Repository-specific public Make verbs"),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraConfigModels.ScriptDispatchSpec | None,
            m.Field(description="Optional script command dispatch contract"),
        ] = None

        makefile_custom_include: Annotated[
            t.NonEmptyStr,
            m.Field(description="Generated custom Make policy include directive"),
        ]
        orchestrated_verbs: Annotated[
            tuple[str, ...],
            m.Field(
                description="Workspace-root gate verbs routed through orchestration"
            ),
        ] = ()
        workspace_cli_group: Annotated[
            t.NonEmptyStr,
            m.Field(description="CLI group used for workspace orchestration"),
        ]
        project_selection_conflict_error: Annotated[
            t.NonEmptyStr,
            m.Field(description="Mutually exclusive project selector error"),
        ]
        mypy_memory_limit_mb: Annotated[
            int, m.Field(gt=0, description="Generated Mypy address-space limit in MiB")
        ]
        mypy_timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Generated Mypy wall-time limit in seconds")
        ]
        mypy_timeout_exit_code: Annotated[
            int, m.Field(gt=0, description="Wall-time limiter timeout exit code")
        ]
        mypy_signal_exit_offset: Annotated[
            int, m.Field(gt=0, description="Shell signal exit-code offset")
        ]
        prlimit_command: Annotated[
            t.NonEmptyStr, m.Field(description="Address-space limiter executable")
        ]
        prlimit_address_space_option: Annotated[
            t.NonEmptyStr, m.Field(description="Address-space limiter option")
        ]
        timeout_command: Annotated[
            t.NonEmptyStr, m.Field(description="Wall-time limiter executable")
        ]
        timeout_kill_after_seconds: Annotated[
            int, m.Field(gt=0, description="Forced-termination grace period")
        ]

    class GitignoreRenderSpec(_ConfigContract):
        """Typed, profile-filtered input for the generated Git ignore file."""

        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(
                min_length=1,
                description="Canonical ignore sections applicable to one profile",
            ),
        ]

    # mro-wkii.17 (Codex): project creation metadata remains a typed manifest input.
    class ProjectSpec(_ConfigContract):
        """Deterministic project metadata required to materialize a new tree."""

        package_name: Annotated[
            t.NonEmptyStr, m.Field(description="Import package name")
        ]
        class_stem: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical public facade class stem")
        ]
        namespace: Annotated[
            t.NonEmptyStr, m.Field(description="Nested c/t/p/m/u namespace")
        ]
        constant_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Configured project name exposed through constants"),
        ]
        namespace_attribute: Annotated[
            t.NonEmptyStr, m.Field(description="Private module namespace token")
        ]
        alias: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical public instance alias")
        ]
        environment_prefix: Annotated[
            t.NonEmptyStr, m.Field(description="Project settings environment prefix")
        ]
        description: Annotated[
            t.NonEmptyStr, m.Field(description="Project description")
        ]
        version: Annotated[t.NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[t.NonEmptyStr, m.Field(description="SPDX license id")]
        author_name: Annotated[
            t.NonEmptyStr, m.Field(description="Author display name")
        ]
        author_email: Annotated[t.NonEmptyStr, m.Field(description="Author email")]
        upstream: Annotated[
            t.NonEmptyStr, m.Field(description="Upstream FLEXT facade module")
        ]
        homepage: Annotated[t.NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            t.NonEmptyStr, m.Field(description="Project documentation URL")
        ]
        workspace_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Declared relative path to the workspace root"),
        ]
        year: Annotated[int, m.Field(ge=2025, description="Copyright year")]

    class MakeRenderContext(MakeCommandContext):
        """Typed input consumed by the generated Make surface."""

        infra_repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(
                description="Canonical bootstrap source for the infrastructure CLI"
            ),
        ]
        infra_repository_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider-owned infrastructure baseline branch"),
        ]
        infra_source_root_rel: Annotated[
            str | None,
            m.Field(
                description=(
                    "Repository-relative local infrastructure source, or None "
                    "when bootstrap must use the configured Git source"
                )
            ),
        ] = None
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Generated Make command contract"),
        ]
        mypy_memory_limit_mb: Annotated[
            int, m.Field(gt=0, description="Generated Mypy address-space limit in MiB")
        ]
        mypy_timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Generated Mypy wall-time limit in seconds")
        ]
        mypy_timeout_exit_code: Annotated[
            int, m.Field(gt=0, description="Wall-time limiter timeout exit code")
        ]
        mypy_signal_exit_offset: Annotated[
            int, m.Field(gt=0, description="Shell signal exit-code offset")
        ]
        prlimit_command: Annotated[
            t.NonEmptyStr, m.Field(description="Address-space limiter executable")
        ]
        prlimit_address_space_option: Annotated[
            t.NonEmptyStr, m.Field(description="Address-space limiter option")
        ]
        timeout_command: Annotated[
            t.NonEmptyStr, m.Field(description="Wall-time limiter executable")
        ]
        timeout_kill_after_seconds: Annotated[
            int, m.Field(gt=0, description="Forced-termination grace period")
        ]
        tooling_runtime: Annotated[
            FlextInfraModelsDepsToolSettings.ToolingRuntimeContext,
            m.Field(description="Resolved project/workspace tooling values"),
        ]

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]

        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor tool value")
        ]
        uv_link_mode: Annotated[
            t.NonEmptyStr, m.Field(description="Configured uv installation link mode")
        ]
        make_profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Generated Make execution profile"),
        ]
        workspace_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Relative path to the declared workspace root"),
        ]
        makefile_custom_include: Annotated[
            str,
            m.Field(
                min_length=1,
                description=("Make directive that includes the custom Make surface"),
            ),
        ]
        workspace_members: Annotated[
            tuple[str, ...], m.Field(description="Ordered workspace member paths")
        ] = ()
        workspace_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered workspace member records"),
        ] = ()
        workspace_gitlinks: Annotated[
            tuple[FlextInfraConfigModels.ManagedGitlinkSpec, ...],
            m.Field(description="Provider-resolved governed Git submodules"),
        ] = ()
        extra_verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Repository-specific additional public Make verbs"),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraConfigModels.ScriptDispatchSpec | None,
            m.Field(description="Opt-in script command-framework routing contract"),
        ] = None
        orchestrated_verbs: Annotated[
            tuple[str, ...],
            m.Field(
                description=(
                    "Gate verbs a workspace-root Makefile fans out across members "
                    "through the generic workspace orchestrate primitive"
                )
            ),
        ] = ()
        workspace_cli_group: Annotated[
            str,
            m.Field(
                description=(
                    "CLI group name for the flext-infra workspace orchestrate route"
                )
            ),
        ] = ""
        project_selection_conflict_error: Annotated[
            t.NonEmptyStr,
            m.Field(description="Mutually exclusive project selector error"),
        ]

    class ProjectRenderContext(MakeRenderContext):
        """Complete typed input consumed by project scaffold templates."""

        @m.computed_field()
        @property
        def repository_env_prefix(self) -> str:
            """Settings environment prefix derived from the distribution name."""
            return f"{self.dist.upper().replace('-', '_')}_"

        scaffold: Annotated[
            FlextInfraConfigModels.ScaffoldSpec,
            m.Field(description="New-project scaffold policy"),
        ]
        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(
                min_length=1,
                description=(
                    "Canonical .gitignore sections derived from the artifact SSOT"
                ),
            ),
        ]
        dependency_profile: Annotated[
            FlextInfraConfigModels.ScaffoldDependencyProfileSpec,
            m.Field(description="Resolved upstream dependency profile"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolSettings.ToolConfigDocument,
            m.Field(description="Canonical validated tooling policy"),
        ]
        environment_path_prepends: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Configured read-only PATH additions for direnv"),
        ] = ()
        beads_tool_selector: Annotated[
            t.NonEmptyStr, m.Field(description="Official Beads mise selector")
        ]
        beads_tool_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Beads CLI version")
        ]
        beads_enabled: Annotated[
            bool, m.Field(description="Whether conform owns this repository's tracker")
        ]
        canonical_project_name: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical project and Beads namespace")
        ]
        const_name: Annotated[
            t.NonEmptyStr, m.Field(description="Configured constant project name")
        ]
        package_name: Annotated[
            t.NonEmptyStr, m.Field(description="Python import package name")
        ]
        packaged_data_dirs: Annotated[
            t.StrSequence,
            m.Field(description="Generated root data directories shipped in wheels"),
        ]
        class_stem: Annotated[
            t.NonEmptyStr, m.Field(description="Public facade class stem")
        ]
        ns: Annotated[t.NonEmptyStr, m.Field(description="Public model namespace")]
        ns_attr: Annotated[
            t.NonEmptyStr, m.Field(description="Private namespace module token")
        ]
        alias: Annotated[t.NonEmptyStr, m.Field(description="Public instance alias")]
        env_prefix: Annotated[
            t.NonEmptyStr, m.Field(description="Settings environment prefix")
        ]
        upstream: Annotated[
            t.NonEmptyStr, m.Field(description="Upstream FLEXT facade module")
        ]
        description: Annotated[
            t.NonEmptyStr, m.Field(description="Project description")
        ]
        version: Annotated[t.NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[t.NonEmptyStr, m.Field(description="SPDX license id")]
        python_required_version: Annotated[
            t.NonEmptyStr, m.Field(description="PEP 440 project Python requirement")
        ]
        kubectl_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kubectl toolchain version")
        ]
        helm_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Helm toolchain version")
        ]
        kind_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kind toolchain version")
        ]
        taplo_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Taplo formatter version")
        ]
        ast_grep_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact ast-grep analyzer version")
        ]
        gitleaks_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Gitleaks scanner version")
        ]
        tokei_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Tokei analyzer version")
        ]
        author_name: Annotated[
            t.NonEmptyStr, m.Field(description="Author display name")
        ]
        author_email: Annotated[t.NonEmptyStr, m.Field(description="Author email")]
        repository: Annotated[
            t.NonEmptyStr, m.Field(description="Project repository page URL")
        ]
        homepage: Annotated[t.NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            t.NonEmptyStr, m.Field(description="Project documentation URL")
        ]
        flext_git_base_url: Annotated[
            t.NonEmptyStr, m.Field(description="FLEXT Git provider base URL")
        ]
        flext_git_branch: Annotated[
            t.NonEmptyStr, m.Field(description="FLEXT Git provider branch")
        ]
        repository_provider: Annotated[
            t.NonEmptyStr, m.Field(description="Repository provider catalog key")
        ]
        repository_git_url: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical repository Git clone URL")
        ]
        repository_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical repository Git branch")
        ]
        workspace_manifest_version: Annotated[
            int,
            m.Field(
                ge=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                le=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                description="Workspace manifest schema version",
            ),
        ]
        workspace_repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Repository rendered into the workspace manifest"),
        ]
        year: Annotated[int, m.Field(description="Copyright year")]
        workspace_exclusions: Annotated[
            tuple[FlextInfraConfigModels.WorkspaceExclusionSpec, ...],
            m.Field(description="Ordered excluded workspace paths"),
        ] = ()
        workspace_policy_overlays: Annotated[
            tuple[FlextInfraConfigModels.RepositoryPolicyOverlaySpec, ...],
            m.Field(description="Repository-local policy overlays"),
        ] = ()

    class WorkspaceExclusionSpec(_ConfigContract):
        """One explicitly rejected workspace path and its reason."""

        path: Annotated[Path, m.Field(description="Workspace-relative path")]
        reason: Annotated[t.NonEmptyStr, m.Field(description="Exclusion rationale")]

    class WorkspaceSpec(_ConfigContract):
        """Declared topology for exactly one orchestrated workspace."""

        version: Annotated[
            int,
            m.Field(
                ge=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                le=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                description="Manifest version",
            ),
        ]
        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Root repository Git contract"),
        ]
        project: Annotated[
            FlextInfraConfigModels.ProjectSpec | None,
            m.Field(description="Metadata required only when materializing a new tree"),
        ] = None
        members: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered active member repository contracts"),
        ] = ()
        external_dependency_paths: Annotated[
            tuple[Path, ...],
            m.Field(description="Observed external or fork Git submodule paths"),
        ] = ()
        exclusions: Annotated[
            tuple[FlextInfraConfigModels.WorkspaceExclusionSpec, ...],
            m.Field(description="Ordered paths deliberately excluded from inventory"),
        ] = ()
        repository_policy_overlays: Annotated[
            tuple[FlextInfraConfigModels.RepositoryPolicyOverlaySpec, ...],
            m.Field(description="Repository-local policy exceptions keyed by project"),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_repository_policy_overlays(self) -> Self:
            """Require local overlays to reference one declared repository each."""
            invalid_external_paths = tuple(
                path
                for path in self.external_dependency_paths
                if path.is_absolute() or not path.parts or ".." in path.parts
            )
            if invalid_external_paths:
                msg = (
                    "external dependency paths must be workspace-relative: "
                    f"{', '.join(path.as_posix() for path in invalid_external_paths)}"
                )
                raise ValueError(msg)
            if len(set(self.external_dependency_paths)) != len(
                self.external_dependency_paths
            ):
                msg = "external dependency paths must be unique"
                raise ValueError(msg)
            member_paths = {item.path for item in self.members}
            overlap = member_paths.intersection(self.external_dependency_paths)
            if overlap:
                msg = (
                    "external dependencies cannot also be governed members: "
                    f"{', '.join(sorted(path.as_posix() for path in overlap))}"
                )
                raise ValueError(msg)
            projects = tuple(item.project for item in self.repository_policy_overlays)
            duplicates = tuple(
                project for project in projects if projects.count(project) > 1
            )
            if duplicates:
                msg = (
                    "repository policy overlays must be unique: "
                    f"{', '.join(sorted(set(duplicates)))}"
                )
                raise ValueError(msg)
            repository_names = {
                item.distribution for item in (self.repository, *self.members)
            }
            unknown = set(projects) - repository_names
            if unknown:
                msg = (
                    "repository policy overlays reference unknown projects: "
                    f"{', '.join(sorted(unknown))}"
                )
                raise ValueError(msg)
            return self

    # NOTE (mro-jnm1.1 / mro-jnm1.4): the artifact list is the SINGLE SSOT for
    # ephemeral/generated resources; VS Code excludes and source_scan ignores
    # are derived projections, never re-declared in YAML.
    class CodegenArtifactSpec(_ConfigContract):
        """One ephemeral/generated resource every ignore/exclude derives from."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Basename of the resource")]
        is_dir: Annotated[bool, m.Field(description="Directory (vs file) resource")] = (
            True
        )
        vscode_exclude: Annotated[
            bool, m.Field(description="Feed VS Code files.exclude + search.exclude")
        ] = True
        watch_exclude: Annotated[
            bool, m.Field(description="Feed VS Code files.watcherExclude")
        ] = True
        gitignore: Annotated[
            bool, m.Field(description="Feed the Python/tool section of .gitignore")
        ] = True
        source_scan_ignore: Annotated[
            bool, m.Field(description="Feed source_scan.ignored_resources")
        ] = False

    class CodegenVscodeSpec(_ConfigContract):
        """Fully modeled content of the ``vscode`` section of ``config/codegen.yaml``."""

        scalar_settings: Annotated[
            Mapping[str, str | bool],
            m.Field(description="VS Code scalar keys enforced on every project"),
        ]
        list_settings: Annotated[
            Mapping[str, tuple[str, ...]],
            m.Field(description="VS Code list keys enforced on every project"),
        ]
        map_union_settings: Annotated[
            Mapping[str, Mapping[str, str | bool]],
            m.Field(description="VS Code map keys union-merged over project settings"),
        ]

    class CodegenConfigSpec(_ConfigContract):
        """Fully modeled content of ``config/codegen.yaml``."""

        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        toolchain: Annotated[
            FlextInfraConfigModels.ToolchainSpec,
            m.Field(description="Exact generated toolchain"),
        ]
        github_actions: Annotated[
            Mapping[str, FlextInfraConfigModels.GithubActionPinSpec],
            m.Field(description="Immutable GitHub Action catalog"),
        ]
        uv_exclude_dependencies: Annotated[
            tuple[FlextInfraConfigModels.UvScopedDependencyExclusionSpec, ...],
            m.Field(description="Project-scoped official uv dependency exclusions"),
        ] = ()
        providers: Annotated[
            tuple[FlextInfraConfigModels.ProviderSpec, ...],
            m.Field(min_length=1, description="Ordered FLEXT-owned Git providers"),
        ]
        branch_policy: Annotated[
            FlextInfraConfigModels.BranchPolicySpec,
            m.Field(description="Global governed branch ancestry policy"),
        ]
        profiles: Annotated[
            tuple[FlextInfraConfigModels.ProfileSpec, ...],
            m.Field(description="Ordered Make profiles"),
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        vscode: Annotated[
            FlextInfraConfigModels.CodegenVscodeSpec,
            m.Field(description="Canonical VS Code settings merge contract"),
        ]
        artifacts: Annotated[
            tuple[FlextInfraConfigModels.CodegenArtifactSpec, ...],
            m.Field(
                min_length=1,
                description=(
                    "Ephemeral/generated artifact SSOT; every ignore/exclude "
                    "projection derives from this list"
                ),
            ),
        ]
        layout: Annotated[
            FlextInfraModelsLayout.LayoutSpec,
            m.Field(
                description=(
                    "Declarative project-layout conformance contract consumed "
                    "by the layout engine and the layout quality gate"
                )
            ),
        ]

        @m.computed_field()
        @property
        def vscode_files_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.exclude`` entries from the artifact SSOT."""
            return {
                f"**/{artifact.name}": True
                for artifact in self.artifacts
                if artifact.vscode_exclude
            }

        @m.computed_field()
        @property
        def vscode_watcher_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.watcherExclude`` entries from the SSOT."""
            return {
                f"**/{artifact.name}/**": True
                for artifact in self.artifacts
                if artifact.watch_exclude
            }

        @m.computed_field()
        @property
        def vscode_search_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``search.exclude`` entries from the artifact SSOT."""
            return dict(self.vscode_files_exclude_map)

        @m.computed_field()
        @property
        def source_scan_ignored(self) -> tuple[str, ...]:
            """Derived ``source_scan.ignored_resources`` names from the SSOT."""
            return tuple(
                artifact.name
                for artifact in self.artifacts
                if artifact.source_scan_ignore
            )

        # NOTE (mro-jnm1.2): the canonical .gitignore body is ONE computed
        # projection — the artifact SSOT feeds the Python/build section and the
        # static scaffold sections carry only what the SSOT cannot express
        # (file globs, secrets, editor/OS noise). Per-project exception fields
        # (extra_ignored / allowed dirs) land in WorkspaceSpec with mro-jnm1.3;
        # this projection is the seam they will extend.
        @m.computed_field()
        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...]:
            """Derived canonical ``.gitignore`` sections (SSOT order, deduplicated).

            Ignore files are order-sensitive: a pattern placed before a
            catch-all such as ``/*`` is dead, and a directory ignored before
            its own ``!`` negation is never re-allowed. The declared sections
            are therefore emitted in their declared order, and derived artifact
            patterns are appended -- never prepended -- so a whitelist policy
            expressed in the SSOT survives the projection intact.
            """
            scaffold_sections = self.scaffold.gitignore_sections
            # A declared section may already govern a derived artifact, in
            # either direction: a whitelist re-allows `.agents/` with `!`, so
            # appending a bare `.agents/` ignore would contradict the declared
            # policy. Only artifacts the SSOT never mentions are appended.
            governed = {
                pattern.lstrip("!")
                for section in scaffold_sections
                for pattern in section.patterns
            }
            managed_allowed: t.MutableSequenceOf[str] = []
            declared_patterns = {
                pattern for section in scaffold_sections for pattern in section.patterns
            }
            for managed in self.managed_files:
                if (
                    managed.policy
                    == FlextInfraConstantsSharedInfra.MANAGED_FILE_POLICY_DELEGATED
                ):
                    continue
                parts = managed.path.parts
                candidates = [
                    *(f"!{'/'.join(parts[:depth])}/" for depth in range(1, len(parts))),
                    f"!{managed.path.as_posix()}",
                ]
                managed_allowed.extend(
                    candidate
                    for candidate in candidates
                    if candidate not in declared_patterns
                    and candidate not in managed_allowed
                )
            derived: t.MutableSequenceOf[str] = []
            for pattern in self.gitignore_artifact_patterns:
                if pattern not in governed and pattern not in derived:
                    derived.append(pattern)
            sections: t.MutableSequenceOf[
                FlextInfraConfigModels.ScaffoldGitignoreSectionSpec
            ] = []
            # Declared sections are emitted verbatim. Cross-section dedup is
            # unsound for ignore files: repeating `.beads/*` after an
            # intervening `!.beads/` is what keeps the directory scanned, so
            # dropping the repeat silently un-ignores its contents.
            sections.extend(scaffold_sections)
            # Derived artifacts are appended as their own trailing section: an
            # ignore file is evaluated in order, so injecting them into the
            # first section would place them before any `!` negation the policy
            # declares later and silently un-ignore governed paths.
            if derived:
                sections.append(
                    FlextInfraConfigModels.ScaffoldGitignoreSectionSpec(
                        name=FlextInfraConstantsSharedInfra.GITIGNORE_DERIVED_SECTION_NAME,
                        patterns=tuple(derived),
                    )
                )
            if managed_allowed:
                sections.append(
                    FlextInfraConfigModels.ScaffoldGitignoreSectionSpec(
                        name=FlextInfraConstantsSharedInfra.GITIGNORE_MANAGED_SECTION_NAME,
                        patterns=tuple(managed_allowed),
                    )
                )
            return tuple(sections)

        @m.computed_field()
        @property
        def gitignore_artifact_patterns(self) -> tuple[str, ...]:
            """Derived ``.gitignore`` artifact patterns from the SSOT (stable order)."""
            return tuple(
                f"{artifact.name}/" if artifact.is_dir else artifact.name
                for artifact in self.artifacts
                if artifact.gitignore
            )

        managed_files: Annotated[
            tuple[FlextInfraConfigModels.ManagedFileSpec, ...],
            m.Field(description="Files owned by conform"),
        ]
        scaffold: Annotated[
            FlextInfraConfigModels.ScaffoldSpec,
            m.Field(description="Typed new-project scaffold policy"),
        ]
        templates: Annotated[
            FlextInfraConfigModels.TemplatesSpec,
            m.Field(description="New-project-only scaffold template manifest"),
        ]
        repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered repository catalog"),
        ]

    # NOTE (multi-agent, mro-wkii.17.24 / agent: codex): production source
    # selection is modeled once so iteration, Rope, and census share one SSOT.
    class SourceScanSpec(_ConfigContract):
        """Canonical production roots and recursively ignored directories."""

        roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Ordered production source directory names"),
        ]

    class StaticRule(_ConfigContract):
        """Shared immutable metadata for one Rope static-analysis rule."""

        kind: t.NonEmptyStr = m.Field(description="Violation kind")
        detail: t.NonEmptyStr = m.Field(description="Root-cause explanation")

    class StaticImportModuleRule(StaticRule):
        """Reject one imported module outside its configured owning project."""

        operator: Literal["import_module"] = m.Field(description="Operator")
        module: t.NonEmptyStr = m.Field(description="Rejected module root")
        owner_project: t.NonEmptyStr | None = m.Field(
            default=None, description="Permitted owning project"
        )

    class StaticImportMemberRule(StaticRule):
        """Reject one member imported from a configured module."""

        operator: Literal["import_member"] = m.Field(description="Operator")
        module: t.NonEmptyStr = m.Field(description="Import source module")
        member: t.NonEmptyStr = m.Field(description="Rejected imported member")

    class StaticAttributeRule(StaticRule):
        """Reject one member accessed through a semantically imported module alias."""

        operator: Literal["attribute"] = m.Field(description="Operator")
        module: t.NonEmptyStr = m.Field(description="Imported module")
        member: t.NonEmptyStr = m.Field(description="Rejected attribute")

    class StaticCallRule(StaticRule):
        """Reject calls to one bare callable name."""

        operator: Literal["call"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Rejected callable")

    class StaticCallKeywordRule(StaticRule):
        """Require one keyword in calls to a configured callable."""

        operator: Literal["call_keyword"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Callable")
        keyword: t.NonEmptyStr = m.Field(description="Required keyword")

    class StaticAnnotationRule(StaticRule):
        """Reject one identifier anywhere in an annotation."""

        operator: Literal["annotation"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Rejected annotation identifier")

    class StaticBareExceptRule(StaticRule):
        """Reject an exception handler without an exception contract."""

        operator: Literal["bare_except"] = m.Field(description="Operator")

    class StaticAnnotatedStringRule(StaticRule):
        """Reject an annotated target assigned directly to a string literal."""

        operator: Literal["annotated_string"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Rejected assignment target")

    class StaticCommentRule(StaticRule):
        """Reject one marker only when Rope classifies its region as a comment."""

        operator: Literal["comment"] = m.Field(description="Operator")
        marker: t.NonEmptyStr = m.Field(description="Rejected comment marker")

    type StaticRuleSpec = Annotated[
        StaticImportModuleRule
        | StaticImportMemberRule
        | StaticAttributeRule
        | StaticCallRule
        | StaticCallKeywordRule
        | StaticAnnotationRule
        | StaticBareExceptRule
        | StaticAnnotatedStringRule
        | StaticCommentRule,
        m.Field(discriminator="operator"),
    ]

    class StaticEnforcementSpec(_ConfigContract):
        """Complete validated static policy evaluated only through Rope facts."""

        rules: Annotated[
            tuple[FlextInfraConfigModels.StaticRuleSpec, ...],
            m.Field(min_length=1, description="Ordered static-analysis rules"),
        ]

    # NOTE (multi-agent, mro-wkii.9 + mro-wkii.17 / agent: codex): this
    # field-only namespace is the sole validated owner exposed as config.Infra.
    class Infra(_ConfigContract):
        """Complete flext-infra configuration namespace."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project distribution name")]
        version: Annotated[
            t.NonEmptyStr, m.Field(description="Project release version")
        ]
        codegen: Annotated[
            FlextInfraConfigModels.CodegenConfigSpec,
            m.Field(description="Unified project and workspace codegen contract"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolSettings.ToolConfigDocument,
            m.Field(description="Validated lint, typecheck, and scaffold policy"),
        ]
        source_scan: Annotated[
            FlextInfraConfigModels.SourceScanSpec,
            m.Field(description="Production-only source discovery contract"),
        ]
        # mro-j47u (codex): static policy is validated data, never detector code.
        enforcement: Annotated[
            FlextInfraConfigModels.StaticEnforcementSpec,
            m.Field(description="Rope-only static enforcement policy"),
        ]

    class Root(_ConfigContract):
        """Root payload deep-merged from flext-infra config files."""

        Infra: Annotated[
            FlextInfraConfigModels.Infra,
            m.Field(description="Validated flext-infra namespace"),
        ]

    class UvEnvironmentPlan(_ConfigContract):
        """One deterministic uv environment operation plan."""

        project_root: Annotated[Path, m.Field(description="Selected project root")]
        environment_root: Annotated[
            Path, m.Field(description="Project supplying the active .venv")
        ]
        lock_path: Annotated[Path, m.Field(description="Required versioned uv.lock")]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Mise/Python version selector")
        ]
        groups: Annotated[
            tuple[str, ...],
            m.Field(description="Ordered dependency groups synchronized by setup"),
        ]
        editable_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Local repositories overlaid after locked sync"),
        ] = ()

    class BeadsPlan(_ConfigContract):
        """One repository-local Beads lifecycle owned by conform."""

        repository_root: Annotated[
            Path, m.Field(description="Repository receiving Beads initialization")
        ]
        enabled: Annotated[
            bool, m.Field(description="Whether this repository owns a Beads tracker")
        ]
        canonical_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required issue prefix derived from project metadata"),
        ]
        expected_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact official Beads version pinned by mise"),
        ]

    class BranchAncestryRef(_ConfigContract):
        """One exact branch or registered worktree ancestry observation."""

        reference: Annotated[
            t.NonEmptyStr, m.Field(description="Git ref or worktree identity")
        ]
        sha: Annotated[
            t.NonEmptyStr, m.Field(description="Observed commit object identifier")
        ]
        excluded: Annotated[
            bool, m.Field(description="Whether typed technical policy excludes the ref")
        ]
        ancestor: Annotated[
            bool | None,
            m.Field(description="Baseline ancestry verdict; None when excluded"),
        ]

    class BranchAncestryPlan(_ConfigContract):
        """Bounded ancestry inventory for one governed repository."""

        repository_root: Annotated[
            Path, m.Field(description="Governed repository root")
        ]
        baseline_reference: Annotated[
            t.NonEmptyStr, m.Field(description="Provider-owned remote baseline ref")
        ]
        baseline_sha: Annotated[
            t.NonEmptyStr, m.Field(description="Resolved baseline commit")
        ]
        references: Annotated[
            tuple[FlextInfraConfigModels.BranchAncestryRef, ...],
            m.Field(description="Local, remote, and worktree ancestry inventory"),
        ]

    class CodegenConformRequest(_ConfigContract):
        """Validated public request for ``flext-infra codegen conform``."""

        root: Annotated[Path, m.Field(description="Repository or workspace root")]
        what: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformSurface,
            m.Field(description="Managed file selection"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformSurface.ALL
        scope: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformScope,
            m.Field(description="Repository selection scope"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformScope.SELF
        mode: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformMode,
            m.Field(description="Read-only check or atomic apply"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformMode.CHECK

    class CodegenFilePlan(_ConfigContract):
        """Expected content and current state for one managed file."""

        path: Annotated[Path, m.Field(description="Absolute managed file path")]
        rendered: Annotated[str, m.Field(description="Fully rendered expected content")]
        expected_sha256: Annotated[
            t.NonEmptyStr, m.Field(description="SHA-256 of expected content")
        ]
        owner: Annotated[
            str,
            m.Field(description="Canonical artifact owner, empty for scaffold files"),
        ] = ""
        policy: Annotated[
            Literal["full", "merge", "create-only", "delegated", "manual"] | None,
            m.Field(description="Governed root artifact policy"),
        ] = None
        current_sha256: Annotated[
            str, m.Field(description="SHA-256 of current content, empty when missing")
        ] = ""
        changed: Annotated[bool, m.Field(description="Whether content differs")]
        blocked: Annotated[
            bool, m.Field(description="Whether unrecognized WIP blocks application")
        ] = False
        reason: Annotated[str, m.Field(description="Blocking explanation")] = ""

    class CodegenPlan(_ConfigContract):
        """Fully validated plan produced before any managed-file write."""

        request: Annotated[
            FlextInfraConfigModels.CodegenConformRequest,
            m.Field(description="Validated public request"),
        ]
        repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            FlextInfraConfigModels.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        make_spec: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        uv_environments: Annotated[
            tuple[FlextInfraConfigModels.UvEnvironmentPlan, ...],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        beads: Annotated[
            tuple[FlextInfraConfigModels.BeadsPlan, ...],
            m.Field(description="Beads lifecycle plans paired with repositories"),
        ]
        branch_ancestry: Annotated[
            tuple[FlextInfraConfigModels.BranchAncestryPlan, ...],
            m.Field(description="Governed branch ancestry observations"),
        ]
        files: Annotated[
            tuple[FlextInfraConfigModels.CodegenFilePlan, ...],
            m.Field(description="All render results validated before application"),
        ]

    class CodegenResult(_ConfigContract):
        """Public conformance outcome for check and apply modes."""

        plan: Annotated[
            FlextInfraConfigModels.CodegenPlan,
            m.Field(description="Plan that governed the operation"),
        ]
        written_files: Annotated[
            tuple[Path, ...], m.Field(description="Files atomically replaced by apply")
        ] = ()
        errors: Annotated[
            tuple[str, ...],
            m.Field(description="Fail-closed validation or write errors"),
        ] = ()


__all__: list[str] = ["FlextInfraConfigModels"]
