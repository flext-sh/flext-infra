"""A member checked out inside a workspace uses the workspace runtime (flext-x8gn6).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, t, tm, u

pytestmark = c.Tests.MARK.slow


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

    @u.Tests.fixture(scope="module")
    @staticmethod
    def runtime_reader_template(tmp_path_factory: t.Tests.TempPathFactory) -> Path:
        """Generate the complete source contract once for independent copies.

        Returns:
            The generated template without an installed environment.

        """
        root, _ = u.Tests.render_make_environment(
            tmp_path_factory.mktemp("runtime-reader"), c.Infra.MakeProfile.STANDALONE
        )
        return root

    @u.Tests.fixture
    @staticmethod
    def runtime_reader(tmp_path: Path, runtime_reader_template: Path) -> Path:
        """Copy declarations into an independently owned Git checkout.

        Returns:
            The isolated checkout with its real trusted native reader.

        """
        root = u.Tests.resolved_make_checkout(
            runtime_reader_template, tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        u.Tests.copy_tracked_mise_seeds(root)
        tm.that(
            Path(u.Tests.git_capture(root, "rev-parse", "--absolute-git-dir").strip()),
            eq=root / c.GIT_DIR_NAME,
        )
        for name in (
            c.PYPROJECT_FILENAME,
            c.Infra.MISE_TOML_FILENAME,
            c.Infra.MISE_LOCK_FILENAME,
        ):
            copied, original = root / name, runtime_reader_template / name
            tm.that(copied.samefile(original), eq=False)
            tm.that(copied.read_bytes(), eq=original.read_bytes())
        return root

    @classmethod
    def _runtime_values(cls, project_root: Path) -> dict[str, str]:
        """Print the resolved runtime through the public help verb's post hook.

        Returns:
            The resulting ``dict[str, str]``.

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
        tmp_path: Path,
        member_source: Path,
        *,
        included: bool = True,
        attached: bool = True,
    ) -> Path:
        """Declare and prove native membership separately from Git attachment.

        Returns:
            The resulting ``Path``.

        """
        operation = (
            ["submodule", "add", "--quiet"] if attached else ["clone", "--quiet"]
        )
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        u.Tests.initialize_git_repo(workspace)
        u.Tests.git_bootstrap(
            workspace,
            (
                "-c",
                "protocol.file.allow=always",
                *operation,
                str(member_source),
                member_source.name,
            ),
        )
        distribution = tm.ok(
            u.Infra.read_project_metadata_state(member_source)
        ).metadata.project.name
        composed = (
            f'dependencies = ["{distribution}"]\n'
            f'[tool.uv.sources]\n"{distribution}" = '
            f'{{path = "{member_source.name}", editable = true}}\n'
            if attached and not included
            else ""
        )
        (workspace / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "fixture-workspace"\nversion = "0.1.0"\n'
            + composed
            + "[tool.uv.workspace]\n"
            + (
                f'members = ["{member_source.name}"]\n'
                if included
                else f'members = []\nexclude = ["{member_source.name}"]\n'
            ),
            encoding="utf-8",
        )
        u.Tests.copy_tracked_mise_seeds(workspace)
        member = workspace / member_source.name
        if not attached:
            u.Tests.copy_tracked_mise_seeds(member)
        tm.that(
            u.Tests.git_capture(
                member, "rev-parse", "--show-superproject-working-tree"
            ).strip(),
            eq=str(workspace) if attached else "",
        )
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
            eq=workspace if attached else member,
        )
        return workspace.resolve()

    @staticmethod
    def _direnv_venv(entry: Path) -> str:
        """Read the ``VENV_DIR`` the real generated ``.envrc`` activation resolves.

        Returns:
            The resulting ``str``.

        """
        owner = tm.ok(u.Infra.runtime_owner_root(entry))
        u.Tests.provision_runtime_environment(owner)
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

    @c.Tests.MARK.parametrize("linked", [False, True])
    def test_checkout_without_superproject_owns_its_runtime(
        self,
        tmp_path: Path,
        runtime_reader: Path,
        *,
        linked: bool,
    ) -> None:
        """Standalone clones and actual linked checkouts own their environments."""
        project_root = runtime_reader
        if linked:
            self._runtime_values(runtime_reader)
            u.Tests.commit_git_changes(runtime_reader, "Seed generated runtime readers")
            project_root = u.Tests.git_linked_lane(
                tmp_path, runtime_reader, "linked-runtime"
            )
            u.Tests.copy_tracked_mise_seeds(project_root)
            tm.that((project_root / c.GIT_DIR_NAME).is_file(), eq=True)

        values = self._runtime_values(project_root)
        root = str(project_root.resolve())
        tm.that(
            u.Tests.git_capture(project_root, "rev-parse", "--show-toplevel").strip(),
            eq=root,
        )
        tm.that(tm.ok(u.Infra.runtime_owner_root(project_root)), eq=project_root)
        tm.that(values["RUNTIME_ROOT"], eq=root)
        tm.that(
            values["RUNTIME_VENV"],
            eq=str(u.Infra.runtime_environment_dir(project_root)),
        )
        tm.that(self._direnv_venv(project_root), eq=values["RUNTIME_VENV"])
        if linked:
            tm.that(u.Infra.runtime_environment_dir(runtime_reader).exists(), eq=False)

    def test_submodule_member_resolves_the_workspace_runtime(
        self,
        tmp_path: Path,
        runtime_reader: Path,
    ) -> None:
        """A member checked out as a submodule shares the superproject runtime."""
        member_source = runtime_reader
        workspace = self._workspace_with_member(tmp_path, member_source)
        member = workspace / member_source.name

        values = self._runtime_values(member)

        tm.that(values["PROJECT_ROOT"], eq=str(member))
        for name in ("REPOSITORY_ROOT", "RUNTIME_ROOT"):
            tm.that(values[name], eq=str(workspace))
        tm.that(values["UV_PROJECT"], empty=True)
        for name in ("RUNTIME_VENV", "UV_PROJECT_ENVIRONMENT"):
            tm.that(
                values[name],
                eq=str(u.Infra.runtime_environment_dir(member, runtime_root=workspace)),
            )

    @c.Tests.MARK.parametrize("attached", [False, True])
    def test_uv_exclusion_retains_declared_runtime_ownership(
        self, tmp_path: Path, runtime_reader: Path, *, attached: bool
    ) -> None:
        """Lock composition shares a runtime; an independent clone owns its own."""
        member_source = runtime_reader
        workspace = self._workspace_with_member(
            tmp_path, member_source, included=False, attached=attached
        )
        member = workspace / member_source.name
        owner = workspace if attached else member
        locks = tuple(
            (path, tm.ok(u.Cli.atomic_read_binary_file_state(path, required=False)))
            for root in (workspace, member)
            for name in (c.Infra.UV_LOCK_FILENAME, c.Infra.MISE_LOCK_FILENAME)
            for path in (root / name,)
        )

        values = self._runtime_values(member)

        tm.that(values["PROJECT_ROOT"], eq=str(member))
        for name in ("REPOSITORY_ROOT", "RUNTIME_ROOT"):
            tm.that(values[name], eq=str(owner))
        tm.that(
            values["RUNTIME_VENV"],
            eq=str(u.Infra.runtime_environment_dir(member, runtime_root=owner)),
        )
        tm.that(self._direnv_venv(member), eq=values["RUNTIME_VENV"])
        for path, before in locks:
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=False)),
                eq=before,
            )

    def test_attached_member_upg_delegates_to_the_runtime_root(
        self,
        tmp_path: Path,
        runtime_reader: Path,
    ) -> None:
        """An attached member hands ``upg`` to its superproject's Makefile.

        The member never resolves locks itself: the runtime root's ``upg`` is
        what runs. The runtime root here declares a ``upg`` that prints a
        marker, so the observable result is that marker on the member's run.
        The local (non-hosted) context is declared explicitly because hosted
        CI rejects attached members before delegation.
        """
        member_source = runtime_reader
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
                env={"GITHUB_ACTIONS": c.ParserBooleanToken.FALSE},
            ),
        )

        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=marker)

    @c.Tests.MARK.parametrize("linked", [False, True])
    @c.Tests.MARK.parametrize("attached", [False, True])
    def test_direnv_resolves_the_make_runtime_environment(
        self,
        tmp_path: Path,
        runtime_reader: Path,
        *,
        attached: bool,
        linked: bool,
    ) -> None:
        """Direnv names the same physical environment as the generated Makefile.

        An attached member activates its superproject's environment; an
        unattached checkout activates its own. Entering through a symlinked
        path never changes the resolved environment.
        """
        project_root = runtime_reader
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
