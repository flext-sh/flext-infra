"""Test and generation verbs admit only their declared public contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraCli, config, m
from tests import c, infra, t, tm, u


class TestsFlextInfraMakeGenRootContract:
    """Native Testmon owns tests; generation stays inside the workspace."""

    @staticmethod
    @c.Tests.MARK.parametrize("provisioned", [False, True])
    def test_native_generation_rejects_foreign_python_before_queueing(
        tmp_path: Path, monkeypatch: t.Tests.MonkeyPatch, *, provisioned: bool
    ) -> None:
        """A nested checkout cannot use the caller's Python for facade resolution."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "host-state"))
        monkeypatch.delenv(c.Infra.GATE_ADMISSION_TICKET_ENV, raising=False)
        monkeypatch.delenv("RUNTIME_ROOT", raising=False)
        outer = tmp_path / "caller"
        target = outer / "nested"
        target.mkdir(parents=True)
        for repository in (outer, target):
            u.Tests.git_bootstrap(repository, ("init", "-b", c.Infra.GIT_MAIN))
        (target / "pyproject.toml").write_text(
            '[project]\nname = "nested"\nversion = "0.0.1"\n', encoding="utf-8"
        )
        if provisioned:
            tm.that(u.Tests.provision_runtime_environment(target).is_file(), eq=True)
        generated = next(
            route
            for route in FlextInfraCli.route_table_for(c.Infra.CLI_GROUP_CODEGEN)
            if route.name == "generate"
        )
        target_environment = target / c.Infra.ENVIRONMENT_DIRECTORY
        tm.fail(
            generated.handler(m.Infra.CodegenGenerateRequest(root=target)),
            has=f"not the target Python environment {target_environment}",
        )
        tm.that(u.Infra.gate_admission_root().exists(), eq=False)

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
