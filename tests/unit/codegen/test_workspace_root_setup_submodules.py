"""Workspace-root submodule setup behavior through generated Make surfaces."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_infra import c, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u

pytestmark = pytest.mark.slow


def _render_workspace_root_makefile(tmp_path: Path) -> str:
    root_repository = test_u.Tests.repository_ref("flext")
    member = test_u.Tests.repository_ref(
        "flext-core", role=c.Infra.RepositoryRole.STANDALONE
    )
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="flext",
        repository=root_repository,
        project=m.Infra.ProjectSpec(
            package_name="flext",
            class_stem="Flext",
            namespace="Flext",
            constant_name="flext",
            namespace_attribute="flext",
            alias="flext",
            environment_prefix="FLEXT_",
            description="FLEXT workspace",
            version="0.12.0.dev0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage="https://github.com/flext-sh/flext",
            documentation="https://github.com/flext-sh/flext",
            workspace_root_rel=".",
            year=2026,
        ),
        members=(member,),
    )
    root = tmp_path / "render-root"
    request = m.Infra.CodegenConformRequest(
        root=root,
        scope=c.Infra.CodegenConformScope.SELF,
        mode=c.Infra.CodegenConformMode.CHECK,
    )
    planned = FlextInfraCodegenConform(
        workspace_root=root, request=request, initial_workspace=workspace
    ).plan(request)
    plan = tm.ok(planned)
    makefile: m.Infra.CodegenFilePlan = next(
        file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
    )
    return makefile.rendered


def _create_member_origin(tmp_path: Path) -> Path:
    member = tmp_path / "member-source"
    member.mkdir()
    (member / "pyproject.toml").write_text(
        "[project]\nname = 'flext-core'\nversion = '0.1.0'\n"
        'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
        encoding="utf-8",
    )
    pkg = member / "src" / "flext_core"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(
        "from __future__ import annotations\n\n__all__: list[str] = []\n",
        encoding="utf-8",
    )
    test_u.Tests.initialize_git_repo(member)
    tm.ok(u.Cli.run_checked([c.Infra.GIT, "checkout", "-b", "0.12.0-dev"], cwd=member))
    tm.ok(u.Cli.run_checked([c.Infra.GIT, "checkout", "main"], cwd=member))
    remote_root = tmp_path / "member-remote"
    remote_root.mkdir()
    origin = test_u.Tests.configure_local_origin(member, remote_root)
    tm.ok(
        u.Cli.run_checked(
            [c.Infra.GIT, "push", "-u", c.Infra.GIT_ORIGIN, "0.12.0-dev"], cwd=member
        )
    )
    tm.ok(
        u.Cli.run_checked(
            [c.Infra.GIT, "symbolic-ref", "HEAD", "refs/heads/0.12.0-dev"], cwd=origin
        )
    )
    return origin


def _create_uninitialized_workspace(tmp_path: Path, makefile: str) -> Path:
    member_origin = _create_member_origin(tmp_path)
    source = tmp_path / "workspace-source"
    source.mkdir()
    (source / "Makefile").write_text(makefile, encoding="utf-8")
    (source / "pyproject.toml").write_text(
        "[project]\nname = 'flext'\nversion = '0.1.0'\n"
        "[tool.uv.workspace]\nmembers = ['flext-core']\n",
        encoding="utf-8",
    )
    test_u.Tests.initialize_git_repo(source)
    tm.ok(
        u.Cli.run_checked(
            [
                "git",
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-q",
                "-b",
                "0.12.0-dev",
                str(member_origin),
                "flext-core",
            ],
            cwd=source,
        )
    )
    test_u.Tests.commit_git_changes(source, "Declare workspace member")
    tm.ok(u.Cli.run_checked([c.Infra.GIT, "checkout", "-b", "0.12.0-dev"], cwd=source))
    tm.ok(u.Cli.run_checked([c.Infra.GIT, "checkout", "main"], cwd=source))
    remote_root = tmp_path / "workspace-remote"
    remote_root.mkdir()
    workspace_origin = test_u.Tests.configure_local_origin(source, remote_root)
    tm.ok(
        u.Cli.run_checked(
            [c.Infra.GIT, "push", "-u", c.Infra.GIT_ORIGIN, "0.12.0-dev"], cwd=source
        )
    )
    tm.ok(
        u.Cli.run_checked(
            [c.Infra.GIT, "symbolic-ref", "HEAD", "refs/heads/0.12.0-dev"],
            cwd=workspace_origin,
        )
    )
    checkout = tmp_path / "workspace-checkout"
    tm.ok(
        u.Cli.run_checked(["git", "clone", "-q", str(workspace_origin), str(checkout)])
    )
    return checkout


class TestsWorkspaceRootSetupSubmodules:
    def test_generated_setup_orders_submodules_before_first_uv(
        self, tmp_path: Path
    ) -> None:
        rendered = _render_workspace_root_makefile(tmp_path)

        tm.that(rendered, has="_builtin_setup_environment: _builtin_setup_submodules")
        tm.that(rendered, has="submodule update --init --")
        tm.that(rendered, has="$(UV) sync --project")
        tm.that(rendered, lacks="submodule update --init --recursive")

    def test_make_setup_initializes_local_submodule_before_environment(
        self, tmp_path: Path
    ) -> None:
        """Generated workspace-root setup initializes declared submodules first."""
        rendered = _render_workspace_root_makefile(tmp_path)
        workspace = _create_uninitialized_workspace(tmp_path, rendered)
        env = os.environ.copy()
        env["GIT_ALLOW_PROTOCOL"] = "file"

        outcome = u.Cli.run_raw(
            ["make", "_builtin_setup_submodules"], cwd=workspace, env=env
        )
        process = outcome.value

        # The fixture bootstraps through submodules; the invariant we care about
        # is that the submodule is initialized before environment provisioning.
        tm.that(process.exit_code, eq=0)
        tm.that(process.stdout + process.stderr, has="Submodule path 'flext-core'")
        tm.that((workspace / "flext-core" / "pyproject.toml").is_file(), eq=True)
