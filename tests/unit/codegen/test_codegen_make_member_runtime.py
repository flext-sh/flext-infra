"""A member checked out inside a workspace uses the workspace runtime (flext-x8gn6).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, settings
from tests import c, m, t, tm, u

pytestmark = pytest.mark.slow


class TestsFlextInfraCodegenMakeMemberRuntime:
    """Prove where a generated member Makefile resolves its runtime."""

    RUNTIME_NAMES = (
        "PROJECT_ROOT",
        "REPOSITORY_ROOT",
        "RUNTIME_ROOT",
        "RUNTIME_VENV",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
    )

    @classmethod
    def _runtime_values(cls, project_root: Path) -> t.StrDict:
        """Print the resolved runtime through the public help verb's post hook.

        Returns:
            The resulting ``t.StrDict``.

        """
        (project_root / "custom.mk").write_text(
            "post-help:\n\t@printf '%s\\n' "
            + " ".join(f"'{name}=$({name})'" for name in cls.RUNTIME_NAMES)
            + "\n",
            encoding="utf-8",
        )
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "help"],
                cwd=project_root,
            ),
        )
        tm.that(u.Cli.process_succeeded(process.outcome), eq=True, msg=process.stderr)
        return dict(
            line.split("=", 1)
            for line in process.stdout.splitlines()
            if line.split("=", 1)[0] in cls.RUNTIME_NAMES
        )

    @staticmethod
    def _workspace_with_member(
        tmp_path: Path, member_source: Path, *, included: bool = True
    ) -> Path:
        """Declare and prove native UV membership of a real Git submodule.

        Returns:
            The resulting ``Path``.

        """
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=member_source))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "--quiet", "-m", "render member"],
                cwd=member_source,
            ),
        )
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        u.Tests.initialize_git_repo(workspace)
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "--quiet",
                    str(member_source),
                    member_source.name,
                ],
                cwd=workspace,
            ),
        )
        (workspace / c.PYPROJECT_FILENAME).write_text(
            "[tool.uv.workspace]\n"
            + (
                f'members = ["{member_source.name}"]\n'
                if included
                else f'members = []\nexclude = ["{member_source.name}"]\n'
            ),
            encoding="utf-8",
        )
        u.Tests.copy_tracked_mise_seeds(workspace)
        member = workspace / member_source.name
        native = tm.ok(
            u.Cli.run_raw(
                (u.Tests.managed_uv(), "workspace", "dir", "--project", str(member)),
                cwd=member,
                options=m.Cli.ProcessOptions(
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            )
        )
        tm.that(
            u.Cli.process_succeeded(native.outcome),
            eq=True,
            msg=native.stdout + native.stderr,
        )
        tm.that(native.stdout.strip(), eq=str(workspace if included else member))
        tm.that(
            tm.ok(u.Infra.runtime_owner_root(member)),
            eq=workspace if included else member,
        )
        return workspace.resolve()

    @staticmethod
    def _direnv_venv(entry: Path) -> str:
        """Read the ``VENV_DIR`` the real generated ``.envrc`` activation resolves.

        Returns:
            The resulting ``str``.

        """
        (entry / ".envrc.local").write_text(
            'export OBSERVED_VENV_DIR="${VENV_DIR}"\n',
            encoding="utf-8",
        )
        tm.ok(u.Cli.run_checked((c.Infra.CLI_DIRENV, "allow", str(entry)), cwd=entry))
        try:
            process = tm.ok(
                u.Cli.run_raw(
                    (
                        c.Infra.CLI_DIRENV,
                        # Enter the directory as a shell does: direnv 2.37
                        # authorizes the physical .envrc, and an explicit
                        # symlinked path argument is checked unresolved.
                        "exec",
                        ".",
                        "printenv",
                        "OBSERVED_VENV_DIR",
                    ),
                    cwd=entry,
                    options=m.Cli.ProcessOptions(
                        remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                    ),
                ),
            )
        finally:
            tm.ok(
                u.Cli.run_checked((c.Infra.CLI_DIRENV, "deny", str(entry)), cwd=entry),
            )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        return process.stdout.strip()

    def test_checkout_without_superproject_owns_its_runtime(
        self,
        tmp_path: Path,
    ) -> None:
        """A standalone clone resolves its own physical environment."""
        project_root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )

        values = self._runtime_values(project_root)

        root = str(project_root.resolve())
        tm.that(values["RUNTIME_ROOT"], eq=root)
        tm.that(
            values["RUNTIME_VENV"],
            eq=str(u.Infra.runtime_environment_dir(project_root)),
        )

    @staticmethod
    @pytest.mark.parametrize("supplier", ["absent", "external", "self"])
    @pytest.mark.parametrize("hosted", [False, True])
    def test_direnv_elects_resolution_after_local_supplier_overrides(
        tmp_path: Path, supplier: str, *, hosted: bool
    ) -> None:
        """Cold activation consumes local inputs once without losing VENV_DIR."""
        project_root, _ = u.Tests.render_make_environment(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        resolution = config.Infra.codegen.make.uv_resolution
        supplier_variable = settings.Infra.EDITABLE_SUPPLIER_ENVIRONMENT
        runtime_environment = u.Infra.runtime_environment_dir(project_root)
        runtime_environment.mkdir(exist_ok=True)
        supplier_root = tmp_path / "supplier"
        supplier_root.mkdir()
        selected = project_root if supplier == "self" else supplier_root
        (project_root / ".envrc.local").write_text(
            'export OBSERVED_VENV_DIR="${VENV_DIR}"\n'
            'printf "loaded\\n" >> overrides.log\n'
            + (
                f'export {supplier_variable}="{selected}"\n'
                if supplier != "absent"
                else f"unset {supplier_variable}\n"
            ),
            encoding="utf-8",
        )
        expected_directory = (
            resolution.standalone_directory
            if hosted
            else resolution.editable_directory
            if supplier == "external"
            else resolution.local_directory
        )
        tm.ok(
            u.Cli.run_checked(
                (c.Infra.CLI_DIRENV, "allow", str(project_root)), cwd=project_root
            )
        )
        try:
            for _ in range(2):
                process = tm.ok(
                    u.Cli.run_raw(
                        (
                            c.Infra.CLI_DIRENV,
                            "exec",
                            ".",
                            "printenv",
                            "UV_PROJECT",
                            "UV_PROJECT_ENVIRONMENT",
                            "OBSERVED_VENV_DIR",
                        ),
                        cwd=project_root,
                        options=m.Cli.ProcessOptions(
                            env={
                                resolution.hosted_variable: (
                                    resolution.hosted_value if hosted else "false"
                                )
                            },
                            remove_env_keys=(
                                *c.Tests.MAKE_ISOLATION_ENV_KEYS,
                                supplier_variable,
                            ),
                        ),
                    )
                )
                tm.that(
                    u.Cli.process_succeeded(process.outcome),
                    eq=True,
                    msg=process.stdout + process.stderr,
                )
                tm.that(
                    process.stdout.splitlines(),
                    eq=[
                        str(project_root / expected_directory),
                        str(runtime_environment),
                        str(runtime_environment),
                    ],
                )
        finally:
            tm.ok(
                u.Cli.run_checked(
                    (c.Infra.CLI_DIRENV, "deny", str(project_root)), cwd=project_root
                )
            )
        tm.that(
            (project_root / "overrides.log").read_text(encoding="utf-8").splitlines(),
            eq=["loaded", "loaded"],
        )

    def test_submodule_member_resolves_the_workspace_runtime(
        self,
        tmp_path: Path,
    ) -> None:
        """A member checked out as a submodule shares the superproject runtime."""
        member_source, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        workspace = self._workspace_with_member(tmp_path, member_source)
        member = workspace / member_source.name

        values = self._runtime_values(member)

        tm.that(values["PROJECT_ROOT"], eq=str(member))
        for name in ("REPOSITORY_ROOT", "RUNTIME_ROOT"):
            tm.that(values[name], eq=str(workspace))
        tm.that(
            values["UV_PROJECT"],
            eq=str(workspace / config.Infra.codegen.make.uv_resolution.local_directory),
        )
        for name in ("RUNTIME_VENV", "UV_PROJECT_ENVIRONMENT"):
            tm.that(
                values[name],
                eq=str(u.Infra.runtime_environment_dir(member, runtime_root=workspace)),
            )

    def test_excluded_submodule_keeps_its_own_runtime(self, tmp_path: Path) -> None:
        """Git attachment cannot override UV's explicit workspace exclusion."""
        member_source, _ = u.Tests.render_make_environment(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        workspace = self._workspace_with_member(tmp_path, member_source, included=False)
        member = workspace / member_source.name

        values = self._runtime_values(member)

        for name in ("PROJECT_ROOT", "REPOSITORY_ROOT", "RUNTIME_ROOT"):
            tm.that(values[name], eq=str(member))
        tm.that(
            values["RUNTIME_VENV"],
            eq=str(u.Infra.runtime_environment_dir(member, runtime_root=member)),
        )

    def test_attached_member_upg_delegates_to_the_runtime_root(
        self,
        tmp_path: Path,
    ) -> None:
        """An attached member hands ``upg`` to its superproject's Makefile.

        The member never resolves locks itself: the runtime root's ``upg`` is
        what runs. The runtime root here declares a ``upg`` that prints a
        marker, so the observable result is that marker on the member's run.
        The local (non-hosted) context is declared explicitly because hosted
        CI rejects attached members before delegation.
        """
        member_source, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        workspace = self._workspace_with_member(tmp_path, member_source)
        marker = "runtime-root-upg"
        (workspace / c.Infra.MAKEFILE_FILENAME).write_text(
            f"upg:\n\t@printf '%s\\n' '{marker}'\n",
            encoding="utf-8",
        )

        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=workspace / member_source.name,
                env={"GITHUB_ACTIONS": "false"},
            ),
        )

        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=marker)

    @pytest.mark.parametrize("linked", [False, True])
    @pytest.mark.parametrize("attached", [False, True])
    def test_direnv_resolves_the_make_runtime_environment(
        self,
        tmp_path: Path,
        *,
        attached: bool,
        linked: bool,
    ) -> None:
        """Direnv names the same physical environment as the generated Makefile.

        An attached member activates its superproject's environment; an
        unattached checkout activates its own. Entering through a symlinked
        path never changes the resolved environment.
        """
        project_root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        owner = project_root.resolve()
        member = owner
        if attached:
            owner = self._workspace_with_member(tmp_path, project_root)
            member = owner / project_root.name
        entry = member
        if linked:
            link = tmp_path / "linked-entry"
            link.symlink_to(owner, target_is_directory=True)
            entry = link / member.relative_to(owner)

        values = self._runtime_values(entry)
        observed = self._direnv_venv(entry)

        tm.that(
            values["RUNTIME_VENV"],
            eq=str(u.Infra.runtime_environment_dir(member, runtime_root=owner)),
        )
        tm.that(observed, eq=values["RUNTIME_VENV"])
