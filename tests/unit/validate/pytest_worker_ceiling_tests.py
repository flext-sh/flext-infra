"""Behavioral tests for the tagged per-project pytest worker ceiling.

Every expected value is derived from the typed SSOT (the PytestWorkerCeiling
model and the live process CPU count) — no hardcoded worker counts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import config
from flext_infra.validate import FlextInfraPytestRunner
from tests import c, m, tm, u


@c.Tests.MARK.unit
class TestsFlextInfraPytestWorkerCeiling:
    """Public contract of the tagged worker ceiling and its resolution."""

    @staticmethod
    def test_legacy_integer_coerces_to_absolute_workers() -> None:
        """The legacy bare-integer YAML form still reads as workers."""
        ceiling = m.Infra.PytestWorkerCeiling.model_validate(4)
        tm.that(ceiling.workers, eq=4)
        tm.that(ceiling.cpu_fraction, eq=None)

    @staticmethod
    def test_exactly_one_form_is_required() -> None:
        """Both or neither form set is rejected."""
        with u.Tests.raises(ValueError, match="exactly one"):
            m.Infra.PytestWorkerCeiling.model_validate({})
        with u.Tests.raises(ValueError, match="exactly one"):
            m.Infra.PytestWorkerCeiling.model_validate({
                "workers": 4,
                "cpu_fraction": "1/4",
            })

    @staticmethod
    def test_cpu_fraction_shape_is_validated() -> None:
        """Non-fraction strings are rejected at validation."""
        with u.Tests.raises(ValueError, match="cpu_fraction"):
            m.Infra.PytestWorkerCeiling.model_validate({"cpu_fraction": "quarter"})

    @staticmethod
    def test_fraction_resolves_from_the_process_cpu_count() -> None:
        """A 1/4 ceiling resolves to max(1, cpus//4) of the process count."""
        ceiling = m.Infra.PytestWorkerCeiling.model_validate({"cpu_fraction": "1/4"})
        cpus = os.process_cpu_count()
        expected = max(1, cpus // 4)
        resolved = FlextInfraPytestRunner.resolve_worker_ceiling(ceiling, cpus)
        tm.that(resolved, eq=expected)
        tm.that(resolved, eq=max(1, resolved))

    @staticmethod
    def test_fraction_never_yields_zero_on_a_single_cpu_host() -> None:
        """A fraction of one CPU still resolves to one worker."""
        ceiling = m.Infra.PytestWorkerCeiling.model_validate({"cpu_fraction": "1/4"})
        resolved = FlextInfraPytestRunner.resolve_worker_ceiling(ceiling, 1)
        tm.that(resolved, eq=1)

    @staticmethod
    def test_absolute_workers_pass_through() -> None:
        """An absolute ceiling resolves to itself regardless of CPU count."""
        ceiling = m.Infra.PytestWorkerCeiling.model_validate({"workers": 3})
        resolved = FlextInfraPytestRunner.resolve_worker_ceiling(
            ceiling,
            os.process_cpu_count(),
        )
        tm.that(resolved, eq=3)

    @staticmethod
    def test_default_arrives_as_a_bare_int_and_passes_through() -> None:
        """The fleet-wide default (int) resolves unchanged."""
        resolved = FlextInfraPytestRunner.resolve_worker_ceiling(
            2,
            os.process_cpu_count(),
        )
        tm.that(resolved, eq=2)

    @staticmethod
    def test_declared_overrides_come_from_the_typed_ssot() -> None:
        """The tooling SSOT carries validated ceilings of either form."""
        overrides = config.Infra.tooling.tools.pytest.parallel_worker_overrides
        for declared in overrides.values():
            tm.that(
                (declared.workers is None) != (declared.cpu_fraction is None),
                eq=True,
            )

    @staticmethod
    @c.Tests.MARK.parametrize(
        "declared_name",
        (None, *config.Infra.tooling.tools.pytest.parallel_worker_overrides),
    )
    def test_project_budget_respects_declared_and_machine_capacity(
        cached_runner_project: Path,
        declared_name: str | None,
    ) -> None:
        """Exercise the default and every current override through native xdist."""
        policy = config.Infra.tooling.tools.pytest
        runner = (
            u.Tests.PytestRunner.runner_for(cached_runner_project)
            if declared_name is None
            else u.Tests.PytestRunner.declared_project_runner(
                cached_runner_project, declared_name
            )
        )
        declared = runner.resolve_worker_ceiling(
            policy.parallel_workers
            if declared_name is None
            else policy.parallel_worker_overrides[declared_name],
            os.process_cpu_count(),
        )
        capacity = u.Infra.machine_worker_capacity(policy.parallel_worker_memory_gb)
        budget = runner.parallel_worker_budget(policy)
        tm.that(budget, eq=min(declared, capacity))
        report = (
            cached_runner_project
            / config.Infra.codegen.make.testmon_cache.reports_directory
        )
        command = runner.build_command(report)
        workers = command[command.index("-n") + 1]
        tm.that(workers, eq=str(budget) if budget > 1 else "0")

    @staticmethod
    @c.Tests.MARK.parametrize("workers", (1, 3))
    def test_project_overlay_declares_its_own_ceiling(
        cached_runner_project: Path,
        workers: int,
    ) -> None:
        """A project's tooling overlay sets its ceiling without flext naming it."""
        overlay = cached_runner_project / "config" / "tooling.yaml"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text(
            "Infra:\n  tooling:\n    tools:\n      pytest:\n"
            f"        parallel-workers: {workers}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        policy = config.Infra.tooling.tools.pytest
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        capacity = u.Infra.machine_worker_capacity(policy.parallel_worker_memory_gb)
        tm.that(runner.parallel_worker_budget(policy), eq=min(workers, capacity))
