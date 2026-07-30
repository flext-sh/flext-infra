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
from flext_infra import c, config, m, p, u
from flext_tests import tm


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(flext_infra.__file__).resolve().parents[2]


def _repository_profile() -> c.Infra.MakeProfile:
    """Return this repository's declared Make profile from the catalog SSOT."""
    metadata: m.ProjectMetadata = tm.ok(u.read_project_metadata(_workspace_root()))
    repository_name: str = metadata.project.name
    return next(
        repository.profile
        for repository in config.Infra.codegen.repositories
        if repository.name == repository_name and repository.profile is not None
    )


def _beads_enabled(profile: c.Infra.MakeProfile) -> bool:
    """Return the beads policy conform derives for this repository's profile."""
    if profile is c.Infra.MakeProfile.WORKSPACE_ROOT:
        return True
    metadata: m.ProjectMetadata = tm.ok(u.read_project_metadata(_workspace_root()))
    return any(
        repository.beads
        for repository in config.Infra.codegen.repositories
        if repository.name == metadata.project.name
    )


def _ssot_patterns() -> tuple[str, ...]:
    """Return ignore patterns exactly as the generator selects them.

    Mirrors the conform gitignore render filter: a section applies when its
    profile list matches (empty means universal) AND its ``beads_enabled``
    marker matches the repository's derived beads policy (``None`` means
    beads-agnostic).
    """
    profile = _repository_profile()
    beads_enabled = _beads_enabled(profile)
    return tuple(
        pattern
        for section in config.Infra.codegen.gitignore_sections
        if not section.profiles or profile in section.profiles
        if section.beads_enabled is None or section.beads_enabled is beads_enabled
        for pattern in section.patterns
    )


def _applies_to_profile(path: str, profile: c.Infra.MakeProfile) -> bool:
    """Return whether a managed file is materialized for this profile.

    The template catalog is the SSOT for which profiles receive a generated
    file: a managed path whose every template entry excludes this profile is
    never created here, so the ignore policy legitimately hides it.
    Paths without a template entry are universal committed artifacts.
    """
    entries = tuple(
        entry
        for entry in config.Infra.codegen.templates.entries
        if entry.destination == path
    )
    if not entries:
        return True
    return any(
        not entry.profiles or profile in entry.profiles for entry in entries
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
        probe: p.Cli.CommandOutput = tm.ok(
            u.Cli.run_raw(["git", "check-ignore", "-q", relative_path], cwd=root)
        )
        is_allowed: bool = probe.exit_code != int(c.Infra.ScriptExitCode.PASS)
    return is_allowed


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_every_managed_file_survives_the_ignore_policy(self) -> None:
        """No committed managed artifact is ignored by the shipped policy.

        ``codegen conform`` creates every entry of ``managed_files`` and then
        verifies the tree through git. A whitelist that blocks one of those
        paths makes the artifact untrackable, so conform re-reports it as a new
        file on every run and the whole transaction never converges.

        ``delegated`` entries are the deliberate exception: they are generated
        into each checkout rather than committed, so being ignored is correct.
        So are entries whose template catalog excludes this repository's
        profile (for example ``.beads/config.yaml``, which only workspace
        roots and opted-in standalone repositories materialize). Both
        distinctions are read from the typed policy, never hardcoded.
        """
        profile = _repository_profile()
        committed = tuple(
            item
            for item in config.Infra.codegen.managed_files
            if item.policy != c.Infra.MANAGED_FILE_POLICY_DELEGATED
            and _applies_to_profile(item.path.as_posix(), profile)
        )
        blocked = tuple(
            item.path.as_posix()
            for item in committed
            if not _is_allowed_by_policy(item.path.as_posix())
        )

        tm.that(blocked, eq=())
