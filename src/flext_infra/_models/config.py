"""Pure Pydantic config and codegen contracts for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatchcase
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u
from flext_infra import t
from flext_infra._constants.codegen_project import FlextInfraConstantsCodegenProject
from flext_infra._constants.make import FlextInfraConstantsMake
from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
from flext_infra._constants.workspace import FlextInfraConstantsWorkspace
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
        """One exact Mise backend selector and immutable version."""

        selector: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical Mise backend selector")
        ]
        version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact tool version installed by Mise")
        ]
        prerelease: Annotated[
            bool,
            m.Field(description="Whether Mise may resolve prerelease tool versions"),
        ] = False
        minimum_release_age: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional per-tool release quarantine override"),
        ] = None

    class ProtectedMiseToolSpec(MiseToolSpec):
        """One fleet-owned Mise distribution identity."""

        selector_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Glob patterns identifying equivalent distributions",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_distribution_patterns(self) -> Self:
            """Require unique patterns that cover the canonical selector."""
            if len(set(self.selector_patterns)) != len(self.selector_patterns):
                msg = "protected Mise selector_patterns must be unique"
                raise ValueError(msg)
            if not any(
                fnmatchcase(self.selector, pattern)
                for pattern in self.selector_patterns
            ):
                msg = (
                    "canonical Mise selector is not covered by selector_patterns: "
                    f"{self.selector}"
                )
                raise ValueError(msg)
            return self

    class MiseLockPlatformSpec(_ConfigContract):
        """Immutable download metadata for one tool platform."""

        checksum: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^sha256:[0-9a-f]{64}$",
                description="SHA-256 digest emitted by Mise",
            ),
        ]
        url: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^https://",
                description="Immutable HTTPS artifact URL emitted by Mise",
            ),
        ]
        url_api: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional immutable provider API URL"),
        ] = None
        provenance: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional artifact provenance mechanism"),
        ] = None
        provenance_verified: Annotated[
            bool | None,
            m.Field(description="Optional local provenance verification result"),
        ] = None

    class MiseLockToolSpec(_ConfigContract):
        """One resolved tool version and its platform artifacts."""

        version: Annotated[
            t.NonEmptyStr, m.Field(description="Resolved immutable tool version")
        ]
        backend: Annotated[
            t.NonEmptyStr, m.Field(description="Resolved Mise backend identity")
        ]
        specifiers: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Selectors resolved by this entry"),
        ]
        platforms: Annotated[
            Mapping[t.NonEmptyStr, FlextInfraConfigModels.MiseLockPlatformSpec],
            m.Field(
                default_factory=dict, description="Resolved platform download metadata"
            ),
        ]

    class MiseLockSpec(_ConfigContract):
        """Typed shape of the generated Mise lockfile."""

        lockfile_version: Annotated[
            Literal[1], m.Field(description="Supported Mise lock schema version")
        ]
        tools: Annotated[
            Mapping[t.NonEmptyStr, tuple[FlextInfraConfigModels.MiseLockToolSpec, ...]],
            m.Field(description="Exactly resolved generated tool set"),
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
        dependency_cooldown_days: Annotated[
            int,
            m.Field(
                ge=1,
                le=90,
                description=(
                    "Supply-chain cooldown shared by uv resolution and "
                    "Dependabot version updates"
                ),
            ),
        ]
        dependency_cooldown_exclusions: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Packages explicitly exempted from cooldown for urgent "
                    "security floors"
                )
            ),
        ] = ()
        dependency_cooldown_overrides: Annotated[
            t.StrMapping,
            m.Field(
                description=(
                    "Per-package cooldown cutoffs, mapping package name to an "
                    "RFC 3339 timestamp. The shared window is a single date for "
                    "the whole resolution, so a project that legitimately "
                    "requires a floor published after it becomes unsatisfiable: "
                    "uv reports the requirement cannot be met and names "
                    "exclude-newer-package as the remedy. A boolean exemption "
                    "cannot express this, because the cutoff has to move to a "
                    "specific instant rather than be switched off, so the "
                    "override carries the timestamp."
                )
            ),
        ] = MappingProxyType({})
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
        uv_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact uv resolver version")
        ]
        qlty_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact qlty code-quality version")
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
        mise_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact mise binary version")
        ]
        mise_lock_platforms: Annotated[
            tuple[
                Literal[
                    "linux-x64",
                    "linux-arm64",
                    "linux-x64-musl",
                    "linux-arm64-musl",
                    "macos-x64",
                    "macos-arm64",
                    "windows-x64",
                ],
                ...,
            ],
            m.Field(
                min_length=1,
                description="Platforms materialized into the project Mise lockfile",
            ),
        ]
        mise_lock_platform_exclusions: Annotated[
            Mapping[
                t.NonEmptyStr,
                tuple[
                    Literal[
                        "linux-x64",
                        "linux-arm64",
                        "linux-x64-musl",
                        "linux-arm64-musl",
                        "macos-x64",
                        "macos-arm64",
                        "windows-x64",
                    ],
                    ...,
                ],
            ],
            m.Field(description="Unsupported platform pairs in the Mise lock"),
        ] = MappingProxyType({})
        beads: Annotated[
            FlextInfraConfigModels.ProtectedMiseToolSpec,
            m.Field(description="Official Beads CLI pin installed through Mise"),
        ]
        protected_mise_tools: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Toolchain owners protected from alternate distributions",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_protected_mise_tools(self) -> Self:
            """Resolve every protected owner to the generic identity contract."""
            if len(set(self.protected_mise_tools)) != len(self.protected_mise_tools):
                msg = "protected_mise_tools must be unique"
                raise ValueError(msg)
            for owner in self.protected_mise_tools:
                if not isinstance(
                    getattr(self, owner, None),
                    FlextInfraConfigModels.ProtectedMiseToolSpec,
                ):
                    msg = f"protected_mise_tools references invalid owner: {owner}"
                    raise TypeError(msg)
            return self

        @u.model_validator(mode="after")
        def _validate_mise_lock_platforms(self) -> Self:
            """Reject duplicate or undeclared lock targets."""
            if len(set(self.mise_lock_platforms)) != len(self.mise_lock_platforms):
                msg = "mise_lock_platforms must be unique"
                raise ValueError(msg)
            declared = set(self.mise_lock_platforms)
            for selector, exclusions in self.mise_lock_platform_exclusions.items():
                if len(set(exclusions)) != len(exclusions):
                    msg = f"Mise lock platform exclusions must be unique: {selector}"
                    raise ValueError(msg)
                if set(exclusions) - declared:
                    msg = (
                        "Mise lock platform exclusions must be declared targets: "
                        f"{selector}"
                    )
                    raise ValueError(msg)
            return self

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

        @m.computed_field()
        @property
        def uv_exclude_newer(self) -> str:
            """Render the shared dependency cooldown in uv duration syntax."""
            return f"{self.dependency_cooldown_days} days"

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
        mise_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Mise runtime version")
        ]
        dependency_cooldown_days: Annotated[
            int,
            m.Field(
                ge=1, le=90, description="Shared uv and Dependabot dependency cooldown"
            ),
        ]
        github_actions: Annotated[
            Mapping[str, FlextInfraConfigModels.GithubActionPinSpec],
            m.Field(description="Immutable GitHub Action catalog"),
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
        ]
        ci_trigger_branches: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(), description="Ordered, deduplicated blocking CI branches"
            ),
        ] = ()
        has_devcontainer: Annotated[
            bool,
            m.Field(
                default=False,
                description=(
                    "Whether the rendered repository ships a .devcontainer "
                    "directory. Dependabot only accepts a devcontainers "
                    "ecosystem entry when one exists; declaring it for a "
                    "repository without that directory makes GitHub reject the "
                    "whole manifest, which silently disables EVERY ecosystem in "
                    "it, security updates included. Derived from the repository "
                    "on disk rather than declared, because the directory is the "
                    "fact and a second declaration could disagree with it "
                    "(hq-36xk)"
                ),
            ),
        ] = False
        checkout_submodules: Annotated[
            t.NonEmptyStr,
            m.Field(
                default="false",
                pattern=r"^(true|false|recursive)$",
                description=(
                    "actions/checkout submodules mode. Defaults to 'false' "
                    "because the default GITHUB_TOKEN cannot clone sibling "
                    "private repositories: 'recursive' aborts the job at "
                    "checkout with 'Repository not found'"
                ),
            ),
        ]
        ci_matrix_auto_run: Annotated[
            bool,
            m.Field(
                description=(
                    "When true, ci-matrix triggers include push to main plus "
                    "workflow_dispatch; when false (default), workflow_dispatch "
                    "only — file remains projected for root/standalone"
                )
            ),
        ] = False

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
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical Make CI token contract for ENV CI=Y"),
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

    class MakeVerbSpec(_ConfigContract):
        """One public Make verb and its complete handler-selector contract."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Public Make verb")]
        default_what: Annotated[
            t.NonEmptyStr, m.Field(description="Default WHAT selector")
        ]
        whats: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Complete ordered handler selectors"),
        ]
        apply_guarded: Annotated[
            bool, m.Field(description="Whether mutation requires APPLY=Y")
        ] = False
        accepts_apply: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether APPLY=Y is legal for this verb without declaring it "
                    "apply-guarded. Used by run handlers that sometimes mutate "
                    "under explicit APPLY but must stay unguarded by default."
                )
            ),
        ] = False
        apply_what: Annotated[
            t.NonEmptyStr,
            m.Field(
                default="all",
                description=(
                    "Selector an apply-guarded or accepts_apply verb resolves "
                    "to when APPLY is set and no explicit WHAT is given. "
                    "Without it, a mutating workflow step could silently "
                    "retain its read-only default selector"
                ),
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_whats(self) -> Self:
            """Require defaults and mutation selectors to name one owned handler."""
            if len(set(self.whats)) != len(self.whats):
                msg = f"make verb {self.name} handler selectors must be unique"
                raise ValueError(msg)
            required = {self.default_what}
            if self.apply_guarded or self.accepts_apply:
                required.add(self.apply_what)
            if self.apply_guarded and self.accepts_apply:
                msg = (
                    f"make verb {self.name} cannot set both apply_guarded and "
                    "accepts_apply"
                )
                raise ValueError(msg)
            if self.apply_guarded and self.default_what == self.apply_what:
                msg = (
                    f"make verb {self.name} apply_guarded default_what must "
                    "differ from apply_what so the fixed-point re-check "
                    "runs without APPLY=Y"
                )
                raise ValueError(msg)
            missing = required - set(self.whats)
            if missing:
                msg = (
                    f"make verb {self.name} selectors have no handler: "
                    f"{', '.join(sorted(missing))}"
                )
                raise ValueError(msg)
            return self

    class MakeWorkflowStepSpec(_ConfigContract):
        """One canonical workflow step and its explicit mutation intent."""

        verb: Annotated[t.NonEmptyStr, m.Field(description="Declared public verb")]
        apply: Annotated[
            bool,
            m.Field(description="Whether the step supplies the configured apply token"),
        ] = False
        contexts: Annotated[
            tuple[Literal["local", "ci", "pre_commit", "pre_push"], ...],
            m.Field(
                min_length=1,
                description="Execution contexts consuming this single workflow row",
            ),
        ]
        what: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                default=None,
                description=(
                    "Explicit WHAT selector for this step. None lets the verb "
                    "resolve its own default_what, so a row names a selector "
                    "only when it deliberately departs from that default."
                ),
            ),
        ] = None
        gates_skip: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Gate ids this step omits when it runs from a hook context "
                    "(pre_commit/pre_push). Local and CI invocations of the "
                    "same verb keep the full default set."
                ),
            ),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_contexts(self) -> Self:
            """Require unique contexts and retain every step in the local workflow."""
            if len(set(self.contexts)) != len(self.contexts):
                msg = f"make workflow contexts must be unique for {self.verb}"
                raise ValueError(msg)
            if "local" not in self.contexts:
                msg = f"make workflow step {self.verb} must run locally"
                raise ValueError(msg)
            allowed = set(FlextInfraConstantsMake.PROJECT_CHECK_GATES_ALLOWED_VALUES)
            unknown = sorted(set(self.gates_skip) - allowed)
            if unknown:
                msg = (
                    f"make workflow step {self.verb} gates_skip contains "
                    f"unknown gates: {', '.join(unknown)}"
                )
                raise ValueError(msg)
            return self

    class MakeCiSpec(_ConfigContract):
        """The only permitted environment delta between local and CI execution."""

        variable: Annotated[t.NonEmptyStr, m.Field(description="CI environment key")]
        value: Annotated[t.NonEmptyStr, m.Field(description="CI environment value")]
        local_value: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Local form of the CI ternary. A hook declares this value "
                    "explicitly so an inherited CI token from the caller can "
                    "never revoke pytest or the type-checker gates."
                )
            ),
        ] = "N"
        local_check_gates: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Gate ids run by make check under the local CI token: the "
                    "slow whole-program type checkers. This is the ONLY "
                    "declared set; the CI token runs its strict complement and "
                    "an unset token runs every allowed gate."
                )
            ),
        ] = FlextInfraConstantsMake.PROJECT_CHECK_GATES_LOCAL_VALUES

        @u.model_validator(mode="after")
        def _validate_local_check_gates(self) -> Self:
            """Every locally owned gate must be in the allowed check vocabulary."""
            allowed = set(FlextInfraConstantsMake.PROJECT_CHECK_GATES_ALLOWED_VALUES)
            unknown = sorted(set(self.local_check_gates) - allowed)
            if unknown:
                msg = (
                    "make.ci.local_check_gates contains unknown gates: "
                    f"{', '.join(unknown)}"
                )
                raise ValueError(msg)
            return self

        @m.computed_field()
        @property
        def check_gates(self) -> tuple[str, ...]:
            """Gates run under the CI token, as the strict complement.

            CI=Y is the inverse of CI=N by construction, never a second list: a
            gate that moves into or out of ``local_check_gates`` moves out of or
            into this set in the same edit, so the two can never overlap nor
            leave a gate unowned.

            The complement is taken over the DEFAULT vocabulary, not ALLOWED.
            ``format`` is allowed as an explicit ``CHECK_GATES=format`` request
            but is absent from the default set because it MUTATES files, so
            deriving over ALLOWED silently scheduled a formatter inside CI's
            read-only check — the one thing the comment on ``local_check_gates``
            says must never happen.
            """
            local = frozenset(self.local_check_gates)
            return tuple(
                gate
                for gate in FlextInfraConstantsMake.PROJECT_CHECK_GATES_DEFAULT_VALUES
                if gate not in local
            )

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

    class DocsGithubRepoSpec(_ConfigContract):
        """One governed GitHub repository used for cross-repo doc links."""

        organization: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub organization")
        ]
        repository: Annotated[t.NonEmptyStr, m.Field(description="GitHub repository")]
        branch: Annotated[
            t.NonEmptyStr, m.Field(description="Working-line branch for doc links")
        ]
        local_checkout: Annotated[
            str,
            m.Field(
                default="",
                description=(
                    "Optional local checkout path (~ expanded) for existence checks"
                ),
            ),
        ] = ""

    class MakeCleanSpec(_ConfigContract):
        """Disposable artifacts the generated clean verb removes.

        Stale caches and traces cause FALSE DIAGNOSES, so the disposable set is
        declared data rather than a literal buried in a recipe: every project
        cleans exactly the same things and a new artifact kind is one config row.
        """

        cache_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Cache directory names removed anywhere in the tree"),
        ]
        root_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Directories removed at the project root only"),
        ]
        root_files: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Files removed at the project root only"),
        ]
        trace_globs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Trace/profile globs removed anywhere in the tree"),
        ]

    class MakeDocsSpec(_ConfigContract):
        """Generated Makefile docs verb lifecycle and audit policy."""

        api_modules: Annotated[
            Mapping[t.NonEmptyStr, tuple[t.NonEmptyStr, ...]],
            m.Field(
                min_length=1,
                description="Public API modules generated per distribution",
            ),
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
        stale_github_organizations: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=("organization",),
                description="Placeholder GitHub orgs that must be rewritten",
            ),
        ] = ("organization",)
        github_repos: Annotated[
            tuple[FlextInfraConfigModels.DocsGithubRepoSpec, ...],
            m.Field(
                default=(),
                description="Governed org/repo/branch map for cross-repo doc URLs",
            ),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_api_modules(self) -> Self:
            """Reject duplicate, empty, or non-importable module declarations."""
            for distribution, modules in self.api_modules.items():
                if not modules:
                    msg = f"docs api_modules must not be empty: {distribution}"
                    raise ValueError(msg)
                if len(set(modules)) != len(modules):
                    msg = f"docs api_modules must be unique: {distribution}"
                    raise ValueError(msg)
                invalid = next(
                    (
                        module
                        for module in modules
                        if not all(part.isidentifier() for part in module.split("."))
                    ),
                    None,
                )
                if invalid is not None:
                    msg = f"docs api module is not importable: {invalid}"
                    raise ValueError(msg)
            return self

    class TestmonCacheSpec(_ConfigContract):
        """Adaptive pytest-testmon GitHub Actions cache policy (mro-dipb)."""

        schema_version: Annotated[
            int, m.Field(ge=1, description="Cache key schema version")
        ]
        mode: Annotated[
            Literal["bootstrap", "stable"], m.Field(description="Cache renewal phase")
        ]
        save_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether CI may upload a new testmon generation. False while "
                    "quota/HTTP 402 blocks fleet-wide saves (QUOTA_HOLD)."
                )
            ),
        ]
        max_bootstrap_generations: Annotated[
            int, m.Field(ge=1, le=10, description="Max retained bootstrap generations")
        ]
        max_stable_generations: Annotated[
            int, m.Field(ge=1, le=10, description="Max retained stable generations")
        ]
        per_repo_budget_bytes: Annotated[
            int, m.Field(ge=1, description="Per-repo testmon namespace budget in bytes")
        ]
        warning_threshold_percent: Annotated[
            int, m.Field(ge=1, le=100, description="Quota warning threshold percent")
        ]
        maintenance_threshold_percent: Annotated[
            int,
            m.Field(ge=1, le=100, description="Quota maintenance threshold percent"),
        ]
        block_threshold_percent: Annotated[
            int, m.Field(ge=1, le=100, description="Quota block-save threshold percent")
        ]
        allowed_save_refs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Refs allowed to save cache generations"),
        ]
        key_prefix: Annotated[
            t.NonEmptyStr, m.Field(description="Immutable cache key prefix")
        ]

        @u.model_validator(mode="after")
        def _validate_thresholds(self) -> Self:
            """Require warning < maintenance < block."""
            if not (
                self.warning_threshold_percent
                < self.maintenance_threshold_percent
                < self.block_threshold_percent
            ):
                msg = "testmon cache thresholds must satisfy warning < maintenance < block"
                raise ValueError(msg)
            return self

    class MakeWorkInProgressSpec(_ConfigContract):
        """Predicate for work-in-progress branches and draft-PR gate behavior.

        A hook that runs the full gate matrix on every push turns an
        in-progress branch into a stop-and-wait loop, so contributors start
        bypassing the hook entirely -- which costs more than it saves. The
        predicate is DATA so the escape is declared and auditable rather than
        improvised per-repository with `--no-verify`.
        """

        draft_pr: Annotated[
            bool, m.Field(description="Treat GitHub draft PRs as work-in-progress")
        ]
        branch_patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Regex patterns that mark a branch as work-in-progress",
            ),
        ]
        merge_lock_target_branches: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Target branches that are blocked for WIP merges",
            ),
        ]

    class MakeSpec(_ConfigContract):
        """Complete generated Makefile public and extension contract."""

        work_in_progress: Annotated[
            FlextInfraConfigModels.MakeWorkInProgressSpec,
            m.Field(description="WIP branch and draft PR gate predicate"),
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
        bootstrap: Annotated[
            FlextInfraConfigModels.MakeBootstrapSpec,
            m.Field(description="Pre-conform project environment contract"),
        ]
        # Why (operator law 2026-08-24): git-hook stages are OFF by default and
        # re-enabled case by case via these config gates. The workflow keeps
        # owning WHICH steps belong to each stage; the booleans only govern
        # whether the stage is generated and installed at all.
        pre_commit: Annotated[
            bool,
            m.Field(
                default=False,
                description="Generate and install the pre-commit git-hook stage",
            ),
        ] = False
        pre_push: Annotated[
            bool,
            m.Field(
                default=False,
                description="Generate and install the pre-push git-hook stage",
            ),
        ] = False
        workflow: Annotated[
            tuple[FlextInfraConfigModels.MakeWorkflowStepSpec, ...],
            m.Field(min_length=1, description="Ordered canonical validation workflow"),
        ]
        ci: Annotated[
            FlextInfraConfigModels.MakeCiSpec,
            m.Field(description="Config-owned CI-only environment delta"),
        ]
        testmon_cache: Annotated[
            FlextInfraConfigModels.TestmonCacheSpec,
            m.Field(description="Adaptive testmon Actions cache policy"),
        ]
        verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Ordered canonical public verbs"),
        ]
        clean: Annotated[
            FlextInfraConfigModels.MakeCleanSpec,
            m.Field(description="Disposable artifacts removed by the clean verb"),
        ]
        docs: Annotated[
            FlextInfraConfigModels.MakeDocsSpec,
            m.Field(description="Public documentation lifecycle policy"),
        ]

        @u.model_validator(mode="after")
        def _validate_verbs(self) -> Self:
            """Validate declared public verbs against workflow and contract.

            Why there is no `"setup" in declared` rejection here (flext-lq86m):
            the message it carried -- "make setup cannot require the managed
            validation environment" -- is a statement about a verb's
            ENVIRONMENT DEPENDENCY, not about the name `setup`. Testing the
            name was the wrong predicate, and it contradicted
            `config/codegen.yaml`, which declares `setup` as a public verb; the
            config singleton builds eagerly at import, so every entrypoint died
            on that contradiction. The real invariant is enforced structurally
            in the template, which excludes `setup` from
            `_builtin_require_environment` (`$(filter-out setup,$(PUBLIC_VERBS))`
            and `{% raw %}{% for verb in make.verbs if verb.name != "setup" %}{% endraw %}`),
            so `setup` never depends on the environment it exists to create.
            """
            declared = {verb.name for verb in self.verbs}
            if len(declared) != len(self.verbs):
                msg = "make public verb names must be unique"
                raise ValueError(msg)
            # Why (hq-36xk, flext-lq86m): the guard that lived here read
            # `if "setup" in serialized` and protected `make setup` from being
            # placed in the serialized mutation set, so it could never require
            # the managed validation environment it is supposed to CREATE.
            # 3e5fbc747 exterminated the serialize-make lifecycle and deleted
            # `self.serialization`, but rebound this condition to `declared`
            # instead of removing it with the concept it guarded. `setup` is a
            # mandatory canonical verb, so the inverted check rejected every
            # valid configuration and `flext_infra.config` could not be built at
            # all. The serialized set no longer exists; the guard has no object.
            workflow_verbs = tuple(step.verb for step in self.workflow)
            if len(set(workflow_verbs)) != len(workflow_verbs):
                msg = "make workflow verbs must be unique"
                raise ValueError(msg)
            unknown_workflow = set(workflow_verbs) - declared
            if unknown_workflow:
                msg = (
                    "make workflow verbs are not declared public verbs: "
                    f"{', '.join(sorted(unknown_workflow))}"
                )
                raise ValueError(msg)
            verb_specs = {verb.name: verb for verb in self.verbs}
            invalid_apply = [
                step.verb
                for step in self.workflow
                if step.apply != verb_specs[step.verb].apply_guarded
            ]
            if invalid_apply:
                msg = (
                    "make workflow apply intent must match verb contract: "
                    f"{', '.join(sorted(invalid_apply))}"
                )
                raise ValueError(msg)
            docs_verb = next((verb for verb in self.verbs if verb.name == "docs"), None)
            if docs_verb is None:
                msg = "make docs verb must be declared"
                raise ValueError(msg)
            docs_actions = set(docs_verb.whats)
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
        def handler_whats(self) -> Mapping[str, tuple[str, ...]]:
            """Canonical public verb-to-handler matrix consumed by every renderer.

            The check verb's what-selectors are augmented with the full gate
            vocabulary (check_gates_allowed) so a consumer can address an
            individual gate with `make check WHAT=<gate>`. The gates are
            rendered into `_ALLOWED_WHATS_check` by Makefile.j2, and per-gate
            `_builtin_check_<gate>` handlers are generated to back them.
            """
            whats: dict[str, tuple[str, ...]] = {
                verb.name: verb.whats for verb in self.verbs
            }
            if "check" in whats:
                whats["check"] = tuple(
                    dict.fromkeys((*whats["check"], *self.check_gates_allowed))
                )
            return whats

        @m.computed_field()
        @property
        def check_gates_allowed(self) -> tuple[str, ...]:
            """Canonical generated Make check-gate vocabulary.

            Project-owned gates are discovered from ``scripts/check`` by Make;
            this model owns only gates implemented by flext-infra.
            """
            return FlextInfraConstantsMake.PROJECT_CHECK_GATES_ALLOWED_VALUES

        @m.computed_field()
        @property
        def check_gates_default(self) -> tuple[str, ...]:
            """Canonical generated Make default check gates.

            Repository scripts remain explicit and do not mutate defaults.
            """
            return FlextInfraConstantsMake.PROJECT_CHECK_GATES_DEFAULT_VALUES

        @m.computed_field()
        @property
        def check_gates_fixable(self) -> tuple[str, ...]:
            """Gates ``make fix APPLY=Y`` can actually repair.

            Asking for a gate that cannot fix anything still pays its full cost;
            a fix pass built from the ALLOWED vocabulary once timed out doing
            exactly that.
            """
            return FlextInfraConstantsMake.PROJECT_CHECK_GATES_FIXABLE_VALUES

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
        conflict_sections: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Dotted sections the owner renders, so a merge conflict in "
                    "them is resolvable by re-rendering rather than by hand. A "
                    "section the owner produces but does not declare here "
                    "dead-ends the merge: absorbing an integration base that "
                    "still carries the previous projection leaves a conflict "
                    "the canonical surface cannot resolve."
                )
            ),
        ] = ()

    class TemplateEntrySpec(_ConfigContract):
        """One scaffold-only template mapping consumed by ``codegen new``."""

        source: Annotated[Path, m.Field(description="Template-root-relative source")]
        destination: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
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

    class ScaffoldUpstreamSpec(_ConfigContract):
        """Dependencies selected by one explicit upstream FLEXT facade."""

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
        upstreams: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldUpstreamSpec, ...],
            m.Field(min_length=1, description="Explicit upstream dependencies"),
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
        """The current repository's immutable identity and Git origin."""

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
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key from the codegen configuration"),
        ]

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
        topology: Annotated[
            FlextInfraConstantsWorkspace.WorkspaceMode,
            m.Field(description="Independent .gitmodules presence fact"),
        ]
        managed: Annotated[
            bool, m.Field(description="Whether pyproject declares [tool.flext]")
        ]
        canonical_project_name: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical PEP 621 project name")
        ]
        baseline_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider-owned integration ancestry baseline"),
        ]
        ci_enabled: Annotated[
            bool, m.Field(description="Whether conform owns the CI projection")
        ]
        ci_matrix_auto_run: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether projected ci-matrix auto-runs on push to main; "
                    "false (default) means workflow_dispatch only"
                )
            ),
        ] = False
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

    class MakeCommandContext(_ConfigContract):
        """Shared command identity required by every generated Make surface."""

        infra_cli: Annotated[
            t.NonEmptyStr, m.Field(description="Installed infrastructure CLI command")
        ]
        pytest: Annotated[
            FlextInfraModelsDepsToolSettings.PytestConfig,
            m.Field(description="Typed pytest execution policy"),
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
        uv_link_mode: Annotated[
            t.NonEmptyStr, m.Field(description="Configured uv installation link mode")
        ]
        uv_exclude_newer: Annotated[
            t.NonEmptyStr,
            m.Field(description="uv exclude-newer cooldown window for [tool.uv]"),
        ]
        dependency_cooldown_exclusions: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Packages exempted from uv dependency cooldown"),
        ] = ()
        dependency_cooldown_overrides: Annotated[
            t.StrMapping,
            m.Field(description="Per-package cooldown cutoffs as RFC 3339 timestamps"),
        ] = MappingProxyType({})
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
        pytest_process_timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Pytest process wall-time boundary")
        ]

    class GitignoreRenderSpec(_ConfigContract):
        """Typed input for the generated Git ignore file."""

        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(
                min_length=1,
                description="Canonical ignore sections applicable to the repository",
            ),
        ]

    class ReleaseAutomationOverrideSpec(_ConfigContract):
        """One distribution's deviation from the shared release contract."""

        release_branch: Annotated[
            t.NonEmptyStr | None,
            m.Field(default=None, description="Branch that produces releases"),
        ] = None
        build_command: Annotated[
            t.NonEmptyStr | None,
            m.Field(default=None, description="Command that produces the artifacts"),
        ] = None
        version_variables: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Extra file:variable version anchors"),
        ] = ()

    class ReleaseAutomationSpec(_ConfigContract):
        """Automated semantic versioning, owned by the market tool.

        Why: bump_version/parse_semver and the release orchestrator already
        existed, but nothing DERIVED the bump -- a human passed
        ``bump=minor`` by hand, which is exactly the judgement the commit
        history already encodes and the one a human gets wrong. Conventional
        Commits plus python-semantic-release replace that judgement with a
        rule, and replace local implementation with a maintained dependency.

        Declared once here so every generated pyproject carries the same
        contract. A project that genuinely differs is expressed in
        ``overrides``, never by editing its own pyproject.
        """

        tool: Annotated[
            t.NonEmptyStr, m.Field(description="Release automation distribution")
        ]
        runner: Annotated[
            t.NonEmptyStr, m.Field(description="Command runner that invokes the tool")
        ]
        commit_parser: Annotated[
            t.NonEmptyStr, m.Field(description="Commit convention driving the bump")
        ]
        release_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Branch that produces releases")
        ]
        version_variables: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="file:variable anchors the tool rewrites"),
        ]
        version_toml: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="file:tomlpath anchors the tool rewrites"),
        ]
        build_command: Annotated[
            t.NonEmptyStr, m.Field(description="Command that produces the artifacts")
        ]
        tag_format: Annotated[
            t.NonEmptyStr, m.Field(description="Tag shape, shared with the workflow")
        ]
        changelog_file: Annotated[
            t.NonEmptyStr, m.Field(description="Generated changelog destination")
        ]
        overrides: Annotated[
            Mapping[
                t.NonEmptyStr, FlextInfraConfigModels.ReleaseAutomationOverrideSpec
            ],
            m.Field(
                default_factory=lambda: MappingProxyType({}),
                description="Per-distribution deviations from the shared contract",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_anchors(self) -> Self:
            """Every anchor must name a target, or the tool rewrites nothing."""
            for anchor in (*self.version_variables, *self.version_toml):
                if ":" not in anchor:
                    msg = f"release version anchor must be '<file>:<target>': {anchor}"
                    raise ValueError(msg)
            return self

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
        uv_exclude_newer: Annotated[
            t.NonEmptyStr,
            m.Field(description="uv exclude-newer cooldown window for [tool.uv]"),
        ]
        dependency_cooldown_exclusions: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Packages exempted from uv dependency cooldown"),
        ] = ()
        dependency_cooldown_overrides: Annotated[
            t.StrMapping,
            m.Field(description="Per-package cooldown cutoffs as RFC 3339 timestamps"),
        ] = MappingProxyType({})
        ruff_per_file_ignores: Annotated[
            t.MappingKV[str, t.StrSequence],
            m.Field(
                description=(
                    "Effective Ruff exemptions: fleet policy composed with this "
                    "repository's own ManagedArtifacts overlay"
                )
            ),
        ] = MappingProxyType({})

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
        upstream_dependencies: Annotated[
            FlextInfraConfigModels.ScaffoldUpstreamSpec,
            m.Field(description="Dependencies for the selected explicit upstream"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolSettings.ToolConfigDocument,
            m.Field(description="Canonical validated tooling policy"),
        ]
        environment_path_prepends: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Configured read-only PATH additions for direnv"),
        ] = ()
        canonical_project_name: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical project name")
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
        uv_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact uv resolver version")
        ]
        qlty_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact qlty code-quality version")
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
        year: Annotated[int, m.Field(description="Copyright year")]

    class WorkspaceSpec(_ConfigContract):
        """Repository-local conformance context without topology policy."""

        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Current repository Git contract"),
        ]
        project: Annotated[
            FlextInfraConfigModels.ProjectSpec | None,
            m.Field(description="Metadata required only when materializing a new tree"),
        ] = None

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
        sgconfig: Annotated[
            FlextInfraConfigModels.SgconfigRenderSpec,
            m.Field(description="Canonical ast-grep project contract for every repo"),
        ]
        release: Annotated[
            FlextInfraConfigModels.ReleaseAutomationSpec,
            m.Field(
                description=(
                    "Automated semantic-release contract shared by every project"
                )
            ),
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
            # Declared sections are emitted verbatim because ignore files use
            # ordered last-match-wins semantics rather than set semantics.
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
        # Operator law: flext-infra owns generic conform policy only. The set
        # of projects it serves is NOT its knowledge — each repository declares
        # its own topology in config/workspace.yaml, and standalone checkouts
        # are derived from their own metadata plus live Git.

        @u.model_validator(mode="after")
        def _validate_github_artifact_ownership(self) -> Self:
            """Require one full-managed conform owner for every GitHub template."""
            github_templates = tuple(
                Path(entry.destination)
                for entry in self.templates.entries
                if Path(entry.destination).parts[:1] == (".github",)
            )
            github_managed = tuple(
                managed
                for managed in self.managed_files
                if managed.path.parts[:1] == (".github",)
            )
            template_paths = set(github_templates)
            managed_paths = {managed.path for managed in github_managed}
            duplicate_templates = len(github_templates) != len(template_paths)
            duplicate_managed = len(github_managed) != len(managed_paths)
            if duplicate_templates or duplicate_managed:
                msg = (
                    "GitHub artifacts must have exactly one template and managed owner"
                )
                raise ValueError(msg)
            if template_paths != managed_paths:
                missing_owners = sorted(
                    path.as_posix() for path in template_paths - managed_paths
                )
                missing_templates = sorted(
                    path.as_posix() for path in managed_paths - template_paths
                )
                msg = (
                    "GitHub template/managed ownership mismatch: "
                    f"missing owners={missing_owners}, "
                    f"missing templates={missing_templates}"
                )
                raise ValueError(msg)
            non_full = sorted(
                managed.path.as_posix()
                for managed in github_managed
                if managed.policy
                != FlextInfraConstantsSharedInfra.MANAGED_FILE_POLICY_FULL
            )
            if non_full:
                msg = f"GitHub artifacts must be full-managed: {non_full}"
                raise ValueError(msg)
            return self

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

    class CodegenConformSurfaceContract(m.Value):
        """Typed ownership contract for one requested conformance surface."""

        # Why: leaf conform planning contract lives on m.Infra only (not nested in services).
        destinations: Annotated[
            frozenset[str] | None,
            m.Field(description="Output paths selected for conformance planning"),
        ] = None
        complete_governed: Annotated[
            bool, m.Field(description="Whether every governed output is represented")
        ] = False
        dependencies_only: Annotated[
            bool, m.Field(description="Whether planning is dependency-only")
        ] = False
        delegates: Annotated[
            bool, m.Field(description="Whether delegated templates are planned")
        ] = True
        pyproject: Annotated[
            bool, m.Field(description="Whether project metadata is planned")
        ] = True
        templates: Annotated[
            bool, m.Field(description="Whether managed templates are planned")
        ] = True

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
        absent: Annotated[
            bool,
            m.Field(
                description=(
                    "When true, apply removes the path instead of writing rendered"
                )
            ),
        ] = False
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
