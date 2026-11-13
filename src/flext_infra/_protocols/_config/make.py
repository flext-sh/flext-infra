# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/make
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra._constants.config import FlextInfraConstantsConfig
from flext_infra._protocols._config import (
    FlextInfraProtocolsConfigContract,
    FlextInfraProtocolsConfigExternalCache,
)

if TYPE_CHECKING:
    from flext_infra import c, t
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigMakeClean,
        FlextInfraProtocolsConfigMakeDocs,
    )


class FlextInfraProtocolsConfigMake:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MakeProjectCheckGateSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Unique gate ID."""
            ...

        @property
        def module(self) -> str:
            """Module executed by the selected physical runtime."""
            ...

        @property
        def arguments(self) -> tuple[str, ...]:
            """Native module argument tokens."""
            ...

        @property
        def integrity(self) -> bool:
            """Include this check in quick runtime integrity."""
            ...

        @property
        def stage(self) -> FlextInfraConstantsConfig.GateStage:
            """Structural member projected from the owning model.

            Earliest approval stage the check's cost admits; a repository-owned
            validator runs locally and at pre-push.
            """
            ...

        @property
        def timeout_seconds(self) -> int:
            """Native module check wall-time limit."""
            ...

    @runtime_checkable
    class RuffCacheSpec(
        FlextInfraProtocolsConfigExternalCache.Directory[str], Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def data_home_environment_variable(self) -> str:
            """XDG persistent cache-home variable."""
            ...

        @property
        def user_home_environment_variable(self) -> str:
            """User home variable for the XDG default."""
            ...

    @runtime_checkable
    class MakeCiSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def variable(self) -> t.NonEmptyStr:
            """CI environment key."""
            ...

        @property
        def value(self) -> t.NonEmptyStr:
            """CI environment value."""
            ...

        @property
        def local_value(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Local form of the CI ternary. Check runs the active local partition;
            other pre-push verbs declare this value to preserve their local
            behavior. Pre-push check unsets CI.
            """
            ...

        @property
        def pre_commit_value(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Token the generated commit hook passes to its check row: check then runs
            only the commit-stage gates (MakeSpec.pre_commit_check_gates) and no
            other validator.
            """
            ...

        @property
        def remote_variable(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Variable every remote runner exports, whatever CI token the step passes;
            a remote check never runs a local-stage gate.
            """
            ...

        @property
        def remote_value(self) -> t.NonEmptyStr:
            """Value of remote_variable on a remote runner."""
            ...

    @runtime_checkable
    class MakeVerbSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Public Make verb."""
            ...

        @property
        def arguments(self) -> tuple[t.NonEmptyStr, ...]:
            """Named Make inputs consumed by this operation."""
            ...

        @property
        def description(self) -> t.NonEmptyStr:
            """Operator-facing help text."""
            ...

        @property
        def requires_activation(self) -> bool:
            """Structural member projected from the owning model.

            Activate the declared environment before consuming it; generation uses
            its provisioned physical runtime directly.
            """
            ...

        @property
        def profiles(self) -> tuple[FlextInfraConstantsConfig.MakeProfile, ...]:
            """Structural member projected from the owning model.

            Make profiles whose generated Makefile declares the verb; a verb exists
            only where its operation applies.
            """
            ...

        @property
        def group(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Declared help section of a repository-owned verb; present exactly when
            the repository declares verb_groups.
            """
            ...

        @property
        def cli(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Console script followed by its route words; the generated handler
            forwards each argument as one --<kebab> option.
            """
            ...

    @runtime_checkable
    class MakeVerbGroupSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Section key."""
            ...

        @property
        def title(self) -> t.NonEmptyStr:
            """Operator-facing section heading."""
            ...

    @runtime_checkable
    class MakeOperationSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def verb(self) -> t.NonEmptyStr:
            """Declared public Make verb."""
            ...

        @property
        def phase(self) -> c.Infra.CheckPhase:
            """Checker evidence phase; other verbs are complete."""
            ...

        @property
        def make_command(self) -> str:
            """Canonical Make transport for this typed workflow operation."""
            ...

    @runtime_checkable
    class MakeLifecycleStepSpec(MakeOperationSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def contexts(self) -> tuple[Literal["local", "ci"], ...]:
            """Contexts where this acceptance step applies."""
            ...

    @runtime_checkable
    class MakeWorkflowRequirementSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def step(self) -> t.NonEmptyStr:
            """Required workflow identity."""
            ...

        @property
        def contexts(
            self,
        ) -> tuple[Literal["local", "ci", "pre_commit", "pre_push"], ...]:
            """Contexts requiring the prior green phase."""
            ...

    @runtime_checkable
    class MakeWorkflowStepSpec(MakeOperationSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def identity(self) -> t.NonEmptyStr:
            """Unique dependency identity, never a new Make verb."""
            ...

        @property
        def contexts(
            self,
        ) -> tuple[Literal["local", "ci", "pre_commit", "pre_push"], ...]:
            """Execution contexts consuming this single workflow row."""
            ...

        @property
        def requires(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeWorkflowRequirementSpec, ...]:
            """Structural member projected from the owning model.

            Earlier workflow identities whose green result admits this step in the
            declared dependency contexts.
            """
            ...

    @runtime_checkable
    class TestmonCachePolicySpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def mode(self) -> Literal["bootstrap", "stable"]:
            """Cache phase: bootstrap seeds, stable saves."""
            ...

        @property
        def save_enabled(self) -> bool:
            """Master switch for cache publishes."""
            ...

        @property
        def max_bootstrap_generations(self) -> int:
            """Retention cap for bootstrap generations."""
            ...

        @property
        def max_stable_generations(self) -> int:
            """Retention cap for stable generations."""
            ...

        @property
        def per_repo_budget_bytes(self) -> int:
            """Per-repository byte budget."""
            ...

        @property
        def warning_threshold_percent(self) -> int:
            """Quota-ladder warning stage."""
            ...

        @property
        def maintenance_threshold_percent(self) -> int:
            """Quota-ladder maintenance stage."""
            ...

        @property
        def block_threshold_percent(self) -> int:
            """Quota-ladder block stage."""
            ...

        @property
        def key_prefix(self) -> t.NonEmptyStr:
            """Actions cache key namespace."""
            ...

    @runtime_checkable
    class MypyCacheSpec(
        FlextInfraProtocolsConfigExternalCache.Directory[
            FlextInfraConstantsConfig.MypyCacheEnvironment
        ],
        FlextInfraProtocolsConfigContract.ConfigContract,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def data_home_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.MypyCacheEnvironment:
            """XDG persistent cache-home variable."""
            ...

        @property
        def user_home_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.MypyCacheEnvironment:
            """User home variable for the XDG default."""
            ...

        @property
        def cache_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.MypyCacheEnvironment:
            """Mypy's cache-directory environment variable."""
            ...

    @runtime_checkable
    class MakeRuffSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def format_check(self) -> tuple[t.NonEmptyStr, ...]:
            """Flags for ruff format --check (read-only fmt)."""
            ...

        @property
        def format_apply(self) -> tuple[t.NonEmptyStr, ...]:
            """Flags for ruff format APPLY."""
            ...

        @property
        def lint_check(self) -> tuple[t.NonEmptyStr, ...]:
            """Flags for ruff check without mutation."""
            ...

        @property
        def lint_fix(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Flags for ruff check --fix; MANDATORY unsafe-fix channel (operator law
            2026-10-05): the lint gate's apply mode (make fix) always applies safe
            and unsafe fixes.
            """
            ...

    @runtime_checkable
    class MakeExecutionSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def examples_timeout_seconds(self) -> int:
            """Workspace examples process deadline."""
            ...

        @property
        def submodule_timeout_seconds(self) -> int:
            """Deadline per wave of concurrent submodule clones."""
            ...

        @property
        def submodule_jobs(self) -> int:
            """Concurrent governed submodule clones."""
            ...

        @property
        def ruff(self) -> FlextInfraProtocolsConfigMake.MakeRuffSpec:
            """Ruff CLI flags for fmt/fix/check Make verbs."""
            ...

        @property
        def fmt_gates(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Gates whose mutating side `make fmt` drives (formatters). The read-only
            side runs in `make check`; `make fix` never repeats them (single-pass
            verb law).
            """
            ...

        @property
        def pre_commit(self) -> Literal[True]:
            """Mandatory projected commit hook; local make setup installs it."""
            ...

        @property
        def pre_push(self) -> bool:
            """Generate the pre-push stage; local make setup installs it."""
            ...

        @property
        def workflow(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeWorkflowStepSpec, ...]:
            """Ordered canonical validation workflow."""
            ...

        @property
        def lifecycle_steps(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeLifecycleStepSpec, ...]:
            """Ordered public runtime acceptance steps."""
            ...

        @property
        def ci(self) -> FlextInfraProtocolsConfigMake.MakeCiSpec:
            """Config-owned CI-only environment delta."""
            ...

        @property
        def native_environment_unset(self) -> tuple[t.NonEmptyStr, ...]:
            """Inherited selectors excluded from native project execution."""
            ...

        @property
        def github_credential_command(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Declared local GitHub credential command: selected once, outside CI,
            when the caller exports no GitHub token and its executable is installed;
            its failure stops the verb.
            """
            ...

        @property
        def setup_timeout_seconds(self) -> int:
            """Native environment installation wall-time budget."""
            ...

    @runtime_checkable
    class MakeHarnessSpec(MakeExecutionSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def testmon_cache(
            self,
        ) -> FlextInfraProtocolsConfigMake.MakeHarnessSpecTestmonCacheSpec:
            """Adaptive testmon Actions cache policy."""
            ...

        @property
        def pytest_scratch(
            self,
        ) -> FlextInfraProtocolsConfigMake.MakeHarnessSpecPytestScratchSpec:
            """Scratch root declared by every pytest verb."""
            ...

        @property
        def executor_environment(
            self,
        ) -> FlextInfraProtocolsConfigMake.MakeHarnessSpecExecutorEnvironmentSpec:
            """Structural member projected from the owning model.

            Isolated environment that runs the residual flext-infra upgrade step
            without importing the project.
            """
            ...

        @property
        def gate_acceptance_policy(
            self,
        ) -> FlextInfraConstantsConfig.GateAcceptancePolicy:
            """Policy recorded by original gate execution receipts."""
            ...

        @property
        def gate_receipts_directory(self) -> Path:
            """Repository-relative immutable execution receipts."""
            ...

        @property
        def generation_profile_path(self) -> Path:
            """Repository-relative canonical generation profile."""
            ...

        @property
        def modification_profile_path(self) -> Path:
            """Repository-relative canonical modification profile."""
            ...

        @property
        def check_profile_path(self) -> Path:
            """Structural member projected from the owning model.

            Repository-relative profile of the check route; the captured checker
            profiles beside its gate receipts.
            """
            ...

        @property
        def check_report_output_environment_variable(self) -> str:
            """Invocation-owned checker report destination transport."""
            ...

        @property
        def testmon_cache_policy(
            self,
        ) -> FlextInfraProtocolsConfigMake.TestmonCachePolicySpec:
            """Structural member projected from the owning model.

            Declarative save/budget/quota policy for the shared testmon cache (#1001
            delta).
            """
            ...

        @property
        def mypy_cache(self) -> FlextInfraProtocolsConfigMake.MypyCacheSpec:
            """Project-keyed shared Mypy analysis cache policy."""
            ...

        @property
        def ruff_cache(self) -> FlextInfraProtocolsConfigMake.RuffCacheSpec:
            """External project-keyed native Ruff cache policy."""
            ...

    @runtime_checkable
    class MakeHarnessSpecTestmonCachePolicySpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def mode(self) -> Literal["bootstrap", "stable"]:
            """Cache phase: bootstrap seeds, stable saves."""
            ...

        @property
        def save_enabled(self) -> bool:
            """Master switch for cache publishes."""
            ...

        @property
        def max_bootstrap_generations(self) -> int:
            """Retention cap for bootstrap generations."""
            ...

        @property
        def max_stable_generations(self) -> int:
            """Retention cap for stable generations."""
            ...

        @property
        def per_repo_budget_bytes(self) -> int:
            """Per-repository byte budget."""
            ...

        @property
        def warning_threshold_percent(self) -> int:
            """Quota-ladder warning stage."""
            ...

        @property
        def maintenance_threshold_percent(self) -> int:
            """Quota-ladder maintenance stage."""
            ...

        @property
        def block_threshold_percent(self) -> int:
            """Quota-ladder block stage."""
            ...

        @property
        def key_prefix(self) -> t.NonEmptyStr:
            """Actions cache key namespace."""
            ...

    @runtime_checkable
    class MakeHarnessSpecTestmonCacheSpec(
        FlextInfraProtocolsConfigExternalCache.Directory[
            FlextInfraConstantsConfig.PytestCacheEnvironment
        ],
        FlextInfraProtocolsConfigContract.ConfigContract,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def data_home_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.PytestCacheEnvironment:
            """XDG persistent cache-home variable."""
            ...

        @property
        def user_home_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.PytestCacheEnvironment:
            """User home variable for the XDG default."""
            ...

        @property
        def database_filename(self) -> t.NonEmptyStr:
            """pytest-testmon database filename."""
            ...

        @property
        def database_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.PytestCacheEnvironment:
            """pytest-testmon's supported database-path variable."""
            ...

        @property
        def target_directory(self) -> Path:
            """Repository-relative pytest target."""
            ...

        @property
        def reports_directory(self) -> Path:
            """Repository-relative pytest reports root."""
            ...

    @runtime_checkable
    class MakeHarnessSpecExecutorEnvironmentSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def directory(self) -> Path:
            """Runtime-root-relative executor environment."""
            ...

        @property
        def dependency_group(self) -> t.NonEmptyStr:
            """Dependency group whose frozen closure pins flext-infra."""
            ...

    @runtime_checkable
    class MakeHarnessSpecPytestScratchSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def user_home_environment_variable(
            self,
        ) -> FlextInfraConstantsConfig.PytestCacheEnvironment:
            """User home variable anchoring the scratch root."""
            ...

        @property
        def home_relative_directory(self) -> t.NonEmptyStr:
            """Home-relative scratch base directory."""
            ...

        @property
        def state_directory_name(self) -> t.NonEmptyStr:
            """Runtime-state directory name under the base."""
            ...

        @property
        def namespace(self) -> t.NonEmptyStr:
            """Scratch namespace below the checkout path."""
            ...

    @runtime_checkable
    class MakeAdmissionOverrideSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def max_load5(self) -> t.PositiveFloat | None:
            """Highest 5-minute load average that admits the verb."""
            ...

        @property
        def memory_limit_gb(self) -> t.PositiveInt | None:
            """Memory limit of each verb recipe, in GiB."""
            ...

        @property
        def max_processes(self) -> t.PositiveInt | None:
            """CPU limit of each verb recipe."""
            ...

    @runtime_checkable
    class MakeAdmissionLimitsSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def max_load5(self) -> t.PositiveFloat:
            """Highest 5-minute load average that admits the verb."""
            ...

        @property
        def memory_limit_gb(self) -> t.PositiveInt:
            """Memory limit of each verb recipe, in GiB."""
            ...

        @property
        def max_processes(self) -> t.PositiveInt:
            """CPU limit of each verb recipe."""
            ...

        @property
        def memory_limit_bytes(self) -> int:
            """Memory limit in bytes, the unit MemoryMax accepts."""
            ...

    @runtime_checkable
    class MakeAdmissionSpec(MakeAdmissionLimitsSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def overrides(
            self,
        ) -> Mapping[
            t.NonEmptyStr, FlextInfraProtocolsConfigMake.MakeAdmissionOverrideSpec
        ]:
            """Explicit per-verb exceptions to the defaults."""
            ...

        @property
        def refusal_guidance(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Lighter-route guidance printed with every refusal; plain Make text
            without '$', '#' or newlines.
            """
            ...

        @property
        def verb_limits(
            self,
        ) -> Mapping[str, FlextInfraProtocolsConfigMake.MakeAdmissionLimitsSpec]:
            """Each overridden verb's limits merged over the defaults."""
            ...

    @runtime_checkable
    class MakeVerbCatalogSpec(MakeHarnessSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def verbs(self) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Ordered canonical public verbs."""
            ...

        @property
        def cli_output_argument(self) -> str:
            """Structural member projected from the owning model.

            Make input every CLI-routed verb accepts to select the CLI output
            format.
            """
            ...

        @property
        def cli_output_environment(self) -> str:
            """Structural member projected from the owning model.

            Environment variable the CLI settings owner reads as its output format.
            """
            ...

        @property
        def common_verb_group(self) -> str:
            """Structural member projected from the owning model.

            Section key that holds the canonical and release verbs when a repository
            declares verb_groups.
            """
            ...

        @property
        def violations_sweep_repair_verbs(self) -> tuple[t.NonEmptyStr, ...]:
            """Default ordered violations-sweep Make operations."""
            ...

        @property
        def type_contract_rules(self) -> tuple[t.NonEmptyStr, ...]:
            """Exact AST migrations of source-declared type contracts."""
            ...

        @property
        def common_arguments(self) -> tuple[t.NonEmptyStr, ...]:
            """Named controls accepted by every generated Make verb."""
            ...

        @property
        def bootstrap_bin_dir(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Repository-local directory of the bootstrap Mise binary, cached by the
            generated CI workflows.
            """
            ...

        @property
        def clean(self) -> FlextInfraProtocolsConfigMakeClean.MakeCleanSpec:
            """Disposable artifacts removed by the clean verb."""
            ...

        @property
        def docs(self) -> FlextInfraProtocolsConfigMakeDocs.MakeDocsSpec:
            """Public documentation lifecycle policy."""
            ...

    @runtime_checkable
    class MakeSpec(MakeVerbCatalogSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def custom_handler_policy(
            self,
        ) -> FlextInfraProtocolsConfigMake.CustomHandlerPolicy:
            """Private custom target policy."""
            ...

        @property
        def custom_handler_profile_overrides(
            self,
        ) -> Mapping[
            t.NonEmptyStr, FlextInfraProtocolsConfigMake.CustomHandlerPolicyOverride
        ]:
            """Per-profile overrides of the custom handler policy."""
            ...

        @property
        def project_check_gates(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeProjectCheckGateSpec, ...]:
            """Structural member projected from the owning model.

            Repository-owned native module checks, executed once by the same
            registry and physical-runtime runner as built-ins.
            """
            ...

        @property
        def check_prerequisite_gates(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Requested gates that must finish across every selected repository before
            the remaining gates execute.
            """
            ...

        @property
        def check_prerequisite_pyrefly_workers(self) -> t.PositiveInt:
            """Structural member projected from the owning model.

            Bounded Pyrefly workers for primary admission while lint retains its own
            native concurrency.
            """
            ...

        @property
        def scan_threads(self) -> t.PositiveInt:
            """Bounded thread budget for ast-grep scan execution."""
            ...

        @property
        def admission(self) -> FlextInfraProtocolsConfigMake.MakeAdmissionSpec:
            """Host admission and run limits of every public verb."""
            ...

        @property
        def approval_verbs(self) -> tuple[str, ...]:
            """Ordered approval derived once from the validated workflow."""
            ...

        @property
        def check_gates_allowed(self) -> tuple[str, ...]:
            """Canonical generated Make check-gate vocabulary."""
            ...

        @property
        def check_gates_default(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Active default gates, shared by local, CI, hooks, and project gates.
            """
            ...

        @property
        def check_gates_local(self) -> tuple[str, ...]:
            """Run the complete active gate universe locally and at pre-push."""
            ...

        @property
        def check_gate_stages(
            self,
        ) -> Mapping[str, FlextInfraConstantsConfig.GateStage]:
            """Earliest approval stage of every active gate."""
            ...

        @property
        def check_gates_ci(self) -> tuple[str, ...]:
            """CI runs the commit-stage and CI-stage gates (gate-budget law)."""
            ...

        @property
        def pre_commit_check_gates(self) -> tuple[str, ...]:
            """The commit hook runs only the fast commit-stage gates."""
            ...

        @property
        def check_gates_fixable(self) -> tuple[str, ...]:
            """Repair-capable gates outside the declared formatter operation."""
            ...

        @property
        def check_gates_file(self) -> tuple[str, ...]:
            """Gates whose checker accepts one declared file."""
            ...

        @property
        def custom_handler_policies(
            self,
        ) -> Mapping[str, FlextInfraProtocolsConfigMake.CustomHandlerPolicy]:
            """Effective custom-handler policy for every Make profile."""
            ...

    @runtime_checkable
    class CustomHandlerPolicy(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def filename(self) -> t.NonEmptyStr:
            """Versioned custom handler filename."""
            ...

        @property
        def target_pattern(self) -> t.NonEmptyStr:
            """Required private target regular expression."""
            ...

        @property
        def allow_public_targets(self) -> bool:
            """Permit public targets."""
            ...

        @property
        def allow_toolchain_declarations(self) -> bool:
            """Permit toolchain declarations."""
            ...

    @runtime_checkable
    class CustomHandlerPolicyOverride(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def allow_public_targets(self) -> bool | None:
            """Permit public targets."""
            ...

        @property
        def allow_toolchain_declarations(self) -> bool | None:
            """Permit toolchain declarations."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigMake",
]
