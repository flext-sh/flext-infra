"""Test and generation verbs admit only their declared public contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

from flext_infra import config, m
from flext_infra.workspace import FlextInfraWorkspaceDetector
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
    def test_member_own_runtime_refuses_provisioning_before_any_effect(
        tmp_path: Path,
    ) -> None:
        """A member checkout that is its own runtime has no flext-infra supplier.

        The credential command is available on PATH, but the cold checkout's
        home has no acquisition Mise. Refusal precedes both credential and
        tool discovery and leaves the runtime and executor absent.
        """
        shape = u.Tests.MakeEnvironmentShape()
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.WORKSPACE,
            shape=shape,
        )
        home = tmp_path / "cold-home"
        home.mkdir()
        tm.not_none(
            shutil.which(config.Infra.codegen.make.github_credential_command[0])
        )
        for verb in ("setup", "upg", "lock"):
            process = tm.ok(
                u.Tests.run_isolated_make(
                    ["--no-print-directory", verb], cwd=root, env={"HOME": str(home)}
                ),
            )
            tm.that(process.outcome.raw_return_code, eq=2)
            tm.that(process.stdout, eq="")
            tm.that(
                process.stderr,
                has=[
                    f"ERROR[{verb}]: {shape.project_name} is a workspace member",
                    f"Run make {verb} from a workspace-shaped lane",
                ],
                lacks=str(home),
            )
        tm.that(tuple(home.iterdir()), eq=())
        tm.that(u.Infra.runtime_environment_dir(root).exists(), eq=False)
        tm.that(
            (root / config.Infra.codegen.make.executor_environment.directory).exists(),
            eq=False,
        )

    @staticmethod
    @c.Tests.MARK.slow
    def test_standalone_runtime_supplies_its_own_provisioning(
        tmp_path: Path,
    ) -> None:
        """A standalone checkout declares flext-infra and keeps its provisioning."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        tm.that(rendered, lacks="REFUSE_MEMBER_RUNTIME")
        tm.that(
            rendered,
            has="_setup_provision: _builtin_require_github_credential "
            "_bootstrap_setup_tools",
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

    @staticmethod
    def _attached_member(root: Path, tmp_path: Path, name: str) -> Path:
        """Attach one real governed submodule the workspace declares as external.

        Returns:
            The attached member checkout.

        """
        origin = tmp_path / f"{name}-origin"
        beads = u.Tests.beads_project(name)
        u.Tests.WorktreeFixture.initialize_governed_project(
            origin,
            name,
            beads=u.Tests.BeadsIdentity(
                workspace=beads.workspace,
                database=beads.database,
                issue_prefix=beads.issue_prefix,
            ),
        )
        branch = u.Tests.checkout_integration(origin)
        u.Tests.git_bootstrap(
            root,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-b",
                branch,
                str(origin),
                name,
            ),
        )
        u.Tests.git_bootstrap(
            root,
            (
                "config",
                "-f",
                c.Infra.GITMODULES,
                f"submodule.{name}.flext-managed",
                c.ParserBooleanToken.FALSE,
            ),
        )
        u.Tests.write_workspace_manifest(
            root,
            root.name,
            role=c.Infra.MakeProfile.WORKSPACE,
        )
        u.Tests.git_bootstrap(root, ("add", c.Infra.GITMODULES, name))
        u.Tests.git_bootstrap(root, ("commit", "-m", f"Declare attached member {name}"))
        return root / name

    @staticmethod
    def test_election_admits_a_governed_attached_member_only(tmp_path: Path) -> None:
        """A declared attached member with its own project and lock is a root.

        The workspace may classify an attached checkout as an external
        dependency; the checkout still owns its projections when it carries
        its own ``pyproject.toml`` and ``mise.lock``. A plain vendored fork
        carries no lock and never becomes a generation root.
        """
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "election-ws")
        member = TestsFlextInfraMakeGenRootContract._attached_member(
            root, tmp_path, "elected-member"
        )
        plain = root / "plain-fork"
        plain.mkdir()
        (plain / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "plain-fork"\nversion = "0.1.0"\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (root / c.Infra.GITMODULES).write_text(
            (root / c.Infra.GITMODULES).read_text(encoding=c.Infra.ENCODING_DEFAULT)
            + '[submodule "plain-fork"]\n'
            "\tpath = plain-fork\n"
            "\turl = https://github.com/foreign-owner/plain-fork.git\n"
            "\tbranch = master\n"
            "\tflext-classification = external-fork\n"
            "\tflext-managed = false\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        elected = u.Infra.generation_root_members(root, workspace)

        tm.that(workspace.subprojects, empty=True)
        tm.ok(member.resolve() in elected)
        tm.fail(plain.resolve() in elected)
        tm.ok(root.resolve() not in elected)

    @staticmethod
    def test_generation_rejects_an_unlocked_declared_member(tmp_path: Path) -> None:
        """A declared member without its own lock is rejected by the service."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "unlocked-ws")
        member = TestsFlextInfraMakeGenRootContract._attached_member(
            root, tmp_path, "unlocked-member"
        )
        (member / c.Infra.MISE_LOCK_FILENAME).unlink()

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        elected = u.Infra.generation_root_members(root, workspace)

        tm.that(workspace.subprojects, empty=True)
        tm.fail(member.resolve() in elected)
        result = infra.codegen_generate(
            m.Infra.CodegenGenerateRequest(
                root=member,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
            )
        )
        tm.fail(
            result,
            has="generation root must be the workspace root or a declared member",
        )

    @staticmethod
    def test_generation_admits_a_governed_attached_member(tmp_path: Path) -> None:
        """The public service generates inside a declared governed member."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "attached-ws")
        member = TestsFlextInfraMakeGenRootContract._attached_member(
            root, tmp_path, "attached-member"
        )

        result = infra.codegen_generate(
            m.Infra.CodegenGenerateRequest(
                root=member,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
            )
        )

        tm.ok(result)
