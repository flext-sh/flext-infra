"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
import time
import tomllib
from difflib import unified_diff
from pathlib import Path

import pytest
from filelock import UnixFileLock
from flext_infra import config, main
from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenProjectNew
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.services.cli_routes_codegen import CodegenRoutes
from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_tests import tm

from tests import c, m, p, r, t, u


_CAPTURE_MODULE_OUTPUT = (
    # Run the real ``flext_infra`` module entry with its stage output mirrored
    # into a file, so a test can observe the child's progress while it runs:
    # the typed process owner captures pipes only once the child has exited.
    "import runpy, sys\n"
    "log = open(sys.argv[1], 'w', buffering=1, encoding='utf-8')\n"
    "sys.stdout = log\n"
    "sys.stderr = log\n"
    "sys.argv = ['flext_infra', *sys.argv[2:]]\n"
    "runpy.run_module('flext_infra', run_name='__main__', alter_sys=True)\n"
)


def _text_if_present(path: Path) -> str:
    """Return the file's text, or an empty string before the child created it."""
    return path.read_text(encoding="utf-8") if path.is_file() else ""


pytestmark = pytest.mark.slow


def _conform_target(
    root: Path, repository: m.Infra.RepositoryRef, *, make_profile: c.Infra.MakeProfile
) -> m.Infra.RepositoryConformTarget:
    """Build a typed rendering target from the same provider SSOT as production."""
    provider = tm.ok(
        u.Infra.repository_provider(repository, config.Infra.codegen.providers)
    )
    return m.Infra.RepositoryConformTarget(
        repository=repository,
        root=root,
        make_profile=make_profile,
        beads=u.Tests.beads_project(repository.name),
        canonical_project_name=repository.distribution,
        baseline_branch=provider.branch,
        ci_enabled=True,
        technical_branch_patterns=(
            config.Infra.codegen.branch_policy.technical_branch_patterns
        ),
        governed_branch_patterns=(
            config.Infra.codegen.branch_policy.governed_branch_patterns
        ),
    )


def _standalone_workspace(root: Path) -> m.Infra.WorkspaceSpec:
    """Load the smallest repository-local topology for conform tests."""
    return u.Tests.standalone_workspace(root)


def _apply_conform_surface(
    root: Path, workspace: m.Infra.WorkspaceSpec, surface: c.Infra.CodegenConformSurface
) -> None:
    """Materialize one exact public conform surface for a focused test."""
    tm.ok(
        FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=surface,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            initial_workspace=workspace,
        )
    )


