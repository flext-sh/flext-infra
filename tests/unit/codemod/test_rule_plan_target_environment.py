"""The rule plan reads the TARGET repository's environment, never the caller's.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraRulePlanTargetEnvironment:
    """Drive the public rule plan against target repositories."""

    @staticmethod
    def test_unprovisioned_target_fails_loud_with_its_environment(
        tmp_path: Path,
    ) -> None:
        """A target without its own environment fails before any rule election."""
        project = tmp_path / "unprovisioned"
        project.mkdir()
        (project / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "unprovisioned"\nversion = "1.0.0"\n'
            'dependencies = ["pulumi-oci"]\n',
            encoding="utf-8",
        )
        tm.ok(u.Cli.capture(["git", "init", "--quiet", str(project)]))
        result = u.Infra.codemod_compose_rule_plan(project, {project.resolve(): None})
        tm.fail(result, has="target repository environment is not provisioned")

    @staticmethod
    def test_workspace_target_elects_from_its_own_environment() -> None:
        """The provisioned workspace target composes its plan from its own venv."""
        root = u.Infra.runtime_owner_root(Path(__file__).resolve().parent).unwrap()
        observation = tm.ok(u.Infra.codemod_target_environment(root))
        tm.that(
            observation.prefix.resolve(),
            eq=u.Infra.runtime_environment_dir(root).resolve(),
        )
        tm.ok(u.Infra.codemod_compose_rule_plan(root, {root.resolve(): None}))
