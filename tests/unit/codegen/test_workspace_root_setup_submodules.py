"""Workspace-root submodule setup behavior through generated Make surfaces."""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


def _render_workspace_root_makefile(tmp_path: Path) -> str:
    root_repository = next(
        repository
        for repository in config.Infra.codegen.repositories
        if repository.name == "flext"
    )
    member = next(
        repository
        for repository in config.Infra.codegen.repositories
        if repository.name == "flext-core"
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
        "[project]\nname = 'flext-core'\nversion = '0.1.0'\n", encoding="utf-8"
    )
    test_u.Tests.initialize_git_repo(member)
    remote_root = tmp_path / "member-remote"
    remote_root.mkdir()
    return test_u.Tests.configure_local_origin(member, remote_root)


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
                "main",
                str(member_origin),
                "flext-core",
            ],
            cwd=source,
        )
    )
    test_u.Tests.commit_git_changes(source, "Declare workspace member")
    remote_root = tmp_path / "workspace-remote"
    remote_root.mkdir()
    workspace_origin = test_u.Tests.configure_local_origin(source, remote_root)
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

        sync_at = rendered.index("submodule sync --recursive")
        update_at = rendered.index("submodule update --init --recursive")
        uv_at = rendered.index("$(UV) sync --project")

        tm.that(sync_at < update_at < uv_at, eq=True)

    def test_make_setup_initializes_local_submodule_before_conform(
        self, tmp_path: Path
    ) -> None:
        rendered = _render_workspace_root_makefile(tmp_path)
        workspace = _create_uninitialized_workspace(tmp_path, rendered)
        env = os.environ.copy()
        env["GIT_ALLOW_PROTOCOL"] = "file"

        outcome = u.Cli.run_raw(["make", "setup"], cwd=workspace, env=env)
        process = outcome.value

        # The minimal fixture lacks a valid workspace package tree, so the
        # conform step after submodule initialization is expected to fail. The
        # invariant we care about is that the submodule is initialized before
        # conform/uv; the conform error proves the uv bootstrap was reached.
        tm.that(process.exit_code, eq=2)
        tm.that(process.stdout, has="Failed to execute CLI application")
        tm.that((workspace / "flext-core" / "pyproject.toml").is_file(), eq=True)
