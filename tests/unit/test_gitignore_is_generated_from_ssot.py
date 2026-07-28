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

from flext_infra import c, config, u
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(flext_infra.__file__).resolve().parents[2]


def _repository_profile() -> c.Infra.MakeProfile:
    """Return this repository's declared Make profile from the catalog SSOT."""
    repository_name = tm.ok(u.read_project_metadata(_workspace_root())).project.name
    return next(
        repository.profile
        for repository in config.Infra.codegen.repositories
        if repository.name == repository_name and repository.profile is not None
    )


def _ssot_patterns() -> tuple[str, ...]:
    """Return ignore patterns applicable to this repository's declared profile."""
    profile = _repository_profile()
    return tuple(
        pattern
        for section in config.Infra.codegen.gitignore_sections
        if not section.profiles or profile in section.profiles
        for pattern in section.patterns
    )


def _is_allowed_by_policy(relative_path: str) -> bool:
    """Return whether git would track *relative_path* under the SSOT policy.

    Ignore semantics are subtle (ordering, negation, directory prefixes), so
    the check is delegated to git itself against a throwaway repository seeded
    with the rendered policy, never reimplemented here.
    """
    rendered = "\n".join(_ssot_patterns()) + "\n"
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


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_generated_claude_policy_tracks_only_approved_files(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "generated-project"
        generated = FlextInfraCodegenProjectNew(
            name="generated-project",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(generated)
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=root))
        paths = (
            ".claude/CLAUDE.md",
            ".claude/settings.json",
            ".claude/settings.local.json",
            ".claude/private-token.txt",
        )
        for relative_path in paths:
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("test\n", encoding="utf-8")

        probes = tuple(
            tm.ok(
                u.Cli.run_raw(["git", "check-ignore", "-q", relative_path], cwd=root)
            ).exit_code
            for relative_path in paths
        )

        tm.that(
            probes,
            eq=(
                int(c.Infra.ScriptExitCode.FAIL),
                int(c.Infra.ScriptExitCode.FAIL),
                int(c.Infra.ScriptExitCode.PASS),
                int(c.Infra.ScriptExitCode.PASS),
            ),
        )

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
