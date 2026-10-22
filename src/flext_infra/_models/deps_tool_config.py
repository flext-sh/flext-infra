"""Tool configuration models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigLinters,
    FlextInfraModelsDepsToolConfigTypeCheckers,
    FlextInfraModelsDuplication,
)


class FlextInfraModelsDepsToolConfig(
    FlextInfraModelsDepsToolConfigLinters,
    FlextInfraModelsDepsToolConfigTypeCheckers,
):
    """Models for tool configuration loaded from YAML."""

    class ModPhasesConfig(m.ArbitraryTypesModel):
        """Component selection for ``make mod`` phases (toggles are data)."""

        import_alignment: Annotated[
            bool,
            m.Field(
                alias="import-alignment",
                default=True,
                description=("Run the rope-native import-alignment phase of make mod."),
            ),
        ] = True

    class ModConfig(m.ArbitraryTypesModel):
        """Declarative policy for the unified modernize verb ``mod``."""

        phases: FlextInfraModelsDepsToolConfig.ModPhasesConfig = m.Field(
            description="Phase toggles read from config/tooling.yaml.",
        )

    class PytestWorkerCeiling(m.ArbitraryTypesModel):
        """Tagged per-project pytest worker ceiling: absolute or CPU fraction.

        Exactly one of ``workers`` (absolute count) or ``cpu_fraction``
        (``"numerator/denominator"`` of the process CPU count) must be set.
        A bare integer (legacy YAML form) coerces to ``workers``.
        """

        workers: Annotated[
            int | None,
            m.Field(
                gt=0,
                le=64,
                description="Absolute xdist worker ceiling for the project.",
            ),
        ] = None
        cpu_fraction: Annotated[
            str | None,
            m.Field(
                pattern=r"^[1-9][0-9]*/[1-9][0-9]*$",
                description=(
                    "CPU-fraction worker ceiling (numerator/denominator of "
                    'the process CPU count), e.g. "1/4".'
                ),
            ),
        ] = None

        @m.model_validator(mode="before")
        @classmethod
        def _coerce_legacy_int(cls, data: t.JsonValue) -> t.JsonValue:
            """Accept the legacy bare-integer form as an absolute ceiling.

            Returns:
                The resulting ``t.JsonValue``.

            """
            if isinstance(data, int) and not isinstance(data, bool):
                return {"workers": data}
            return data

        @m.model_validator(mode="after")
        def _require_exactly_one_form(
            self,
        ) -> FlextInfraModelsDepsToolConfig.PytestWorkerCeiling:
            """Reject ambiguous (both or neither) ceiling forms.

            Returns:
                The resulting ``FlextInfraModelsDepsToolConfig.PytestWorkerCeiling``.

            Raises:
                ValueError: If PytestWorkerCeiling requires exactly one of workers or
                    cpu_fraction.

            """
            if (self.workers is None) == (self.cpu_fraction is None):
                msg = (
                    "PytestWorkerCeiling requires exactly one of"
                    " workers or cpu_fraction"
                )
                raise ValueError(msg)
            return self

    class PytestConfig(m.ArbitraryTypesModel):
        """Pytest baseline settings loaded from YAML."""

        # Every rendered pytest value is validated config data.
        slow_timeout_seconds: Annotated[
            int,
            m.Field(
                alias="slow-timeout-seconds",
                gt=0,
                description="Hard maximum runtime for one explicitly slow item.",
            ),
        ]
        slow_marker: Annotated[
            t.NonEmptyStr,
            m.Field(
                alias="slow-marker",
                description="Native pytest marker whose items run in their own phase.",
            ),
        ]
        run_timeout_seconds: Annotated[
            int,
            m.Field(
                alias="run-timeout-seconds",
                gt=0,
                description=(
                    "Fleet-default wall-clock maximum for one testmon runner operation."
                ),
            ),
        ]
        run_timeout_overrides: Annotated[
            Mapping[str, Annotated[int, m.Field(gt=0)]],
            m.Field(
                alias="run-timeout-overrides",
                description="Per-project hard wall for one testmon runner operation.",
            ),
        ] = {}
        termination_grace_seconds: Annotated[
            int,
            m.Field(
                alias="termination-grace-seconds",
                gt=0,
                description="Grace period reserved inside the invocation deadline.",
            ),
        ]
        max_failures: Annotated[
            int,
            m.Field(
                alias="max-failures",
                ge=1,
                description="Maximum failures before the pytest invocation stops.",
            ),
        ]
        enforcement_plugin: Annotated[
            t.NonEmptyStr,
            m.Field(
                alias="enforcement-plugin",
                description="Required pytest11 enforcement plugin loaded by Make.",
            ),
        ]
        progress_args: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="progress-args",
                strict=False,
                min_length=1,
                description="Arguments that expose each pytest item and live progress.",
            ),
        ]
        report_args: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="report-args",
                strict=False,
                min_length=1,
                description="Canonical concise pytest reporting arguments.",
            ),
        ]
        diagnostic_args: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="diagnostic-args",
                strict=False,
                min_length=1,
                description="Canonical expanded pytest diagnostic arguments.",
            ),
        ]
        parallel_workers: Annotated[
            int,
            m.Field(
                alias="parallel-workers",
                gt=0,
                le=16,
                description="Upper pytest-xdist worker ceiling for full runs.",
            ),
        ]
        parallel_worker_memory_gb: Annotated[
            int,
            m.Field(
                alias="parallel-worker-memory-gb",
                gt=0,
                le=64,
                description=(
                    "Physical-memory reservation per xdist worker; the runner "
                    "also bounds workers by available CPU."
                ),
            ),
        ]
        parallel_distribution: Annotated[
            Literal["load", "loadscope"],
            m.Field(
                alias="parallel-distribution",
                description="Pytest-xdist scheduler for full runs.",
            ),
        ]
        loadscope_reorder: Annotated[
            bool,
            m.Field(
                alias="loadscope-reorder",
                strict=True,
                description=(
                    "Let the native loadscope scheduler reorder scopes by size."
                ),
            ),
        ]
        parallel_schedule_chunk: Annotated[
            int,
            m.Field(
                alias="parallel-schedule-chunk",
                ge=1,
                description=(
                    "Maximum tests scheduled per dispatch step under the load "
                    "distribution. One makes the declared max-failures stop "
                    "take effect at the next item boundary in every worker "
                    "instead of after each worker drains a large pre-assigned "
                    "chunk, so a red suite exits typed and early at fleet "
                    "scale inside the fixed run budget."
                ),
            ),
        ]
        parallel_worker_overrides: Annotated[
            Mapping[str, FlextInfraModelsDepsToolConfig.PytestWorkerCeiling],
            m.Field(
                alias="parallel-worker-overrides",
                description=(
                    "Per declared-project worker ceilings (``[project].name`` "
                    "→ absolute ``workers`` or CPU ``cpu_fraction``) resolved "
                    "by the runner over the fleet-wide ``parallel-workers`` "
                    "default: a consumer whose measured suite cannot fit the "
                    "single-worker process boundary declares its ceiling "
                    "here, inside the fleet cycle. The legacy bare-integer "
                    "form still reads as an absolute ``workers`` ceiling."
                ),
            ),
        ] = {}
        profile_sort: Annotated[
            Literal[
                "calls",
                "cumulative",
                "filename",
                "line",
                "name",
                "nfl",
                "pcalls",
                "stdname",
                "time",
            ],
            m.Field(alias="profile-sort", description="Sort key for cProfile reports."),
        ]
        profile_limit: Annotated[
            int,
            m.Field(
                alias="profile-limit",
                gt=0,
                le=1000,
                description="Maximum cProfile rows rendered.",
            ),
        ]
        profile_suite_filename: Annotated[
            t.NonEmptyStr,
            m.Field(
                alias="profile-suite-filename",
                description="Suite cProfile artifact filename",
            ),
        ]
        profile_process_directory: Annotated[
            t.NonEmptyStr,
            m.Field(
                alias="profile-process-directory",
                description="Per-process cProfile artifact directory",
            ),
        ]
        # Collection roots are validated config, not local state.

        standard_markers: Annotated[
            t.StrSequence,
            m.Field(
                alias="standard-markers",
                description="Standard pytest markers enforced by modernizer.",
            ),
        ]
        external_gate_markers: Annotated[
            tuple[str, ...],
            m.Field(
                alias="external-gate-markers",
                strict=False,
                description=(
                    "Markers of external-token gates deselected by offline"
                    " verification and reported as NOT EXECUTED; each must be"
                    " declared in standard-markers."
                ),
            ),
        ]

        @property
        def external_gate_deselection(self) -> str:
            """Pytest ``-m`` expression that skips external gates."""
            return f"not ({' or '.join(self.external_gate_markers)})"

        ci_excluded_markers: Annotated[
            tuple[str, ...],
            m.Field(
                alias="ci-excluded-markers",
                strict=False,
                description="Declared markers deselected in CI and pre-commit only.",
            ),
        ]
        ci_excluded_fixtures: Annotated[
            tuple[str, ...],
            m.Field(
                alias="ci-excluded-fixtures",
                strict=False,
                description="Fixtures that need local-only provisioning",
            ),
        ] = ()

        @m.computed_field
        @property
        def parallel_arguments(self) -> t.StrTuple:
            """Native scheduler arguments derived from the typed policy."""
            scheduling = (
                ("--maxschedchunk", str(self.parallel_schedule_chunk))
                if self.parallel_distribution == "load"
                else (
                    "--loadscope-reorder"
                    if self.loadscope_reorder
                    else "--no-loadscope-reorder",
                )
            )
            return ("--dist", self.parallel_distribution, *scheduling)

        @property
        def process_timeout_seconds(self) -> int:
            """Derive the fleet-default outer wall without a second config field."""
            return self.run_timeout_seconds + (self.termination_grace_seconds * 2)

        @property
        def slow_suite_stop_reserve_seconds(self) -> int:
            """Derive the slow-phase reserve bounded by the slow ceiling."""
            return (
                self.xdist_items_per_worker * self.slow_timeout_seconds
                + self.termination_grace_seconds
            )

        @property
        def slow_serial_suite_stop_reserve_seconds(self) -> int:
            """Derive the slow-phase serial reserve: one slow item plus grace."""
            return self.slow_timeout_seconds + self.termination_grace_seconds

        @property
        def xdist_items_per_worker(self) -> int:
            """Xdist depth per worker: the running item plus one queued, or a chunk."""
            return max(2, self.parallel_schedule_chunk)

        @m.model_validator(mode="after")
        def _validate_execution_limits(self) -> Self:
            """Keep slow-item and termination budgets inside the invocation cap.

            Returns:
                The resulting ``Self``.

            """
            self._validate_timeouts()
            self._validate_arg_vocabulary()
            return self

        def _validate_timeouts(self) -> None:
            """Keep slow-item and termination budgets inside the invocation cap.

            Raises:
                ValueError: If termination or slow budgets exceed the invocation
                    wall; baseline arguments override execution policy; or
                    progress arguments hide item names.

            """
            if self.termination_grace_seconds >= self.run_timeout_seconds:
                msg = "pytest termination grace must be less than run timeout"
                raise ValueError(msg)
            if self.slow_timeout_seconds >= self.run_timeout_seconds:
                msg = "pytest slow timeout must be less than run timeout"
                raise ValueError(msg)
            # Only the slow phase has a bounded item drain. Ordinary items are
            # stopped by the aggregate process wall, not a synthetic item cap.
            reserve = self.slow_suite_stop_reserve_seconds
            if any(
                timeout <= reserve
                for timeout in (
                    self.run_timeout_seconds,
                    *self.run_timeout_overrides.values(),
                )
            ):
                msg = "pytest run timeout must exceed the suite stop reserve"
                raise ValueError(msg)
            if "--verbose" not in self.progress_args:
                msg = "pytest progress args must expose verbose item progress"
                raise ValueError(msg)

        def _validate_arg_vocabulary(self) -> None:
            """Bind the declared CLI vocabulary to the standard marker table.

            Raises:
                ValueError: If pytest ci-excluded-markers must be declared in
                    standard-markers; or if pytest slow-marker must be declared in
                    standard-markers; or if pytest external-gate-markers must be a
                    non-empty subset of standard-markers; undeclared; or if pytest
                    reporting args must not override runner-owned policy.

            """
            declared_markers = {
                marker.split(":", 1)[0].strip() for marker in self.standard_markers
            }
            if any(
                marker not in declared_markers for marker in self.ci_excluded_markers
            ):
                msg = "pytest ci-excluded-markers must be declared in standard-markers"
                raise ValueError(msg)
            if self.slow_marker not in declared_markers:
                msg = "pytest slow-marker must be declared in standard-markers"
                raise ValueError(msg)
            undeclared = [
                marker
                for marker in self.external_gate_markers
                if marker not in declared_markers
            ]
            if not self.external_gate_markers or undeclared:
                msg = (
                    "pytest external-gate-markers must be a non-empty subset of"
                    f" standard-markers; undeclared: {undeclared}"
                )
                raise ValueError(msg)
            runner_owned_prefixes = (
                "-k",
                "-n",
                "-o",
                "-p",
                "-x",
                "--cov",
                "--dist",
                "--loadscope-reorder",
                "--no-loadscope-reorder",
                "--maxschedchunk",
                "--junitxml",
                "--override-ini",
                "--timeout",
            )
            for argument in (
                *self.progress_args,
                *self.report_args,
                *self.diagnostic_args,
            ):
                if (
                    not argument.startswith("-")
                    or any(character in argument for character in "\0\r\n")
                    or argument.startswith(runner_owned_prefixes)
                ):
                    msg = "pytest reporting args must not override runner-owned policy"
                    raise ValueError(msg)

    class TomlsortConfig(m.ArbitraryTypesModel):
        """Process budget for native TOML formatting."""

        process_timeout_seconds: Annotated[
            int,
            m.Field(
                alias="process-timeout-seconds",
                gt=0,
                le=60,
                description="Maximum runtime for Taplo resolution or formatting.",
            ),
        ]

    class JscpdToolConfig(m.ArbitraryTypesModel):
        """jscpd's own clone-semantics passes the duplication gate selects."""

        similarity: Annotated[
            float,
            m.Field(
                gt=0,
                le=1,
                description="Lowest structural similarity reported (--similarity).",
            ),
        ]
        semantic: Annotated[
            FlextInfraModelsDuplication.JscpdSemantic,
            m.Field(description="Embedding pass host (--semantic)."),
        ]

    class MarkdownConfig(m.ArbitraryTypesModel):
        """Markdown lint rules and excluded non-documentation surfaces."""

        findings_exit_codes: Annotated[
            t.VariadicTuple[int],
            m.Field(
                alias="findings-exit-codes",
                description="Exit statuses with which rumdl reports its findings.",
            ),
        ]
        rules: Annotated[
            t.Infra.SettingsPairs,
            m.Field(description="Ordered native Markdown rule key/value declarations."),
        ]
        exclude: t.StrTuple = m.Field(
            description="Glob patterns excluded from Markdown quality checks.",
        )

    class ToolConfigTools(m.ArbitraryTypesModel):
        """Tool map loaded from YAML."""

        markdown: FlextInfraModelsDepsToolConfig.MarkdownConfig = m.Field(
            description="Markdown lint settings",
        )
        ruff: FlextInfraModelsDepsToolConfig.RuffConfig = m.Field(
            description="Ruff settings",
        )
        mypy: FlextInfraModelsDepsToolConfig.MypyConfig = m.Field(
            description="Mypy settings",
        )
        pyright: FlextInfraModelsDepsToolConfig.PyrightConfig = m.Field(
            description="Pyright settings",
        )
        pyrefly: FlextInfraModelsDepsToolConfig.PyreflyConfig = m.Field(
            description="Pyrefly settings",
        )
        pytest: FlextInfraModelsDepsToolConfig.PytestConfig = m.Field(
            description="Pytest settings",
        )
        tomlsort: FlextInfraModelsDepsToolConfig.TomlsortConfig = m.Field(
            description="Tomlsort settings",
        )
        jscpd: FlextInfraModelsDepsToolConfig.JscpdToolConfig = m.Field(
            description="jscpd clone-semantics passes",
        )

    class LazyInitConfig(m.ArbitraryTypesModel):
        """Declarative policy for ``__init__.py`` lazy export generation."""

        import_layer_order: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                alias="import-layer-order",
                description=(
                    "Canonical dependency layer order for project "
                    "imports. Lower index = lower layer. A module may "
                    "runtime-import modules at equal or lower index "
                    "(relative-dot within the same package); importing "
                    "a module at higher index is a reverse dependency "
                    "and the engine emits it under ``if TYPE_CHECKING:`` "
                    "(see ``reverse_import_mode``). Any value not in "
                    "the fleet SSOT is rejected."
                ),
            ),
        ]
        reverse_import_mode: Annotated[
            Literal["type_checking"],
            m.Field(
                alias="reverse-import-mode",
                description=(
                    "How reverse (upward) runtime dependencies are "
                    "emitted. ``type_checking`` moves the import into "
                    "an ``if TYPE_CHECKING:`` block. The engine rejects "
                    "any other value; reverse runtime imports are a "
                    "module defect fixed at the module root cause."
                ),
            ),
        ]
        forward_import_form: Annotated[
            Literal["absolute"],
            m.Field(
                alias="forward-import-form",
                description=(
                    "How forward (downward) intra-project imports are "
                    "emitted. ``absolute`` names the full module path; "
                    "relative imports are banned."
                ),
            ),
        ]

    class ToolConfigDocument(m.ContractModel, str_strip_whitespace=False):
        """Root schema for canonical ``config/tooling.yaml`` policy data."""

        settings: Annotated[
            t.MappingKV[
                t.NonEmptyStr,
                t.Infra.SettingsPairs,
            ],
            m.Field(
                description=(
                    "Native tool-table paths and ordered option pairs. "
                    "Later pairs replace complete values without reordering arrays."
                )
            ),
        ]

        derived_tool_roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="derived-tool-roots",
                strict=False,
                description=(
                    "Native roots whose owner combines declared options with "
                    "typed topology or execution policy."
                ),
            ),
        ]

        derived_settings: Annotated[
            t.MappingKV[
                t.NonEmptyStr,
                Annotated[tuple[t.NonEmptyStr, ...], m.Field(strict=False)],
            ],
            m.Field(
                alias="derived-settings",
                description="Native keys owned by topology and execution policy.",
            ),
        ]
        raw_check_receipt_suffix: Annotated[
            t.NonEmptyStr,
            m.Field(
                alias="raw-check-receipt-suffix",
                pattern=r"^\.[A-Za-z0-9_.-]+$",
                description="Filename suffix for verbatim native check receipts.",
            ),
        ]
        tools: FlextInfraModelsDepsToolConfig.ToolConfigTools = m.Field(
            description="Tools",
        )
        lazy_init: FlextInfraModelsDepsToolConfig.LazyInitConfig = m.Field(
            alias="lazy-init",
            description="Declarative lazy-init generation policy.",
        )

        mod: FlextInfraModelsDepsToolConfig.ModConfig = m.Field(
            description="Declarative make-mod phase policy.",
        )

        @m.model_validator(mode="after")
        def validate_native_table_names(self) -> Self:
            """Require unambiguous native table paths.

            Returns:
                The unchanged declarations.

            Raises:
                ValueError: If a table path is not a dotted bare TOML key.

            """
            if any(
                not part
                or not part.isascii()
                or not all(
                    character.isalnum() or character in "_-" for character in part
                )
                for path in self.settings
                for part in path.split(".")
            ):
                msg = "Native tool settings require dotted bare table names"
                raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def validate_derived_options(self) -> Self:
            """Reject native pairs that would be overwritten by a semantic owner.

            Returns:
                The declarations with one writable owner per protected key.

            Raises:
                ValueError: If a native option shadows a derived setting.

            """
            for table, protected in self.derived_settings.items():
                declared = dict(self.settings.get(table, ()))
                collision = sorted(declared.keys() & set(protected))
                if collision:
                    msg = (
                        f"Native {table} options cannot shadow policy-owned keys: "
                        f"{', '.join(collision)}"
                    )
                    raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def validate_mypy_overrides(self) -> Self:
            """Keep native override pairs within the diagnostic policy.

            Returns:
                The unchanged declaration.

            Raises:
                ValueError: If an override hides diagnostics or changes owned keys.

            """
            for override in self.tools.mypy.overrides:
                override_options = dict(override.settings)
                ignored = override_options.get("ignore_errors")
                if ignored is not None and ignored is not False:
                    msg = "Mypy overrides cannot ignore diagnostics"
                    raise ValueError(msg)
                if override_options.keys() & set(self.derived_settings.get("mypy", ())):
                    msg = "Mypy override cannot shadow policy-owned options"
                    raise ValueError(msg)
                if any(
                    not key.isascii() or not key.isidentifier()
                    for key in override_options
                ):
                    msg = "Mypy override requires plain option names"
                    raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def validate_mypy_options(self) -> Self:
            """Preserve Mypy ownership and mandatory Pydantic integration.

            Returns:
                Native options without changing their values.

            Raises:
                ValueError: If an option bypasses its policy owner.

            """
            if "mypy" not in self.settings:
                msg = "Native Mypy settings must be declared"
                raise ValueError(msg)
            options = dict(self.settings["mypy"])
            if any(not key.isascii() or not key.isidentifier() for key in options):
                msg = "Mypy policy requires plain option names, not TOML syntax"
                raise ValueError(msg)
            error_codes = options.get("enable_error_code")
            if error_codes is not None and not (
                isinstance(error_codes, str)
                or (
                    isinstance(error_codes, list)
                    and all(isinstance(code, str) for code in error_codes)
                )
            ):
                msg = "Mypy enabled error codes must be a string or string array"
                raise ValueError(msg)
            if (
                options.get("ignore_errors") is not None
                and options["ignore_errors"] is not False
            ):
                msg = "Mypy policy cannot ignore diagnostics"
                raise ValueError(msg)
            plugins = options.get("plugins")
            if (
                not isinstance(plugins, list)
                or any(not isinstance(plugin, str) for plugin in plugins)
                or "pydantic.mypy" not in plugins
                or "pydantic.v1.mypy" in plugins
            ):
                msg = "Mypy requires pydantic.mypy and forbids pydantic.v1.mypy"
                raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def validate_pytest_options(self) -> Self:
            """Keep runtime-derived pytest switches out of native addopts.

            Returns:
                The options with execution policy ownership preserved.

            Raises:
                ValueError: If addopts override the runtime contract.

            """
            options = dict(self.settings["pytest.ini_options"])
            addopts = options.get("addopts")
            if not isinstance(addopts, list) or any(
                not isinstance(option, str) for option in addopts
            ):
                msg = "pytest addopts must be an ordered string array"
                raise ValueError(msg)
            derived = (
                "--timeout",
                "--session-timeout",
                "--dist",
                "--loadscope-reorder",
                "--no-loadscope-reorder",
                "--maxschedchunk",
                "-n",
            )
            if any(
                isinstance(option, str)
                and (
                    option in {"-o", "--override-ini"}
                    or option.startswith(("-o=", "--override-ini=", *derived))
                )
                for option in addopts
            ):
                msg = "pytest runtime policy options are derived from typed fields"
                raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def validate_pyright_options(self) -> Self:
            """Require strict checking in the elected native configuration.

            Returns:
                The configuration with strict diagnostics preserved.

            Raises:
                ValueError: If the elected checking mode weakens diagnostics.

            """
            if dict(self.settings["pyright"]).get("typeCheckingMode") != "strict":
                msg = "Pyright typeCheckingMode must remain strict"
                raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def validate_pyrefly_options(self) -> Self:
            """Preserve strict Pyrefly diagnostics for every selected rule.

            Returns:
                The declarations without enabling diagnostic suppression.

            Raises:
                ValueError: If a selected rule is weakened or generated code hidden.

            """
            if any(
                value != "error"
                for value in dict(self.settings["pyrefly.errors"]).values()
            ):
                msg = "Pyrefly selected diagnostics must remain errors"
                raise ValueError(msg)
            if (
                dict(self.settings["pyrefly"]).get("ignore-errors-in-generated-code")
                is True
            ):
                msg = "Pyrefly cannot hide generated-code diagnostics"
                raise ValueError(msg)
            return self

    class ToolingInputs(m.ContractModel):
        """One elected tooling document and its publication preimages."""

        document: Annotated[
            FlextInfraModelsDepsToolConfig.ToolConfigDocument,
            m.Field(description="Validated project-specific tooling configuration."),
        ]
        sources: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(description="Captured canonical and project configuration layers."),
        ]

    class ToolingRuntimeContext(m.ArbitraryTypesModel):
        """Resolved topology and native tool tables consumed by every template."""

        document: Annotated[
            FlextInfraModelsDepsToolConfig.ToolConfigDocument | None,
            m.Field(
                exclude=True,
                description=(
                    "The elected tooling policy shared by every render context."
                ),
            ),
        ] = None
        project_kind: Annotated[
            t.NonEmptyStr,
            m.Field(description="Resolved project classification"),
        ]
        configuration: Annotated[
            str,
            m.Field(description="Native TOML for every declared managed tool table"),
        ]
        tool_options: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(description="Conformed native tables keyed by declared table path"),
        ]
        sources: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                exclude=True,
                description="Original configuration layers bound to the render",
            ),
        ] = ()


__all__: list[str] = ["FlextInfraModelsDepsToolConfig"]
