"""Runtime ownership through real standalone Git roots and submodules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import config
from tests import m, tm, u


class TestsFlextInfraRuntimeRoot:
    """The execution context elects exactly one lock and environment owner."""

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
