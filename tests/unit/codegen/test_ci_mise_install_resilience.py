"""The CI Mise install step provisions whatever state the committed lock is in.

Premise (operator-ruling-2026-10-09-setup-resilient): a stale, incomplete or
unreadable lock never stops a job before ``make setup``; ``make audit`` reports
the lock and ``make upg`` cures it.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from flext_tests import tm

from tests import c, m, u
from tests.unit.codegen import test_ci_integration_branch_triggers as triggers


class TestsFlextInfraCiMiseInstallResilience:
    """Run the rendered CI step against every lock shape a consumer can carry."""

    _STEP = "Install the mise release declared by mise.lock or .mise.toml"

    @classmethod
    def _rendered_step(cls) -> str:
        """Return the ``run`` body of the rendered CI Mise install step.

        Returns:
            The shell body GitHub Actions executes.

        """
        steps = u.CodegenTestSupport.Ci.ci_job_steps(
            triggers.TestsFlextInfraCiIntegrationBranchTriggers.render_ci(
                repository_branch="0.12.0-dev",
            ),
        )
        return str(next(step for step in steps if step.get("name") == cls._STEP)["run"])

    @staticmethod
    def _shape(root: Path, shape: str) -> None:
        """Seed the tracked declaration and lock, then reshape the lock."""
        u.Tests.copy_tracked_mise_seeds(root)
        lock = root / c.Infra.MISE_LOCK_FILENAME
        text = lock.read_text(encoding="utf-8")
        if shape == "without-self-pin":
            text = re.sub(
                r'\[\[tools\."github:jdx/mise"\]\].*?(?=\n\[\[tools\.|\Z)',
                "",
                text,
                flags=re.DOTALL,
            )
        elif shape == "merge-markers":
            text = f"<<<<<<< ours\n{text}=======\n>>>>>>> theirs\n"
        lock.write_text(text, encoding="utf-8")

    @pytest.mark.remote
    @pytest.mark.slow
    @pytest.mark.parametrize("shape", ["pinned", "without-self-pin", "merge-markers"])
    def test_step_provisions_mise_without_reading_a_broken_lock(
        self,
        tmp_path: Path,
        shape: str,
    ) -> None:
        """Every lock shape installs the declared Mise, silently, lock untouched."""
        project = tmp_path / "project"
        project.mkdir()
        self._shape(project, shape)
        lock = project / c.Infra.MISE_LOCK_FILENAME
        before = lock.read_bytes()
        home = tmp_path / "home"
        runner = tmp_path / "runner"
        github_path = tmp_path / "github_path"
        home.mkdir()
        runner.mkdir()
        process = tm.ok(
            u.Cli.run_raw(
                ["bash", "-c", self._rendered_step()],
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env={
                        "PATH": "/usr/bin:/bin",
                        "HOME": str(home),
                        "RUNNER_OS": "Linux",
                        "RUNNER_ARCH": "X64",
                        "RUNNER_TEMP": str(runner),
                        "GITHUB_PATH": str(github_path),
                    },
                ),
            ),
        )
        output = process.stdout + process.stderr
        tm.that(u.Cli.process_succeeded(process.outcome), eq=True, msg=output)
        tm.that(output, lacks=["WARN", "ERROR"])
        tm.that(lock.read_bytes(), eq=before)
        published = github_path.read_text(encoding="utf-8").splitlines()
        tm.that(published[-1], has="github-jdx-mise")
