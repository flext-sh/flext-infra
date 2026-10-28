"""Runtime ownership through real standalone Git roots and submodules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import re
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
        *,
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
            tm.ok(observed.failure)
            tm.ok(u.Infra.runtime_owner_root(root).failure)
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

    @staticmethod
    @pytest.mark.parametrize("excluded", [False, True])
    def test_native_monorepo_owner_retains_the_requested_project(
        tmp_path: Path,
        *,
        excluded: bool,
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
        observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(child))

        owner = child if excluded else root
        tm.that(observed.project_root, eq=child.resolve())
        tm.that(observed.runtime_root, eq=owner.resolve())
        tm.that(observed.resolution_root, eq=owner.resolve())
        tm.that(observed.environment_path, eq=owner / c.Infra.ENVIRONMENT_DIRECTORY)

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

    @staticmethod
    @pytest.mark.parametrize("attached", [False, True])
    def test_resolution_view_preserves_physical_environment(
        tmp_path: Path,
        *,
        attached: bool,
    ) -> None:
        """The elected runtime owns its manifest, lock and physical environment."""
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
        observed = tm.ok(FlextInfraWorkspaceDetector.resolution_context(project))
        expected = workspace.resolve()

        tm.that(observed.project_root, eq=project.resolve())
        tm.that(observed.runtime_root, eq=expected)
        tm.that(observed.environment_path, eq=workspace / c.Infra.ENVIRONMENT_DIRECTORY)
        tm.that(observed.resolution_root, eq=expected)
        tm.that(observed.pyproject_path, eq=expected / c.PYPROJECT_FILENAME)
        tm.that(observed.lock_path, eq=expected / c.Infra.UV_LOCK_FILENAME)

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
    @pytest.mark.parametrize("ci", [False, True])
    def test_attached_member_runtime_owner(
        tmp_path: Path,
        *,
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

    @staticmethod
    @pytest.mark.parametrize("ci", [False, True])
    def test_standalone_runtime_owner(
        tmp_path: Path,
        *,
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

    @staticmethod
    def test_workspace_packages_follow_runtime_dependencies(
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
            (root / c.PYPROJECT_FILENAME).write_text(
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

    @staticmethod
    @pytest.mark.parametrize(
        "invalid",
        ["", "malformed", "duplicate", "cycle", "foreign"],
    )
    def test_workspace_order_uses_owned_projected_manifest(
        tmp_path: Path,
        invalid: str,
    ) -> None:
        """A projected birth supplies bytes without inventing a physical manifest."""
        provider = u.Tests.repository_ref("fixture-provider", path=Path("provider"))
        consumer = u.Tests.repository_ref("fixture-consumer", path=Path())
        provider_root = tmp_path / provider.path
        provider_root.mkdir()
        (provider_root / c.PYPROJECT_FILENAME).write_text(
            "[project]\n"
            f'name = "{provider.distribution}"\n'
            f"dependencies = "
            f"{[consumer.distribution] if invalid == 'cycle' else []!r}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        path = tmp_path / c.PYPROJECT_FILENAME
        before = tm.ok(u.Cli.atomic_read_binary_file_state(path))
        plan = m.Infra.CodegenFilePlan(
            project=tmp_path.parent if invalid == "foreign" else tmp_path,
            path=path,
            before=before,
            desired_content=(
                b"[project"
                if invalid == "malformed"
                else (
                    "[project]\n"
                    f'name = "{consumer.distribution}"\n'
                    f"dependencies = {[provider.distribution]!r}\n"
                ).encode(c.DEFAULT_ENCODING)
            ),
            desired_mode=0o644,
        )
        with pytest.raises(
            ValueError, match=rf"{re.escape(c.PYPROJECT_FILENAME)}' not found"
        ):
            u.Infra.workspace_dependency_order(tmp_path, (consumer, provider))
        if invalid:
            messages = {
                "malformed": "invalid planned manifest",
                "duplicate": "duplicate planned manifest paths",
                "cycle": "cyclic dependency graph",
                "foreign": "planned manifest has no owning payload",
            }
            with pytest.raises(ValueError, match=messages[invalid]):
                u.Infra.workspace_dependency_order(
                    tmp_path,
                    (consumer, provider),
                    planned_manifests=(
                        (plan, plan) if invalid == "duplicate" else (plan,)
                    ),
                )
        else:
            tm.that(
                u.Infra.workspace_dependency_order(
                    tmp_path,
                    (consumer, provider),
                    planned_manifests=(plan,),
                ),
                eq=(provider.distribution, consumer.distribution),
            )
        tm.ok(not path.exists())