def _project_tree(root: Path) -> tuple[tuple[str, bytes], ...]:
    """Return the versionable project tree independently of Git test fixtures."""
    return tuple(
        sorted(
            (path.relative_to(root).as_posix(), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.relative_to(root).parts
            and ".infra-baseline" not in path.relative_to(root).parts
        )
    )


def _project_tree_diff(
    expected: tuple[tuple[str, bytes], ...], actual: tuple[tuple[str, bytes], ...]
) -> str:
    """Render only differing generated files when a fixed-point contract fails."""
    expected_files = dict(expected)
    actual_files = dict(actual)
    return "\n".join(
        line
        for path in sorted(expected_files.keys() | actual_files.keys())
        if expected_files.get(path) != actual_files.get(path)
        for line in unified_diff(
            expected_files.get(path, b"").decode(errors="replace").splitlines(),
            actual_files.get(path, b"").decode(errors="replace").splitlines(),
            fromfile=f"created/{path}",
            tofile=f"conformed/{path}",
            lineterm="",
        )
    )


def _seed_infra_package_tree(root: Path) -> None:
    """Seed the minimal flext-infra tree (pyproject, src package, tests package).

    The conform templates materialize tests/fixtures/ci/docker/*, and the
    existing-tree tooling render discovers python roots from directories that
    exist on disk (env_dirs). Seeding tests/ makes the first render match the
    post-apply fixed point.
    """
    dist = u.Tests.repository_ref(config.Infra.name).distribution
    tm.ok(
        u.Cli.atomic_write_text_file(
            root / "pyproject.toml",
            f'[project]\nname = "{dist}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n',
        )
    )
    package_init = root / "src" / "flext_infra" / "__init__.py"
    package_init.parent.mkdir(parents=True, exist_ok=True)
    tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
    tests_init = root / "tests" / "__init__.py"
    tests_init.parent.mkdir(parents=True, exist_ok=True)
    tm.ok(u.Cli.atomic_write_text_file(tests_init, ""))
    # The full surface validates the committed Mise seeds instead of minting
    # them, so a governed fixture tree carries them exactly as a repository does.
    u.Tests.copy_tracked_mise_seeds(root)


class TestCodegenConform:
    """Prove one SSOT for project creation and existing-tree conformance."""

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            ("body\n<<<<<<< incoming\n", "<<<<<<< incoming"),
            ("body\n||||||| base\nancestor\n", "||||||| base"),
            ("# Title\n=======\n", None),
        ],
        ids=("two_way", "diff3", "setext_heading"),
    )
    def test_merge_control_detection_uses_public_utility(
        self, content: str, expected: str | None
    ) -> None:
        """Recognize control lines without misclassifying Markdown content."""
        tm.that(u.Infra.first_merge_conflict_marker(content), eq=expected)

    @pytest.mark.slow
    def test_apply_recovers_declared_managed_pyproject_conflict(
        self, infra_git_repo: Path
    ) -> None:
        """Repair a committed managed block through the normal apply plan."""
        root = infra_git_repo
        distribution = u.Tests.repository_ref(config.Infra.name).distribution
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "\n"
            "[tool.pytest.ini_options]\n"
            'addopts = ["--timeout=10"]\n',
            encoding="utf-8",
        )
        package_init = root / "src" / distribution.replace("-", "_") / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        package_init.write_text("", encoding="utf-8")

        applied = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.PYPROJECT,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.ok(applied)
        rendered = (root / "pyproject.toml").read_text(encoding="utf-8")
        tm.that(rendered, lacks="<<<<<<<")
        payload = tomllib.loads(rendered)
        addopts = payload["tool"]["pytest"]["ini_options"]["addopts"]
        tm.that(
            addopts,
            has=f"--timeout={config.Infra.tooling.tools.pytest.case_timeout_seconds}",
        )

    @pytest.mark.slow
    def test_branch_ancestry_accepts_active_merge_parent(self, tmp_path: Path) -> None:
        root = tmp_path / "repository"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        baseline = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "update-ref", "refs/remotes/origin/0.12.0-dev", baseline],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "remote", "set-url", "origin", str(tmp_path / "missing")],
                cwd=root,
            )
        )
        empty_tree = tm.ok(u.Cli.capture(["git", "mktree"], cwd=root))
        divergent = tm.ok(
            u.Cli.capture(
                ["git", "commit-tree", empty_tree, "-m", "Create divergent local line"],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "checkout", "-B", "0.12.0-dev", divergent], cwd=root
            )
        )
        divergent_check = tm.ok(
            u.Cli.run_raw(
                ["git", "merge-base", "--is-ancestor", baseline, divergent], cwd=root
            )
        )
        tm.that(divergent_check.exit_code, eq=1)
        repository = u.Tests.repository_ref("flext-infra").model_copy(
            update={"path": Path()}
        )
        workspace = m.Infra.WorkspaceSpec(
            name=repository.name,
            beads=u.Tests.beads_project(repository.name),
            repository=repository,
            project=u.Tests.project_spec(repository.name),
        )
        (root / "pyproject.toml").write_text(
            f"[project]\nname = '{repository.distribution}'\nversion = '0.1.0'\n",
            encoding="utf-8",
        )
        package = root / "src" / repository.distribution.replace("-", "_")
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        )

        before_merge = tm.ok(service.plan(request)).branch_ancestry[0]
        divergent_current = next(
            reference
            for reference in before_merge.references
            if reference.reference == "refs/heads/0.12.0-dev"
        )
        tm.that(divergent_current.ancestor, eq=False)

        merge_head = tm.ok(
            u.Cli.capture(["git", "rev-parse", "--git-path", "MERGE_HEAD"], cwd=root)
        )
        (root / merge_head).write_text(f"{baseline}\n", encoding="utf-8")
        during_merge = tm.ok(service.plan(request)).branch_ancestry[0]
        merging_current = next(
            reference
            for reference in during_merge.references
            if reference.reference == "refs/heads/0.12.0-dev"
        )

        tm.that(merging_current.ancestor, eq=True)

    def test_branch_ancestry_anchors_baseline_to_triggering_commit(
        self, tmp_path: Path
    ) -> None:
        """A concurrent publisher on the lane must not fail a linear commit.

        flext-9ehwb (run 31218338222). ``refs/remotes/origin/<lane>`` is the
        remote's LIVE tip: ``actions/checkout`` fetches at job start, so the tip
        advances whenever another actor publishes while this run waits in the
        queue. Gating against it asks whether the commit already absorbed work
        published AFTER it was written -- false by construction for a perfectly
        linear commit, which then fails with "does not descend from".

        The baseline is therefore anchored to ``merge-base(live_tip,
        GITHUB_SHA)``: the lane point the triggering commit actually knew.
        Concurrent publishers move the tip; they never move that merge base.

        The repository here reproduces the race exactly: HEAD is linear on top
        of the lane, and the remote tip then advances by one unrelated commit.
        """
        root = tmp_path / "repository"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        lane_point = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "checkout", "-B", "0.12.0-dev", lane_point], cwd=root
            )
        )
        # Our commit: written linearly on top of the lane as it existed.
        (root / "ours.txt").write_text("ours\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "ours.txt"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-m", "Our linear commit on the lane"], cwd=root
            )
        )
        triggering_sha = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=root))
        # A concurrent actor publishes to the same lane while our run queues,
        # so the fetched remote tip moves past the point we branched from.
        empty_tree = tm.ok(u.Cli.capture(["git", "mktree"], cwd=root))
        concurrent_tip = tm.ok(
            u.Cli.capture(
                [
                    "git",
                    "commit-tree",
                    empty_tree,
                    "-p",
                    lane_point,
                    "-m",
                    "Concurrent publisher advances the lane",
                ],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "update-ref", "refs/remotes/origin/0.12.0-dev", concurrent_tip],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "remote", "set-url", "origin", str(tmp_path / "missing")],
                cwd=root,
            )
        )
        # The live tip is genuinely NOT an ancestor of our commit: this is the
        # exact state the old gate rejected.
        live_tip_check = tm.ok(
            u.Cli.run_raw(
                ["git", "merge-base", "--is-ancestor", concurrent_tip, triggering_sha],
                cwd=root,
            )
        )
        tm.that(live_tip_check.exit_code, eq=1)

        repository = u.Tests.repository_ref("flext-infra").model_copy(
            update={"path": Path()}
        )
        workspace = m.Infra.WorkspaceSpec(
            name=repository.name,
            beads=u.Tests.beads_project(repository.name),
            repository=repository,
            project=u.Tests.project_spec(repository.name),
        )
        (root / "pyproject.toml").write_text(
            f"[project]\nname = '{repository.distribution}'\nversion = '0.1.0'\n",
            encoding="utf-8",
        )
        package = root / "src" / repository.distribution.replace("-", "_")
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        )

        with tm.scope(env={c.Infra.ENV_VAR_GITHUB_SHA: triggering_sha}):
            anchored = tm.ok(service.plan(request)).branch_ancestry[0]

        current = next(
            reference
            for reference in anchored.references
            if reference.reference == "refs/heads/0.12.0-dev"
        )
        tm.that(current.ancestor, eq=True)
        tm.that(anchored.baseline_sha, eq=lane_point)

    def test_branch_ancestry_skips_triggering_sha_in_submodule_context(
        self, tmp_path: Path
    ) -> None:
        """GITHUB_SHA from the superproject must not break submodule ancestry.

        In CI, GITHUB_SHA is the superproject's PR merge commit, which does
            not exist inside a submodule's object database. ``git merge-base``
            then fails with exit 128 ("Not a valid commit name"), breaking
            ``gen check`` for every governed submodule (PR #187).

        When triggering_sha does not resolve locally the gate must skip the
        merge-base pin and fall back to the live baseline tip, the same
            behavior a local (non-CI) checkout would use.
        """
        root = tmp_path / "repository"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        lane_point = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "checkout", "-B", "0.12.0-dev", lane_point], cwd=root
            )
        )
        (root / "ours.txt").write_text("ours\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "ours.txt"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-m", "Our commit on the lane"], cwd=root
            )
        )
        # GITHUB_SHA is a SHA that does NOT exist in this repo (simulating a
        # superproject merge commit visible only at the workspace root).
        foreign_sha = "9" * 40
        tm.that(
            u.Cli.run_raw(
                ["git", "cat-file", "-t", foreign_sha], cwd=root
            ).value.exit_code,
            eq=128,
        )
        repository = u.Tests.repository_ref("flext-infra").model_copy(
            update={"path": Path()}
        )
        workspace = m.Infra.WorkspaceSpec(
            name=repository.name,
            beads=u.Tests.beads_project(repository.name),
            repository=repository,
            project=u.Tests.project_spec(repository.name),
        )
        (root / "pyproject.toml").write_text(
            f"[project]\nname = '{repository.distribution}'\nversion = '0.1.0'\n",
            encoding="utf-8",
        )
        package = root / "src" / repository.distribution.replace("-", "_")
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        )

        with tm.scope(env={c.Infra.ENV_VAR_GITHUB_SHA: foreign_sha}):
            anchored = tm.ok(service.plan(request)).branch_ancestry[0]
        tm.that(anchored.baseline_sha, eq=lane_point)

    def test_branch_ancestry_skips_bare_main_worktree_entry(
        self, tmp_path: Path
    ) -> None:
        """A bare main worktree (Gas Town rig .repo.git) must not fail the plan.

        `git worktree list --porcelain` lists the bare repository itself as a
        worktree entry carrying only the `bare` attribute — no HEAD line. The
        ancestry parser used to reject that block with "worktree has no HEAD";
        it must skip it and keep planning.
        """
        bare = tmp_path / "repo.git"
        tm.ok(u.Cli.run_checked(["git", "init", "-b", "dev", "--bare", str(bare)]))
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(bare),
                "config",
                "user.email",
                "tests@flext.local",
            ])
        )
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(bare),
                "config",
                "user.name",
                "Flext Tests",
            ])
        )
        empty_tree = tm.ok(u.Cli.capture(["git", "-C", str(bare), "mktree"]))
        seed = tm.ok(
            u.Cli.capture([
                "git",
                "-C",
                str(bare),
                "commit-tree",
                empty_tree,
                "-m",
                "seed",
            ])
        )
        checkout = tmp_path / "checkout"
        tm.ok(
            u.Cli.run_checked(
                ["git", "-C", str(bare), "worktree", "add", str(checkout), seed],
                cwd=tmp_path,
            )
        )
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(checkout),
                "update-ref",
                "refs/remotes/origin/0.12.0-dev",
                seed,
            ])
        )
        repository = u.Tests.repository_ref("flext-infra").model_copy(
            update={"path": Path()}
        )
        workspace = m.Infra.WorkspaceSpec(
            name=repository.name,
            beads=u.Tests.beads_project(repository.name),
            repository=repository,
            project=u.Tests.project_spec(repository.name),
        )
        (checkout / "pyproject.toml").write_text(
            f"[project]\nname = '{repository.distribution}'\nversion = '0.1.0'\n",
            encoding="utf-8",
        )
        package = checkout / "src" / repository.distribution.replace("-", "_")
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        request = m.Infra.CodegenConformRequest(
            root=checkout,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(
            repository_root=checkout, request=request, initial_workspace=workspace
        )

        plan = tm.ok(service.plan(request))

        tm.that(
            any(
                entry.reference == "refs/remotes/origin/0.12.0-dev"
                for entry in plan.branch_ancestry[0].references
            ),
            eq=True,
        )

    # This end-to-end scenario scaffolds a project and runs its console entry
    # point in a fresh interpreter. The slow marker opts into the single
    # config-owned slow-item budget; tests must not restate that policy locally.
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("kind", "name"),
        [
            (c.Infra.ProjectKind.EXTERNAL, "flext-demo"),
            (c.Infra.ProjectKind.INTERNAL, "flext-member"),
        ],
    )
    def test_new_project_is_complete_and_idempotent(
        self, tmp_path: Path, kind: c.Infra.ProjectKind, name: str
    ) -> None:
        root = tmp_path / kind.value
        service = FlextInfraCodegenProjectNew(
            name=name,
            kind=kind,
            output_root=root,
            provider="flext-sh",
            beads_workspace=name,
            beads_database=name.replace("-", "_"),
            beads_issue_prefix=name,
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        )
        first = service.execute()
        first_result = tm.ok(first)
        tm.that(bool(first_result.written_files), eq=True)
        tm.that(
            tuple(file.path for file in first_result.plan.files if file.changed), eq=()
        )
        makefile_plan = next(
            item
            for item in first_result.plan.files
            if item.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(
            makefile_plan.rendered,
            has=f"MAKE_PROFILE := {c.Infra.MakeProfile.STANDALONE.value}",
        )
        tm.that(first_result.plan.request.root, eq=root.resolve())
        tm.that((root / "config" / "workspace.yaml").exists(), eq=False)
        tm.that((root / "config" / "beads.yaml").is_file(), eq=True)
        tm.that((root / "pyproject.toml").is_file(), eq=True)
        tm.that((root / ".env.example").is_file(), eq=True)
        package_name = name.replace("-", "_")
        pythonpath = os.pathsep.join(
            part
            for part in (str(root / "src"), os.environ.get("PYTHONPATH", ""))
            if part
        )
        process = u.Cli.capture(
            [sys.executable, "-m", package_name, "ping"],
            cwd=root,
            env={**os.environ, "PYTHONPATH": pythonpath},
            timeout=c.Infra.TIMEOUT_DEFAULT,
        )
        tm.ok(process)
        tm.that(process.value, eq="✅ pong")

    @pytest.mark.slow
    def test_generated_make_uses_unpinned_environment_uv(
        self, infra_git_repo: Path
    ) -> None:
        """Generated Make delegates uv selection to the caller environment."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.MAKEFILE)
        selected = u.Cli.run_raw(
            ["make", "-C", str(root), "--dry-run", "status"],
            remove_env_keys=("MAKEFLAGS",),
        )

        selected_process = tm.ok(selected)
        selected_output = selected_process.stdout + selected_process.stderr
        tm.that(selected_process.exit_code, eq=0)
        tm.that(selected_output, has="uv --version")
        tm.that(selected_output, lacks="uv@")
        tm.that(selected_output, lacks="UV_VERSION")
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile, has="UV ?= uv")
        tm.that(makefile, lacks="UV_VERSION")
        tm.that(makefile, lacks="uv@")
        tm.that(makefile, lacks="mise exec")

    @pytest.mark.slow
    def test_python_root_outside_env_dirs_still_reaches_a_fixed_point(
        self, infra_git_repo: Path
    ) -> None:
        """The gen verb converges for a Python root beyond declarative env_dirs.

        Two derivations used to select the pyright execution environments: the
        dependency command discovered roots ON DISK, while conform planned them
        from declarative ``env_dirs``. A project owning a Python directory
        outside that list therefore oscillated between two writers. Conform is
        the sole generation owner, so it must discover and preserve the extra
        root by itself and immediately reach a fixed point.
        """
        root = infra_git_repo
        _seed_infra_package_tree(root)
        # The defect needs a Python root the declarative env_dirs never lists.
        extra_root = "tools"
        module = root / extra_root / "maintenance.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(module, "VALUE = 1\n"))
        tm.that(extra_root in u.Infra.discover_python_dirs(root), eq=True)
        tm.that(
            extra_root in config.Infra.tooling.tools.pyright.path_rules.env_dirs,
            eq=False,
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed python root beyond env_dirs"],
                cwd=root,
            )
        )

        applied = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.ok(applied)

        fixed_point = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(fixed_point)
        tm.that(fixed_point.value.written_files, eq=())

    @pytest.mark.slow
    def test_empty_rendered_directory_is_not_a_python_root(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        _seed_infra_package_tree(root)
        (root / "scripts").mkdir()

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.ok(result)
        payload = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        tm.that(
            payload["tool"]["pyrefly"]["project-includes"], lacks="scripts/**/*.py*"
        )
        tm.that(payload["tool"]["pyright"]["include"], lacks="scripts")

    # Why (suite budget): two conform apply cycles plus a check over a full
    # managed tree on a real git repo; the per-case wall only holds idle.
    @pytest.mark.slow
    def test_manifestless_existing_root_plans_artifacts_without_project_spec(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        repository = u.Tests.repository_ref(
            config.Infra.name, role=c.Infra.MakeProfile.STANDALONE
        )
        local_repository = repository.model_copy(update={"path": Path()})
        create_only = {
            "LICENSE": "existing license\n",
            "README.md": "# Existing repository\n",
            "custom.mk": "_custom_status_diagnostics:\n\t@true\n",
        }
        _seed_infra_package_tree(root)
        managed_source = root / "config" / "managed-artifacts.yaml"
        managed_source.parent.mkdir()
        tm.ok(u.Cli.atomic_write_text_file(managed_source, "ManagedArtifacts: {}\n"))
        for relative, content in create_only.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed manifest-less tree"],
                cwd=root,
            )
        )

        derived = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(derived.repository, eq=local_repository)
        tm.that(derived.project, eq=None)

        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        initial_plan = tm.ok(
            FlextInfraCodegenConform(repository_root=root).plan(request)
        )
        plans = {
            file.path.relative_to(root).as_posix(): file for file in initial_plan.files
        }
        mise_sources = plans[c.Infra.MISE_TOML_FILENAME].source_states
        tm.that(
            f"{c.Infra.MISE_TOML_FILENAME}.j2"
            in tuple(source.path.name for source in mise_sources),
            eq=True,
        )
        tm.that(
            managed_source in tuple(source.path for source in mise_sources), eq=True
        )
        tm.that(all(source.content is not None for source in mise_sources), eq=True)
        env_plan = plans[".env.example"]
        tm.that(env_plan.owner, eq="codegen")
        tm.that(env_plan.policy, eq="create-only")
        tm.that(env_plan.changed, eq=False)
        tm.that(env_plan.blocked, eq=False)
        tm.that(env_plan.current_sha256, eq="")
        tm.that((root / ".env.example").exists(), eq=False)
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.that(plans[required].changed, eq=True)

        applied = FlextInfraCodegenConform.execute_request(request)
        tm.ok(applied)
        for relative, content in create_only.items():
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        tm.that((root / "Makefile").is_file(), eq=True)
        tm.that((root / ".mise.toml").is_file(), eq=True)
        tm.that((root / ".python-version").is_file(), eq=True)
        tm.that((root / ".gitignore").is_file(), eq=True)
        tm.that((root / ".env.example").exists(), eq=False)
        tm.that(root / ".env.example" in applied.value.written_files, eq=False)

        fixed_point = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(fixed_point)
        tm.that(fixed_point.value.written_files, eq=())

    def test_workspace_uv_plan_owns_root_lock_and_editable_repositories(
        self, tmp_path: Path
    ) -> None:
        """Keep workspace setup data complete without Make-side re-derivation."""
        root_repository = u.Tests.repository_ref("flext")
        member = u.Tests.repository_ref("flext-core", path=Path("flext-core"))
        workspace = m.Infra.WorkspaceSpec(
            name="flext",
            beads=u.Tests.beads_project("flext"),
            repository=root_repository,
            project=u.Tests.project_spec("flext"),
            declared_repositories=(member,),
        )
        root = tmp_path / "flext"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        ).plan(request)
        tm.ok(planned)
        environment = planned.value.uv_environments[0]
        tm.that(environment.environment_root, eq=root.resolve())
        tm.that(environment.lock_path, eq=root.resolve() / "uv.lock")
        tm.that(environment.groups, eq=("dev", "codegen", "workspace"))
        tm.that(
            tuple(item.name for item in environment.editable_repositories),
            eq=("flext-core",),
        )

    @pytest.mark.slow
    def test_repository_root_catalog_profile_preserves_platform_coverage(
        self, tmp_path: Path
    ) -> None:
        """Route an arbitrary repository root through its typed catalog profile."""
        provider = u.Tests.provider()
        repository = u.Tests.repository_ref("arbitrary-root").model_copy(
            update={
                "name": "arbitrary-root",
                "distribution": "arbitrary-root",
                "url": f"{provider.base_url}/arbitrary-root.git",
                "path": Path(),
                "role": c.Infra.MakeProfile.WORKSPACE,
                "package": False,
                "editable": False,
            }
        )
        workspace = m.Infra.WorkspaceSpec(
            name="arbitrary-root",
            beads=u.Tests.beads_project("arbitrary-root"),
            repository=repository,
            project=u.Tests.project_spec("arbitrary-root"),
        )
        root = tmp_path / "arbitrary-root"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        )

        first = tm.ok(service.plan(request))
        second = tm.ok(service.plan(request))
        first_pyproject = next(
            item for item in first.files if item.path.name == c.Infra.PYPROJECT_FILENAME
        )
        second_pyproject = next(
            item
            for item in second.files
            if item.path.name == c.Infra.PYPROJECT_FILENAME
        )
        rendered_tooling = tomllib.loads(first_pyproject.rendered)["tool"]
        report = rendered_tooling["coverage"]["report"]
        addopts = set(rendered_tooling["pytest"]["ini_options"]["addopts"])
        pytest_policy = config.Infra.tooling.tools.pytest

        tm.that(second_pyproject.rendered, eq=first_pyproject.rendered)
        tm.that(addopts, has=f"--timeout={pytest_policy.case_timeout_seconds}")
        tm.that(addopts, lacks="--session-timeout")
        tm.that(addopts >= set(pytest_policy.standard_addopts), eq=True)
        tm.that(
            report["fail_under"],
            eq=config.Infra.tooling.tools.coverage.fail_under.platform,
        )

    @pytest.mark.slow
    def test_workspace_root_excludes_only_the_distributions_it_declares(
        self, tmp_path: Path
    ) -> None:
        """Route uv exclusions by the declared topology, not the Make profile.

        A content workspace whose submodules are not FLEXT distributions must
        not inherit the FLEXT reverse-edge exclusions: doing so drops a
        dependency its own venv still needs (flext-cee4z). A workspace that
        declares those distributions keeps every exclusion routed to them.
        """
        exclusions = config.Infra.codegen.uv_exclude_dependencies
        member = u.Tests.repository_ref("flext-core", path=Path("flext-core"))
        content = u.Tests.repository_ref("docs-content", path=Path("docs-content"))

        def rendered_excludes(
            name: str, declared: tuple[m.Infra.RepositoryRef, ...]
        ) -> list[t.JsonMapping]:
            workspace = m.Infra.WorkspaceSpec(
                name=name,
                beads=u.Tests.beads_project(name),
                repository=u.Tests.repository_ref(
                    name, role=c.Infra.MakeProfile.WORKSPACE
                ),
                project=u.Tests.project_spec(name),
                declared_repositories=declared,
            )
            root = tmp_path / name
            request = m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
            planned = tm.ok(
                FlextInfraCodegenConform(
                    repository_root=root, request=request, initial_workspace=workspace
                ).plan(request)
            )
            pyproject = next(
                item
                for item in planned.files
                if item.path.name == c.Infra.PYPROJECT_FILENAME
            )
            uv_table = tomllib.loads(pyproject.rendered)["tool"]["uv"]
            return list(uv_table.get("exclude-dependencies", []))

        expected_for_member = [
            item
            for item in exclusions
            if item.project in {"flext", member.distribution}
        ]
        tm.that(rendered_excludes("content-root", (content,)), eq=[])
        tm.that(len(rendered_excludes("flext", (member,))), eq=len(expected_for_member))

    @pytest.mark.slow
    def test_project_root_exports_only_declared_upstream_facets(
        self, tmp_path: Path
    ) -> None:
        repository = u.Tests.repository_ref("consumer")
        project = u.Tests.project_spec("consumer").model_copy(
            update={"upstream": "flext_cli"}
        )
        workspace = m.Infra.WorkspaceSpec(
            name="consumer",
            beads=u.Tests.beads_project("consumer"),
            repository=repository,
            project=project,
        )
        root = tmp_path / "consumer"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )

        plan = tm.ok(
            FlextInfraCodegenConform(
                repository_root=root, request=request, initial_workspace=workspace
            ).plan(request)
        )
        package_root = next(
            item
            for item in plan.files
            if item.path == root / "src/consumer/__init__.py"
        )
        tm.that(package_root.rendered, lacks='"r"')

        declared_workspace = workspace.model_copy(
            update={"project": project.model_copy(update={"inherited_facets": ("r",)})}
        )
        declared_plan = tm.ok(
            FlextInfraCodegenConform(
                repository_root=root,
                request=request,
                initial_workspace=declared_workspace,
            ).plan(request)
        )
        declared_root = next(
            item
            for item in declared_plan.files
            if item.path == root / "src/consumer/__init__.py"
        )
        tm.that(declared_root.rendered, has='"r"')
        tm.that(declared_root.rendered, has="from flext_cli import r as r")

    def test_make_context_accepts_manifest_without_project_metadata(
        self, tmp_path: Path
    ) -> None:
        """Build Make context from repository-owned data alone."""
        repository = u.Tests.repository_ref("consumer")
        workspace = m.Infra.WorkspaceSpec(
            name="consumer",
            beads=u.Tests.beads_project("consumer"),
            repository=repository,
        )
        target = _conform_target(
            tmp_path, repository, make_profile=c.Infra.MakeProfile.STANDALONE
        )
        tooling_runtime = tm.ok(
            FlextInfraPyprojectModernizer(
                repository_root=tmp_path, skip_check=True
            ).resolve_tooling_context(
                project_name=repository.distribution,
                package_name=repository.distribution.replace("-", "_"),
                path=tmp_path / "pyproject.toml",
                declared_python_dirs=("src",),
            )
        )
        context = FlextInfraCodegenConform.make_render_context(
            repository,
            target,
            workspace,
            config.Infra.codegen,
            tooling_runtime=tooling_runtime,
        )
        rendered = tm.ok(context)
        tm.that(isinstance(rendered, m.Infra.MakeRenderContext), eq=True)
        tm.that(isinstance(rendered, m.Infra.ProjectRenderContext), eq=False)
        tm.that(rendered.repository_root_rel, eq=".")

    # Why (suite budget): parametrized over both conform modes, each running a
    # full plan/apply cycle on a real git repo; 10s only holds on an idle CPU.
    @pytest.mark.slow
    @pytest.mark.parametrize("mode", tuple(c.Infra.CodegenConformMode))
    def test_public_cli_routes_check_and_apply_to_one_handler(
        self, infra_git_repo: Path, mode: c.Infra.CodegenConformMode
    ) -> None:
        """Execute one public mode without changing an already conform tree."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.MAKEFILE)
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed generated project"],
                cwd=root,
            )
        )
        route = next(
            route
            for route in CodegenRoutes.codegen_routes[c.Infra.CLI_GROUP_CODEGEN]
            if route.name == "conform"
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
        )
        tm.ok(route.handler(request))
        status = tm.ok(u.Cli.capture(["git", "status", "--porcelain"], cwd=root))
        tm.that(status, eq="")

    # Why (suite budget): dependencies-only apply+check runs two full conform
    # cycles on a real git repo; the per-case wall only holds on an idle CPU.
    @pytest.mark.slow
    def test_dependency_surface_excludes_unowned_managed_files(
        self, infra_git_repo: Path
    ) -> None:
        """Plan only dependency metadata when another managed surface is invalid."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(
            root, workspace, c.Infra.CodegenConformSurface.DEPENDENCIES
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk", ".PHONY: public-handler\npublic-handler:\n\t@true\n"
            )
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed generated project"],
                cwd=root,
            )
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.DEPENDENCIES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(repository_root=root, request=request).plan(
            request
        )
        tm.ok(planned)
        tm.that(
            tuple(file.path.name for file in planned.value.files),
            eq=("pyproject.toml",),
        )
        tm.that(tuple(file.changed for file in planned.value.files), eq=(False,))
        exit_code = main([
            "codegen",
            "conform",
            "--root",
            str(root),
            "--what",
            "dependencies",
            "--scope",
            "self",
            "--mode",
            "check",
        ])
        tm.that(exit_code, eq=0)

    # Why (suite budget): full conform cycle plus subprocess make validation;
    # the default case timeout only holds on an idle machine.

    def test_invalid_public_custom_make_fails_without_side_effects(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        custom = root / "custom.mk"
        content = ".PHONY: public-handler\npublic-handler:\n\t@true\n"
        tm.ok(u.Cli.atomic_write_text_file(custom, content))
        policy: m.Infra.CustomHandlerPolicy = (
            config.Infra.codegen.make.custom_handler_policies[
                c.Infra.MakeProfile.STANDALONE
            ]
        )
        result = FlextInfraCodegenConform.validate_custom_make(
            tm.ok(u.Cli.files_read_text(custom)), policy
        )
        tm.fail(result)
        rejection = Path(f"{custom}.rej")
        tm.that(
            result.error or "", has="custom.mk line 1 is not a private custom handler"
        )
        tm.that(rejection.exists(), eq=False)
        tm.that(custom.read_text(encoding="utf-8"), eq=content)

    @pytest.mark.slow
    def test_valid_private_custom_make_has_no_rejection(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        custom = root / "custom.mk"
        tm.ok(
            u.Cli.atomic_write_text_file(
                custom,
                (
                    ".PHONY: \\\n"
                    "\t_custom-propagate \\\n"
                    "\t_custom-activate\n"
                    "_custom-propagate:\n\t@true\n"
                    "_custom-activate:\n\t@true\n"
                ),
            )
        )
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            initial_workspace=workspace,
        )
        tm.ok(result)
        tm.that("WARN:" in capsys.readouterr().out, eq=False)
        tm.that(Path(f"{custom}.rej").exists(), eq=False)

    def test_custom_make_rejects_unterminated_phony_continuation(self) -> None:
        """Fail closed when a multiline private-handler declaration is truncated."""
        policy: m.Infra.CustomHandlerPolicy = (
            config.Infra.codegen.make.custom_handler_policies[
                c.Infra.MakeProfile.STANDALONE
            ]
        )

        result = FlextInfraCodegenConform.validate_custom_make(
            ".PHONY: \\\n\t_custom-propagate \\", policy
        )

        tm.fail(result, has="unterminated .PHONY continuation")

    @pytest.mark.slow
    def test_scaffold_make_runs_pre_and_post_verb_hooks_in_order(
        self, infra_git_repo: Path
    ) -> None:
        """Generated public check runs pre-hook, owner, and post-hook in order."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.MAKEFILE)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: pre-check post-check\n"
                "pre-check:\n\t@echo HOOK_PRE\n"
                "post-check:\n\t@echo HOOK_POST\n",
            )
        )
        # `check` requires a provisioned interpreter, which `make setup` would
        # build. Stub it so this test stays about hook ordering.
        u.Tests.write_executable(
            root / ".venv" / "bin" / "python", "#!/bin/sh\necho HOOK_BODY\n"
        )
        outcome = u.Cli.run_raw(["make", "-C", str(root), "check", "APPLY=Y"])
        output = tm.ok(outcome)
        tm.that(output.exit_code, eq=0)
        combined = output.stdout + output.stderr
        pre_at = combined.find("HOOK_PRE")
        body_at = combined.find("HANDLER_BODY")
        post_at = combined.find("HOOK_POST")
        tm.that(pre_at >= 0 and body_at >= 0 and post_at >= 0, eq=True)
        tm.that(pre_at < body_at, eq=True)
        tm.that(body_at < post_at, eq=True)

    def test_custom_make_accepts_pre_post_verb_hooks(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """custom.mk may append selector-free pre/post verb hooks."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        custom = root / "custom.mk"
        tm.ok(
            u.Cli.atomic_write_text_file(
                custom,
                ".PHONY: pre-check post-check\n"
                "pre-check:\n\t@true\n"
                "post-check:\n\t@true\n",
            )
        )
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            initial_workspace=workspace,
        )
        tm.ok(result)
        tm.that("WARN:" in capsys.readouterr().out, eq=False)
        tm.that(Path(f"{custom}.rej").exists(), eq=False)

    @pytest.mark.slow
    def test_non_regular_custom_make_remains_fatal(self, infra_git_repo: Path) -> None:
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.MAKEFILE)
        tm.ok(u.Cli.files_delete(root / "custom.mk"))
        (root / "custom.mk").mkdir()
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            ),
            initial_workspace=workspace,
        )
        tm.fail(result)
        tm.that(result.error, has="not a regular file")
        tm.that(result.error, has=str(root / "custom.mk"))


class TestScriptDispatchMakefile:
    """Prove per-repo extra verbs and script-dispatch WHAT normalization."""

    @staticmethod
    def _render_root_makefile(
        tmp_path: Path,
        *,
        extra_verbs: tuple[m.Infra.MakeVerbSpec, ...],
        script_dispatch: m.Infra.ScriptDispatchSpec | None,
    ) -> str:
        # The engine is consumer-agnostic, so this fixture models a
        # neutral downstream root and takes its provider from the engine's own
        # configured provider catalog instead of naming a real consumer.
        provider = u.Tests.provider()
        root_repository = m.Infra.RepositoryRef(
            name="demo-root",
            distribution="demo-root",
            url=f"{provider.base_url}/demo-root.git",
            path=Path(),
            # Script dispatch is a generic capability: exercise it on standalone.
            role=c.Infra.MakeProfile.STANDALONE,
            provider=provider.name,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
            extra_verbs=extra_verbs,
            script_dispatch=script_dispatch,
        )
        workspace = m.Infra.WorkspaceSpec(
            name="demo-root",
            beads=u.Tests.beads_project("demo-root"),
            repository=root_repository,
            project=u.Tests.project_spec("demo-root"),
            declared_repositories=(),
        )
        root = tmp_path / "demo-root"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        ).plan(request)
        plan = tm.ok(planned)
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        rendered: str = makefile.rendered
        return rendered

    def test_script_dispatch_repo_routes_extra_verbs(self, tmp_path: Path) -> None:
        """Extra verbs join PUBLIC_VERBS and route by their canonical name."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="incidente",
                    description="Run the incident workflow.",
                    requires_apply=True,
                ),
                m.Infra.MakeVerbSpec(
                    name="charts",
                    description="Run the chart workflow.",
                    requires_apply=True,
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
        )
        # Extra verbs are public targets the dispatcher can reach.
        tm.that("incidente" in rendered, eq=True)
        tm.that("charts" in rendered, eq=True)
        tm.that("WHAT=" in rendered, eq=False)
        tm.that("scripts/dispatch.py" in rendered, eq=True)
        tm.that("_builtin-incidente:" in rendered, eq=True)
        tm.that('"incidente"' in rendered, eq=True)

    def test_repo_without_script_dispatch_routes_declared_custom_verb(
        self, tmp_path: Path
    ) -> None:
        """A declared verb routes to its same-named private custom owner."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="propagate",
                    description="Propagate the installed runtime.",
                    requires_apply=True,
                ),
            ),
            script_dispatch=None,
        )
        tm.that("tr '-' '_'" in rendered, eq=False)
        tm.that("scripts/dispatch.py" in rendered, eq=False)
        tm.that("propagate: _require-environment" in rendered, eq=True)
        tm.that("_builtin-propagate:" in rendered, eq=True)
        tm.that(
            "$(filter _custom-$(1),$(CUSTOM_DECLARED_TARGETS))" in rendered, eq=True
        )
        tm.that(
            "declared operation propagate has no implementation" in rendered, eq=True
        )

    def test_canonical_waza_can_delegate_to_a_repository_custom_owner(
        self, tmp_path: Path
    ) -> None:
        """Every canonical verb may use its declared repository implementation."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        tm.that("waza: _require-environment" in rendered, eq=True)
        tm.that(
            "$(filter _custom-$(1),$(CUSTOM_DECLARED_TARGETS))" in rendered, eq=True
        )

    def test_gen_replaces_codegen_as_the_single_conform_verb(
        self, tmp_path: Path
    ) -> None:
        """``make gen`` is THE conform verb; ``codegen`` no longer exists.

        The convergence spine fuses codegen+conform under the
        single short ``gen`` verb: one verb, one meaning. The old ``codegen``
        Make verb is fully replaced across config, rendered handlers, and the
        regeneration header.
        """
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.that("gen" in verb_names, eq=True)
        tm.that("codegen" in verb_names, eq=False)
        gen = next(verb for verb in make_config.verbs if verb.name == "gen")
        tm.that(gen.requires_apply, eq=True)
        tm.that(hasattr(make_config, "serialization"), eq=False)
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(" gen" in public_line, eq=True)
        tm.that(" codegen" in public_line, eq=False)
        tm.that("_builtin-gen:" in rendered, eq=True)
        tm.that("_builtin-codegen" in rendered, eq=False)
        phony_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith(".PHONY:") and "_builtin-" in line
        )
        tm.that("$(addprefix _builtin-,$(PUBLIC_VERBS))" in phony_line, eq=True)
        body = rendered.split("_builtin-gen:", 1)[1].split("\n\n", 1)[0]
        tm.that(body.count("codegen conform"), eq=1)
        tm.that("--mode apply" in body, eq=True)
        tm.that('codegen layout --workspace "$(PROJECT_ROOT)" --apply' in body, eq=True)
        tm.that(
            'codegen lazy-init --workspace "$(PROJECT_ROOT)" --apply' in body, eq=True
        )
        initialize_body = rendered.split("_builtin-initialize:", 1)[1].split("\n\n", 1)[
            0
        ]
        tm.that(initialize_body.count("codegen lazy-init"), eq=2)
        tm.that("codegen init" in initialize_body, eq=False)
        tm.that("@$(SELF_MAKE) conform APPLY=Y" in body, eq=True)
        tm.that("WHAT=" in rendered, eq=False)
        tm.that("# @flext-regenerate: make gen APPLY=Y" in rendered, eq=True)

    @pytest.mark.parametrize("beads_state", ["absent", "poison"])
    @pytest.mark.parametrize("workspace_state", ["manifest", "manifestless"])
    def test_makefile_surface_reads_only_declared_projection_inputs(
        self, tmp_path: Path, beads_state: str, workspace_state: str
    ) -> None:
        """Apply the public Makefile surface without operational discovery."""
        root = tmp_path / "declared-target"
        if workspace_state == "manifest":
            u.Tests.write_standalone_workspace_manifest(root, "flext-demo")
        package = root / "src" / "flext_demo"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "flext-demo"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "dependencies = []\n"
            "[project.urls]\n"
            'Repository = "https://github.com/flext-sh/flext-demo"\n',
            encoding="utf-8",
        )
        if beads_state == "poison":
            (root / ".beads").write_text(
                "the Makefile projection must never inspect this path\n",
                encoding="utf-8",
            )

        forbidden = root / "forbidden.calls"
        sentinel_bin = root / "sentinel-bin"
        git_binary = shutil.which("git")
        tm.that(git_binary is not None, eq=True)
        for command in ("git", "bd", "mise", "uv"):
            version_passthrough = (
                f'if [ "${{1:-}}" = "version" ]; then exec "{git_binary}" "$@"; fi\n'
                if command == "git"
                else ""
            )
            u.Tests.write_executable(
                sentinel_bin / command,
                "#!/bin/sh\n"
                f"{version_passthrough}"
                f"printf '%s\\n' '{command}' >> '{forbidden}'\n"
                "exit 97\n",
            )
        environment = dict(os.environ)
        environment["PATH"] = f"{sentinel_bin}:{environment['PATH']}"

        invoked = u.Cli.run_raw(
            [
                sys.executable,
                "-m",
                "flext_infra",
                "codegen",
                "conform",
                "--root",
                str(root),
                "--what",
                c.Infra.CodegenConformSurface.MAKEFILE.value,
                "--scope",
                c.Infra.CodegenConformScope.SELF.value,
                "--mode",
                c.Infra.CodegenConformMode.APPLY.value,
            ],
            cwd=root,
            env=environment,
        )

        output = tm.ok(invoked)
        tm.that(
            output.exit_code,
            eq=0,
            msg=f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}",
        )
        tm.that(forbidden.exists(), eq=False)
        makefile = (root / c.Infra.MAKEFILE_FILENAME).read_text(encoding="utf-8")
        tm.that(makefile, has="PROJECT_NAME := flext-demo")
        tm.that(makefile, has=f"MAKE_PROFILE := {c.Infra.MakeProfile.STANDALONE.value}")

    def test_concurrent_makefile_change_is_preserved_before_promotion(
        self, tmp_path: Path
    ) -> None:
        """Reject real concurrent WIP observed while the public CLI waits for owner."""
        root = tmp_path / "declared-target"
        u.Tests.write_standalone_workspace_manifest(root, "flext-demo")
        package = root / "src" / "flext_demo"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "flext-demo"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "dependencies = []\n",
            encoding="utf-8",
        )
        makefile = root / c.Infra.MAKEFILE_FILENAME
        original = b"original Makefile bytes\n"
        makefile.write_bytes(original)
        lock_path = FlextInfraCodegenConform.conform_transaction_lock_path(root)
        child_log = tmp_path / "conform-child.log"
        command = [
            sys.executable,
            "-c",
            _CAPTURE_MODULE_OUTPUT,
            str(child_log),
            "codegen",
            "conform",
            "--root",
            str(root),
            "--what",
            c.Infra.CodegenConformSurface.MAKEFILE.value,
            "--scope",
            c.Infra.CodegenConformScope.SELF.value,
            "--mode",
            c.Infra.CodegenConformMode.APPLY.value,
        ]
        with UnixFileLock(lock_path, fallback_to_soft=False):
            started = tm.ok(
                u.Cli.process_start(command, cwd=root, env={"PYTHONUNBUFFERED": "1"})
            )
            # The child plans against the original bytes and then reports that
            # it is waiting for the transaction owner. That stage line is the
            # observable proof the concurrent edit below lands after planning;
            # a "still alive" probe cannot tell waiting from interpreter startup.
            deadline = time.monotonic() + c.Infra.TIMEOUT_SHORT
            while "stage=wait-transaction-lock" not in _text_if_present(child_log):
                tm.that(
                    started.poll(),
                    eq=None,
                    msg=f"conform exited before the lock:\n{_text_if_present(child_log)}",
                )
                tm.that(
                    time.monotonic() < deadline,
                    eq=True,
                    msg="conform never reached the transaction lock",
                )
                time.sleep(0.05)
            concurrent = b"concurrent human WIP\n"
            makefile.write_bytes(concurrent)
            concurrent_inode = makefile.stat().st_ino
        return_code = tm.ok(started.wait(timeout=c.Infra.TIMEOUT_SHORT))
        output_text = _text_if_present(child_log)

        tm.that(return_code, eq=1, msg=output_text)
        tm.that(output_text, has="Makefile projection changed")
        tm.that(makefile.read_bytes(), eq=concurrent)
        tm.that(makefile.stat().st_ino, eq=concurrent_inode)

    def test_public_apply_rejects_real_source_mutation_before_publication(
        self, infra_git_repo: Path, tmp_path: Path
    ) -> None:
        """Keep every destination unchanged when a planned YAML source changes."""
        root = infra_git_repo
        _seed_infra_package_tree(root)
        managed_source = root / "config" / "managed-artifacts.yaml"
        managed_source.parent.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(managed_source, "ManagedArtifacts: {}\n")
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "add",
                    "--",
                    ".beads",
                    ".infra-baseline",
                    ".mise.toml",
                    "bin",
                    "config",
                    "mise.lock",
                    "pyproject.toml",
                    "src",
                    "tests",
                ],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-m", "Seed source barrier"], cwd=root
            )
        )
        mise_path = root / c.Infra.MISE_TOML_FILENAME
        before = mise_path.read_bytes()
        child_log = tmp_path / "source-barrier-child.log"
        command = [
            sys.executable,
            "-c",
            _CAPTURE_MODULE_OUTPUT,
            str(child_log),
            "codegen",
            "conform",
            "--root",
            str(root),
            "--scope",
            c.Infra.CodegenConformScope.SELF.value,
            "--mode",
            c.Infra.CodegenConformMode.APPLY.value,
        ]
        started = tm.ok(
            u.Cli.process_start(command, cwd=root, env={"PYTHONUNBUFFERED": "1"})
        )
        deadline = time.monotonic() + c.Infra.TIMEOUT_SHORT
        while "stage=templates" not in _text_if_present(child_log):
            tm.that(
                started.poll(),
                eq=None,
                msg=f"conform exited before template planning:\n{_text_if_present(child_log)}",
            )
            tm.that(
                time.monotonic() < deadline,
                eq=True,
                msg="conform never reached template planning",
            )
            time.sleep(0.05)
        tm.ok(
            u.Cli.atomic_write_text_file(
                managed_source,
                "ManagedArtifacts:\n  Gitignore:\n    patterns: [source-mutated/]\n",
            )
        )

        return_code = tm.ok(started.wait(timeout=c.Infra.TIMEOUT_SHORT))
        output_text = _text_if_present(child_log)

        tm.that(return_code, eq=1, msg=output_text)
        tm.that(output_text, has="codegen source")
        tm.that(mise_path.read_bytes(), eq=before)

    def test_makefile_transaction_lock_recovers_after_process_crash(
        self, tmp_path: Path
    ) -> None:
        """Let the kernel release the canonical owner when its process is killed."""
        root = tmp_path / "declared-target"
        root.mkdir()
        lock_path = FlextInfraCodegenConform.conform_transaction_lock_path(root)
        acquired_marker = tmp_path / "child-acquired"
        child = u.Cli.run_raw(
            [
                sys.executable,
                "-c",
                (
                    "import os, signal; "
                    "from pathlib import Path; "
                    "from filelock import UnixFileLock; "
                    f"lock = UnixFileLock({str(lock_path)!r}, fallback_to_soft=False); "
                    "lock.acquire(); "
                    f"Path({str(acquired_marker)!r}).write_text('acquired'); "
                    "os.kill(os.getpid(), signal.SIGKILL)"
                ),
            ],
            cwd=root,
        )
        crashed = tm.ok(child)

        tm.that(crashed.exit_code != 0, eq=True)
        tm.that(acquired_marker.read_text(encoding="utf-8"), eq="acquired")
        with UnixFileLock(lock_path, timeout=0, fallback_to_soft=False) as recovered:
            tm.that(recovered.is_locked, eq=True)

    @pytest.mark.parametrize("destination_kind", ["symlink", "hardlink", "fifo"])
    def test_makefile_special_destination_fails_without_mutation(
        self, tmp_path: Path, destination_kind: str
    ) -> None:
        """Reject linked, shared-inode and nonregular destinations by nominal path."""
        root = tmp_path / "declared-target"
        u.Tests.write_standalone_workspace_manifest(root, "flext-demo")
        package = root / "src" / "flext_demo"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "flext-demo"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "dependencies = []\n",
            encoding="utf-8",
        )
        makefile = root / c.Infra.MAKEFILE_FILENAME
        source = root / "human-source"
        source.write_bytes(b"human WIP\n")
        if destination_kind == "symlink":
            makefile.symlink_to(source.name)
        elif destination_kind == "hardlink":
            makefile.hardlink_to(source)
        else:
            os.mkfifo(makefile)

        applied = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.fail(applied, has="managed destination")
        tm.that(source.read_bytes(), eq=b"human WIP\n")
        if destination_kind == "symlink":
            tm.that(makefile.is_symlink(), eq=True)
        elif destination_kind == "hardlink":
            tm.that(makefile.stat().st_ino, eq=source.stat().st_ino)
        else:
            tm.that(stat.S_ISFIFO(os.lstat(makefile).st_mode), eq=True)

    def test_work_lifecycle_is_not_projected(self, tmp_path: Path) -> None:
        """Gas City owns lanes; generated repositories expose no second lifecycle."""
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.that("work" in verb_names, eq=False)
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(" work" in public_line, eq=False)
        tm.that(rendered, lacks="_builtin_work_")
        tm.that(rendered, lacks="workspace work")

        tm.that("$(PROJECT_ROOT)/scripts" in rendered, eq=False)


__all__: list[str] = []
