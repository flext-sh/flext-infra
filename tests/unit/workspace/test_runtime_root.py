"""Runtime ownership through real standalone Git roots and submodules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, tm, u


class TestsFlextInfraRuntimeRoot:
    """The execution context elects exactly one lock and environment owner."""

    @staticmethod
    @pytest.mark.parametrize("malformed_parent_git", [False, True])
    def test_python_parent_does_not_invent_a_containing_git_owner(
        tmp_path: Path,
        malformed_parent_git: bool,
    ) -> None:
        """A Git child stays independent, while a malformed parent marker is red."""
        parent = tmp_path / "python-parent"
        parent.mkdir()
        (parent / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-parent'\nversion = '1.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        root = parent / "standalone"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-child'\nversion = '1.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        if malformed_parent_git:
            (parent / c.Infra.GIT_DIR).write_text(
                "gitdir: absent-storage\n",
                encoding=c.DEFAULT_ENCODING,
            )

        observed = FlextInfraWorkspaceDetector.resolution_context(root)

        if malformed_parent_git:
            tm.that(observed.failure, eq=True)
            tm.that(u.Infra.runtime_owner_root(root).failure, eq=True)
        else:
            context = tm.ok(observed)
            tm.that(context.project_root, eq=root.resolve())
            tm.that(context.runtime_root, eq=root.resolve())
            tm.that(u.Infra.runtime_environment_dir(root), eq=context.environment_path)

    @staticmethod
    def test_root_context_is_available_before_managed_toml_recovery(
        tmp_path: Path,
    ) -> None:
        """An authenticated root does not need a parseable target to elect itself."""
        root = tmp_path / "standalone"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-root'\nversion = '1.0'\n"
            "[tool.uv]\n<<<<<<< HEAD\n=======\n>>>>>>> incoming\n",
            encoding="utf-8",
        )

        observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(root))

        tm.that(observed.project_root, eq=root.resolve())
        tm.that(observed.runtime_root, eq=root.resolve())

    @pytest.mark.parametrize("excluded", [False, True])
    @pytest.mark.parametrize("hosted", [False, True])
    @pytest.mark.parametrize("ci", [False, True])
    def test_native_monorepo_owner_retains_the_requested_project(
        self,
        tmp_path: Path,
        excluded: bool,
        hosted: bool,
        ci: bool,
    ) -> None:
        """UV membership and exclusions elect runtime without flattening a child."""
        root = tmp_path / "monorepo"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        u.Tests.copy_tracked_mise_seeds(root)
        child = root / "packages" / ("independent" if excluded else "member")
        child.mkdir(parents=True)
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-monorepo'\nversion = '1.0'\n"
            "[tool.uv.workspace]\nmembers = ['packages/*']\n"
            "exclude = ['packages/independent']\n",
            encoding="utf-8",
        )
        (child / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-child'\nversion = '1.0'\n",
            encoding="utf-8",
        )
        gates = config.Infra.codegen.make.ci
        policy = config.Infra.codegen.make.uv_resolution
        previous_ci = os.environ.get(gates.variable)
        previous_hosted = os.environ.get(policy.hosted_variable)
        try:
            os.environ[gates.variable] = gates.value if ci else gates.local_value
            u.Tests.restore_env(
                policy.hosted_variable,
                policy.hosted_value if hosted else None,
            )

            observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(child))

            owner = child if excluded or hosted else root
            directory = (
                policy.standalone_directory if hosted else policy.local_directory
            )
            tm.that(observed.project_root, eq=child.resolve())
            tm.that(observed.runtime_root, eq=owner.resolve())
            tm.that(observed.resolution_root, eq=owner / directory)
            tm.that(observed.environment_path, eq=owner / c.Infra.ENVIRONMENT_DIRECTORY)
        finally:
            u.Tests.restore_env(gates.variable, previous_ci)
            u.Tests.restore_env(policy.hosted_variable, previous_hosted)

    @staticmethod
    def test_independent_nested_git_checkout_keeps_its_runtime(tmp_path: Path) -> None:
        """A nested Git checkout is not associated merely by directory ancestry."""
        root = tmp_path / "enclosing"
        child = root / "independent"
        root.mkdir()
        child.mkdir()
        u.Tests.initialize_git_repo(root)
        u.Tests.initialize_git_repo(child)
        u.Tests.copy_tracked_mise_seeds(root)
        for directory, name in ((root, "fixture-parent"), (child, "fixture-child")):
            (directory / c.PYPROJECT_FILENAME).write_text(
                f"[project]\nname = '{name}'\nversion = '1.0'\n",
                encoding="utf-8",
            )

        observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(child))

        tm.that(observed.project_root, eq=child.resolve())
        tm.that(observed.runtime_root, eq=child.resolve())

    @staticmethod
    @pytest.mark.parametrize("association", ["member", "excluded", "own-workspace"])
    def test_native_membership_controls_a_nested_clone(
        tmp_path: Path,
        association: str,
    ) -> None:
        """Native declarations associate a clone; its Git root alone does not."""
        root = tmp_path / "workspace"
        child = root / "member"
        root.mkdir()
        child.mkdir()
        u.Tests.initialize_git_repo(root)
        u.Tests.initialize_git_repo(child)
        u.Tests.copy_tracked_mise_seeds(root)
        excluded = "exclude = ['member']\n" if association == "excluded" else ""
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-workspace'\nversion = '1.0'\n"
            "[tool.uv.workspace]\nmembers = ['member']\n" + excluded,
            encoding="utf-8",
        )
        (child / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-clone'\nversion = '1.0'\n"
            + ("[tool.uv.workspace]\n" if association == "own-workspace" else ""),
            encoding="utf-8",
        )

        observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(child))

        tm.that(observed.project_root, eq=child.resolve())
        tm.that(
            observed.runtime_root,
            eq=(root if association == "member" else child).resolve(),
        )
        tm.that(u.Infra.runtime_environment_dir(child), eq=observed.environment_path)
        tm.that(
            u.Infra.runtime_python(child).parent.parent,
            eq=observed.environment_path,
        )

    @pytest.mark.parametrize("attached", [False, True])
    @pytest.mark.parametrize("hosted", [False, True])
    @pytest.mark.parametrize("ci", [False, True])
    def test_resolution_view_preserves_physical_environment(
        self,
        tmp_path: Path,
        attached: bool,
        hosted: bool,
        ci: bool,
    ) -> None:
        """Hosted execution selects resolver input without changing ownership."""
        workspace = tmp_path / "runtime"
        workspace.mkdir()
        u.Tests.initialize_git_repo(workspace)
        (workspace / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-runtime'\nversion = '1.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        project = workspace
        if attached:
            origin = tmp_path / "origin"
            origin.mkdir()
            u.Tests.initialize_git_repo(origin)
            tm.ok(
                u.Cli.run_checked(
                    (
                        "git",
                        "-c",
                        "protocol.file.allow=always",
                        "submodule",
                        "add",
                        str(origin),
                        "member",
                    ),
                    cwd=workspace,
                ),
            )
            project = workspace / "member"
            (project / c.PYPROJECT_FILENAME).write_text(
                "[project]\nname = 'fixture-member'\nversion = '1.0'\n",
                encoding=c.DEFAULT_ENCODING,
            )
        policy = config.Infra.codegen.make.uv_resolution
        gates = config.Infra.codegen.make.ci
        previous_hosted = os.environ.get(policy.hosted_variable)
        previous_ci = os.environ.get(gates.variable)
        try:
            u.Tests.restore_env(
                policy.hosted_variable,
                policy.hosted_value if hosted else None,
            )
            os.environ[gates.variable] = gates.value if ci else gates.local_value
            observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(project))
            directory = (
                policy.standalone_directory if hosted else policy.local_directory
            )
            owner = project if hosted else workspace
            expected = owner.resolve() / directory

            tm.that(observed.project_root, eq=project.resolve())
            tm.that(observed.runtime_root, eq=owner.resolve())
            tm.that(observed.environment_path, eq=owner / c.Infra.ENVIRONMENT_DIRECTORY)
            tm.that(observed.resolution_root, eq=expected)
            tm.that(observed.pyproject_path, eq=expected / c.PYPROJECT_FILENAME)
            tm.that(observed.lock_path, eq=expected / c.Infra.UV_LOCK_FILENAME)
            tm.that(observed.standalone, eq=hosted)
        finally:
            u.Tests.restore_env(policy.hosted_variable, previous_hosted)
            u.Tests.restore_env(gates.variable, previous_ci)

    @staticmethod
    def test_project_context_exposes_the_same_runtime_election(tmp_path: Path) -> None:
        """The public project context shares the bootstrap-safe ownership model."""
        repository = tmp_path / "project"
        u.Tests.WorktreeFixture.initialize_governed_project(
            repository,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture_database",
                issue_prefix="fixture",
            ),
        )

        expected = tm.ok(FlextInfraWorkspaceDetector.resolution_context(repository))
        observed = tm.ok(infra.project_context(repository))

        tm.that(observed.runtime, eq=expected)

    @staticmethod
    @pytest.mark.parametrize("directory", [Path(), Path(".."), Path("/outside")])
    def test_resolution_directories_stay_within_the_runtime(directory: Path) -> None:
        """Configuration cannot redirect a resolver view to a foreign runtime."""
        payload = config.Infra.codegen.make.uv_resolution.model_dump()
        payload["local_directory"] = directory

        with pytest.raises(m.ValidationError):
            m.Infra.MakeUvResolutionSpec.model_validate(payload)

    @pytest.mark.parametrize("ci", [False, True])
    def test_attached_member_runtime_owner(
        self,
        tmp_path: Path,
        ci: bool,
    ) -> None:
        """Attached members inherit independently of the gate partition."""
        workspace = tmp_path / "workspace"
        origin = tmp_path / "origin"
        workspace.mkdir()
        origin.mkdir()
        u.Tests.initialize_git_repo(workspace)
        u.Tests.initialize_git_repo(origin)
        tm.ok(
            u.Cli.run_checked(
                (
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    str(origin),
                    "member",
                ),
                cwd=workspace,
            ),
        )
        member = workspace / "member"
        policy = config.Infra.codegen.make.ci
        original = os.environ.get(policy.variable)
        try:
            os.environ[policy.variable] = policy.value if ci else policy.local_value
            observed = tm.ok(
                u.Infra.git_repository_root(
                    m.Infra.GitRepoRequest(repo_root=member),
                ),
            )
            tm.that(
                observed.repository_root,
                eq=workspace.resolve(),
            )
        finally:
            u.Tests.restore_env(policy.variable, original)

    @pytest.mark.parametrize("ci", [False, True])
    def test_standalone_runtime_owner(
        self,
        tmp_path: Path,
        ci: bool,
    ) -> None:
        """An independent checkout always owns its locks and environment."""
        repository = tmp_path / "independent"
        repository.mkdir()
        u.Tests.initialize_git_repo(repository)
        policy = config.Infra.codegen.make.ci
        original = os.environ.get(policy.variable)
        try:
            os.environ[policy.variable] = policy.value if ci else policy.local_value
            observed = tm.ok(
                u.Infra.git_repository_root(
                    m.Infra.GitRepoRequest(repo_root=repository),
                ),
            )
            tm.that(observed.repository_root, eq=repository.resolve())
        finally:
            u.Tests.restore_env(policy.variable, original)

    def test_workspace_packages_follow_runtime_dependencies(
        self,
        tmp_path: Path,
    ) -> None:
        """Source binding follows provider-before-consumer order."""
        provider = u.Tests.repository_ref(
            "fixture-provider",
            path=Path("provider"),
        )
        consumer = u.Tests.repository_ref(
            "fixture-consumer",
            path=Path("consumer"),
        )
        for repository, dependencies in (
            (provider, ()),
            (consumer, (provider.distribution,)),
        ):
            root = tmp_path / repository.path
            root.mkdir()
            (root / "pyproject.toml").write_text(
                "[project]\n"
                f'name = "{repository.distribution}"\n'
                'version = "1.0.0"\n'
                f"dependencies = {list(dependencies)!r}\n",
                encoding="utf-8",
            )
        ordered = u.Infra.workspace_dependency_order(
            tmp_path,
            (consumer, provider),
        )
        tm.that(
            ordered,
            eq=(provider.distribution, consumer.distribution),
        )
