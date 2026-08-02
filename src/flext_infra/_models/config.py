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
        reported_version: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Version string the pinned binary self-reports; runtime "
                    "gates compare exactly against this value. It differs from "
                    "the mise selector version whenever the pin is a go-module "
                    "commit whose --version output is the module version."
                )
            ),
        ]
        checksum: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                pattern=r"^[0-9a-f]{64}$",
                description=(
                    "SHA-256 of the pinned artifact; runtime verification fails "
                    "closed when the resolved binary digest diverges"
                ),
            ),
        ] = None
        expected_schema: Annotated[
            int | None,
            m.Field(
                gt=0,
                description=(
                    "Schema version the pinned tool must report for its managed "
                    "data store (e.g. the Beads Dolt ledger schema)"
                ),
            ),
        ] = None

    class BeadsServerSpec(_ConfigContract):
        """Machine-wide shared Dolt server connection for Beads ledgers."""

        mode: Annotated[
            Literal["server"],
            m.Field(description="Dolt connection mode; ledgers never embed locally"),
        ]
        shared_server: Annotated[
            bool,
            m.Field(description="Route through the machine-wide shared Dolt server"),
        ]
        host: Annotated[t.NonEmptyStr, m.Field(description="Dolt server host")]
        port: Annotated[int, m.Field(gt=0, le=65535, description="Dolt server port")]
        user: Annotated[t.NonEmptyStr, m.Field(description="Dolt server user")]
        auto_commit: Annotated[
            Literal["off", "on", "batch"],
            m.Field(description="Dolt auto-commit policy for ledger writes"),
        ]

    class BeadsToolSpec(MiseToolSpec):
        """Beads tool pin plus the shared Dolt ledger connection."""

        server: Annotated[
            FlextInfraConfigModels.BeadsServerSpec | None,
            m.Field(
                description=(
                    "Shared Dolt server connection rendered into ledger routing "
                    "configs; None keeps repository-local embedded state"
                )
            ),
        ] = None

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
        qlty: Annotated[
            FlextInfraConfigModels.MiseToolSpec,
            m.Field(description="Official Qlty CLI installed through mise"),
        ]
        mise_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact mise binary version")
        ]
        beads: Annotated[
            FlextInfraConfigModels.BeadsToolSpec,
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
        """One GitHub organization and its default repository policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Provider key")]
        organization: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub organization")
        ]
        base_url: Annotated[t.NonEmptyStr, m.Field(description="GitHub HTTPS base URL")]
        branch: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Default integration branch used only when a repository has "
                    "not declared or published its own branch"
                )
            ),
        ]

    class BranchPolicySpec(_ConfigContract):
        """Global ancestry policy shared by every governed provider."""

        production_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical branch receiving integration promotions"),
        ]
        technical_branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "GitHub/Dolt technical branches excluded from ancestry validation"
                )
            ),
        ]
        additional_governed_branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Additional governed lines beyond production and provider branches"
                )
            ),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_technical_patterns(self) -> Self:
            """Reject duplicate branch policy rows without embedding policy literals."""
            if len(set(self.technical_branch_patterns)) != len(
                self.technical_branch_patterns
            ):
                msg = "technical branch patterns must be unique"
                raise ValueError(msg)
            if len(set(self.additional_governed_branch_patterns)) != len(
                self.additional_governed_branch_patterns
            ):
                msg = "additional governed branch patterns must be unique"
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
        production_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Configured promotion target branch")
        ]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor line")
        ]
        github_actions: Annotated[
            Mapping[str, FlextInfraConfigModels.GithubActionPinSpec],
            m.Field(description="Immutable GitHub Action catalog"),
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
        ]
        workspace_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(
                default=(),
                description=(
                    "Governed member repositories consumed by workspace-scoped "
                    "workflow templates (docs paths, dependabot directories)"
                ),
            ),
        ]
        checkout_submodules: Annotated[
            t.NonEmptyStr,
            m.Field(
                default="false",
                pattern=r"^(true|false|recursive)$",
                description=(
                    "actions/checkout submodules mode. Defaults to 'false' "
                    "because the default GITHUB_TOKEN cannot clone sibling "
                    "private repositories: 'recursive' aborts the job at "
                    "checkout with 'Repository not found'. Projects whose "
                    "submodules are public, or that provide a PAT, override "
                    "it per project in codegen.yaml"
                ),
            ),
        ]

    class MakeWorkflowRenderSpec(_ConfigContract):
        """Typed input shared by generated local workflow surfaces."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
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
            Literal["root", "self"], m.Field(description="uv environment ownership")
        ]
        setup_scope: Annotated[
            Literal["root", "root-and-members", "self"],
            m.Field(description="setup orchestration scope"),
        ]
        execution_scope: Annotated[
            Literal["root", "self"], m.Field(description="check/test runtime scope")
        ]
        discovery_scope: Annotated[
            Literal["manifest", "root", "none"],
            m.Field(description="repository discovery policy"),
        ]

    class MakeWorkflowMembershipSpec(_ConfigContract):
        """Ordered workflow membership owned by one concrete Make handler."""

        order: Annotated[
            int, m.Field(gt=0, description="Unique canonical workflow position")
        ]
        contexts: Annotated[
            tuple[Literal["local", "ci", "pre_commit"], ...],
            m.Field(
                min_length=1,
                description="Execution contexts consuming this single workflow row",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_contexts(self) -> Self:
            """Require unique contexts and retain every step in the local workflow."""
            if len(set(self.contexts)) != len(self.contexts):
                msg = "make workflow contexts must be unique"
                raise ValueError(msg)
            if "local" not in self.contexts:
                msg = "every make workflow handler must run locally"
                raise ValueError(msg)
            return self

    class MakeInputSpec(_ConfigContract):
        """One typed caller input transported from Make to the runtime engine."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[a-z][a-z0-9_-]*$",
                description="Logical input name consumed by operations",
            ),
        ]
        variables: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Equivalent public Make variables for this input",
            ),
        ]
        codec: Annotated[
            Literal[
                "argv",
                "boolean",
                "branch",
                "distribution-name",
                "expression",
                "gate-selection",
                "path",
                "path-nodeid",
                "project-selection",
            ],
            m.Field(description="Canonical boundary parser for the input value"),
        ]

        @u.model_validator(mode="after")
        def _validate_variables(self) -> Self:
            """Reject ambiguous or invalid public Make variable names."""
            if len(set(self.variables)) != len(self.variables):
                msg = f"make input {self.name} variables must be unique"
                raise ValueError(msg)
            invalid = tuple(
                variable
                for variable in self.variables
                if not variable.replace("_", "").isalnum()
                or variable != variable.upper()
                or variable[0].isdigit()
            )
            if invalid:
                msg = (
                    f"make input {self.name} has invalid variables: "
                    f"{', '.join(invalid)}"
                )
                raise ValueError(msg)
            return self

    class MakeOperationSpec(_ConfigContract):
        """One reusable runtime operation selected by public Make verbs."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[a-z][a-z0-9_.-]*$",
                description="Stable operation identifier owned by the runtime engine",
            ),
        ]
        executor: Annotated[
            Literal["bootstrap", "runtime", "generation", "script"],
            m.Field(description="Typed execution boundary for this operation"),
        ]
        scope: Annotated[
            Literal["self", "environment-owner", "governed-selection"],
            m.Field(description="Capability-derived repository selection scope"),
        ]
        consistency: Annotated[
            Literal["none", "single-flight"],
            m.Field(description="Concurrency contract for one complete operation"),
        ] = "none"
        mutation: Annotated[
            Literal["never", "apply", "always"],
            m.Field(description="Sole repository mutation policy for the operation"),
        ] = "never"
        requires: Annotated[
            tuple[Literal["environment", "git", "managed", "package", "script"], ...],
            m.Field(description="Repository capabilities required by the operation"),
        ] = ()
        inputs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Logical caller inputs accepted by the operation"),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_operation(self) -> Self:
            """Reject repeated capabilities or input references."""
            if len(set(self.requires)) != len(self.requires):
                msg = f"make operation {self.name} capabilities must be unique"
                raise ValueError(msg)
            if len(set(self.inputs)) != len(self.inputs):
                msg = f"make operation {self.name} inputs must be unique"
                raise ValueError(msg)
            return self

    class MakeHandlerSpec(_ConfigContract):
        """One public WHAT selector bound to its operation inputs and APPLY policy."""

        what: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^[a-z][a-z0-9-]*$", description="Public WHAT selector"),
        ]
        default: Annotated[
            bool, m.Field(description="Whether this is the no-argument selector")
        ] = False
        apply_policy: Annotated[
            Literal["never", "required", "optional"],
            m.Field(description="Exact APPLY contract for this handler"),
        ] = "never"
        apply_default: Annotated[
            bool, m.Field(description="Whether APPLY without WHAT selects this handler")
        ] = False
        required_inputs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Operation inputs required by this selector"),
        ] = ()
        workflow: Annotated[
            FlextInfraConfigModels.MakeWorkflowMembershipSpec | None,
            m.Field(description="Optional canonical workflow membership"),
        ] = None

        @u.model_validator(mode="after")
        def _validate_handler(self) -> Self:
            """Reject duplicated inputs and contradictory APPLY contracts."""
            if self.apply_default and self.apply_policy == "never":
                msg = f"read-only handler {self.what} cannot be the APPLY default"
                raise ValueError(msg)
            if len(set(self.required_inputs)) != len(self.required_inputs):
                msg = f"Make handler {self.what} required inputs must be unique"
                raise ValueError(msg)
            return self

    class MakeVerbSpec(_ConfigContract):
        """One public Make verb; every derived surface consumes its handlers."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^[a-z][a-z0-9-]*$", description="Public Make verb"),
        ]
        operation: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical runtime operation used by this verb"),
        ]
        handlers: Annotated[
            tuple[FlextInfraConfigModels.MakeHandlerSpec, ...],
            m.Field(min_length=1, description="Complete ordered handler tree"),
        ]

        @u.model_validator(mode="after")
        def _validate_handlers(self) -> Self:
            """Require one default and unique selectors/defaults per verb."""
            whats = tuple(handler.what for handler in self.handlers)
            if len(set(whats)) != len(whats):
                msg = f"make verb {self.name} handler selectors must be unique"
                raise ValueError(msg)
            defaults = tuple(handler for handler in self.handlers if handler.default)
            if len(defaults) != 1:
                msg = f"make verb {self.name} requires exactly one default handler"
                raise ValueError(msg)
            apply_defaults = tuple(
                handler for handler in self.handlers if handler.apply_default
            )
            if len(apply_defaults) > 1:
                msg = f"make verb {self.name} has multiple APPLY defaults"
                raise ValueError(msg)
            workflow_handlers = tuple(
                handler for handler in self.handlers if handler.workflow is not None
            )
            if len(workflow_handlers) > 1:
                msg = f"make verb {self.name} has multiple workflow handlers"
                raise ValueError(msg)
            return self

        @m.computed_field()
        @property
        def whats(self) -> tuple[str, ...]:
            """Ordered selectors derived from the handler tree."""
            return tuple(handler.what for handler in self.handlers)

        @m.computed_field()
        @property
        def default_what(self) -> str:
            """No-argument selector derived from the sole default handler."""
            return next(handler.what for handler in self.handlers if handler.default)

        @m.computed_field()
        @property
        def apply_default_what(self) -> str | None:
            """Explicit selector used only when APPLY is present without WHAT."""
            return next(
                (handler.what for handler in self.handlers if handler.apply_default),
                None,
            )

        @m.computed_field()
        @property
        def apply_what(self) -> str:
            """APPLY selector, falling back to the ordinary default when valid."""
            return self.apply_default_what or self.default_what

        @m.computed_field()
        @property
        def apply_guarded(self) -> bool:
            """Whether at least one handler accepts or requires APPLY."""
            return any(handler.apply_policy != "never" for handler in self.handlers)

        @m.computed_field()
        @property
        def required_apply_whats(self) -> tuple[str, ...]:
            """Handlers that fail closed without APPLY."""
            return tuple(
                handler.what
                for handler in self.handlers
                if handler.apply_policy == "required"
            )

        @m.computed_field()
        @property
        def optional_apply_whats(self) -> tuple[str, ...]:
            """Handlers supporting both preview and apply modes."""
            return tuple(
                handler.what
                for handler in self.handlers
                if handler.apply_policy == "optional"
            )

        @m.computed_field()
        @property
        def never_apply_whats(self) -> tuple[str, ...]:
            """Strictly read-only handlers."""
            return tuple(
                handler.what
                for handler in self.handlers
                if handler.apply_policy == "never"
            )

    class MakeWorkflowStepSpec(_ConfigContract):
        """Computed workflow projection from one handler row."""

        verb: Annotated[t.NonEmptyStr, m.Field(description="Declared public verb")]
        what: Annotated[t.NonEmptyStr, m.Field(description="Selected handler")]
        apply: Annotated[
            bool, m.Field(description="Whether the selected handler receives APPLY")
        ]
        contexts: Annotated[
            tuple[Literal["local", "ci", "pre_commit"], ...],
            m.Field(description="Contexts consuming this handler"),
        ]

    class MakeInputValueSpec(_ConfigContract):
        """One normalized logical input resolved from its public Make variables."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Logical input name")]
        values: Annotated[
            tuple[str, ...],
            m.Field(description="Canonical values produced by the configured codec"),
        ] = ()

    class MakeInvocationSpec(_ConfigContract):
        """One fully resolved request crossing the public Make boundary."""

        verb: Annotated[
            FlextInfraConfigModels.MakeVerbSpec,
            m.Field(description="Resolved public verb and its sole handler tree"),
        ]
        operation: Annotated[
            FlextInfraConfigModels.MakeOperationSpec,
            m.Field(description="Resolved canonical runtime operation"),
        ]
        handler: Annotated[
            FlextInfraConfigModels.MakeHandlerSpec,
            m.Field(description="Selected canonical handler row"),
        ]
        applying: Annotated[
            bool, m.Field(description="Whether the validated APPLY token is active")
        ]
        target_scope: Annotated[
            Literal["profile", "self"],
            m.Field(description="Effective config-resolved repository target scope"),
        ]
        inputs: Annotated[
            tuple[FlextInfraConfigModels.MakeInputValueSpec, ...],
            m.Field(description="Inputs parsed once at the external boundary"),
        ]

    class MakeCiSpec(_ConfigContract):
        """The only permitted environment delta between local and CI execution."""

        variable: Annotated[t.NonEmptyStr, m.Field(description="CI environment key")]
        value: Annotated[t.NonEmptyStr, m.Field(description="CI environment value")]
        target_scope: Annotated[
            Literal["profile", "self"],
            m.Field(description="Repository target scope active in CI"),
        ]

    class MakeExecutorSpec(_ConfigContract):
        """Canonical CLI boundary invoked by every generated Make recipe."""

        group: Annotated[t.NonEmptyStr, m.Field(description="CLI command group")]
        route: Annotated[t.NonEmptyStr, m.Field(description="CLI command route")]

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

    class MakeSerializationSpec(_ConfigContract):
        """Portable per-checkout serialization for state-sensitive Make verbs."""

        lock_path: Annotated[
            Path, m.Field(description="Repository-relative native process-lock path")
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

        @m.field_validator("lock_path")
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
            if self.lock_path not in self.snapshot_excludes:
                msg = (
                    "make serialization lock path must be snapshot-excluded: "
                    f"{self.lock_path.as_posix()}"
                )
                raise ValueError(msg)
            return self

    class MakeBootstrapSpec(_ConfigContract):
        """Hermetic project dependency surface used before conform."""

        environment: Annotated[
            Literal["isolated"], m.Field(description="uv environment isolation policy")
        ]
        dependency_groups: Annotated[
            Literal["all"],
            m.Field(description="Project dependency-group selection policy"),
        ]
        extras: Annotated[
            Literal["all"],
            m.Field(description="Project optional-dependency selection policy"),
        ]

    class MakeDocsSpec(_ConfigContract):
        """Generated Makefile docs verb lifecycle and audit policy."""

        reports_dir: Annotated[
            Path, m.Field(description="Repository-relative docs reports directory")
        ]
        cross_project_relative_link_pattern: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Regex rejecting cross-project relative Markdown links"
            ),
        ]

    class MakeTestSpec(_ConfigContract):
        """Generated Make test-runner output policy."""

        reports_dir: Annotated[
            Path, m.Field(description="Repository-relative test reports directory")
        ]

    class MakeCheckGateSpec(_ConfigContract):
        """One ordered executable check-gate policy row."""

        id: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^[a-z][a-z0-9-]*$", description="Runtime gate id"),
        ]
        command: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Config-owned external command argv"),
        ] = ()
        execution_scope: Annotated[
            Literal["project", "workspace"],
            m.Field(description="Root from which the gate command executes"),
        ] = "project"
        mode: Annotated[
            Literal["error", "warn"],
            m.Field(description="Configured gate failure posture"),
        ] = "error"
        profiles: Annotated[
            tuple[Literal["safe-execution"], ...],
            m.Field(description="Named reusable gate subsets containing this row"),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_profiles(self) -> Self:
            if len(set(self.profiles)) != len(self.profiles):
                msg = f"make check gate {self.id} profiles must be unique"
                raise ValueError(msg)
            return self

    class MakeCheckSpec(_ConfigContract):
        """Ordered policy for every executable check gate."""

        gates: Annotated[
            tuple[FlextInfraConfigModels.MakeCheckGateSpec, ...],
            m.Field(min_length=1, description="Complete ordered check gate catalog"),
        ]

        @u.model_validator(mode="after")
        def _validate_gates(self) -> Self:
            ids = tuple(item.id for item in self.gates)
            if len(set(ids)) != len(ids):
                msg = "make check gate ids must be unique"
                raise ValueError(msg)
            return self

        @m.computed_field()
        @property
        def gate_ids(self) -> tuple[str, ...]:
            """Every configured gate exactly once in execution order."""
            return tuple(item.id for item in self.gates)

        def gate_for(
            self, gate_id: str
        ) -> FlextInfraConfigModels.MakeCheckGateSpec | None:
            """Return the config-owned execution row for one gate id."""
            return next((item for item in self.gates if item.id == gate_id), None)

        def profile_gate_ids(self, profile: str) -> tuple[str, ...]:
            """Return the configured ordered subset for one named profile."""
            return tuple(item.id for item in self.gates if profile in item.profiles)

    class MakeSpec(_ConfigContract):
        """Complete generated Makefile public and extension contract."""

        executor: Annotated[
            FlextInfraConfigModels.MakeExecutorSpec,
            m.Field(description="Single runtime operation dispatcher"),
        ]

        selector: Annotated[
            t.NonEmptyStr, m.Field(description="Single selector variable name")
        ]
        apply_variable: Annotated[
            t.NonEmptyStr, m.Field(description="Write-enable variable name")
        ]
        apply_value: Annotated[
            t.NonEmptyStr, m.Field(description="Only accepted write-enable value")
        ]
        apply_absent_value: Annotated[
            t.NonEmptyStr,
            m.Field(
                default="N",
                description=(
                    "Value the generated Makefile seeds when the caller enables "
                    "nothing. It is forwarded verbatim on every read-only run, "
                    "so the boundary must read it as 'not applying' instead of "
                    "as an invalid write-enable token"
                ),
            ),
        ]
        input_environment_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[A-Z][A-Z0-9_]*_$",
                description="Namespace used to transport declared Make inputs",
            ),
        ]
        bootstrap: Annotated[
            FlextInfraConfigModels.MakeBootstrapSpec,
            m.Field(description="Pre-conform project environment contract"),
        ]
        serialization: Annotated[
            FlextInfraConfigModels.MakeSerializationSpec,
            m.Field(description="Per-checkout Make validation serialization"),
        ]
        ci: Annotated[
            FlextInfraConfigModels.MakeCiSpec,
            m.Field(description="Config-owned CI-only environment delta"),
        ]
        inputs: Annotated[
            tuple[FlextInfraConfigModels.MakeInputSpec, ...],
            m.Field(description="Complete typed public input catalog"),
        ]
        operations: Annotated[
            tuple[FlextInfraConfigModels.MakeOperationSpec, ...],
            m.Field(description="Reusable capability-driven runtime operations"),
        ]
        verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Ordered canonical public verbs"),
        ]
        docs: Annotated[
            FlextInfraConfigModels.MakeDocsSpec,
            m.Field(description="Public documentation lifecycle policy"),
        ]
        test: Annotated[
            FlextInfraConfigModels.MakeTestSpec,
            m.Field(description="Public test-runner policy"),
        ]
        check: Annotated[
            FlextInfraConfigModels.MakeCheckSpec,
            m.Field(description="Complete executable check-gate policy"),
        ]

        @u.model_validator(mode="after")
        def _validate_handler_tree(self) -> Self:
            """Validate inputs, operations, verbs, and handlers as one graph."""
            input_names = tuple(item.name for item in self.inputs)
            if len(set(input_names)) != len(input_names):
                msg = "make input names must be unique"
                raise ValueError(msg)
            variables = tuple(
                variable for item in self.inputs for variable in item.variables
            )
            if len(set(variables)) != len(variables):
                msg = "public Make input variables must have one logical owner"
                raise ValueError(msg)
            operation_names = tuple(item.name for item in self.operations)
            if len(set(operation_names)) != len(operation_names):
                msg = "make operation names must be unique"
                raise ValueError(msg)
            input_name_set = set(input_names)
            for operation in self.operations:
                unknown_inputs = set(operation.inputs) - input_name_set
                if unknown_inputs:
                    msg = (
                        f"make operation {operation.name} references unknown inputs: "
                        f"{', '.join(sorted(unknown_inputs))}"
                    )
                    raise ValueError(msg)
            declared = {verb.name for verb in self.verbs}
            if len(declared) != len(self.verbs):
                msg = "make public verb names must be unique"
                raise ValueError(msg)
            if len(set(self.hook_targets)) != len(self.hook_targets):
                msg = "make verb and handler names produce colliding hook targets"
                raise ValueError(msg)
            operations = {operation.name: operation for operation in self.operations}
            unknown_operation = next(
                (verb for verb in self.verbs if verb.operation not in operations),
                None,
            )
            if unknown_operation is not None:
                msg = (
                    f"make verb {unknown_operation.name} references unknown operation "
                    f"{unknown_operation.operation}"
                )
                raise ValueError(msg)
            for verb in self.verbs:
                operation = operations[verb.operation]
                allowed_inputs = set(operation.inputs)
                for handler in verb.handlers:
                    unknown_required = set(handler.required_inputs) - allowed_inputs
                    if unknown_required:
                        msg = (
                            f"make handler {verb.name}:{handler.what} requires "
                            f"unsupported inputs: {', '.join(sorted(unknown_required))}"
                        )
                        raise ValueError(msg)
                handler_accepts_apply = any(
                    handler.apply_policy != "never" for handler in verb.handlers
                )
                if handler_accepts_apply != (operation.mutation == "apply"):
                    msg = (
                        f"make verb {verb.name} APPLY policy diverges from operation "
                        f"mutation={operation.mutation}"
                    )
                    raise ValueError(msg)
                if operation.mutation != "never" and (
                    operation.consistency != "single-flight"
                ):
                    msg = (
                        f"mutating make verb {verb.name} must use a single-flight "
                        "operation"
                    )
                    raise ValueError(msg)
            workflow_orders = tuple(
                handler.workflow.order
                for verb in self.verbs
                for handler in verb.handlers
                if handler.workflow is not None
            )
            if not workflow_orders or len(set(workflow_orders)) != len(workflow_orders):
                msg = "make workflow handler orders must be nonempty and unique"
                raise ValueError(msg)
            generation_operations = tuple(
                operation
                for operation in self.operations
                if operation.executor == "generation"
            )
            generation_verbs = tuple(
                verb
                for verb in self.verbs
                if operations[verb.operation].executor == "generation"
            )
            if len(generation_operations) != 1 or len(generation_verbs) != 1:
                msg = "make graph requires exactly one generation operation and verb"
                raise ValueError(msg)
            if (
                self.docs.reports_dir.is_absolute()
                or ".." in self.docs.reports_dir.parts
            ):
                msg = "make docs reports_dir must be repository-relative"
                raise ValueError(msg)
            if (
                self.test.reports_dir.is_absolute()
                or ".." in self.test.reports_dir.parts
            ):
                msg = "make test reports_dir must be repository-relative"
                raise ValueError(msg)
            return self

        @m.computed_field()
        @property
        def workflow(self) -> tuple[FlextInfraConfigModels.MakeWorkflowStepSpec, ...]:
            """Ordered validation workflow derived from handler memberships."""
            rows = sorted(
                (
                    (handler.workflow, verb, handler)
                    for verb in self.verbs
                    for handler in verb.handlers
                    if handler.workflow is not None
                ),
                key=lambda row: row[0].order,
            )
            return tuple(
                FlextInfraConfigModels.MakeWorkflowStepSpec(
                    verb=verb.name,
                    what=handler.what,
                    apply=handler.apply_policy != "never",
                    contexts=membership.contexts,
                )
                for membership, verb, handler in rows
            )

        @m.computed_field()
        @property
        def hook_targets(self) -> tuple[str, ...]:
            """Ordered hooks derived exclusively from the verb-handler graph."""
            return tuple(
                target
                for verb in self.verbs
                for phase in ("pre", "post")
                for target in (
                    f"{phase}-{verb.name}",
                    *(
                        f"{phase}-{verb.name}-{handler.what}"
                        for handler in verb.handlers
                    ),
                )
            )

    class ManagedSurfaceSpec(_ConfigContract):
        """One owned repository surface and its complete projection contract."""

        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative output path"),
        ]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical owner")]
        policy: Annotated[
            Literal["full", "merge", "create-only", "manual"],
            m.Field(description="Canonical ownership and mutation policy"),
        ]
        source: Annotated[
            Path | None, m.Field(description="Optional template-root-relative source")
        ] = None
        profiles: Annotated[
            tuple[FlextInfraConstantsCodegenProject.MakeProfile, ...],
            m.Field(
                min_length=1, description="Repository profiles consuming this surface"
            ),
        ] = tuple(FlextInfraConstantsCodegenProject.MakeProfile)
        delegate: Annotated[
            Literal["render", "manifest", "vscode-settings"],
            m.Field(description="Canonical surface rendering delegate"),
        ] = "render"
        render_context: Annotated[
            Literal[
                "project",
                "gitignore",
                "sgconfig",
                "make-workflow",
                "toolchain",
                "tooling",
                "beads",
                "github",
                "docker",
                "make",
            ],
            m.Field(description="Typed context factory selected for this projection"),
        ] = "project"
        surface: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformSurface,
            m.Field(description="Read-only conform surface"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformSurface.ALL
        make_role: Annotated[
            Literal["none", "wrapper", "engine"],
            m.Field(description="Role within the generated Make include surface"),
        ] = "none"
        requires_ci: Annotated[
            bool, m.Field(description="Render only for repositories with CI enabled")
        ] = False
        requires_beads: Annotated[
            bool,
            m.Field(description="Render only for repositories owning/routing Beads"),
        ] = False
        merge_strategy: Annotated[
            Literal["replace", "gitmodules"],
            m.Field(description="Config-selected projection merge strategy"),
        ] = "replace"

        @property
        def operations(self) -> tuple[Literal["scaffold", "conform", "generate"], ...]:
            """Keep generated projections exclusive to scaffold and generation."""
            if self.policy in {"create-only", "manual"}:
                return ("scaffold",)
            return ("scaffold", "generate")

        @u.model_validator(mode="after")
        def _validate_surface_contract(self) -> Self:
            """Reject unsafe paths and contradictory lifecycle declarations."""
            output_path = Path(self.path)
            if (
                output_path.is_absolute()
                or output_path == Path()
                or ".." in output_path.parts
            ):
                msg = f"surface path must stay repository-relative: {self.path}"
                raise ValueError(msg)
            if len(set(self.profiles)) != len(self.profiles):
                msg = f"surface profiles must be unique: {self.path}"
                raise ValueError(msg)
            if self.source is not None and (
                self.source.is_absolute()
                or self.source == Path()
                or ".." in self.source.parts
            ):
                msg = f"surface source must stay template-relative: {self.path}"
                raise ValueError(msg)
            if self.delegate in {"render", "manifest"} and self.source is None:
                msg = f"template delegate requires source: {self.path}"
                raise ValueError(msg)
            if self.delegate == "vscode-settings" and self.source is not None:
                msg = f"vscode-settings delegate must be source-less: {self.path}"
                raise ValueError(msg)
            if self.merge_strategy != "replace" and self.policy != "merge":
                msg = f"merge strategy requires merge policy: {self.path}"
                raise ValueError(msg)
            if self.make_role in {"wrapper", "engine"} and (
                self.policy != "full"
                or self.source is None
                or self.render_context != "make"
            ):
                msg = f"invalid generated Make projection: {self.path}"
                raise ValueError(msg)
            return self

    class SurfaceCatalogSpec(_ConfigContract):
        """Single ordered owner for every managed and rendered surface."""

        root: Annotated[Path, m.Field(description="Package-relative template root")]
        entries: Annotated[
            tuple[FlextInfraConfigModels.ManagedSurfaceSpec, ...],
            m.Field(min_length=1, description="Complete ordered surface catalog"),
        ]

        @u.model_validator(mode="after")
        def _validate_catalog(self) -> Self:
            """Require unique paths and one surface for every Make role."""
            if (
                self.root.is_absolute()
                or self.root == Path()
                or ".." in self.root.parts
            ):
                msg = "surface template root must stay package-relative"
                raise ValueError(msg)
            paths = tuple(entry.path for entry in self.entries)
            if len(set(paths)) != len(paths):
                msg = "surface paths must be unique"
                raise ValueError(msg)
            roles = tuple(
                entry.make_role for entry in self.entries if entry.make_role != "none"
            )
            if any(roles.count(role) != 1 for role in ("wrapper", "engine")):
                msg = "surface catalog requires one Make wrapper and one Make engine"
                raise ValueError(msg)
            return self

        @property
        def make_wrapper_path(self) -> t.NonEmptyStr:
            """The generated Make wrapper path."""
            return next(
                entry.path for entry in self.entries if entry.make_role == "wrapper"
            )

        @property
        def make_engine_path(self) -> t.NonEmptyStr:
            """The generated Make engine path."""
            return next(
                entry.path for entry in self.entries if entry.make_role == "engine"
            )

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
        _GIT_REF_FIRST_PRINTABLE_ASCII_CODEPOINT: ClassVar[int] = 32
        _GIT_REF_DELETE_ASCII_CODEPOINT: ClassVar[int] = 127

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
        branch: Annotated[
            t.NonEmptyStr, m.Field(description="Repository-owned integration branch")
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

        @u.model_validator(mode="after")
        def _validate_role_contract(self) -> Self:
            """Bind each governed role to its one physical checkout kind."""
            branch_parts = self.branch.split("/")
            invalid_branch = (
                self.branch in {"@", "HEAD"}
                or self.branch.startswith(("-", "/", "refs/heads/", "refs/remotes/"))
                or self.branch.endswith(("/", "."))
                or ".." in self.branch
                or "@{" in self.branch
                or "//" in self.branch
                or any(character in self.branch for character in " ~^:?*[\\")
                or any(
                    ord(character) < self._GIT_REF_FIRST_PRINTABLE_ASCII_CODEPOINT
                    or ord(character) == self._GIT_REF_DELETE_ASCII_CODEPOINT
                    for character in self.branch
                )
                or any(
                    not part or part.startswith(".") or part.endswith(".lock")
                    for part in branch_parts
                )
            )
            if invalid_branch:
                msg = f"invalid repository integration branch: {self.branch}"
                raise ValueError(msg)
            checkout_by_role = {
                FlextInfraConstantsCodegenProject.RepositoryRole.WORKSPACE_ROOT: (
                    FlextInfraConstantsCodegenProject.CheckoutKind.ROOT
                ),
                FlextInfraConstantsCodegenProject.RepositoryRole.WORKSPACE_MEMBER: (
                    FlextInfraConstantsCodegenProject.CheckoutKind.SUBMODULE
                ),
                FlextInfraConstantsCodegenProject.RepositoryRole.STANDALONE: (
                    FlextInfraConstantsCodegenProject.CheckoutKind.INDEPENDENT
                ),
            }
            expected = checkout_by_role.get(self.role)
            if expected is not None and self.checkout is not expected:
                msg = (
                    "repository role/checkout mismatch: "
                    f"{self.role.value}/{self.checkout.value}"
                )
                raise ValueError(msg)
            if self.editable and not self.package:
                msg = "editable repositories must publish a Python package"
                raise ValueError(msg)
            excluded = (
                self.role is FlextInfraConstantsCodegenProject.RepositoryRole.EXCLUDED
                or self.state
                is FlextInfraConstantsCodegenProject.RepositoryState.EXCLUDED
            )
            if excluded and not (
                self.role is FlextInfraConstantsCodegenProject.RepositoryRole.EXCLUDED
                and self.state
                is FlextInfraConstantsCodegenProject.RepositoryState.EXCLUDED
                and self.codegen is FlextInfraConstantsCodegenProject.CodegenKind.NONE
                and self.read_only
            ):
                msg = (
                    "excluded repositories must be excluded, read-only and codegen-none"
                )
                raise ValueError(msg)
            return self

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
            bool, m.Field(description="Whether generation owns the governed CI surface")
        ] = True
        extra_ignored_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Project-owned .gitignore extensions composed after the "
                    "fleet-wide generated sections"
                )
            ),
        ] = ()

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
        attached_standalone: Annotated[
            bool,
            m.Field(
                description=(
                    "Marker-attached standalone routed to the workspace ledger; "
                    "receives a routing-only Beads config, never tracker state"
                )
            ),
        ] = False
        routing_only: Annotated[
            bool,
            m.Field(
                description=(
                    "Routing-only Beads config; never initializes local tracker state"
                )
            ),
        ] = False
        canonical_project_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical PEP 621 project name and Beads namespace"),
        ]
        baseline_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository-owned integration ancestry baseline"),
        ]
        ci_enabled: Annotated[
            bool, m.Field(description="Whether generation owns the CI projection")
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

        @property
        def conform_scope(
            self,
        ) -> FlextInfraConstantsCodegenProject.CodegenConformScope:
            """Derive repository reach once from the topology-owned Make profile."""
            if (
                self.make_profile
                == FlextInfraConstantsCodegenProject.MakeProfile.WORKSPACE_ROOT
            ):
                return FlextInfraConstantsCodegenProject.CodegenConformScope.ALL
            return FlextInfraConstantsCodegenProject.CodegenConformScope.SELF

    class ManagedGitlinkSpec(_ConfigContract):
        """One governed submodule with its repository-owned baseline branch."""

        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Governed repository identity"),
        ]
        branch: Annotated[
            t.NonEmptyStr, m.Field(description="Repository-owned integration branch")
        ]

    class BeadsConfigRenderSpec(_ConfigContract):
        """Field-only render input for the generated Beads ledger config."""

        issue_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Issue prefix from the repository tracker declaration"),
        ]
        database: Annotated[
            t.NonEmptyStr,
            m.Field(description="Dolt database from the workspace ledger identity"),
        ]
        server: Annotated[
            FlextInfraConfigModels.BeadsServerSpec,
            m.Field(
                description="Shared Dolt server connection from the toolchain SSOT"
            ),
        ]
        routing: Annotated[
            bool,
            m.Field(
                description=(
                    "Routing-only client config for an attached standalone; "
                    "False marks the workspace-root owned ledger"
                )
            ),
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

    class SgconfigRenderSpec(_ConfigContract):
        """Typed input for the generated ast-grep project config.

        Why (ai-hub-qwoc): a provider manifest can declare ``sgconfig.yml`` as a
        required surface, but no generator owned it, so the file was authored by
        hand in one repository and simply absent in another -- provider discovery
        then failed closed with ``missing declared file: sgconfig.yml``. The rule
        and fixture directories are declared here so every repository renders the
        same contract from the SSOT instead of a hand-written copy.
        """

        rule_dirs: Annotated[
            tuple[str, ...],
            m.Field(
                min_length=1,
                description="Directories holding this project's ast-grep rules",
            ),
        ]
        test_dirs: Annotated[
            tuple[str, ...],
            m.Field(
                default=(),
                description="Directories holding rule fixtures and snapshots",
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
        year: Annotated[int, m.Field(ge=2025, description="Copyright year")]

    class MakeRenderContext(_ConfigContract):
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
        make_engine_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Config-declared Make engine included by the wrapper"),
        ]
        runtime_environment_dir: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical environment directory under its owner"),
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
        profile: Annotated[
            FlextInfraConfigModels.ProfileSpec,
            m.Field(description="Resolved generated Make execution profile"),
        ]
        workspace_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Relative path to the declared workspace root"),
        ]
        workspace_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered workspace member records"),
        ] = ()
        workspace_gitlinks: Annotated[
            tuple[FlextInfraConfigModels.ManagedGitlinkSpec, ...],
            m.Field(description="Provider-resolved governed Git submodules"),
        ] = ()

        @m.computed_field()
        @property
        def make_profile(self) -> FlextInfraConstantsCodegenProject.MakeProfile:
            """Project the profile name for templates that only render its identity."""
            return self.profile.name

    class ProjectRenderContext(MakeRenderContext):
        """Complete typed input consumed by project scaffold templates."""

        is_package: Annotated[
            bool,
            m.Field(description="Repository packaging capability from topology SSOT"),
        ]

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
            bool,
            m.Field(description="Whether governance owns this repository's tracker"),
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
        ledger_id: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Beads ledger identity declared by the workspace root; None "
                    "uses the standalone canonical project name"
                )
            ),
        ] = None
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
        content_only: Annotated[
            tuple[Path, ...],
            m.Field(
                description=(
                    "Vendored gitlinks present in the tree but never managed, "
                    "mutated, or included in conform fan-out"
                )
            ),
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
            if self.repository.path != Path():
                msg = "workspace manifest owner path must be '.'"
                raise ValueError(msg)
            member_paths = tuple(item.path for item in self.members)
            invalid_members = tuple(
                item
                for item in self.members
                if item.role
                is not FlextInfraConstantsCodegenProject.RepositoryRole.WORKSPACE_MEMBER
                or item.state
                is not FlextInfraConstantsCodegenProject.RepositoryState.ACTIVE
                or item.path.is_absolute()
                or not item.path.parts
                or item.path == Path()
                or ".." in item.path.parts
            )
            if invalid_members:
                msg = (
                    "workspace members must be active relative member paths: "
                    + ", ".join(item.name for item in invalid_members)
                )
                raise ValueError(msg)
            for attribute in ("name", "distribution", "path"):
                values = tuple(getattr(item, attribute) for item in self.members)
                if len(set(values)) != len(values):
                    msg = f"workspace member {attribute} values must be unique"
                    raise ValueError(msg)
            if any(
                member.name == self.repository.name
                or member.distribution == self.repository.distribution
                for member in self.members
            ):
                msg = "workspace root and member identities must be distinct"
                raise ValueError(msg)
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
            overlap = set(member_paths).intersection(self.external_dependency_paths)
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

    class MakeTargetSpec(_ConfigContract):
        """One governed repository selected for a normalized Make invocation."""

        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Typed repository capability owner"),
        ]
        root: Annotated[
            Path, m.Field(description="Resolved checkout root for the repository")
        ]

    class MakeExecutionContext(_ConfigContract):
        """Fully resolved context shared by every Make operation implementation."""

        workspace_root: Annotated[
            Path, m.Field(description="Governing workspace or standalone root")
        ]
        workspace: Annotated[
            FlextInfraConfigModels.WorkspaceSpec,
            m.Field(description="Canonical governed topology"),
        ]
        target: Annotated[
            FlextInfraConfigModels.RepositoryConformTarget,
            m.Field(description="Repository that received the public Make call"),
        ]
        profile: Annotated[
            FlextInfraConfigModels.ProfileSpec,
            m.Field(description="Resolved root/member/standalone execution profile"),
        ]
        environment_root: Annotated[
            Path, m.Field(description="Profile-derived managed environment owner")
        ]
        targets: Annotated[
            tuple[FlextInfraConfigModels.MakeTargetSpec, ...],
            m.Field(min_length=1, description="Ordered governed execution targets"),
        ]
        invocation: Annotated[
            FlextInfraConfigModels.MakeInvocationSpec,
            m.Field(description="Parsed verb, handler, operation, and inputs"),
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Effective repository Make graph"),
        ]

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
        cleanup: Annotated[
            Literal["preserve", "root", "recursive"],
            m.Field(description="Bounded cleanup scope for make clean"),
        ] = "preserve"

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

    class CliTransactionPathOptionSpec(_ConfigContract):
        """One config-owned CLI path option and its transaction role."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^--[a-z][a-z0-9-]*$", description="CLI path option"),
        ]
        workspace_root: Annotated[
            bool, m.Field(description="Whether the option locates the workspace owner")
        ] = False
        scope: Annotated[
            bool, m.Field(description="Whether the option narrows transaction scope")
        ] = False
        relative_to: Annotated[
            Literal["cwd", "workspace"],
            m.Field(description="Base for relative option values"),
        ] = "cwd"

        @u.model_validator(mode="after")
        def _validate_role(self) -> Self:
            """Require every declared path option to own a transaction role."""
            if not (self.workspace_root or self.scope):
                msg = "CLI transaction path options require a workspace or scope role"
                raise ValueError(msg)
            if self.workspace_root and self.relative_to != "cwd":
                msg = "workspace-root path options must resolve relative to cwd"
                raise ValueError(msg)
            return self

    class CliTransactionPolicySpec(_ConfigContract):
        """One declarative transaction policy shared by compatible CLI routes."""

        routes: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="CLI group:command routes using policy"),
        ]
        apply_option: Annotated[
            t.NonEmptyStr,
            m.Field(pattern=r"^--[a-z][a-z0-9-]*$", description="Mutation option"),
        ]
        check_options: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Options requiring a zero-delta transaction"),
        ] = ()
        strip_options: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Outer intent options removed from inner command"),
        ] = ()
        path_options: Annotated[
            tuple[FlextInfraConfigModels.CliTransactionPathOptionSpec, ...],
            m.Field(
                min_length=1, description="Config-owned transaction path semantics"
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_path_options(self) -> Self:
            """Reject duplicate option semantics inside one transaction policy."""
            names = tuple(option.name for option in self.path_options)
            duplicates = sorted({name for name in names if names.count(name) > 1})
            if duplicates:
                msg = f"duplicate CLI transaction path options: {duplicates}"
                raise ValueError(msg)
            return self

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
        checkout_submodules: Annotated[
            t.NonEmptyStr,
            m.Field(
                default="false",
                pattern=r"^(true|false|recursive)$",
                description=(
                    "Default actions/checkout submodules mode for every "
                    "generated workflow. 'false' keeps CI green on projects "
                    "whose submodules are private: the default GITHUB_TOKEN "
                    "cannot clone sibling private repositories and "
                    "'recursive' aborts the job at checkout"
                ),
            ),
        ]
        checkout_submodules_overrides: Annotated[
            Mapping[str, str],
            m.Field(
                default_factory=lambda: MappingProxyType({}),
                description=(
                    "Per-distribution override of checkout_submodules, for "
                    "projects that really do exercise their subprojects in CI"
                ),
            ),
        ]
        sgconfig: Annotated[
            FlextInfraConfigModels.SgconfigRenderSpec,
            m.Field(description="Canonical ast-grep project contract for every repo"),
        ]
        uv_exclude_dependencies: Annotated[
            tuple[FlextInfraConfigModels.UvScopedDependencyExclusionSpec, ...],
            m.Field(description="Project-scoped official uv dependency exclusions"),
        ] = ()
        providers: Annotated[
            tuple[FlextInfraConfigModels.ProviderSpec, ...],
            m.Field(min_length=1, description="Ordered FLEXT-owned Git providers"),
        ]
        default_provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider used when no repository URL owns the source"),
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
        cli_transactions: Annotated[
            tuple[FlextInfraConfigModels.CliTransactionPolicySpec, ...],
            m.Field(min_length=1, description="Typed CLI worktree transaction policy"),
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

        @u.model_validator(mode="after")
        def _validate_cli_transaction_routes(self) -> Self:
            """Reject incomplete profiles or multiply-owned transaction routes."""
            provider_names = tuple(provider.name for provider in self.providers)
            if len(set(provider_names)) != len(provider_names):
                msg = "provider names must be unique"
                raise ValueError(msg)
            if provider_names.count(self.default_provider) != 1:
                msg = "default_provider must resolve exactly one provider"
                raise ValueError(msg)
            profile_names = tuple(profile.name for profile in self.profiles)
            expected_profiles = set(FlextInfraConstantsCodegenProject.MakeProfile)
            if set(profile_names) != expected_profiles or len(profile_names) != len(
                expected_profiles
            ):
                msg = "codegen profiles must cover every Make profile exactly once"
                raise ValueError(msg)
            routes = tuple(
                route for policy in self.cli_transactions for route in policy.routes
            )
            duplicates = sorted({route for route in routes if routes.count(route) > 1})
            if duplicates:
                msg = f"duplicate CLI transaction routes: {duplicates}"
                raise ValueError(msg)
            return self

        @property
        def default_provider_spec(self) -> FlextInfraConfigModels.ProviderSpec:
            """Resolve the configured default provider after model validation."""
            return next(
                provider
                for provider in self.providers
                if provider.name == self.default_provider
            )

        @m.computed_field()
        @property
        def governed_branch_patterns(self) -> tuple[str, ...]:
            """Derive governed lines from their production/provider owners."""
            return tuple(
                dict.fromkeys((
                    self.branch_policy.production_branch,
                    *(provider.branch for provider in self.providers),
                    *self.branch_policy.additional_governed_branch_patterns,
                ))
            )

        def cli_transaction_policy(
            self, route: str
        ) -> FlextInfraConfigModels.CliTransactionPolicySpec | None:
            """Resolve one route through the typed transaction SSOT."""
            return next(
                (policy for policy in self.cli_transactions if route in policy.routes),
                None,
            )

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
            for managed in self.surfaces.entries:
                parts = Path(managed.path).parts
                candidates = [
                    *(f"!{'/'.join(parts[:depth])}/" for depth in range(1, len(parts))),
                    f"!{managed.path}",
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

        scaffold: Annotated[
            FlextInfraConfigModels.ScaffoldSpec,
            m.Field(description="Typed new-project scaffold policy"),
        ]
        surfaces: Annotated[
            FlextInfraConfigModels.SurfaceCatalogSpec,
            m.Field(description="Single managed and rendered surface catalog"),
        ]
        # Operator law: flext-infra owns generic conform policy only. The set
        # of projects it serves is NOT its knowledge — each repository declares
        # its own topology in config/workspace.yaml, and standalone checkouts
        # are derived from their own metadata plus live Git.

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

    class BeadsTrackerDeclaration(_ConfigContract):
        """The tracker identity a repository commits in ``.beads/config.yaml``.

        mro-o0cc: the committed file IS the declaration (e.g. the shared
        ``mro`` ledger on the machine-wide Dolt server). It is parsed once at
        the boundary into this model, so consumers read a validated prefix
        instead of probing an untyped mapping at runtime.
        """

        issue_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tracker namespace declared by the repository"),
        ]

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
        expected_checksum: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                pattern=r"^[0-9a-f]{64}$",
                description=(
                    "SHA-256 the resolved Beads binary must match; declared by "
                    "the toolchain SSOT, verified fail-closed"
                ),
            ),
        ] = None
        expected_schema: Annotated[
            int | None,
            m.Field(
                gt=0,
                description=(
                    "Ledger schema the pinned binary must know; content identity "
                    "of the artifact is the enforcement surface"
                ),
            ),
        ] = None
        ledger_root: Annotated[
            Path,
            m.Field(
                description=(
                    "Checkout root that owns the ledger. Equal to "
                    "repository_root when this repository owns its own tracker, "
                    "and the principal checkout when the tracker is routed."
                )
            ),
        ]

        @m.computed_field()
        @property
        def routes_to_principal_ledger(self) -> bool:
            """Whether the tracker lives in another checkout than this one."""
            return self.ledger_root != self.repository_root

        ledger_id: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Ledger identity declared by the workspace manifest SSOT; "
                    "never derived from the repository name"
                )
            ),
        ] = None

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

    class WorkspaceEnvironmentSyncRequest(_ConfigContract):
        """Validated public request for one workspace environment sync."""

        workspace_root: Annotated[
            Path, m.Field(description="Workspace root receiving the sync")
        ]
        apply: Annotated[
            bool, m.Field(description="Write changes instead of reporting them")
        ] = True
        force: Annotated[
            bool, m.Field(description="Replace custom files with generated content")
        ] = False

    class WorkspaceEnvironmentSyncResult(_ConfigContract):
        """Outcome of one workspace environment sync."""

        changed_files: Annotated[
            tuple[Path, ...],
            m.Field(description="Environment files created, updated, or removed"),
        ] = ()

        @m.computed_field()
        @property
        def changed(self) -> bool:
            """Whether the sync altered any environment file."""
            return bool(self.changed_files)

    class CodegenConformRequest(_ConfigContract):
        """Validated read-only request for ``flext-infra codegen conform``."""

        root: Annotated[Path, m.Field(description="Repository or workspace root")]
        what: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformSurface,
            m.Field(description="Managed file selection"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformSurface.ALL
        scope: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformScope,
            m.Field(description="Repository selection scope"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformScope.SELF

    class CodegenFilePlan(_ConfigContract):
        """Expected content and current state for one managed file."""

        path: Annotated[Path, m.Field(description="Absolute managed file path")]
        rendered: Annotated[str, m.Field(description="Fully rendered expected content")]
        expected_sha256: Annotated[
            t.NonEmptyStr, m.Field(description="SHA-256 of expected content")
        ]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical artifact owner")]
        policy: Annotated[
            Literal["full", "merge", "create-only", "manual"],
            m.Field(description="Governed root artifact policy"),
        ]
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
