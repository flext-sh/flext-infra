"""Test and generation verbs admit only their declared public contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import config, m
from tests import c, infra, tm, u


class TestsFlextInfraMakeGenRootContract:
    """Native Testmon owns tests; generation stays inside the workspace."""

    @staticmethod
    def test_test_verbs_declare_no_manual_file_selector() -> None:
        """The typed catalog exposes no per-file selector for tests."""
        verbs = {verb.name: verb for verb in config.Infra.codegen.make.verbs}
        for name in ("tests", "tests-full"):
            tm.that(verbs[name].arguments, eq=())
            tm.that(verbs[name].description.upper(), lacks="FILE")

    @staticmethod
    @c.Tests.MARK.slow
    def test_rendered_test_verbs_invoke_only_the_native_runner(
        tmp_path: Path,
    ) -> None:
        """The generated recipes pass no manual file selector to the runner."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        for target in ("_builtin_tests_all", "_builtin_tests_full_all"):
            recipe = rendered.split(f"{target}:", 1)[1].split("\n\n", 1)[0]
            tm.that(recipe, lacks=["--file", "$${FILE"])
            tm.that(
                recipe,
                has='--repository-root "$(PROJECT_ROOT)" --scope "$(GATE_SCOPE)"',
            )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize(
        "profile",
        [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE],
    )
    def test_ci_and_the_commit_hook_validate_only_their_own_repository(
        tmp_path: Path,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """CI and the commit hook scope every gate verb to the invoked root.

        Locally check covers every governed repository in every profile, and
        a workspace root's fmt, fix and tests do too; a standalone checkout's
        fmt, fix and tests have only itself.
        """
        root, _ = u.Tests.render_make_environment(tmp_path, profile)
        ci = config.Infra.codegen.make.ci
        own = c.Infra.CodegenConformScope.SELF
        every = c.Infra.CodegenConformScope.ALL
        remote = {ci.variable: ci.local_value, ci.remote_variable: ci.remote_value}
        local_scope = every if profile is c.Infra.MakeProfile.WORKSPACE else own
        no_token: Mapping[str, str] = {}
        for env, check_scope, gate_scope in (
            ({ci.variable: ci.value}, own, own),
            ({ci.variable: ci.pre_commit_value}, own, own),
            (remote, own, own),
            ({ci.variable: ci.local_value}, every, local_scope),
            (no_token, every, local_scope),
        ):
            for verb, scope in (
                (c.Infra.VERB_CHECK, check_scope),
                (c.Infra.CheckGateSet.FMT.value, gate_scope),
                (c.Infra.CheckGateSet.FIX.value, gate_scope),
                (c.Infra.VERB_TEST, gate_scope),
            ):
                execution = tm.ok(
                    u.Cli.run_raw(
                        [c.Infra.MAKE, "--dry-run", f"_builtin-{verb}"],
                        cwd=root,
                        options=m.Cli.ProcessOptions(
                            env=env,
                            remove_env_keys=(
                                "MAKEFLAGS",
                                *sorted({ci.variable, ci.remote_variable} - set(env)),
                            ),
                        ),
                    ),
                )
                output = (execution.stdout + execution.stderr).replace('"', "")
                tm.ok(u.Cli.process_succeeded(execution.outcome), msg=output)
                tm.that(output, has=f"--scope {scope.value}")
                tm.that(
                    output,
                    lacks=[
                        f"--scope {other.value}"
                        for other in (own, every)
                        if other is not scope
                    ],
                )

    @staticmethod
    def test_typed_root_selection_admits_workspace_and_declared_members(
        tmp_path: Path,
    ) -> None:
        """The typed containment contract admits only the declared topology."""
        root = tmp_path / "typed-workspace"
        member = root / "member"
        selection = m.Infra.CodegenRootSelection(
            workspace_root=root,
            requested_root=member,
            members=(member,),
        )
        tm.that(selection.requested_root, eq=member)
        with u.Tests.raises(ValueError, match="workspace root or a declared member"):
            m.Infra.CodegenRootSelection(
                workspace_root=root,
                requested_root=tmp_path / "outside",
                members=(member,),
            )

    @staticmethod
    def test_generation_rejects_a_root_outside_the_declared_topology(
        tmp_path: Path,
    ) -> None:
        """The public service never generates an arbitrary requested root."""
        root = tmp_path / "fixture-workspace"
        u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        stray = root / "stray"
        stray.mkdir()
        result = infra.codegen_generate(
            m.Infra.CodegenGenerateRequest(
                root=stray,
                what=c.Infra.CodegenConformSurface.DEPENDENCIES,
                scope=c.Infra.CodegenConformScope.SELF,
            )
        )
        tm.fail(
            result,
            has="generation root must be the workspace root or a declared member",
        )
