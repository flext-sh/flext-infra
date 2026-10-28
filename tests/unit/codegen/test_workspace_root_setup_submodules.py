"""Workspace submodule setup behavior through generated Make surfaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import os
import shlex
import shutil
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, p, tm, u

pytestmark = pytest.mark.slow


class TestsFlextInfraWorkspaceRootSetupSubmodules:
    """Prove root submodule setup initializes once and never repairs."""

    @staticmethod
    def _git_stdout(repository: Path, *args: str) -> str:
        process = tm.ok(u.Cli.run_raw([c.Infra.GIT, *args], cwd=repository))
        tm.ok(u.Cli.process_succeeded(process.outcome))
        return process.stdout.strip()

    def _git_state(self, repository: Path) -> tuple[str, str]:
        return (
            self._git_stdout(repository, "branch", "--show-current"),
            self._git_stdout(repository, "rev-parse", "HEAD"),
        )

    @staticmethod
    def _run_setup(workspace: Path, env: dict[str, str]) -> p.Cli.CommandOutput:
        return tm.ok(
            u.Cli.run_raw(
                ["make", "_builtin_setup_submodules"],
                cwd=workspace,
                options=m.Cli.ProcessOptions(env=env),
            ),
        )

    @staticmethod
    def _render_repository_root_makefile(tmp_path: Path) -> str:
        root_repository = u.Tests.repository_ref("flext")
        member = u.Tests.repository_ref(
            "flext-core",
            path=Path("flext-core"),
            role=c.Infra.MakeProfile.STANDALONE,
        )
        workspace = u.Tests.workspace_spec(
            root_repository,
            project=u.Tests.project_spec("flext"),
            subprojects=(member,),
        )
        rendered: str = u.Tests.conform_makefile_text(
            tmp_path / "render-root",
            workspace,
        )
        return rendered

    @staticmethod
    def _create_member_origin(tmp_path: Path) -> Path:
        member = tmp_path / "member-source"
        member.mkdir()
        (member / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'flext-core'\nversion = '0.1.0'\n"
            'requires-python = "'
            f"{config.Infra.codegen.toolchain.python_required_version}"
            '"\ndependencies = []\n',
            encoding="utf-8",
        )
        pkg = member / "src" / "flext_core"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text(
            "from __future__ import annotations\n\n__all__: list[str] = []\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(member)
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "checkout", "-b", "0.12.0-dev"],
                cwd=member,
            ),
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "checkout", "main"], cwd=member))
        remote_root = tmp_path / "member-remote"
        remote_root.mkdir()
        origin = u.Tests.configure_local_origin(member, remote_root)
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "push", "-u", c.Infra.GIT_ORIGIN, "0.12.0-dev"],
                cwd=member,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "symbolic-ref", "HEAD", "refs/heads/0.12.0-dev"],
                cwd=origin,
            ),
        )
        return origin

    def _create_uninitialized_workspace(self, tmp_path: Path, makefile: str) -> Path:
        member_origin = self._create_member_origin(tmp_path)
        source = tmp_path / "workspace-source"
        source.mkdir()
        (source / "Makefile").write_text(makefile, encoding="utf-8")
        (source / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'flext'\nversion = '0.1.0'\n"
            "[tool.uv.workspace]\nmembers = ['flext-core']\n",
            encoding="utf-8",
        )
        u.Tests.copy_tracked_mise_seeds(source)
        u.Tests.initialize_git_repo(source)
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
                    member_origin.as_uri(),
                    "flext-core",
                ],
                cwd=source,
            ),
        )
        u.Tests.commit_git_changes(source, "Declare workspace project")
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "checkout", "-b", "0.12.0-dev"],
                cwd=source,
            ),
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "checkout", "main"], cwd=source))
        remote_root = tmp_path / "workspace-remote"
        remote_root.mkdir()
        workspace_origin = u.Tests.configure_local_origin(source, remote_root)
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "push", "-u", c.Infra.GIT_ORIGIN, "0.12.0-dev"],
                cwd=source,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "symbolic-ref", "HEAD", "refs/heads/0.12.0-dev"],
                cwd=workspace_origin,
            ),
        )
        checkout = tmp_path / "workspace-checkout"
        tm.ok(
            u.Cli.run_checked([
                "git",
                "clone",
                "-q",
                str(workspace_origin),
                str(checkout),
            ]),
        )
        return checkout

    def test_generated_setup_orders_submodules_before_first_uv(
        self,
        tmp_path: Path,
    ) -> None:
        """Outside CI, setup initializes the gitlinks before the first uv call.

        In CI the checkout action already materialized the gitlinks, so the
        environment recipe gains the submodule prerequisite only when the
        config-owned CI switch is off.
        """
        rendered = self._render_repository_root_makefile(tmp_path)
        ci = config.Infra.codegen.make.ci

        tm.that(
            rendered,
            has=(
                "_builtin_setup_environment: "
                f"$(if $(filter "
                f"{ci.value},$({ci.variable})),,_builtin_setup_submodules)"
            ),
        )
        # uv syncs the runtime root's project (UV_PROJECT := RUNTIME_ROOT).
        tm.that(rendered, has='$(UV) sync --project "$(UV_PROJECT)"')
        tm.that(rendered, lacks="submodule update --init --recursive")

    def test_setup_discovers_an_absent_member_despite_stale_generated_membership(
        self,
        tmp_path: Path,
    ) -> None:
        """The actual Git input provisions a member absent from a projected roster."""
        rendered = self._render_repository_root_makefile(tmp_path)
        workspace = self._create_uninitialized_workspace(tmp_path, rendered)
        env = os.environ.copy()
        env["GIT_ALLOW_PROTOCOL"] = "file"

        process = tm.ok(
            u.Cli.run_raw(
                [
                    "make",
                    "_builtin_setup_submodules",
                    "WORKSPACE_SUBPROJECTS=",
                ],
                cwd=workspace,
                options=m.Cli.ProcessOptions(env=env),
            ),
        )

        tm.ok(u.Cli.process_succeeded(process.outcome))
        tm.that(
            (workspace / "flext-core" / c.PYPROJECT_FILENAME).is_file(),
            eq=True,
        )
        declarations = tm.ok(u.Infra.git_submodule_declarations(workspace))
        tm.that(
            tuple(declaration.path for declaration in declarations),
            eq=(Path("flext-core"),),
        )

    def test_setup_rejects_malformed_management_before_provisioning(
        self,
        tmp_path: Path,
    ) -> None:
        """Native Git rejects malformed policy before an absent member is cloned."""
        rendered = self._render_repository_root_makefile(tmp_path)
        workspace = self._create_uninitialized_workspace(tmp_path, rendered)
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "config",
                    "-f",
                    c.Infra.GITMODULES,
                    "submodule.flext-core.flext-managed",
                    "invalid-boolean",
                ],
                cwd=workspace,
            ),
        )
        env = os.environ.copy()
        env["GIT_ALLOW_PROTOCOL"] = "file"

        process = self._run_setup(workspace, env)

        tm.fail(u.Cli.process_succeeded(process.outcome))
        tm.ok(bool(process.stderr))
        tm.fail((workspace / "flext-core" / c.GIT_DIR_NAME).exists())

    def test_make_setup_initializes_once_then_leaves_present_checkout_untouched(
        self,
        tmp_path: Path,
    ) -> None:
        """Initialize the exact gitlink once; never touch a present checkout."""
        rendered = self._render_repository_root_makefile(tmp_path)
        workspace = self._create_uninitialized_workspace(tmp_path, rendered)
        env = os.environ.copy()
        env["GIT_ALLOW_PROTOCOL"] = "file"

        process = self._run_setup(workspace, env)

        # The fixture bootstraps through submodules; the invariant we care about
        # is that the submodule is initialized before environment provisioning.
        if process.outcome.raw_return_code != 0:
            start = rendered.index("_builtin_setup_environment:")
            excerpt = rendered[
                start : rendered.index("# End SECTION: setup environment", start)
            ]
            pytest.fail(f"{process.stdout}{process.stderr}\n{excerpt}")
        tm.ok(u.Cli.process_succeeded(process.outcome))
        tm.ok((workspace / "flext-core" / c.PYPROJECT_FILENAME).is_file())
        child = workspace / "flext-core"
        state = self._git_state(child)
        gitlink = self._git_stdout(workspace, "rev-parse", "HEAD:flext-core")
        tm.that(state, eq=("", gitlink))

        second = self._run_setup(workspace, env)
        tm.ok(u.Cli.process_succeeded(second.outcome))
        tm.that(self._git_state(child), eq=state)
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "switch", "-c", "conflict"], cwd=child))
        process = self._run_setup(workspace, env)

        # An initialized checkout on its own named change lane is never
        # touched: setup only initializes gitlinks Git reports as uninitialized.
        tm.ok(u.Cli.process_succeeded(process.outcome))
        tm.that(self._git_state(child), eq=("conflict", state[1]))

    def test_setup_refuses_relocated_git_index(self, tmp_path: Path) -> None:
        """A relocated index is refused before any gitlink is materialized."""
        workspace = self._create_uninitialized_workspace(
            tmp_path,
            self._render_repository_root_makefile(tmp_path),
        )
        env = {
            **os.environ,
            "GIT_ALLOW_PROTOCOL": "file",
            "GIT_INDEX_FILE": str(tmp_path / "relocated-index"),
        }

        process = self._run_setup(workspace, env)

        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has="relocated Git index")
        tm.fail((workspace / "flext-core" / c.GIT_DIR_NAME).exists())

    def test_missing_submodule_origin_fails_without_materializing_checkout(
        self,
        tmp_path: Path,
    ) -> None:
        """A failed real Git clone stays red and leaves its gitlink uninitialized."""
        rendered = self._render_repository_root_makefile(tmp_path)
        workspace = self._create_uninitialized_workspace(tmp_path, rendered)
        missing_origin = tmp_path / "missing-member-origin"
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "config",
                    "-f",
                    ".gitmodules",
                    "submodule.flext-core.url",
                    str(missing_origin),
                ],
                cwd=workspace,
            ),
        )
        credential = "test-submodule-credential-never-log"
        env = {**os.environ, "GIT_ALLOW_PROTOCOL": "file", "GITHUB_TOKEN": credential}

        process = self._run_setup(workspace, env)

        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has=str(missing_origin))
        tm.that(process.stdout + process.stderr, lacks=credential)
        tm.fail((workspace / "flext-core" / c.GIT_DIR_NAME).exists())

    def test_setup_environment_provisions_members_before_the_environment(
        self,
        tmp_path: Path,
    ) -> None:
        """Setup provisions governed gitlinks, then the environment, lock-free.

        The workspace projections derive from the member checkouts, so a
        member-less CI checkout renders a different workspace and breaks the
        gen fixed point (flext-gdm8w). The fixture commits no uv.lock: setup
        still provisions the environment from the manifests
        (operator-ruling-2026-10-09-setup-resilient) and never derives a lock;
        only `make upg` writes uv.lock. The fixture manifest declares no
        flext-infra, so the later lifecycle stages cannot run here; the full
        lockless setup is proven by the make-environment suite.
        """
        rendered = self._render_repository_root_makefile(tmp_path)
        tm.that(rendered, has="MAKE_PROFILE := workspace")
        workspace = self._create_uninitialized_workspace(tmp_path, rendered)
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"SETUP_PYTHON", "CI"}
        }
        env["GIT_ALLOW_PROTOCOL"] = "file"

        process = tm.ok(
            u.Cli.run_raw(
                ["make", "--no-print-directory", "_builtin_setup_environment"],
                cwd=workspace,
                options=m.Cli.ProcessOptions(env=env),
            ),
        )

        tm.ok((workspace / "flext-core" / c.PYPROJECT_FILENAME).is_file())
        gitlink = self._git_stdout(workspace, "rev-parse", "HEAD:flext-core")
        tm.that(self._git_state(workspace / "flext-core"), eq=("", gitlink))
        output = process.stdout + process.stderr
        tm.that(output, has=["+ flext==", "+ flext-core=="], msg=output)
        tm.that(output, has="No module named flext_infra", msg=output)
        tm.that(output, lacks=["uv.lock", "WARN"])
        tm.fail((workspace / "uv.lock").exists())
        tm.that(
            (u.Infra.runtime_environment_dir(workspace) / "pyvenv.cfg").is_file(),
            eq=True,
        )

    def test_unexpected_git_probe_failure_preserves_cause(self, tmp_path: Path) -> None:
        """A failing submodule status probe propagates its own cause and code."""
        workspace = self._create_uninitialized_workspace(
            tmp_path,
            self._render_repository_root_makefile(tmp_path),
        )
        real_git = tm.not_none(shutil.which("git"))
        fake_bin = tmp_path / "failing-git-bin"
        fake_bin.mkdir()
        command_fragment = "submodule status"
        u.Tests.write_executable(
            fake_bin / "git",
            "#!/bin/sh\n"
            "set -eu\n"
            f'case "$*" in *{shlex.quote(command_fragment)}*)\n'
            "  printf 'injected git failure\\n' >&2\n"
            "  exit 42\n"
            "  ;;\n"
            "esac\n"
            f'exec {shlex.quote(real_git)} "$@"\n',
        )
        env = {
            **os.environ,
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "GIT_ALLOW_PROTOCOL": "file",
        }

        process = self._run_setup(workspace, env)

        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has="injected git failure")
        tm.that(process.stderr, has="Error 42")
