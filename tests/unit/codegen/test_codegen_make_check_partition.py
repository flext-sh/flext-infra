"""Every check partition derives from each gate's declared stage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from tests import c, e, m, t, tm, u
from tests.unit.codegen.test_ci_integration_branch_triggers import (
    TestsFlextInfraCiIntegrationBranchTriggers,
)


class TestsFlextInfraCodegenMakeCheckPartition:
    """Keep CI, local checks and the fast hook on their declared boundaries."""

    @staticmethod
    def test_sonarcloud_render_contract_round_trips_typed_configuration() -> None:
        """Resolve the full public render schema before filesystem scaffolding."""
        codegen = config.Infra.codegen
        policy = m.Infra.SonarcloudSpec.model_validate(
            codegen.sonarcloud.model_dump(),
        )
        tm.that(policy, eq=codegen.sonarcloud)
        for exclusion in policy.issue_exclusions:
            restored_exclusion = (
                m.Infra.SonarcloudIssueExclusionSpec.model_validate_json(
                    exclusion.model_dump_json(),
                )
            )
            tm.that(restored_exclusion, eq=exclusion)
        rendered = m.Infra.SonarcloudRenderSpec(
            sonarcloud=policy,
            tests_dir=c.Infra.DIR_TESTS,
            generated_source_globs=codegen.generated_source_globs,
        )
        restored = m.Infra.SonarcloudRenderSpec.model_validate_json(
            rendered.model_dump_json(),
        )
        tm.that(restored, eq=rendered)
        tm.that(restored.sonarcloud, eq=codegen.sonarcloud)

    @staticmethod
    def test_registry_declares_one_kind_per_gate() -> None:
        """Every gate vocabulary is derived from the single kind declaration."""
        declared = [
            gate for tools in c.Infra.GATE_TOOLS_BY_KIND.values() for gate in tools
        ]
        tm.that(len(declared), eq=len(set(declared)))
        tm.that(set(c.Infra.GATE_KINDS), eq=set(c.Infra.SARIF_TOOL_INFO))
        tm.that(set(c.Infra.GATE_KINDS), eq=set(c.Infra.ALLOWED_GATES))
        tm.that(
            c.Infra.TYPE_CHECKER_GATES,
            eq=frozenset(
                gate
                for gate, kind in c.Infra.GATE_KINDS.items()
                if kind is c.Infra.GateKind.TYPE_CHECKER
            ),
        )

    @staticmethod
    def test_runtime_gate_selection_follows_the_ci_token() -> None:
        """The checker resolves each requested gate set from the typed Make spec."""
        make = config.Infra.codegen.make
        ci = make.ci
        expected = {
            ci.value: make.check_gates_ci,
            ci.pre_commit_value: make.pre_commit_check_gates,
            ci.local_value: make.check_gates_local,
        }
        for token, gates in expected.items():
            with u.Tests.env_vars_context(env_vars={ci.variable: token}):
                tm.that(
                    u.Infra.selected_check_gates(make, c.Infra.CheckGateSet.CHECK),
                    eq=gates,
                )
        with u.Tests.env_vars_context(vars_to_clear=(ci.variable,)):
            tm.that(
                u.Infra.selected_check_gates(make, c.Infra.CheckGateSet.CHECK),
                eq=make.check_gates_default,
            )
        tm.that(
            u.Infra.selected_check_gates(make, c.Infra.CheckGateSet.FIX),
            eq=make.check_gates_fixable,
        )
        tm.that(
            u.Infra.selected_check_gates(make, c.Infra.CheckGateSet.FMT),
            eq=make.fmt_gates,
        )

    @staticmethod
    def test_partitions_derive_from_each_gate_declared_stage() -> None:
        """Every context partition is the stage-admitted slice of the default set.

        The commit hook admits only commit-stage gates, CI admits the commit
        and CI stages, and local/pre-push runs keep every active gate.
        """
        make = config.Infra.codegen.make
        stages = make.check_gate_stages
        tm.that(set(stages), eq=set(make.check_gates_default))
        tm.that(make.check_gates_default, eq=make.check_gates_allowed)
        tm.that(make.check_gates_local, eq=make.check_gates_default)
        tm.that(
            make.check_gates_ci,
            eq=tuple(
                gate
                for gate in make.check_gates_default
                if stages[gate] is not c.Infra.GateStage.PUSH
            ),
        )
        tm.that(
            make.pre_commit_check_gates,
            eq=tuple(
                gate
                for gate in make.check_gates_default
                if stages[gate] is c.Infra.GateStage.COMMIT
            ),
        )
        tm.ok(set(make.pre_commit_check_gates) <= set(make.check_gates_ci))
        tm.ok(set(make.check_gates_ci) <= set(make.check_gates_local))

    @staticmethod
    def test_type_checkers_follow_their_declared_stage() -> None:
        """A type checker reaches CI exactly when its stage admits CI."""
        make = config.Infra.codegen.make
        active_type_checkers = c.Infra.TYPE_CHECKER_GATES & set(
            make.check_gates_default,
        )
        tm.ok(bool(active_type_checkers))
        for gate in active_type_checkers:
            stage = c.Infra.GATE_STAGES[gate]
            tm.that(
                gate in make.check_gates_ci,
                eq=stage is not c.Infra.GateStage.PUSH,
            )
            tm.fail(gate in make.pre_commit_check_gates)

    @staticmethod
    @pytest.mark.parametrize("stage", tuple(c.Infra.GateStage))
    def test_project_declared_gates_follow_their_declared_stage(
        stage: c.Infra.GateStage,
    ) -> None:
        """A repository-owned gate lands in every partition its stage admits."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["project_check_gates"] = (
            {
                "name": "fixture-project-gate",
                "module": "fixture_project.gate",
                "stage": stage,
            },
        )

        active = m.Infra.MakeSpec.model_validate(payload)

        tm.that(active.check_gates_default, has="fixture-project-gate")
        tm.that(active.check_gates_local, has="fixture-project-gate")
        tm.that(
            "fixture-project-gate" in active.check_gates_ci,
            eq=stage is not c.Infra.GateStage.PUSH,
        )
        tm.that(
            "fixture-project-gate" in active.pre_commit_check_gates,
            eq=stage is c.Infra.GateStage.COMMIT,
        )

    @staticmethod
    def test_project_declared_gate_defaults_to_the_push_stage() -> None:
        """An undeclared stage keeps a repository validator out of CI and commits."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["project_check_gates"] = (
            {"name": "fixture-project-gate", "module": "fixture_project.gate"},
        )

        active = m.Infra.MakeSpec.model_validate(payload)

        tm.that(
            active.check_gate_stages["fixture-project-gate"],
            eq=c.Infra.GateStage.PUSH,
        )
        tm.that(active.check_gates_ci, lacks="fixture-project-gate")

    @staticmethod
    def test_context_tokens_must_be_distinct() -> None:
        """Two contexts sharing one token would silently merge their partitions."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["ci"] = {**payload["ci"], "pre_commit_value": payload["ci"]["value"]}
        with pytest.raises(e.PydanticValidationError, match="tokens must be distinct"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    def test_ci_workflow_runs_only_the_ci_partition() -> None:
        """The CI job runs each approval verb once, in order, under the CI token.

        CI never runs the pre-commit hook verb and never the local partition.
        """
        make = config.Infra.codegen.make
        steps = u.CodegenTestSupport.Ci.ci_job_steps(
            TestsFlextInfraCiIntegrationBranchTriggers.render_ci(
                repository_branch="0.12.0-dev",
            ),
        )
        commands = [str(step.get("run", "")) for step in steps]
        approvals = [
            f"{make.ci.variable}={make.ci.value} make {verb}"
            for verb in make.approval_verbs
        ]
        positions = [commands.index(approval) for approval in approvals]
        tm.that(positions, eq=sorted(positions))
        local = f"{make.ci.variable}={make.ci.local_value} make"
        tm.fail(any(local in command for command in commands))
        tm.fail(any("make pre-commit" in command for command in commands))

    @staticmethod
    def test_pre_commit_runs_only_the_check_operation() -> None:
        """The commit hook declares exactly the read-only check row."""
        make = config.Infra.codegen.make
        tm.that(
            tuple(step.verb for step in make.workflow if "pre_commit" in step.contexts),
            eq=(c.Infra.VERB_CHECK,),
        )

    @staticmethod
    def test_pre_commit_workflow_refuses_every_other_operation() -> None:
        """Any other declared workflow verb in the commit hook is refused."""
        base = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        others = [
            row["verb"] for row in base["workflow"] if row["verb"] != c.Infra.VERB_CHECK
        ]
        tm.that(others, empty=False)
        for verb in others:
            payload = {
                **base,
                "workflow": [
                    {
                        **row,
                        "contexts": (
                            (*row["contexts"], "pre_commit")
                            if row["verb"] == verb
                            else row["contexts"]
                        ),
                    }
                    for row in base["workflow"]
                ],
            }
            with pytest.raises(
                e.PydanticValidationError, match="pre-commit hook requires"
            ):
                m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize("verb", ["setup", "tests"])
    def test_ci_workflow_requires_its_provisioning_and_test_boundaries(
        verb: str,
    ) -> None:
        """Removing CI provisioning or the closing tests owner is refused."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["workflow"] = [
            {
                **row,
                "contexts": tuple(
                    context for context in row["contexts"] if context != "ci"
                )
                if row["verb"] == verb
                else row["contexts"],
            }
            for row in payload["workflow"]
        ]
        with pytest.raises(e.PydanticValidationError, match="CI requires setup"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(("first", "second"), [("setup", "check")])
    def test_ci_workflow_rejects_reordered_milestones(first: str, second: str) -> None:
        """Provisioning precedes the approval milestones."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        rows = list(payload["workflow"])
        positions = [
            next(i for i, row in enumerate(rows) if row["verb"] == verb)
            for verb in (first, second)
        ]
        rows[positions[0]], rows[positions[1]] = rows[positions[1]], rows[positions[0]]
        payload["workflow"] = rows
        with pytest.raises(e.PydanticValidationError, match="CI requires setup"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    @pytest.mark.parametrize("before", ["check", "tests"])
    def test_ci_workflow_renders_additional_admissible_phases(
        profile: c.Infra.MakeProfile,
        before: str,
    ) -> None:
        """The public renderer consumes arbitrary valid phases from the typed owner."""
        make = config.Infra.codegen.make
        payload = make.model_dump(exclude_computed_fields=True)
        phase = m.Infra.MakeVerbSpec(
            name="fixture-ci-phase",
            description="Additional configured CI phase",
        )
        payload["verbs"] = (*payload["verbs"], phase.model_dump())
        rows = list(payload["workflow"])
        rows.insert(
            next(i for i, row in enumerate(rows) if row["verb"] == before),
            m.Infra.MakeWorkflowStepSpec(
                verb=phase.name,
                contexts=("local", "ci"),
            ).model_dump(),
        )
        payload["workflow"] = rows
        active = m.Infra.MakeSpec.model_validate(payload)
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="workflow-consumer",
            make_profile=profile,
            repository_branch="integration/workflow-consumer",
            ci_trigger_branches=(),
        ).model_copy(update={"make": active})
        steps = u.CodegenTestSupport.Ci.ci_job_steps(
            tm.ok(
                u.Cli.template_render(
                    TestsFlextInfraCiIntegrationBranchTriggers.ci_template,
                    spec,
                )
            )
        )
        tm.that(
            tuple(
                step["run"]
                for step in steps
                if str(step.get("id", "")).startswith("approval-")
            ),
            eq=tuple(
                f"{active.ci.variable}={active.ci.value} make {verb}"
                for verb in active.approval_verbs
            ),
        )

    @staticmethod
    def test_ci_workflow_requires_all_profile_verbs() -> None:
        """A declared workflow operation must be callable by every consumer."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["verbs"] = [
            {**row, "profiles": tuple(c.Infra.MakeProfile)[:-1]}
            if row["name"] == c.Infra.VERB_CHECK
            else row
            for row in payload["verbs"]
        ]
        with pytest.raises(
            e.PydanticValidationError, match="available in every profile"
        ):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    def test_tests_workflow_step_must_require_check() -> None:
        """Tests run only on a green check: the requirement cannot be dropped."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["workflow"] = [
            {**row, "requires": ()} if row["verb"] == c.Infra.VERB_TEST else row
            for row in payload["workflow"]
        ]
        with pytest.raises(
            e.PydanticValidationError, match="tests run only on a green check"
        ):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_ci_step_runs_only_after_its_required_steps(
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Each CI approval step is admitted only by its required steps' success."""
        make = config.Infra.codegen.make
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="workflow-consumer",
            make_profile=profile,
            repository_branch="integration/workflow-consumer",
            ci_trigger_branches=(),
        ).model_copy(update={"make": make})
        steps = {
            str(step.get("id", "")): str(step.get("if", ""))
            for step in u.CodegenTestSupport.Ci.ci_job_steps(
                tm.ok(
                    u.Cli.template_render(
                        TestsFlextInfraCiIntegrationBranchTriggers.ci_template,
                        spec,
                    )
                )
            )
        }
        required = [row for row in make.workflow if "ci" in row.contexts]
        tm.that([row for row in required if row.requires], empty=False)
        for row in required:
            for prerequisite in row.requires:
                tm.that(
                    steps[f"approval-{row.verb}"],
                    has=f"steps.approval-{prerequisite}.outcome == 'success'",
                )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("context", ["ci", "local", "all"])
    def test_make_check_keeps_a_missing_runtime_fatal(
        tmp_path: Path,
        context: str,
    ) -> None:
        """A missing runtime fails at activation before any check gate executes."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.create_python_environment(root))
        policy = config.Infra.codegen.make
        environment: t.StrMapping
        if context == "ci":
            environment = {policy.ci.variable: policy.ci.value}
        elif context == "local":
            environment = {policy.ci.variable: policy.ci.local_value}
        else:
            environment = {}
        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "check"],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env=environment,
                    remove_env_keys=(
                        *c.Tests.MAKE_ISOLATION_ENV_KEYS,
                        *((policy.ci.variable,) if context == "all" else ()),
                    ),
                ),
            ),
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        tm.that(process.stdout, eq="")
        tm.that(
            process.stderr,
            has="No module named flext_infra",
        )
        tm.that(
            process.stderr,
            has="_builtin_require_environment",
        )
        tm.that(
            process.stderr,
            lacks="no active check gates remain in the selected context",
        )
