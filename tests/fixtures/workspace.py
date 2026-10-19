"""Workspace and Rope fixtures for FLEXT infra tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from flext_infra import config, infra, p
from tests import c, t, tm, u


@pytest.fixture
def rope_sibling_scopes(
    tmp_path: Path,
) -> t.Pair[t.Pair[Path, Path], t.Pair[Path, Path]]:
    """Declare sibling consumers sharing one structural Rope root.

    Returns:
        The governed root and source package for each independent consumer.

    """
    return (
        u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="rope-producer",
            package_name="rope_producer",
        ),
        u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="rope-consumer",
            package_name="rope_consumer",
        ),
    )


@pytest.fixture
def rope_contract_consumer(
    tmp_path: Path,
) -> Iterator[t.Pair[p.Infra.RopeWorkspaceDsl, Path]]:
    """Compose the inherited workspace factory with a real public Rope session.

    Yields:
        The live workspace and its isolated consumer source path.

    """
    root, package = u.Tests.create_lazy_init_workspace(tmp_path)
    with infra.rope_workspace(root) as workspace:
        yield workspace, package / "consumer.py"


@pytest.fixture
def rope_workspace(tmp_path: Path) -> Iterator[p.Infra.RopeWorkspaceDsl]:
    """Provide one real Rope workspace through the public composition root.

    Yields:
        Each ``p.Infra.RopeWorkspaceDsl``.

    """
    with infra.rope_workspace(tmp_path) as workspace:
        yield workspace


@pytest.fixture
def constants_workspace(tmp_path: Path) -> t.Pair[Path, Path]:
    """Use the shared real project factory for constants phase consumers.

    Returns:
        The governed workspace root and its package directory.

    """
    return u.Tests.create_lazy_init_workspace(tmp_path)


@pytest.fixture
def constant_candidate(
    constants_workspace: t.Pair[Path, Path],
) -> t.Tests.SourceCandidate:
    """Publish a public constants plan only after its complete fixed-point check.

    Returns:
        A factory that checks and publishes the complete source candidate.

    """
    root, _package = constants_workspace

    def candidate(
        sources: t.MappingKV[Path, str], expected_paths: t.VariadicTuple[Path]
    ) -> t.MappingKV[Path, str]:
        """Validate the phase through its public entry point.

        Returns:
            The published sources after a proven fixed point.

        """
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as workspace:
            phase = c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=workspace, sources=sources
                )
            )
            tm.that(tuple(edit.file_path for edit in edits), eq=expected_paths)
            proposed = {
                **sources,
                **{edit.file_path: edit.updated_source for edit in edits},
            }
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        phase, rope_workspace=workspace, sources=proposed
                    )
                ),
                empty=True,
            )
        for path, source in proposed.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        return proposed

    return candidate


@pytest.fixture
def infra_test_workspace(tmp_path: Path) -> Path:
    """Create a minimal typed project workspace for public service tests.

    Returns:
        The resulting ``Path``.

    """
    workspace = tmp_path / "workspace"
    src_pkg = workspace / "src" / "infra_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (workspace / "pyproject.toml").write_text(
        "[project]\nname='infra-pkg'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    (workspace / "Makefile").write_text("help:\n\t@pwd\n", encoding="utf-8")
    (src_pkg / "__init__.py").write_text("", encoding="utf-8")
    return workspace


@pytest.fixture
def infra_git_repo(infra_test_workspace: Path) -> Path:
    """Provide a provider-governed clone whose upstream is a local bare repo.

    Conformance reads this repository twice and both reads must agree. Detection
    only accepts a remote whose host and organization match the provider, while
    integration-branch discovery reads the already materialized tracking ref.
    Declaring the real upstream URL satisfies detection but grades the fixture
    against the live repository; declaring a local path fails detection outright.
    The fixture therefore declares the provider URL and rewrites it to a local
    bare origin through Git's own ``url.<base>.insteadOf`` mechanism. Fixture
    setup materializes the tracking ref once; conformance itself stays offline.

    Returns:
        The resulting ``Path``.

    """
    repo = infra_test_workspace / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    # The governed tree above the clone carries the committed Mise
    # declaration and lock that activate its locked tools.
    u.Tests.copy_tracked_mise_seeds(infra_test_workspace.parent)
    # The repository carries its own committed lock: the declaration the
    # conform publishes into it resolves only against its sibling mise.lock.
    u.Tests.seed_locked_taplo(repo)
    baseline_file = repo / ".infra-baseline"
    baseline_file.write_text("baseline\n", encoding="utf-8")
    u.Tests.write_project_beads_config(repo, config.Infra.name)
    upstream = u.Tests.repository_ref(config.Infra.name).url
    origin = infra_test_workspace / "origin.git"
    origin.mkdir(parents=True, exist_ok=True)
    u.Tests.git_bootstrap(origin, ("init", "--bare"))
    u.Tests.initialize_git_repo(repo, origin_url=upstream)
    u.Tests.git_bootstrap(
        repo,
        ("config", "--local", f"url.{origin}.insteadOf", upstream),
    )
    u.Tests.git_bootstrap(
        repo,
        (
            "push",
            "-q",
            c.Infra.GIT_ORIGIN,
            f"HEAD:refs/heads/{u.Tests.provider_branch()}",
        ),
    )
    u.Tests.git_bootstrap(
        repo,
        (
            "fetch",
            "-q",
            c.Infra.GIT_ORIGIN,
            (
                f"+refs/heads/{u.Tests.provider_branch()}:refs/remotes/origin/"
                f"{u.Tests.provider_branch()}"
            ),
        ),
    )
    return repo


@pytest.fixture
def rope_project(tmp_path: Path) -> Iterator[t.Infra.RopeProject]:
    """Shared minimal rope project for refactor unit tests.

    Yields:
        Each ``t.Infra.RopeProject``.

    """
    project = u.Infra.init_rope_project(tmp_path)
    yield project
    project.close()
