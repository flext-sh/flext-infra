"""Tests that no generated executable surface silences a command failure.

A recipe line ending in ``|| true`` discards the command's exit code, so a
crashed tool, a missing binary or a malformed rule file is reported to the
operator as success. That is indistinguishable from a real pass, which makes
every gate built on it untrustworthy.

The pattern is sometimes defended as "the scanner exits non-zero when it finds
something". That defence is false for the scanner this workspace uses:
``ast-grep scan`` exits 0 both with and without findings, and reserves non-zero
for genuine errors (6 = unreadable rule, 127 = binary absent). ``|| true``
therefore masks *only* real failures and protects nothing.

Read-only verbs that must not fail the build on findings express that by
reporting explicitly, never by discarding the exit code.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import flext_infra
from flext_infra import c, u
from flext_tests import tm


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[2]


def _executable_surfaces() -> tuple[Path, ...]:
    """Return active Make/workflow surfaces and their executable templates.

    Generated surfaces are projections, so fixing one on disk is undone by the
    next regeneration. The shipped templates are therefore in scope: they are
    where the defect must not exist.
    """
    root = _workspace_root()
    names = (c.Infra.MAKEFILE_FILENAME, c.Infra.CUSTOM_MAKE_FILENAME)
    templates = Path(flext_infra.__file__).resolve().parent / "templates"
    workflows = root / ".github" / "workflows"
    return (
        *(path for name in names if (path := root / name).is_file()),
        *sorted(workflows.glob("*.yml")),
        *sorted(templates.rglob("*.j2")),
    )


def _cqrs_template() -> Path:
    """Return the generated CQRS shell surface."""
    return (
        Path(flext_infra.__file__).resolve().parent
        / "templates"
        / "project"
        / "base"
        / ".github"
        / "scripts"
        / "check-cqrs-compliance.sh.j2"
    )


def _silencing_lines(surface: Path) -> tuple[str, ...]:
    """Return executable lines that discard a command's exit status."""
    return tuple(
        f"{surface.name}:{number}: {line.strip()}"
        for number, line in enumerate(
            surface.read_text(encoding="utf-8").splitlines(), start=1
        )
        if "|| true" in line or "|| :" in line
    )


class TestsFlextInfraMakeSurfaceNeverSilencesFailures:
    def test_no_executable_surface_discards_a_command_exit_code(self) -> None:
        """No generated shell or workflow swallows a command failure."""
        offenders = {
            str(surface.relative_to(_workspace_root())): lines
            for surface in _executable_surfaces()
            if (lines := _silencing_lines(surface))
        }

        tm.that(len(offenders), eq=0)

    def test_cqrs_scanner_propagates_rg_failure(self, tmp_path: Path) -> None:
        """The CQRS wrapper preserves a scanner crash instead of reporting green."""
        script = tmp_path / ".github" / "scripts" / "check-cqrs-compliance.sh"
        script.parent.mkdir(parents=True)
        script.write_text(_cqrs_template().read_text(encoding="utf-8"), encoding="utf-8")
        source = tmp_path / "demo" / "src"
        source.mkdir(parents=True)
        (source / "sample.py").write_text("value = 1\n", encoding="utf-8")
        fake_bin = tmp_path / "fake-bin"
        fake_bin.mkdir()
        fake_rg = fake_bin / "rg"
        fake_rg.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")
        fake_rg.chmod(0o755)
        path = os.environ["PATH"]

        output = tm.ok(
            u.Cli.run_raw(
                ["bash", str(script)],
                cwd=tmp_path,
                env={"PATH": f"{fake_bin}{os.pathsep}{path}"},
            )
        )

        tm.that(output.exit_code, eq=42)
        tm.that(output.stdout, lacks="All CQRS checks passed")
