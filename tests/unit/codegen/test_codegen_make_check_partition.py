"""CI follows its declared partition; local checks retain every active gate.

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
    def test_ci_excludes_only_declared_local_only_gates() -> None:
        """Local checks cover every active gate; CI excludes its declared set."""
        make = config.Infra.codegen.make
        local = frozenset(make.ci.local_check_gates)
        tm.that(make.check_gates_default, eq=make.check_gates_allowed)
        tm.that(
            make.check_gates_ci,
            eq=tuple(gate for gate in make.check_gates_default if gate not in local),
        )
        tm.that(make.check_gates_local, eq=make.check_gates_default)
        tm.that(
            set(make.check_gates_ci) <= set(make.check_gates_local),
            eq=True,
        )

    @staticmethod
    def test_ci_partition_runs_the_non_local_type_checkers() -> None:
        """Active type checkers follow the declared partition for any value.

        The local-only set is config-owned: a checker declared in
        ``ci.local_check_gates`` stays out of CI, and every checker outside the
        declared local set surfaces in the CI partition.
        """
        make = config.Infra.codegen.make
        active_type_checkers = c.Infra.TYPE_CHECKER_GATES & set(
            make.check_gates_default,
        )
        tm.ok(bool(active_type_checkers))
        local = frozenset(make.ci.local_check_gates)
        tm.that(
            active_type_checkers & local <= set(make.check_gates_local),
            eq=True,
        )
        tm.that(
            active_type_checkers - local <= set(make.check_gates_ci),
            eq=True,
        )

    @staticmethod
    def test_project_declared_gates_follow_the_declared_partition() -> None:
        """A project gate absent from the local set runs in the CI partition."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["project_check_gates"] = ("fixture-project-gate",)

        active = m.Infra.MakeSpec.model_validate(payload)

        tm.that(active.check_gates_default, eq=active.check_gates_allowed)
        tm.that(active.check_gates_default, has="fixture-project-gate")
        tm.that(active.check_gates_ci, has="fixture-project-gate")
        tm.that(active.check_gates_local, has="fixture-project-gate")

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
    def test_pre_commit_uses_the_ci_validation_workflow() -> None:
        """Commit checks and tests derive from the same CI workflow rows."""
        make = config.Infra.codegen.make
        ci_validation = tuple(
            step.verb
            for step in make.workflow
            if "ci" in step.contexts
            and step.verb in {c.Infra.VERB_CHECK, c.Infra.VERB_TEST}
        )
        commit_validation = tuple(
            step.verb for step in make.workflow if "pre_commit" in step.contexts
        )
        tm.that(commit_validation, eq=ci_validation)

    @staticmethod
    @pytest.mark.parametrize("verb", ["setup", "audit", "verify-clean"])
    def test_pre_commit_workflow_refuses_other_lifecycle_steps(verb: str) -> None:
        """Provisioning and clean-tree approval remain separate lifecycle operations."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["workflow"] = [
            {
                **row,
                "contexts": (
                    (*row["contexts"], "pre_commit")
                    if row["verb"] == verb
                    else row["contexts"]
                ),
            }
            for row in payload["workflow"]
        ]
        with pytest.raises(e.PydanticValidationError, match="pre-commit hook requires"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        "verb", ["setup", "audit", "check", "test", "verify-clean"]
    )
    def test_ci_workflow_requires_the_closing_clean_tree(verb: str) -> None:
        """Removing any mandatory CI milestone is refused."""
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
        with pytest.raises(e.PydanticValidationError, match="verify-clean workflow"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        ("first", "second"),
        [
            ("setup", "audit"),
            ("audit", "check"),
            ("check", "test"),
            ("test", "verify-clean"),
        ],
    )
    def test_ci_workflow_rejects_reordered_milestones(first: str, second: str) -> None:
        """Provisioning, approval order, and closing clean boundary are mandatory."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        rows = list(payload["workflow"])
        positions = [
            next(i for i, row in enumerate(rows) if row["verb"] == verb)
            for verb in (first, second)
        ]
        rows[positions[0]], rows[positions[1]] = rows[positions[1]], rows[positions[0]]
        payload["workflow"] = rows
        with pytest.raises(e.PydanticValidationError, match="verify-clean workflow"):
            m.Infra.MakeSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    @pytest.mark.parametrize("before", ["audit", "check", "test", "verify-clean"])
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
    @pytest.mark.parametrize("restriction", ["arguments", "profiles"])
    def test_ci_workflow_requires_selector_free_all_profile_verbs(
        restriction: str,
    ) -> None:
        """A declared workflow operation must be callable by every consumer."""
        payload = config.Infra.codegen.make.model_dump(exclude_computed_fields=True)
        payload["verbs"] = [
            {
                **row,
                restriction: ("fixture-selector",)
                if restriction == "arguments"
                else tuple(c.Infra.MakeProfile)[:-1],
            }
            if row["name"] == c.Infra.VERB_CHECK
            else row
            for row in payload["verbs"]
        ]
        with pytest.raises(
            e.PydanticValidationError, match="selector-free in every profile"
        ):
            m.Infra.MakeSpec.model_validate(payload)

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
