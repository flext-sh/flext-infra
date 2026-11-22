"""Validated environment and filesystem boundary for pytest execution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Self

from flext_infra import c, m, p, s, settings, t, u
from flext_infra._utilities import FlextInfraUtilitiesProjectManagedArtifacts


class FlextInfraPytestRunnerBase(s[int]):
    """Own immutable inputs shared by all pytest runner phases."""

    started_at_monotonic: Annotated[
        float,
        m.Field(
            gt=0,
            description=(
                "Suite clock: captured before FLEXT imports; the suite deadline "
                "is measured from it."
            ),
        ),
    ]
    target: Annotated[Path, m.Field(description="Repository-relative test root.")]
    target_file: Annotated[
        Path | None,
        m.Field(
            description=(
                "Optional repository-relative single test file; it replaces "
                "the test root as the only pytest node target when declared."
            ),
        ),
    ] = None
    reports: Annotated[Path, m.Field(description="Repository-relative report root.")]
    testmon_db: Annotated[
        Path | None,
        m.Field(
            description=(
                "This checkout's native pytest-testmon SQLite database at the "
                "repository root; each checkout owns its own database."
            ),
        ),
    ] = None
    config_receipts: Annotated[
        Path | None,
        m.Field(
            description=(
                "Checkout-root directory of the typed config receipts Testmon "
                "records beside each test's Python dependencies."
            ),
        ),
    ] = None
    run_timeout_seconds: Annotated[
        int | None,
        m.Field(
            gt=0,
            description=(
                "Repository-elected suite wall-clock maximum. The election "
                "always includes the packaged fleet default as its merge base, "
                "so this single source decides the deadline. FULL owns none."
            ),
        ),
    ]
    termination_grace_seconds: Annotated[
        int,
        m.Field(
            gt=0,
            description="Repository-elected graceful stop reserve inside the deadline.",
        ),
    ]
    ci_context: Annotated[
        bool,
        m.Field(description="CI/pre-commit selection captured at the Make boundary."),
    ] = False
    collection_command_prefix: Annotated[
        t.StrTuple,
        m.Field(
            description="Explicit profiling child invocation from the outer boundary.",
        ),
    ] = ()
    profile_enabled: Annotated[
        bool,
        m.Field(
            description="Profile the real suite child and preserve its native exit",
        ),
    ] = False
    slow_phase: Annotated[
        bool,
        m.Field(
            description=(
                "Run only the configured slow marker in its own phase; otherwise "
                "the budgeted phase runs everything else."
            ),
        ),
    ] = False
    tooling: Annotated[
        m.Infra.ToolConfigDocument,
        m.Field(
            description=(
                "The repository's tooling document, elected once at the runner "
                "boundary; the deadline and every pytest policy read come from it."
            ),
        ),
    ]
    harness_marker: Annotated[
        str | None,
        m.Field(
            description=(
                "One declared harness gate marker narrowing the harness scope; "
                "absent selects every harness gate marker."
            ),
        ),
    ] = None

    @staticmethod
    def _environment_value(name: str) -> str:
        """Read one Make-owned runner input.

        Returns:
            The resulting ``str``.

        """
        return u.Cli.env_read(name, dict(os.environ)).unwrap().strip()

    @classmethod
    def _optional_environment_path(cls, name: str) -> Path | None:
        """Read one optional Make-owned runner path input.

        Returns:
            The resulting ``Path | None``.

        """
        value = cls._environment_value(name)
        return Path(value) if value else None

    @classmethod
    def from_project_context(
        cls,
        context: p.Infra.WorkspaceProjectContext,
        *,
        started_at_monotonic: float,
        target_file: Path | None = None,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
        harness_marker: str | None = None,
    ) -> Self:
        """Bind the native runner to one repository's typed policy and identity.

        Returns:
            The runner with independent persistent storage and operation clock.

        """
        # The suite runs on the submitted project, the root `make check` wrote
        # its receipt under; the Git toplevel is an ancestor when the project
        # is a subdirectory of its checkout (CI checks out into <repo>/<repo>).
        root = context.cwd
        # Pytest keeps its own basetemp under the declared temporary root; an
        # undeclared one would fall back to the system /tmp (storage law).
        settings.env_required(c.Infra.TEMPORARY_DIRECTORY_VARIABLE)
        make = u.Infra.load_codegen_inputs(root).unwrap().spec.make
        cache = make.testmon_cache
        tooling = cls._elect_tooling(root)
        run_timeout_seconds, termination_grace_seconds = cls._elected_deadline(
            tooling, execution_mode=execution_mode
        )
        return cls(
            repository_root=root,
            started_at_monotonic=started_at_monotonic,
            tooling=tooling,
            run_timeout_seconds=run_timeout_seconds,
            termination_grace_seconds=termination_grace_seconds,
            target=cache.target_directory,
            target_file=target_file,
            reports=cache.reports_directory,
            testmon_db=(
                root / cache.database_filename
                if execution_mode.records_testmon
                else None
            ),
            config_receipts=(
                root / cache.config_receipts_directory
                if execution_mode.records_testmon
                else None
            ),
            ci_context=u.Infra.env_value(make.ci.variable) == make.ci.value,
            profile_enabled=settings.Infra.profile,
            harness_marker=harness_marker,
        )

    @classmethod
    def _elect_tooling(cls, repository_root: Path) -> m.Infra.ToolConfigDocument:
        """Elect the repository's tooling document from its governed YAML layers.

        The election always merges the packaged fleet defaults as its base. It
        runs once per runner, so the deadline and every pytest policy read share
        one validated document that cannot change mid-run.

        Returns:
            The repository-elected tooling document.

        Raises:
            ValueError: If the repository tooling election fails.

        """
        tooling = FlextInfraUtilitiesProjectManagedArtifacts.load_tooling_inputs(
            repository_root,
        )
        if tooling.failure:
            msg = f"repository pytest tooling election failed: {tooling.error}"
            raise ValueError(msg)
        return m.Infra.ToolConfigDocument.model_validate(tooling.value.document)

    @staticmethod
    def _elected_deadline(
        tooling: m.Infra.ToolConfigDocument,
        *,
        execution_mode: c.Infra.PytestExecutionMode,
    ) -> tuple[int | None, int]:
        """Return the suite deadline; the harness scope owns its own clock.

        FULL is local, load-admitted and unbounded: it elects no run timeout.

        Returns:
            The elected run timeout (absent for FULL) and termination grace.

        """
        pytest_section = tooling.tools.pytest
        return (
            None
            if execution_mode == c.Infra.PytestExecutionMode.FULL
            else pytest_section.harness_run_timeout_seconds
            if execution_mode == c.Infra.PytestExecutionMode.HARNESS
            else pytest_section.run_timeout_seconds,
            pytest_section.termination_grace_seconds,
        )

    def pytest_policy(self) -> p.Infra.PytestConfig:
        """Return the pytest policy of this runner's elected tooling document.

        Returns:
            The policy elected with the suite deadline.

        """
        return self.tooling.tools.pytest

    @classmethod
    def from_environment(
        cls,
        *,
        started_at_monotonic: float,
        collection_command_prefix: t.StrTuple = (),
        profile_enabled: bool = False,
        slow_phase: bool = False,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
    ) -> Self:
        """Create the runner exclusively from generated Make inputs.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If the Make-owned pytest repository root is not absolute.

        """
        repository_root = Path(
            settings.env_required(c.Infra.PYTEST_ENV_REPOSITORY_ROOT)
        )
        if not repository_root.is_absolute():
            msg = "Make-owned pytest repository root must be absolute"
            raise ValueError(msg)
        make = u.Infra.load_codegen_inputs(repository_root).unwrap().spec.make
        ci = make.ci
        tooling = cls._elect_tooling(repository_root)
        run_timeout_seconds, termination_grace_seconds = cls._elected_deadline(
            tooling, execution_mode=execution_mode
        )
        return cls(
            repository_root=repository_root,
            tooling=tooling,
            run_timeout_seconds=run_timeout_seconds,
            termination_grace_seconds=termination_grace_seconds,
            started_at_monotonic=started_at_monotonic,
            collection_command_prefix=collection_command_prefix,
            profile_enabled=profile_enabled,
            slow_phase=slow_phase,
            ci_context=(u.Infra.env_lookup(ci.variable) or "").strip() == ci.value,
            target=Path(cls._environment_value(c.Infra.PYTEST_ENV_TARGET)),
            target_file=cls._optional_environment_path(
                c.Infra.PYTEST_ENV_TARGET_FILE,
            ),
            reports=Path(cls._environment_value(c.Infra.PYTEST_ENV_REPORTS)),
            testmon_db=(
                repository_root / make.testmon_cache.database_filename
                if execution_mode.records_testmon
                else None
            ),
            config_receipts=(
                repository_root / make.testmon_cache.config_receipts_directory
                if execution_mode.records_testmon
                else None
            ),
        )

    @m.model_validator(mode="after")
    def _validate_paths(self) -> Self:
        r"""Require repository-contained target and report paths.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If the test target is not an existing directory or file,
                the testmon database path is not absolute, a target or reports path
                is not a normalized repository-relative path or escapes the
                repository, or the target file is not an existing repository file.

        """
        for name, path in (("target", self.target), ("reports", self.reports)):
            raw = str(path)
            if (
                path.is_absolute()
                or not path.parts
                or any(part in {"", ".", ".."} for part in path.parts)
                or any(character in raw for character in "\0\r\n\\")
            ):
                msg = f"{name} must be a normalized repository-relative path"
                raise ValueError(msg)
            resolved = (self.repository_root / path).resolve()
            if not resolved.is_relative_to(self.repository_root.resolve()):
                msg = f"{name} escapes the repository"
                raise ValueError(msg)
        target_path = self.repository_root / self.target
        if (
            not (target_path.is_dir() or target_path.is_file())
            or target_path.is_symlink()
        ):
            msg = f"test target must be an existing directory or file: {self.target}"
            raise ValueError(msg)
        if self.testmon_db is not None and not self.testmon_db.is_absolute():
            msg = "testmon database path must be absolute"
            raise ValueError(msg)
        return self._validate_target_file()

    def _validate_target_file(self) -> Self:
        """Require the declared single-file target to be repository-contained.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If target file must be a normalized repository-relative
                path; or if target file escapes the repository; or if test
                target file must be an existing repository file.

        """
        if self.target_file is None:
            return self
        raw_file = str(self.target_file)
        if (
            self.target_file.is_absolute()
            or not self.target_file.parts
            or any(part in {"", ".", ".."} for part in self.target_file.parts)
            or any(character in raw_file for character in "\0\r\n\\")
        ):
            msg = "target_file must be a normalized repository-relative path"
            raise ValueError(msg)
        resolved_file = (self.repository_root / self.target_file).resolve()
        if not resolved_file.is_relative_to(self.repository_root.resolve()):
            msg = "target_file escapes the repository"
            raise ValueError(msg)
        file_path = self.repository_root / self.target_file
        if not file_path.is_file() or file_path.is_symlink():
            msg = f"test target file must be an existing file: {self.target_file}"
            raise ValueError(msg)
        return self

    def _declared_project_name(self) -> str | None:
        """Read the declared project identity shared by runtime policies.

        Returns:
            The resulting ``str | None``.

        """
        pyproject_path = self.repository_root / c.PYPROJECT_FILENAME
        payload = u.Infra.pyproject_payload(pyproject_path)
        if "project" not in payload:
            return None
        return u.Infra.project_name_from_payload(pyproject_path, payload)

    def _declared_worker_ceiling(self) -> int | p.Infra.PytestWorkerCeiling:
        """Resolve the declared project's ceiling over the fleet default.

        The ceiling is elected from the same governed YAML layers as the suite
        deadline, so a project declares ``Infra.tooling.tools.pytest.
        parallel-workers`` in its own ``config/tooling.yaml`` overlay and the
        fleet config never has to name it.

        Returns:
            The resulting ``int | m.Infra.PytestWorkerCeiling``.

        """
        elected = self.pytest_policy()
        name = self._declared_project_name()
        if name is None:
            return elected.parallel_workers
        return elected.parallel_worker_overrides.get(name, elected.parallel_workers)

    @staticmethod
    def resolve_worker_ceiling(
        ceiling: int | p.Infra.PytestWorkerCeiling,
        cpu_count: int,
    ) -> int:
        """Resolve a declared ceiling against the process CPU count.

        Absolute ``workers`` ceilings pass through; ``cpu_fraction`` ceilings
        resolve to ``max(1, cpu_count * numerator // denominator)`` so the
        fraction never yields zero workers on small hosts. The fleet-wide
        default arrives as a bare int.

        Returns:
            The resulting ``int``.

        """
        if isinstance(ceiling, int):
            return ceiling
        if ceiling.workers is not None:
            return ceiling.workers
        numerator_text, denominator_text = (ceiling.cpu_fraction or "1/1").split("/")
        return max(1, cpu_count * int(numerator_text) // int(denominator_text))

    def parallel_worker_budget(self, policy: p.Infra.PytestConfig) -> int:
        """Bound xdist by configuration, CPU, and physical memory.

        A project declares its measured ceiling in its own tooling overlay
        (``parallel-workers``); FLEXT members may sit in the fleet override map
        (``[project].name`` → absolute workers or CPU fraction); the fleet-wide
        default stays one worker so ``max-failures: 1`` remains exact
        everywhere else. CPU capacity is the process-scoped count (the cgroup
        affinity the runner actually gets), not the host-wide count.

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If CPU capacity is unavailable; or if physical memory cannot
                support one pytest worker.

        """
        ceiling = self._declared_worker_ceiling()
        cpu_count = os.process_cpu_count()
        if cpu_count <= 0:
            msg = "CPU capacity is unavailable"
            raise ValueError(msg)
        declared_workers = self.resolve_worker_ceiling(ceiling, cpu_count)
        return min(
            declared_workers,
            u.Infra.machine_worker_capacity(policy.parallel_worker_memory_gb),
        )

    def _report_directory(self) -> Path:
        """Create a collision-resistant report directory.

        Returns:
            The resulting ``Path``.

        """
        run_id = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S.%fZ") + f"-{os.getpid()}"
        report_dir: Path = self.repository_root / self.reports / run_id
        u.Cli.ensure_dir(report_dir).unwrap()
        u.Cli.info(f"pytest run receipt: {report_dir}")
        return report_dir


__all__: list[str] = ["FlextInfraPytestRunnerBase"]
