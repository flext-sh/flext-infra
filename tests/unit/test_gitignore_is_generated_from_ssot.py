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

from flext_infra import c, config, u
from flext_tests import tm


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[2]


def _ssot_patterns() -> tuple[str, ...]:
    """Return ignore patterns declared for this repository's profile."""
    repository = next(
        item
        for item in config.Infra.codegen.repositories
        if item.distribution == config.Infra.name
    )
    profile = repository.profile
    assert profile is not None
    return tuple(
        pattern
        for section in config.Infra.codegen.gitignore_sections
        if not section.profiles or profile in section.profiles
        for pattern in section.patterns
    )


def _live_patterns() -> tuple[str, ...]:
    """Return every meaningful line of the governed ``.gitignore``."""
    text = (_workspace_root() / ".gitignore").read_text(encoding="utf-8")
    return tuple(
        stripped
        for line in text.splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
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
        probe = u.Cli.run_checked(
            ["git", "check-ignore", "-q", relative_path], cwd=root
        )
    ignored: bool = probe.failure
    return ignored


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_ssot_declares_every_governed_ignore_pattern(self) -> None:
        """No pattern exists on disk that the SSOT cannot reproduce."""
        declared = frozenset(_ssot_patterns())
        missing = tuple(
            pattern for pattern in _live_patterns() if pattern not in declared
        )

        tm.that(missing, eq=())

    def test_ssot_reproduces_the_governed_pattern_order(self) -> None:
        """The projection opens with the governed sequence, in order.

        Ignore policy is order-sensitive, so set equality is not enough.
        Derived artifacts follow the declared sections, which is why this is a
        prefix rather than a whole-sequence comparison.
        """
        live = _live_patterns()

        tm.that(_ssot_patterns()[: len(live)], eq=live)

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
