"""Tests that the workspace ``.gitignore`` is reproducible from the config SSOT.

``.gitignore`` is declared a managed artifact, but the workspace root uses a
whitelist strategy (``/*`` blocks everything, then explicit ``!`` negations
re-allow the governed paths) that was never declared in
``codegen.gitignore_sections``. The generator therefore rendered a conventional
blacklist instead, and ``codegen conform`` proposed replacing 371 lines with
~76 — which would un-ignore hundreds of paths.

That single unexpressed policy blocks the whole conform transaction, so no
other generator fix can reach the tree. The strategy must live in the SSOT so
the rendered output equals the governed file.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import flext_infra
from flext_tests import tm

from flext_infra import c, config, u


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
