"""Authorized gate suspensions preserve the active Make check contract."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from pydantic import ValidationError

from flext_infra import config
from tests import c, m, u


class TestsFlextInfraCodegenMakeGateSuspensions:
    """One typed gate universe drives local, CI, and hook execution."""

    def test_project_gates_and_suspensions_share_the_ci_partition(self) -> None:
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["project_check_gates"] = ("fixture-active", "fixture-suspended")
        payload["check_gate_suspensions"] = ()
        declared = m.Infra.MakeSpec.model_validate(payload)
        suspended_gate = declared.check_gates_default[0]
        payload["check_gate_suspensions"] = tuple(
            {
                "gate": gate,
                "authority": "fixture recovery decision",
                "reason": "fixture policy suspension",
            }
            for gate in (suspended_gate, "fixture-suspended")
        )

        active = m.Infra.MakeSpec.model_validate(payload)

        tm.that(active.check_gates_allowed, eq=declared.check_gates_allowed)
        tm.that(
            active.check_gates_default,
            eq=tuple(
                gate
                for gate in declared.check_gates_default
                if gate not in {suspended_gate, "fixture-suspended"}
            ),
        )
        tm.that(active.check_gates_ci, has="fixture-active")
        tm.that(
            active.check_gates_ci,
            eq=tuple(
                gate
                for gate in active.check_gates_default
                if gate not in active.ci.local_check_gates
            ),
        )

    @pytest.mark.parametrize("invalid", ["unknown", "duplicate", "missing", "blank"])
    def test_suspensions_require_a_known_unique_gate_and_authority(
        self, invalid: str
    ) -> None:
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        row = {
            "gate": config.Infra.codegen.make.check_gates_allowed[0],
            "authority": "fixture authorization",
            "reason": "fixture decision",
        }
        if invalid == "unknown":
            row["gate"] = "undeclared-fixture-gate"
        elif invalid == "missing":
            del row["authority"]
        elif invalid == "blank":
            row["reason"] = " \n"
        payload["check_gate_suspensions"] = (
            [row, row] if invalid == "duplicate" else [row]
        )

        with pytest.raises(ValidationError):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.slow
    @pytest.mark.parametrize("ci", [False, True])
    def test_make_reports_suspensions_without_hiding_a_runtime_failure(
        self, tmp_path: Path, *, ci: bool
    ) -> None:
        """A real missing runtime remains fatal after the authorized receipts."""
        root, _ = u.Tests.render_make_environment(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        tm.ok(u.Tests.create_python_environment(root))
        policy = config.Infra.codegen.make
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "check"],
                cwd=root,
                env={
                    policy.ci.variable: policy.ci.value if ci else policy.ci.local_value
                },
            )
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        tm.that(process.stderr, has="No module named flext_infra")
        for suspension in policy.check_gate_suspensions:
            tm.that(
                process.stdout,
                has=(
                    f"INFO: SUSPENDED check gate {suspension.gate}; "
                    f"authority={suspension.authority}; reason={suspension.reason}"
                ),
            )


__all__: list[str] = ["TestsFlextInfraCodegenMakeGateSuspensions"]
