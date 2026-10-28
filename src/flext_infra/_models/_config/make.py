"""Make workflow, verb, CI, and cache specification models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal, Self

from flext_cli import m, t

from flext_infra import c
from flext_infra._constants.config import FlextInfraConstantsConfig
from flext_infra._models._config.contract import FlextInfraModelsConfigContract
from flext_infra._models._config.external_cache import (
    FlextInfraExternalCacheDirectorySpec,
)
from flext_infra._models._config.make_clean import FlextInfraModelsConfigMakeClean
from flext_infra._models._config.make_docs import FlextInfraModelsConfigMakeDocs
from flext_infra.make_contract import FlextInfraConfigMakeContract


def _effective_custom_handler_policies(
    base: FlextInfraModelsConfigMake.CustomHandlerPolicy,
    overrides: tuple[
        tuple[str, FlextInfraModelsConfigMake.CustomHandlerPolicyOverride], ...
    ],
) -> Mapping[str, FlextInfraModelsConfigMake.CustomHandlerPolicy]:
    """Derive the effective per-profile policy from frozen policy inputs.

    Pure function of frozen models: the returned mapping is read-only.

    Args:
        base: The strictest base policy every profile falls back to.
        overrides: Sorted ``(profile, relaxed policy)`` declaration pairs.

    Returns:
        The resulting ``Mapping[str,
            FlextInfraModelsConfigMake.CustomHandlerPolicy]``.

    """
    # Keys are normalised to the profile's string value: MakeProfile is a
    # StrEnum, so a raw YAML key and its enum subproject must land on the SAME
    # entry. Mixing both would make a lookup silently miss and fall back to
    # the strict base policy. The plain dict serializes through the computed
    # field; the read-only ``Mapping`` contract keeps callers from mutating it.
    return {
        str(profile): (
            base.model_copy(update=override.model_dump(exclude_none=True))
            if (override := dict(overrides).get(str(profile)))
            else base
        )
        for profile in (
            *dict(overrides),
            *FlextInfraConstantsConfig.MakeProfile,
        )
    }


class FlextInfraModelsConfigMake(
    FlextInfraModelsConfigMakeClean,
    FlextInfraModelsConfigMakeDocs,
):
    """Make workflow, verb, CI, and cache specification models."""

    class MakeProjectCheckGateSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One repository-owned native module check in the shared registry."""

        name: Annotated[
            str, m.Field(pattern=r"^[a-z][a-z0-9-]*$", description="Unique gate ID")
        ]
        module: Annotated[
            str,
            m.Field(
                pattern=r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$",
                description="Module executed by the selected physical runtime",
            ),
        ]
        arguments: Annotated[
            t.VariadicTuple[str], m.Field(description="Native module argument tokens")
        ] = ()
        integrity: Annotated[
            bool, m.Field(description="Include this check in quick runtime integrity")
        ] = False
        stage: Annotated[
            FlextInfraConstantsConfig.GateStage,
            m.Field(
                description=(
                    "Earliest approval stage the check's cost admits; a "
                    "repository-owned validator runs locally and at pre-push"
                ),
            ),
        ] = FlextInfraConstantsConfig.GateStage.PUSH
        timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Native module check wall-time limit")
        ] = c.Infra.TIMEOUT_DEFAULT

    class RuffCacheSpec(FlextInfraExternalCacheDirectorySpec.Directory[str]):
        """External Ruff cache with the declared default environment keys."""

        data_home_environment_variable: Annotated[
            str,
            m.Field(min_length=1, description="XDG persistent cache-home variable"),
        ] = FlextInfraConstantsConfig.MypyCacheEnvironment.DATA_HOME.value
        user_home_environment_variable: Annotated[
            str,
            m.Field(
                min_length=1,
                description="User home variable for the XDG default",
            ),
        ] = FlextInfraConstantsConfig.MypyCacheEnvironment.USER_HOME.value

    class MakeCiSpec(FlextInfraModelsConfigContract.ConfigContract):
        """The only permitted environment delta between local and CI execution."""

        variable: Annotated[t.NonEmptyStr, m.Field(description="CI environment key")]
        value: Annotated[t.NonEmptyStr, m.Field(description="CI environment value")]
        local_value: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Local form of the CI ternary. Check runs the active local "
                    "partition; other pre-push verbs declare this value to "
                    "preserve their local behavior. Pre-push check unsets CI."
                ),
            ),
        ] = "N"
        pre_commit_value: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Token the generated commit hook passes to its check row: "
                    "check then runs only the commit-stage gates "
                    "(MakeSpec.pre_commit_check_gates) and no other validator."
                ),
            ),
        ]

        @m.model_validator(mode="after")
        def _validate_distinct_tokens(self) -> Self:
            """Each declared context token selects exactly one check partition.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If two context tokens share one value.

            """
            tokens = (self.value, self.local_value, self.pre_commit_value)
            if len(set(tokens)) != len(tokens):
                msg = (
                    f"make.ci tokens must be distinct: value={self.value}, "
                    f"local_value={self.local_value}, "
                    f"pre_commit_value={self.pre_commit_value}"
                )
                raise ValueError(msg)
            return self

    class MakeVerbSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One selector-free public Make operation."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Public Make verb")]
        arguments: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Named Make inputs consumed by this operation"),
        ] = ()
        description: Annotated[
            t.NonEmptyStr,
            m.Field(description="Operator-facing help text"),
        ]
        requires_activation: Annotated[
            bool,
            m.Field(
                description=(
                    "Activate the declared environment before consuming it; "
                    "generation uses its provisioned physical runtime directly"
                ),
            ),
        ] = True
        profiles: Annotated[
            t.VariadicTuple[FlextInfraConstantsConfig.MakeProfile],
            m.Field(
                min_length=1,
                description=(
                    "Make profiles whose generated Makefile declares the verb; "
                    "a verb exists only where its operation applies"
                ),
            ),
        ] = tuple(FlextInfraConstantsConfig.MakeProfile)

    class MakeOperationSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One typed public operation and its distinct checker evidence phase."""

        verb: Annotated[t.NonEmptyStr, m.Field(description="Declared public Make verb")]
        phase: Annotated[
            c.Infra.CheckPhase,
            m.Field(description="Checker evidence phase; other verbs are complete"),
        ] = c.Infra.CheckPhase.COMPLETE

        @m.computed_field
        @property
        def make_command(self) -> str:
            """Canonical Make transport for this typed workflow operation."""
            return f"make {self.verb}" + (
                f" CHECK_PHASE={self.phase}"
                if self.phase == c.Infra.CheckPhase.PRIMARY
                else ""
            )

        @m.model_validator(mode="after")
        def _validate_phase(self) -> Self:
            """Keep source-admission semantics on the checker alone.

            Returns:
                The validated operation.

            Raises:
                ValueError: If another verb claims primary checker evidence.

            """
            if (
                self.phase == c.Infra.CheckPhase.PRIMARY
                and self.verb != c.Infra.VERB_CHECK
            ):
                msg = "only check declares primary workflow evidence"
                raise ValueError(msg)
            return self

    class MakeLifecycleStepSpec(MakeOperationSpec):
        """One public command in the declared runtime acceptance sequence."""

        contexts: Annotated[
            t.VariadicTuple[Literal["local", "ci"]],
            m.Field(
                min_length=1, description="Contexts where this acceptance step applies"
            ),
        ]

    class MakeWorkflowRequirementSpec(FlextInfraModelsConfigContract.ConfigContract):
        """An earlier phase required in explicitly declared execution contexts."""

        step: Annotated[
            t.NonEmptyStr, m.Field(description="Required workflow identity")
        ]
        contexts: Annotated[
            t.VariadicTuple[Literal["local", "ci", "pre_commit", "pre_push"]],
            m.Field(
                min_length=1, description="Contexts requiring the prior green phase"
            ),
        ]

    class MakeWorkflowStepSpec(MakeOperationSpec):
        """One canonical workflow step."""

        identity: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[A-Za-z_][A-Za-z0-9_-]*$",
                description="Unique dependency identity, never a new Make verb",
            ),
        ]
        contexts: Annotated[
            t.VariadicTuple[Literal["local", "ci", "pre_commit", "pre_push"]],
            m.Field(
                min_length=1,
                description="Execution contexts consuming this single workflow row",
            ),
        ]
        requires: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigMake.MakeWorkflowRequirementSpec],
            m.Field(
                description=(
                    "Earlier workflow identities whose green result admits this step "
                    "in the declared dependency contexts"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_contexts(self) -> Self:
            """Require unique contexts and retain every step in the local workflow.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If make workflow contexts must be unique for; or if make
                    workflow step.

            """
            if len(set(self.contexts)) != len(self.contexts):
                msg = f"make workflow contexts must be unique for {self.verb}"
                raise ValueError(msg)
            if "local" not in self.contexts:
                msg = f"make workflow step {self.verb} must run locally"
                raise ValueError(msg)
            return self

    class TestmonCachePolicySpec(FlextInfraModelsConfigContract.ConfigContract):
        """Declarative Actions-cache policy for the shared testmon database.

        Implements the preserved #1001 delta (bead flext-j0u23): two-phase
        generations with per-mode caps, a per-repository byte budget with a
        three-stage quota ladder and a cache-key namespace. Event identity
        determines publication eligibility; branch names are not policy.
        The packaged codegen configuration owns all policy values. This
        declaration validates them and never supplies a second policy when
        required configuration is missing.
        """

        mode: Annotated[
            Literal["bootstrap", "stable"],
            m.Field(description="Cache phase: bootstrap seeds, stable saves"),
        ]
        save_enabled: Annotated[
            bool,
            m.Field(description="Master switch for cache publishes"),
        ]
        max_bootstrap_generations: Annotated[
            int,
            m.Field(gt=0, description="Retention cap for bootstrap generations"),
        ]
        max_stable_generations: Annotated[
            int,
            m.Field(gt=0, description="Retention cap for stable generations"),
        ]
        per_repo_budget_bytes: Annotated[
            int,
            m.Field(gt=0, description="Per-repository byte budget"),
        ]
        warning_threshold_percent: Annotated[
            int,
            m.Field(ge=0, le=100, description="Quota-ladder warning stage"),
        ]
        maintenance_threshold_percent: Annotated[
            int,
            m.Field(ge=0, le=100, description="Quota-ladder maintenance stage"),
        ]
        block_threshold_percent: Annotated[
            int,
            m.Field(ge=0, le=100, description="Quota-ladder block stage"),
        ] = 95
        key_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Actions cache key namespace"),
        ]

        @m.model_validator(mode="after")
        def require_ascending_quota_ladder(self) -> Self:
            """Keep the quota ladder strictly ascending within the percent scale.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If testmon cache quota ladder must ascend warning <
                    maintenance < block <= 100.

            """
            full_scale = 100
            if not (
                self.warning_threshold_percent
                < self.maintenance_threshold_percent
                < self.block_threshold_percent
                <= full_scale
            ):
                msg = (
                    "testmon cache quota ladder must ascend "
                    "warning < maintenance < block <= 100"
                )
                raise ValueError(msg)
            return self

    class MypyCacheSpec(
        FlextInfraExternalCacheDirectorySpec.Directory[
            FlextInfraConstantsConfig.MypyCacheEnvironment
        ],
        FlextInfraModelsConfigContract.ConfigContract,
    ):
        """Project-keyed shared Mypy cache, one analysis reused across relocks."""

        cache_environment_variable: Annotated[
            FlextInfraConstantsConfig.MypyCacheEnvironment,
            m.Field(
                description="Mypy's cache-directory environment variable",
            ),
        ] = FlextInfraConstantsConfig.MypyCacheEnvironment.CACHE_DIR
        data_home_environment_variable: Annotated[
            FlextInfraConstantsConfig.MypyCacheEnvironment,
            m.Field(
                description="XDG persistent cache-home variable",
            ),
        ] = FlextInfraConstantsConfig.MypyCacheEnvironment.DATA_HOME
        user_home_environment_variable: Annotated[
            FlextInfraConstantsConfig.MypyCacheEnvironment,
            m.Field(
                description="User home variable for the XDG default",
            ),
        ] = FlextInfraConstantsConfig.MypyCacheEnvironment.USER_HOME

        @m.model_validator(mode="after")
        def require_external_cache_contract(self) -> Self:
            """Keep the official cache variable and the external path policy exact.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If mypy cache.

            """
            for name, actual, expected in (
                (
                    "cache_environment_variable",
                    self.cache_environment_variable,
                    FlextInfraConstantsConfig.MypyCacheEnvironment.CACHE_DIR,
                ),
                (
                    "data_home_environment_variable",
                    self.data_home_environment_variable,
                    FlextInfraConstantsConfig.MypyCacheEnvironment.DATA_HOME,
                ),
                (
                    "user_home_environment_variable",
                    self.user_home_environment_variable,
                    FlextInfraConstantsConfig.MypyCacheEnvironment.USER_HOME,
                ),
            ):
                if actual != expected:
                    msg = f"mypy cache {name} must be {expected.value}"
                    raise ValueError(msg)
            return self

    class MakeRuffSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Ruff CLI contract for generated Make verbs and quality gates.

        Operator 2026-09-08: ruff is the style and autofix rule. Every
        invocation uses preview. Never weaken ruff to keep a file; change the
        code. Single-pass verb law (operator 2026-09-18): ``make fmt`` runs
        format only and ``make fix`` owns lint repair through the lint gate —
        there is deliberately no ``lint_apply`` key, because a lint pass
        inside fmt would repeat the lint gate's fix.

        *** Operator law 2026-10-05 (direct order, OBLIGATORY and NEVER to be
        disabled again): ``make fix`` ALWAYS applies Ruff's unsafe fixes —
        ``lint_fix`` MUST carry the unsafe-fix flag in every project and
        subproject, forever. A configuration without it fails validation;
        re-adding it after a removal is a mandated repair, and removing it is
        a regression against an explicit operator order. Rules whose fixes
        would destroy information stay declared ``unfixable`` in
        ``tooling.yaml`` — that is rule selection, never disabling the
        mandatory unsafe channel. ***
        """

        format_check: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Flags for ruff format --check (read-only fmt)"),
        ]
        format_apply: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Flags for ruff format APPLY"),
        ]
        lint_check: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Flags for ruff check without mutation"),
        ]
        lint_fix: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Flags for ruff check --fix; MANDATORY unsafe-fix channel"
                    " (operator law 2026-10-05): the lint gate's apply mode"
                    " (make fix) always applies safe and unsafe fixes"
                ),
            ),
        ]

        @m.model_validator(mode="after")
        def _require_unsafe_fixes(self) -> Self:
            """Keep the mandatory unsafe lint-repair channel enabled.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If make.ruff.lint_fix lacks the mandatory flag.

            """
            if c.Infra.RUFF_UNSAFE_FIXES_FLAG not in self.lint_fix:
                msg = (
                    "make.ruff.lint_fix must carry "
                    f"{c.Infra.RUFF_UNSAFE_FIXES_FLAG} (operator"
                    " law 2026-10-05: the unsafe repair channel is mandatory"
                    " and never disabled again)"
                )
                raise ValueError(msg)
            return self

    class MakeSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Complete generated Makefile public and extension contract."""

        class TestmonCachePolicySpec(FlextInfraModelsConfigContract.ConfigContract):
            """Declarative Actions-cache policy for the shared testmon database.

            Implements the preserved #1001 delta (bead flext-j0u23): two-phase
            generations with per-mode caps, a per-repository byte budget with a
            three-stage quota ladder and a cache-key namespace. Event identity
            determines publication eligibility; branch names are not policy.
            """

            mode: Annotated[
                Literal["bootstrap", "stable"],
                m.Field(description="Cache phase: bootstrap seeds, stable saves"),
            ] = "stable"
            save_enabled: Annotated[
                bool,
                m.Field(description="Master switch for cache publishes"),
            ] = False
            max_bootstrap_generations: Annotated[
                int,
                m.Field(gt=0, description="Retention cap for bootstrap generations"),
            ] = 3
            max_stable_generations: Annotated[
                int,
                m.Field(gt=0, description="Retention cap for stable generations"),
            ] = 3
            per_repo_budget_bytes: Annotated[
                int,
                m.Field(gt=0, description="Per-repository byte budget"),
            ] = 52_428_800
            warning_threshold_percent: Annotated[
                int,
                m.Field(ge=0, le=100, description="Quota-ladder warning stage"),
            ] = 80
            maintenance_threshold_percent: Annotated[
                int,
                m.Field(ge=0, le=100, description="Quota-ladder maintenance stage"),
            ] = 90
            block_threshold_percent: Annotated[
                int,
                m.Field(ge=0, le=100, description="Quota-ladder block stage"),
            ] = 95
            key_prefix: Annotated[
                t.NonEmptyStr,
                m.Field(description="Actions cache key namespace"),
            ] = "flext-testmon"

            @m.model_validator(mode="after")
            def require_ascending_quota_ladder(self) -> Self:
                """Keep the quota ladder strictly ascending within the percent scale.

                Returns:
                    The resulting ``Self``.

                Raises:
                    ValueError: If testmon cache quota ladder must ascend warning <
                        maintenance < block <= 100.

                """
                full_scale = 100
                if not (
                    self.warning_threshold_percent
                    < self.maintenance_threshold_percent
                    < self.block_threshold_percent
                    <= full_scale
                ):
                    msg = (
                        "testmon cache quota ladder must ascend"
                        " warning < maintenance < block <= 100"
                    )
                    raise ValueError(msg)
                return self

        class TestmonCacheSpec(
            FlextInfraExternalCacheDirectorySpec.Directory[
                FlextInfraConstantsConfig.PytestCacheEnvironment
            ],
            FlextInfraModelsConfigContract.ConfigContract,
        ):
            """Persistent pytest-testmon database and runner paths."""

            database_filename: Annotated[
                t.NonEmptyStr,
                m.Field(description="pytest-testmon database filename"),
            ]
            database_environment_variable: Annotated[
                FlextInfraConstantsConfig.PytestCacheEnvironment,
                m.Field(
                    description="pytest-testmon's supported database-path variable",
                ),
            ]
            data_home_environment_variable: Annotated[
                FlextInfraConstantsConfig.PytestCacheEnvironment,
                m.Field(description="XDG persistent cache-home variable"),
            ] = m.Field()
            user_home_environment_variable: Annotated[
                FlextInfraConstantsConfig.PytestCacheEnvironment,
                m.Field(
                    description="User home variable for the XDG default",
                ),
            ] = m.Field()
            target_directory: Annotated[
                Path,
                m.Field(description="Repository-relative pytest target"),
            ]
            reports_directory: Annotated[
                Path,
                m.Field(description="Repository-relative pytest reports root"),
            ]

            @m.model_validator(mode="after")
            def require_external_database_contract(self) -> Self:
                """Keep testmon's official path variable and external path policy exact.

                Returns:
                    The resulting ``Self``.

                Raises:
                    ValueError: If testmon cache database_filename must be a filename;
                        or if testmon cache.

                """
                for name, actual, expected in (
                    (
                        "database_environment_variable",
                        self.database_environment_variable,
                        FlextInfraConstantsConfig.PytestCacheEnvironment.DATABASE_FILE,
                    ),
                    (
                        "data_home_environment_variable",
                        self.data_home_environment_variable,
                        FlextInfraConstantsConfig.PytestCacheEnvironment.DATA_HOME,
                    ),
                    (
                        "user_home_environment_variable",
                        self.user_home_environment_variable,
                        FlextInfraConstantsConfig.PytestCacheEnvironment.USER_HOME,
                    ),
                ):
                    if actual != expected:
                        msg = f"testmon cache {name} must be {expected.value}"
                        raise ValueError(msg)
                if Path(self.database_filename).name != self.database_filename:
                    msg = "testmon cache database_filename must be a filename"
                    raise ValueError(msg)
                return self

        class PytestScratchSpec(FlextInfraModelsConfigContract.ConfigContract):
            """Scratch root every pytest-running verb declares (storage law).

            The root is ``$<home>/<home_relative_directory>/<state_directory_name>``
            followed by the absolute checkout path and ``<namespace>``: never
            ``/tmp`` and never inside a versioned tree (a workspace member's
            parent directory is the superproject checkout).
            """

            user_home_environment_variable: Annotated[
                FlextInfraConstantsConfig.PytestCacheEnvironment,
                m.Field(description="User home variable anchoring the scratch root"),
            ]
            home_relative_directory: Annotated[
                t.NonEmptyStr,
                m.Field(description="Home-relative scratch base directory"),
            ]
            state_directory_name: Annotated[
                t.NonEmptyStr,
                m.Field(description="Runtime-state directory name under the base"),
            ]
            namespace: Annotated[
                t.NonEmptyStr,
                m.Field(description="Scratch namespace below the checkout path"),
            ]

            @m.model_validator(mode="after")
            def require_home_relative_components(self) -> Self:
                """Keep the scratch root anchored at home and free of traversal.

                Returns:
                    The resulting ``Self``.

                Raises:
                    ValueError: If the home variable is not the user home, or a
                        component is absolute, traverses upward, or is not a
                        single path segment where one is required.

                """
                if (
                    self.user_home_environment_variable
                    != FlextInfraConstantsConfig.PytestCacheEnvironment.USER_HOME
                ):
                    msg = (
                        "pytest scratch user_home_environment_variable must be "
                        f"{FlextInfraConstantsConfig.PytestCacheEnvironment.USER_HOME.value}"
                    )
                    raise ValueError(msg)
                base = Path(self.home_relative_directory)
                if base.is_absolute() or ".." in base.parts:
                    msg = "pytest scratch home_relative_directory must stay below home"
                    raise ValueError(msg)
                for name, value in (
                    ("state_directory_name", self.state_directory_name),
                    ("namespace", self.namespace),
                ):
                    if Path(value).name != value or value in {".", ".."}:
                        msg = f"pytest scratch {name} must be one path segment"
                        raise ValueError(msg)
                return self

        examples_timeout_seconds: Annotated[
            int,
            m.Field(gt=0, le=120, description="Workspace examples process deadline"),
        ]
        submodule_timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                le=600,
                description="Deadline per wave of concurrent submodule clones",
            ),
        ]
        submodule_jobs: Annotated[
            int,
            m.Field(ge=1, le=32, description="Concurrent governed submodule clones"),
        ]
        ruff: Annotated[
            FlextInfraModelsConfigMake.MakeRuffSpec,
            m.Field(description="Ruff CLI flags for fmt/fix/check Make verbs"),
        ]
        fmt_gates: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Gates whose mutating side `make fmt` drives (formatters). "
                    "The read-only side runs in `make check`; `make fix` never "
                    "repeats them (single-pass verb law)."
                ),
            ),
        ] = ("markdown-format",)
        pre_commit: Annotated[
            Literal[True],
            m.Field(
                default=True,
                description=(
                    "Mandatory projected commit hook; local make setup installs it"
                ),
            ),
        ] = True
        pre_push: Annotated[
            bool,
            m.Field(
                default=False,
                description="Generate the pre-push stage; local make setup installs it",
            ),
        ] = False
        workflow: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigMake.MakeWorkflowStepSpec],
            m.Field(min_length=1, description="Ordered canonical validation workflow"),
        ]
        lifecycle_steps: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigMake.MakeLifecycleStepSpec],
            m.Field(
                min_length=1, description="Ordered public runtime acceptance steps"
            ),
        ]
        ci: Annotated[
            FlextInfraModelsConfigMake.MakeCiSpec,
            m.Field(description="Config-owned CI-only environment delta"),
        ]
        native_environment_unset: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description="Inherited selectors excluded from native project execution"
            ),
        ]
        github_credential_command: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description=(
                    "Declared local GitHub credential command: selected once, "
                    "outside CI, when the caller exports no GitHub token and "
                    "its executable is installed; its failure stops the verb"
                ),
            ),
        ]
        setup_timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0, description="Native environment installation wall-time budget"
            ),
        ]
        testmon_cache: Annotated[
            TestmonCacheSpec,
            m.Field(description="Adaptive testmon Actions cache policy"),
        ]
        pytest_scratch: Annotated[
            PytestScratchSpec,
            m.Field(description="Scratch root declared by every pytest verb"),
        ]
        gate_acceptance_policy: Annotated[
            FlextInfraConstantsConfig.GateAcceptancePolicy,
            m.Field(description="Policy recorded by original gate execution receipts"),
        ] = FlextInfraConstantsConfig.GateAcceptancePolicy.CLEAN
        gate_receipts_directory: Annotated[
            Path,
            m.Field(description="Repository-relative immutable execution receipts"),
        ] = Path(".reports/gates")
        generation_profile_path: Annotated[
            Path,
            m.Field(description="Repository-relative canonical generation profile"),
        ]
        modification_profile_path: Annotated[
            Path,
            m.Field(description="Repository-relative canonical modification profile"),
        ]
        check_profile_path: Annotated[
            Path,
            m.Field(
                description=(
                    "Repository-relative profile of the check route; the "
                    "captured checker profiles beside its gate receipts"
                )
            ),
        ]
        check_report_output_environment_variable: Annotated[
            str,
            m.Field(
                pattern=r"^[A-Z][A-Z0-9_]*$",
                description="Invocation-owned checker report destination transport",
            ),
        ]
        testmon_cache_policy: Annotated[
            FlextInfraModelsConfigMake.TestmonCachePolicySpec,
            m.Field(
                description=(
                    "Declarative save/budget/quota policy for the shared"
                    " testmon cache (#1001 delta)"
                ),
            ),
        ]
        mypy_cache: Annotated[
            FlextInfraModelsConfigMake.MypyCacheSpec,
            m.Field(
                description="Project-keyed shared Mypy analysis cache policy",
            ),
        ]
        ruff_cache: Annotated[
            FlextInfraModelsConfigMake.RuffCacheSpec,
            m.Field(description="External project-keyed native Ruff cache policy"),
        ]
        verbs: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigMake.MakeVerbSpec],
            m.Field(description="Ordered canonical public verbs"),
        ]
        violations_sweep_repair_verbs: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Default ordered violations-sweep Make operations",
            ),
        ]
        type_contract_rules: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Exact AST migrations of source-declared type contracts",
            ),
        ]
        common_arguments: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Named controls accepted by every generated Make verb"),
        ] = ()
        clean: Annotated[
            FlextInfraModelsConfigMake.MakeCleanSpec,
            m.Field(description="Disposable artifacts removed by the clean verb"),
        ]
        docs: Annotated[
            FlextInfraModelsConfigMake.MakeDocsSpec,
            m.Field(description="Public documentation lifecycle policy"),
        ]
        custom_handler_policy: Annotated[
            FlextInfraModelsConfigMake.CustomHandlerPolicy,
            m.Field(description="Private custom target policy"),
        ]
        custom_handler_profile_overrides: Annotated[
            Mapping[
                t.NonEmptyStr,
                FlextInfraModelsConfigMake.CustomHandlerPolicyOverride,
            ],
            m.Field(description="Per-profile overrides of the custom handler policy"),
        ]
        project_check_gates: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigMake.MakeProjectCheckGateSpec],
            m.Field(
                default=(),
                description=(
                    "Repository-owned native module checks, executed once by "
                    "the same registry and physical-runtime runner as built-ins"
                ),
            ),
        ] = ()
        check_prerequisite_gates: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description=(
                    "Requested gates that must finish across every selected "
                    "repository before the remaining gates execute"
                ),
            ),
        ]

        @m.model_validator(mode="after")
        def _validate_project_check_gates(self) -> Self:
            """Project gates are unique and never shadow a built-in gate.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If make project_check_gates must be unique; or if make
                    project_check_gates shadow built-in gates; or if make
                    opt_in_check_gates name unknown gates.

            """
            names = tuple(gate.name for gate in self.project_check_gates)
            if len(set(names)) != len(names):
                msg = "make project_check_gates must be unique"
                raise ValueError(msg)
            builtin = set(c.Infra.CANONICAL_GATE_IDS)
            shadowed = sorted(set(names) & builtin)
            if shadowed:
                msg = (
                    "make project_check_gates shadow built-in gates: "
                    f"{', '.join(shadowed)}"
                )
                raise ValueError(msg)
            prerequisites = self.check_prerequisite_gates
            if len(set(prerequisites)) != len(prerequisites):
                msg = "make check_prerequisite_gates must be unique"
                raise ValueError(msg)
            unknown = set(prerequisites).difference(self.check_gates_allowed)
            if unknown:
                msg = (
                    "make check_prerequisite_gates name unknown gates: "
                    f"{', '.join(sorted(unknown))}"
                )
                raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
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
            and
            `{% raw %}{% for verb in make.verbs
            if verb.name != "setup" %}{% endraw %}`),
            so `setup` never depends on the environment it exists to create.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If make public verb names must be unique; or if make
                    workflow verbs must be unique; or if make workflow verbs are not
                    declared public verbs; or if make workflow verbs must exist in every
                    profile; or if make fmt gates are not declared gate vocabulary; or
                    if make docs reports_dir must
                    be repository-relative.

            """
            declared = {verb.name for verb in self.verbs}
            if len(declared) != len(self.verbs):
                msg = "make public verb names must be unique"
                raise ValueError(msg)
            admissible = {
                verb.name
                for verb in self.verbs
                if FlextInfraConfigMakeContract.make_verb_supports_profiles(
                    verb.profiles,
                    tuple(FlextInfraConstantsConfig.MakeProfile),
                )
            }
            if set(self.violations_sweep_repair_verbs) - admissible:
                msg = "make violations sweep requires declared verbs in every profile"
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
            self._validate_workflow(declared, admissible)
            self._validate_workflow_requirements()
            self._validate_docs_policy()
            return self

        def _validate_workflow(self, declared: set[str], admissible: set[str]) -> None:
            """Validate the workflow verbs against the declared public verbs.

            CI provisions first and runs the read-only check and complete test
            owners in order. The pre-commit rows select only the read-only check.

            Raises:
                ValueError: If make workflow verbs must be unique; or if make
                    workflow verbs are not declared public verbs; or if make
                    workflow verbs must be available in every profile; or if CI
                    approval boundaries or milestone order are invalid; or if
                    pre-commit selects an operation other than check.

            """
            workflow_verbs = tuple(step.verb for step in self.workflow)
            identities = tuple(step.identity for step in self.workflow)
            if len(set(identities)) != len(identities):
                msg = "make workflow phase identities must be unique"
                raise ValueError(msg)
            unknown_workflow = set(workflow_verbs) - declared
            if unknown_workflow:
                msg = (
                    "make workflow verbs are not declared public verbs: "
                    f"{', '.join(sorted(unknown_workflow))}"
                )
                raise ValueError(msg)
            unknown_lifecycle = {step.verb for step in self.lifecycle_steps} - declared
            if unknown_lifecycle:
                msg = (
                    "make lifecycle verbs are not declared public verbs: "
                    f"{', '.join(sorted(unknown_lifecycle))}"
                )
                raise ValueError(msg)
            # Optional data inputs do not narrow a common handler's operation.
            partial_workflow = sorted(
                f"{verb.name}(profiles="
                f"{tuple(str(profile) for profile in verb.profiles)!r})"
                for verb in self.verbs
                if verb.name in workflow_verbs and verb.name not in admissible
            )
            if partial_workflow:
                required_profiles = tuple(
                    str(profile) for profile in FlextInfraConstantsConfig.MakeProfile
                )
                msg = (
                    "make workflow verbs must be available in every profile: "
                    f"{', '.join(partial_workflow)}; required_profiles="
                    f"{required_profiles!r}"
                )
                raise ValueError(msg)
            approval = tuple(step for step in self.workflow if "ci" in step.contexts)
            milestones = (
                (c.Infra.VERB_CHECK, c.Infra.CheckPhase.PRIMARY),
                (c.Infra.VERB_TEST, c.Infra.CheckPhase.COMPLETE),
                (c.Infra.VERB_CHECK, c.Infra.CheckPhase.COMPLETE),
                (c.Infra.VERB_TEST, c.Infra.CheckPhase.COMPLETE),
            )
            if (
                not approval
                or approval[0].verb != "setup"
                or tuple(
                    (step.verb, step.phase)
                    for step in approval
                    if step.verb in {c.Infra.VERB_CHECK, c.Infra.VERB_TEST}
                )
                != milestones
            ):
                msg = (
                    "CI requires setup followed by primary check, native tests "
                    "and complete check followed by final incremental tests"
                )
                raise ValueError(msg)
            hook = tuple(
                step.verb for step in self.workflow if "pre_commit" in step.contexts
            )
            if hook != (c.Infra.VERB_CHECK,):
                msg = "the pre-commit hook requires only the check operation"
                raise ValueError(msg)

        def _validate_workflow_requirements(self) -> None:
            """Validate the declared phase dependency topology and contexts.

            Raises:
                ValueError: If a required phase is not earlier or does not run
                    in the declared dependency contexts.

            """
            for index, step in enumerate(self.workflow):
                earlier = {
                    prior.identity: set(prior.contexts)
                    for prior in self.workflow[:index]
                }
                for required in step.requires:
                    if required.step not in earlier:
                        msg = (
                            f"make workflow step {step.identity} "
                            f"requires {required.step}, which must precede it"
                        )
                        raise ValueError(msg)
                    if not set(required.contexts) <= (
                        set(step.contexts) & earlier[required.step]
                    ):
                        msg = (
                            f"make workflow step {step.identity} "
                            f"requires {required.step} "
                            "in unavailable dependency contexts"
                        )
                        raise ValueError(msg)
            for step in self.workflow:
                if step.verb == c.Infra.VERB_TEST:
                    self._validate_test_admission(step)
            self._validate_admission_requirements()

        def _validate_test_admission(
            self, tests: FlextInfraModelsConfigMake.MakeWorkflowStepSpec
        ) -> None:
            """Require primary evidence in every context of each test invocation.

            Raises:
                ValueError: If any test context lacks a declared primary dependency.

            """
            primary = {
                step.identity
                for step in self.workflow
                if step.verb == c.Infra.VERB_CHECK
                and step.phase == c.Infra.CheckPhase.PRIMARY
            }
            covered = {
                context
                for required in tests.requires
                if required.step in primary
                for context in required.contexts
            }
            if covered != set(tests.contexts):
                msg = (
                    "tests require fresh global primary check evidence: "
                    "every tests context must require the primary check phase"
                )
                raise ValueError(msg)

        def _validate_admission_requirements(self) -> None:
            """Keep initial source, behavioral and complete acceptance distinct.

            Raises:
                ValueError: If tests lack global primary admission or complete
                    check lacks prior behavioral admission outside the commit hook.

            """
            tests = next(
                step for step in self.workflow if step.verb == c.Infra.VERB_TEST
            )
            complete = next(
                step
                for step in self.workflow
                if step.verb == c.Infra.VERB_CHECK
                and step.phase == c.Infra.CheckPhase.COMPLETE
            )
            if not any(
                required.step == tests.identity
                and set(required.contexts) == set(complete.contexts) - {"pre_commit"}
                for required in complete.requires
            ):
                msg = "complete check requires native tests outside the commit hook"
                raise ValueError(msg)
            final_tests = next(
                step
                for step in reversed(self.workflow)
                if step.verb == c.Infra.VERB_TEST
            )
            if not any(
                required.step == complete.identity
                and set(required.contexts) == set(final_tests.contexts)
                for required in final_tests.requires
            ):
                msg = "final native tests require complete check acceptance"
                raise ValueError(msg)

        def _validate_docs_policy(self) -> None:
            """Validate formatter ownership and repository-relative report paths.

            Raises:
                ValueError: If make fmt gates are not declared gate vocabulary; or
                    if report paths are empty, absolute or escape the repository.

            """
            unknown_fmt_gates = set(self.fmt_gates) - set(
                c.Infra.SARIF_TOOL_INFO,
            )
            if unknown_fmt_gates:
                msg = (
                    "make fmt gates are not declared gate vocabulary: "
                    f"{', '.join(sorted(unknown_fmt_gates))}"
                )
                raise ValueError(msg)
            for name, path in (
                ("docs.reports_dir", self.docs.reports_dir),
                ("generation_profile_path", self.generation_profile_path),
                ("modification_profile_path", self.modification_profile_path),
                ("check_profile_path", self.check_profile_path),
            ):
                if path.is_absolute() or ".." in path.parts or not path.parts:
                    msg = f"make {name} must be nonempty and repository-relative"
                    raise ValueError(msg)

        @m.computed_field
        @property
        def approval_verbs(self) -> t.VariadicTuple[str]:
            """Ordered approval derived once from the validated workflow."""
            return tuple(step.verb for step in self.workflow if "ci" in step.contexts)

        @m.computed_field
        @property
        def check_gates_allowed(self) -> t.VariadicTuple[str]:
            """Canonical generated Make check-gate vocabulary.

            The built-in gates this package implements, plus the gates the
            project declares for itself. The built-in tuple is the BASE, never
            the whole vocabulary: a consuming repository owns gates this
            package knows nothing about, and rejecting them as unknown is what
            kept working handlers unreachable from `make check`.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return (
                c.Infra.RUNTIME_INTEGRITY,
                *(gate.name for gate in self.project_check_gates if gate.integrity),
                *(
                    gate
                    for gate in c.Infra.CANONICAL_GATE_IDS
                    if gate != c.Infra.RUNTIME_INTEGRITY
                ),
                *(gate.name for gate in self.project_check_gates if not gate.integrity),
            )

        @m.computed_field
        @property
        def check_gates_default(self) -> t.VariadicTuple[str]:
            """Active default gates, shared by local, CI, hooks, and project gates.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return self.check_gates_allowed

        @m.computed_field
        @property
        def check_gates_local(self) -> t.VariadicTuple[str]:
            """Run the complete active gate universe locally and at pre-push.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return self.check_gates_default

        @m.computed_field
        @property
        def check_gate_stages(
            self,
        ) -> Mapping[str, FlextInfraConstantsConfig.GateStage]:
            """Earliest approval stage of every active gate.

            Built-in stages come from their registry rows; a repository-owned
            gate carries its own declared stage.

            Returns:
                The stage of each gate in ``check_gates_default``.

            """
            return {
                **c.Infra.GATE_STAGES,
                **{gate.name: gate.stage for gate in self.project_check_gates},
            }

        @m.computed_field
        @property
        def check_gates_ci(self) -> t.VariadicTuple[str]:
            """CI runs the commit-stage and CI-stage gates (gate-budget law).

            Returns:
                The active gates, in default order, CI admits.

            """
            stages = self.check_gate_stages
            return tuple(
                gate
                for gate in self.check_gates_default
                if stages[gate] != FlextInfraConstantsConfig.GateStage.PUSH
            )

        @m.computed_field
        @property
        def pre_commit_check_gates(self) -> t.VariadicTuple[str]:
            """The commit hook runs only the fast commit-stage gates.

            Returns:
                The active gates, in default order, the commit hook admits.

            """
            stages = self.check_gate_stages
            return tuple(
                gate
                for gate in self.check_gates_default
                if stages[gate] == FlextInfraConstantsConfig.GateStage.COMMIT
            )

        @m.computed_field
        @property
        def check_gates_fixable(self) -> t.VariadicTuple[str]:
            """Repair-capable gates outside the declared formatter operation.

            Asking for a gate that cannot fix anything still pays its full cost;
            a fix pass built from the ALLOWED vocabulary once timed out doing
            exactly that.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                gate
                for gate in c.Infra.CANONICAL_FIXABLE_GATE_IDS
                if gate not in self.fmt_gates
            )

        @m.computed_field
        @property
        def check_gates_file(self) -> t.VariadicTuple[str]:
            """Gates whose checker accepts one declared file.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return c.Infra.CANONICAL_FILE_GATE_IDS

        @m.computed_field
        @property
        def custom_handler_policies(
            self,
        ) -> Mapping[str, FlextInfraModelsConfigMake.CustomHandlerPolicy]:
            """Effective custom-handler policy for every Make profile.

            The base policy states the strictest contract (private handlers
            only). A profile whose custom surface legitimately owns more --
            a workspace root orchestrating its subprojects -- declares only the
            fields it relaxes, so the engine never has to know which project
            it is conforming.

            Returns:
                The resulting ``Mapping[str,
                    FlextInfraModelsConfigMake.CustomHandlerPolicy]``.

            """
            base = self.custom_handler_policy
            overrides = self.custom_handler_profile_overrides
            return _effective_custom_handler_policies(
                base,
                tuple(sorted(overrides.items())),
            )

    class CustomHandlerPolicy(FlextInfraModelsConfigContract.ConfigContract):
        """Strict schema for the only handwritten Make extension file."""

        filename: Annotated[
            t.NonEmptyStr,
            m.Field(description="Versioned custom handler filename"),
        ]
        target_pattern: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required private target regular expression"),
        ]
        allow_public_targets: bool = m.Field(description="Permit public targets")
        allow_toolchain_declarations: bool = m.Field(
            description="Permit toolchain declarations",
        )

    class CustomHandlerPolicyOverride(FlextInfraModelsConfigContract.ConfigContract):
        """Per-profile relaxation of the strict custom-handler contract.

        Every field is optional: a profile declares ONLY what it relaxes, so a
        new permission added to the base policy propagates automatically
        instead of having to be repeated in each profile.
        """

        allow_public_targets: bool | None = m.Field(
            default=None,
            description="Permit public targets",
        )
        allow_toolchain_declarations: bool | None = m.Field(
            default=None,
            description="Permit toolchain declarations",
        )


__all__: list[str] = ["FlextInfraModelsConfigMake"]
