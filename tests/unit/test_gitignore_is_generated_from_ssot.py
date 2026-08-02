"""Tests that this repository's ``.gitignore`` is reproducible from config.

The generator filters the shared policy by the repository profile. Workspace
roots receive the ordered whitelist while members receive only universal
ignore sections. This test follows that same typed topology instead of freezing
the workspace-root projection into every repository.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import flext_infra
from flext_tests import tm

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(flext_infra.__file__).resolve().parents[2]


def _repository_profile() -> c.Infra.MakeProfile:
    """Return this repository's profile inferred by the production detector."""
    return tm.ok(
        FlextInfraWorkspaceDetector.conform_target(_workspace_root())
    ).make_profile


def _ssot_patterns() -> tuple[str, ...]:
    """Return ignore patterns applicable to this repository's declared profile."""
    profile = _repository_profile()
    return tuple(
        pattern
        for section in config.Infra.codegen.gitignore_sections
        if not section.profiles or profile in section.profiles
        for pattern in section.patterns
    )


def _is_tracked_under(rendered: str, relative_path: str) -> bool:
    """Return whether git would track *relative_path* under *rendered*.

    Ignore semantics are subtle (ordering, negation, directory prefixes), so
    the check is delegated to git itself against a throwaway repository seeded
    with the rendered policy, never reimplemented here.
    """
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        tm.ok(u.Cli.run_checked(["git", "init", "-q", str(root)]))
        (root / ".gitignore").write_text(rendered, encoding="utf-8")
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
        # `git check-ignore` exits 0 when the path IS ignored, 1 when it is
        # not, so a failed run is the success case for a tracked artifact.
        probe = tm.ok(
            u.Cli.run_raw(["git", "check-ignore", "-q", relative_path], cwd=root)
        )
    return probe.exit_code != int(c.Infra.ScriptExitCode.PASS)


def _is_allowed_by_policy(relative_path: str) -> bool:
    """Return whether the shipped SSOT policy keeps *relative_path* trackable."""
    return _is_tracked_under("\n".join(_ssot_patterns()) + "\n", relative_path)


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_every_managed_file_survives_the_ignore_policy(self) -> None:
        """No committed managed artifact is ignored by the shipped policy.

        ``codegen conform`` creates every entry of ``managed_files`` and then
        verifies the tree through git. A whitelist that blocks one of those
        paths makes the artifact untrackable, so conform re-reports it as a new
        file on every run and the whole transaction never converges.

        ``delegated`` entries are the deliberate exception: they are generated
        into each checkout rather than committed, so being ignored is correct.
        The distinction is read from the managed-file policy, never hardcoded.
        """
        committed = tuple(
            item
            for item in config.Infra.codegen.managed_files
            if item.policy != c.Infra.MANAGED_FILE_POLICY_DELEGATED
        )
        blocked = tuple(
            item.path.as_posix()
            for item in committed
            if not _is_allowed_by_policy(item.path.as_posix())
        )

        tm.that(blocked, eq=())

    def test_declared_members_are_trackable_under_the_rendered_policy(
        self,
    ) -> None:
        """A member declared in the manifest is trackable in the rendered body.

        The workspace-root policy denies every top-level directory (``/*`` and
        ``/*/``), so a governed member only becomes trackable if the whitelist
        is DERIVED from the manifest. This exercises arbitrary member paths —
        including a nested one, whose every ancestor must be unignored — so it
        stays valid for any manifest instead of freezing today's members.
        """
        members = ("probe-member", "nested/probe-member")
        workspace = m.Infra.WorkspaceSpec(
            repository=m.Infra.RepositoryRef(name="probe-root", path=Path(".")),
            members=tuple(
                m.Infra.RepositoryRef(name=Path(item).name, path=Path(item))
                for item in members
            ),
        )
        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
                project_name="probe-root",
                workspace=workspace,
            )
        )

        blocked = tuple(
            member
            for member in members
            if not _is_tracked_under(rendered, f"{member}/pyproject.toml")
        )

        tm.that(blocked, eq=())
