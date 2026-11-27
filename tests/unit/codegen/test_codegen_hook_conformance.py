"""Behavioral contracts for generated Git-hook conformance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shlex
from pathlib import Path

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, tm, u

pytestmark = c.Tests.MARK.slow


_HOOK_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
    / ".pre-commit-config.yaml.j2"
)


def _conform(
    root: Path,
    mode: c.Infra.CodegenConformMode,
) -> p.Result[p.Infra.CodegenResult]:
    """Run one conform operation through its public owner.

    Returns:
        The resulting ``p.Result[p.Infra.CodegenResult]``.

    """
    return infra.codegen_conform(
        u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
        ),
    )


class TestsFlextInfraCodegenHookConformance:
    """Prove generation owns hook artifacts and preserves runtime installation."""

    @staticmethod
    def _render_hooks(root: Path) -> str:
        """Render the manifest-owned hook artifact through the public owner.

        Returns:
            The resulting ``str``.

        """
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=config.Infra.codegen.make,
                ),
            ),
        )
        tm.ok(u.Cli.atomic_write_text_file(root / ".pre-commit-config.yaml", rendered))
        return rendered

    @staticmethod
    def _check(root: Path) -> p.Result[p.Infra.CodegenResult]:
        return _conform(root, c.Infra.CodegenConformMode.CHECK)

    def test_check_never_requires_runtime_hook_installation(
        self,
        infra_git_repo: Path,
    ) -> None:
        """Conform owns generated files; AI Hub owns hook installation."""
        root = infra_git_repo
        self._render_hooks(root)

        result = self._check(root)

        if result.failure:
            tm.that(result.error or "", lacks="git hook is not installed")

    @staticmethod
    def test_apply_does_not_install_hook_shims(infra_git_repo: Path) -> None:
        """Apply materializes files only and never provisions hook shims."""
        root = infra_git_repo
        hooks_dir = root / c.GIT_DIR_NAME / "hooks"

        _conform(root, c.Infra.CodegenConformMode.APPLY)

        for stage in ("pre-commit", "pre-push"):
            hook = hooks_dir / stage
            if hook.is_file():
                tm.that(hook.read_text(encoding="utf-8"), lacks=f"--hook-type={stage}")

    @staticmethod
    def test_generated_hooks_use_one_strict_shell_per_workflow_step(
        infra_git_repo: Path,
    ) -> None:
        """Each enabled stage runs every declared verb in its own strict shell.

        The template gives each Make verb its own hook so the pre-commit runner
        reports per-step status natively.
        """
        root = infra_git_repo
        make = config.Infra.codegen.make.model_copy(
            update={"pre_commit": True, "pre_push": True},
        )
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=make,
                ),
            ),
        )
        tm.ok(u.Cli.atomic_write_text_file(root / ".pre-commit-config.yaml", rendered))
        expected = sum(
            1
            for step in make.workflow
            for context in ("pre_commit", "pre_push")
            if context in step.contexts
        )
        tm.that(rendered.count("bash -eu -o pipefail -c"), eq=expected)
        tm.that(rendered, lacks=".local")

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize("inherited", ["ci", "local"])
    def test_pre_push_refuses_when_the_make_runtime_is_unprovisioned(
        tmp_path: Path,
        inherited: str,
    ) -> None:
        """Inherited CI cannot turn the native check's failure into a pass."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.create_python_environment(root))
        policy = config.Infra.codegen.make
        make = m.Infra.MakeSpec.model_validate({
            **policy.model_dump(exclude_computed_fields=True),
            "pre_push": True,
        })
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="fixture-project",
                    make=make,
                ),
            ),
        )
        hook_config = root / c.Infra.PRE_COMMIT_CONFIG_FILENAME
        tm.ok(u.Cli.atomic_write_text_file(hook_config, rendered))
        document = u.Cli.yaml_load_mapping(hook_config)
        repositories = u.Cli.json_as_sequence(document["repos"])
        repository = u.Cli.json_as_mapping(repositories[0])
        hooks = u.Cli.json_as_sequence(repository["hooks"])
        check = next(step for step in make.workflow if "pre_push" in step.contexts)
        hook = next(
            mapping
            for row in hooks
            if (mapping := u.Cli.json_as_mapping(row))["id"]
            == f"flext-pre-push-{check.identity}"
        )
        entry = u.Cli.json_pick_str(hook, "entry")
        tm.that(entry, empty=False)
        process = tm.ok(
            u.Cli.run_raw(
                shlex.split(entry),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        policy.ci.variable: (
                            policy.ci.value
                            if inherited == "ci"
                            else policy.ci.local_value
                        ),
                    },
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        tm.that(process.stderr, has="No module named flext_infra")

    def test_check_and_apply_never_overwrite_foreign_hook_shims(
        self,
        infra_git_repo: Path,
    ) -> None:
        """Conform never overwrites a foreign executable hook."""
        root = infra_git_repo
        self._render_hooks(root)
        hooks_dir = root / c.GIT_DIR_NAME / "hooks"
        foreign = "#!/bin/sh\nexit 0\n"
        for stage in ("pre-commit", "pre-push"):
            (hooks_dir / stage).write_text(foreign, encoding="utf-8")

        self._check(root)
        _conform(root, c.Infra.CodegenConformMode.APPLY)

        for stage in ("pre-commit", "pre-push"):
            tm.that((hooks_dir / stage).read_text(encoding="utf-8"), eq=foreign)

    @staticmethod
    def test_commit_context_selects_only_the_commit_stage_gates() -> None:
        """The declared commit token selects only commit-stage validators."""
        make = config.Infra.codegen.make
        with u.Tests.env_vars_context(
            env_vars={make.ci.variable: make.ci.pre_commit_value},
        ):
            selected = u.Infra.selected_check_gates(
                make,
                c.Infra.CheckGateSet.CHECK,
            )
        tm.that(selected, eq=make.pre_commit_check_gates)
        tm.ok(
            all(
                make.check_gate_stages[gate] is c.Infra.GateStage.COMMIT
                for gate in selected
            ),
        )

    @staticmethod
    def test_commit_hook_checks_through_the_make_runtime_route(
        tmp_path: Path,
    ) -> None:
        """The commit check runs its Make verb with the commit-stage CI value.

        Make forces the runtime environment and selects the commit-stage gates,
        so the hook never picks an interpreter or engine path by itself.
        """
        make = config.Infra.codegen.make.model_copy(update={"pre_commit": True})
        hook_config = tmp_path / c.Infra.PRE_COMMIT_CONFIG_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                hook_config,
                tm.ok(
                    u.Cli.template_render(
                        _HOOK_TEMPLATE,
                        m.Infra.MakeWorkflowRenderSpec(
                            dist="flext-demo",
                            make=make,
                        ),
                    ),
                ),
            ),
        )
        repositories = u.Cli.json_as_sequence(
            u.Cli.yaml_load_mapping(hook_config)["repos"],
        )
        hooks = u.Cli.json_as_sequence(
            u.Cli.json_as_mapping(repositories[0])["hooks"],
        )
        check = next(
            step
            for step in make.workflow
            if step.verb == c.Infra.VERB_CHECK and "pre_commit" in step.contexts
        )
        entry = u.Cli.json_pick_str(
            next(
                mapping
                for row in hooks
                if (mapping := u.Cli.json_as_mapping(row))["id"]
                == f"flext-pre-commit-{check.identity}"
            ),
            "entry",
        )
        tm.that(
            entry,
            has=f"{make.ci.variable}={make.ci.pre_commit_value} {check.make_command}",
        )
        tm.that(entry, lacks=['"$FLEXT"', ".venv/bin", "rumdl"])

    @staticmethod
    def test_hook_stages_follow_configuration() -> None:
        """The projection follows the current typed configuration."""
        make = config.Infra.codegen.make
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=make,
                ),
            ),
        )
        tm.that("flext-pre-commit-" in rendered, eq=make.pre_commit)
        tm.that("flext-pre-push-" in rendered, eq=make.pre_push)

    @staticmethod
    def test_disabled_gates_render_no_hook_stages() -> None:
        """With both gates off the generated config carries zero hook steps."""
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=config.Infra.codegen.make.model_copy(
                        update={"pre_commit": False, "pre_push": False},
                    ),
                ),
            ),
        )

        tm.that(rendered, lacks="stages: [pre-commit]")
        tm.that(rendered, lacks="stages: [pre-push]")
        tm.that(rendered, lacks="flext-pre-commit-")
        tm.that(rendered, lacks="flext-pre-push-")

    @staticmethod
    def test_pre_push_runs_the_incremental_tests_after_the_primary_check() -> None:
        """Pre-push runs the primary check, then the incremental tests.

        Operator decision 2026-11-19: a project that opts into pre-push gets
        its primary check followed by its incremental tests in that hook; CI
        runs the same fast tests since the 2026-11-22 decision.
        """
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    scenario_data_roots=config.Infra.codegen.exclusions.scenario_data_roots,
                    dist="flext-demo",
                    make=config.Infra.codegen.make.model_copy(
                        update={"pre_push": True},
                    ),
                ),
            ),
        )
        check = rendered.find("id: flext-pre-push-check-primary")
        tests = rendered.find("id: flext-pre-push-tests-primary")
        tm.that(check, ne=-1)
        tm.that(tests > check, truth=True)

    @staticmethod
    def test_enabled_gates_render_exactly_the_declared_stages() -> None:
        """Each gate renders exactly its configured workflow rows, no more."""
        make = config.Infra.codegen.make

        both = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=make.model_copy(update={"pre_commit": True, "pre_push": True}),
                ),
            ),
        )
        expected = sum(
            1
            for step in make.workflow
            for context in ("pre_commit", "pre_push")
            if context in step.contexts
        )
        tm.that(both.count("bash -eu -o pipefail -c"), eq=expected)

        commit_only = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=make.model_copy(
                        update={"pre_commit": True, "pre_push": False},
                    ),
                ),
            ),
        )
        tm.that(commit_only, has="stages: [pre-commit]")
        tm.that(commit_only, lacks="stages: [pre-push]")

    @staticmethod
    def test_standalone_hook_config_is_not_retired(tmp_path: Path) -> None:
        """Keep a generated projection whose template declares standalone."""
        root = tmp_path / "flext-member"
        root.mkdir()
        hook_config = root / ".pre-commit-config.yaml"
        hook_config.write_text(
            "# Generated by flext_infra codegen for flext-member — DO NOT EDIT\n"
            "repos: []\n",
            encoding="utf-8",
        )

        planned = FlextInfraCodegenConform.Generate.retired_projection_plans(
            root,
            c.Infra.MakeProfile.STANDALONE,
        )

        retired = {plan.path for plan in tm.ok(planned) if plan.desired_content is None}
        tm.fail(hook_config in retired)

    @staticmethod
    def test_standalone_retires_workspace_only_generated_projection(
        tmp_path: Path,
    ) -> None:
        """Remove a generated projection excluded from the selected profile."""
        target = tmp_path / ".github/ci-template/ci.yml"
        target.parent.mkdir(parents=True)
        target.write_text(
            f"# {c.Infra.TEMPLATE_GENERATED_MARKERS[0]}\n",
            encoding="utf-8",
        )

        planned = FlextInfraCodegenConform.Generate.retired_projection_plans(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )

        retired = {plan.path for plan in tm.ok(planned) if plan.desired_content is None}
        tm.ok(target in retired)
