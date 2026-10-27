"""Tests run only on a green same-scope check receipt.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.check import FlextInfraWorkspaceChecker
from tests import c, m, tm, u


class TestsFlextInfraCheckReceiptAdmission:
    """The tests verb refuses a candidate no green check has approved."""

    @staticmethod
    @pytest.mark.parametrize("phase", tuple(c.Infra.CheckPhase))
    def test_refuses_without_any_check_receipt(
        infra_git_repo: Path,
        phase: c.Infra.CheckPhase,
    ) -> None:
        """A repository whose check never ran cannot admit tests."""
        make = config.Infra.codegen.make
        with u.Tests.env_vars_context(vars_to_clear=(make.ci.variable,)):
            admitted = u.Infra.git_require_green_check_receipt(
                infra_git_repo,
                make,
                phase=phase,
                plan_global_targets=FlextInfraWorkspaceChecker(
                    repository_root=infra_git_repo,
                ).plan_global_targets,
            )
        tm.fail(admitted)
        tm.that(admitted.error or "", has="tests run only on a green check")
        tm.that(admitted.error or "", has="run make check first")

    @staticmethod
    @pytest.mark.parametrize("phase", tuple(c.Infra.CheckPhase))
    def test_refuses_an_incomplete_check_of_the_same_scope(
        infra_git_repo: Path,
        phase: c.Infra.CheckPhase,
    ) -> None:
        """A started but unfinished check of the context's gates is not green."""
        make = config.Infra.codegen.make
        with u.Tests.env_vars_context(env_vars={make.ci.variable: make.ci.value}):
            gates = u.Infra.selected_check_gates(
                make, c.Infra.CheckGateSet.CHECK, phase=phase
            )
            started = u.Infra.git_begin_gate_capture(
                m.Infra.GateCaptureBeginRequest(
                    repository_root=infra_git_repo,
                    gate=c.Infra.VERB_CHECK,
                    command=(c.Infra.VERB_CHECK,),
                    intent=m.Infra.GateExecutionIntent(
                        phase=phase, requested_gates=gates
                    ),
                    runtime_identity="fixture-runtime",
                ),
                inputs=u.Infra.load_codegen_inputs(infra_git_repo).unwrap(),
            )
            run = infra_git_repo / make.gate_receipts_directory / "20990101T000000Z-1"
            tm.ok(u.Cli.ensure_dir(run))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    run / c.Infra.GATE_CAPTURE_START_FILENAME,
                    started.model_dump_json(round_trip=True) + "\n",
                ),
            )
            for required_phase in c.Infra.CheckPhase:
                admitted = u.Infra.git_require_green_check_receipt(
                    infra_git_repo,
                    make,
                    phase=required_phase,
                    plan_global_targets=FlextInfraWorkspaceChecker(
                        repository_root=infra_git_repo,
                    ).plan_global_targets,
                )
                tm.fail(admitted)
                tm.that(
                    admitted.error or "",
                    has="never completed"
                    if required_phase == phase
                    else "no check receipt",
                )

    @staticmethod
    @pytest.mark.parametrize("phase", tuple(c.Infra.CheckPhase))
    def test_newest_same_phase_wrong_inventory_is_not_skipped(
        infra_git_repo: Path,
        phase: c.Infra.CheckPhase,
    ) -> None:
        """A newer partial intent refuses admission instead of finding older proof."""
        make = config.Infra.codegen.make
        gates = u.Infra.selected_check_gates(
            make, c.Infra.CheckGateSet.CHECK, phase=phase
        )
        for index, inventory in enumerate((gates, (*gates, *gates))):
            started = u.Infra.git_begin_gate_capture(
                m.Infra.GateCaptureBeginRequest(
                    repository_root=infra_git_repo,
                    gate=c.Infra.VERB_CHECK,
                    command=(c.Infra.VERB_CHECK,),
                    intent=m.Infra.GateExecutionIntent(
                        phase=phase, requested_gates=inventory
                    ),
                    runtime_identity="fixture-runtime",
                ),
                inputs=u.Infra.load_codegen_inputs(infra_git_repo).unwrap(),
            )
            run = infra_git_repo / make.gate_receipts_directory / f"fixture-{index}"
            tm.ok(u.Cli.ensure_dir(run))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    run / c.Infra.GATE_CAPTURE_START_FILENAME,
                    started.model_dump_json(round_trip=True) + "\n",
                )
            )
        admitted = u.Infra.git_require_green_check_receipt(
            infra_git_repo,
            make,
            phase=phase,
            plan_global_targets=FlextInfraWorkspaceChecker(
                repository_root=infra_git_repo,
            ).plan_global_targets,
        )
        tm.fail(admitted)
        tm.that(
            admitted.error or "", has="differs from the current phase gate inventory"
        )
