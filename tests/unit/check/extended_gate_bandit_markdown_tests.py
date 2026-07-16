"""Public Bandit and Markdown gate behavior tests using protocol runners.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m, p, r, t
from flext_infra.gates.bandit import FlextInfraBanditGate
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from tests import TestsFlextInfraUtilities as u


class TestBanditAndMarkdownGates:
    """Declarative public-contract tests for Bandit and Markdown gates."""

    @staticmethod
    def make_ctx(root: Path) -> p.Infra.GateContext:
        """Build a gate context rooted in the temporary workspace."""
        return m.Infra.GateContext(workspace=root, reports_dir=root)

    @staticmethod
    def make_runner(*results: p.Result[p.Cli.CommandOutput]) -> u.Tests.SequenceRunner:
        """Build a deterministic command runner from prepared results."""
        return u.Tests.SequenceRunner(list(results))

    @pytest.mark.parametrize(
        ("with_src", "runner_results", "passed", "issues_len"),
        [
            (False, (), True, 0),
            (
                True,
                (
                    r.ok(
                        u.Tests.stub_run(
                            stdout=(
                                '{"results": [{"filename": "a.py", '
                                '"line_number": 1, "test_id": "B101", '
                                '"issue_text": "Assert used", '
                                '"issue_severity": "MEDIUM"}]}'
                            ),
                            returncode=1,
                        )
                    ),
                ),
                False,
                1,
            ),
            (
                True,
                (r.ok(u.Tests.stub_run(stdout="invalid json", returncode=1)),),
                False,
                1,
            ),
        ],
    )
    def test_bandit_check(
        self,
        tmp_path: Path,
        *,
        with_src: bool,
        runner_results: tuple[r[p.Cli.CommandOutput], ...],
        passed: bool,
        issues_len: int,
    ) -> None:
        """Report Bandit outcomes for absent, valid, and malformed outputs."""
        project_dir = u.Tests.mk_project(tmp_path, "bandit-project")
        if with_src:
            (project_dir / "src").mkdir()
            (project_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")

        gate = FlextInfraBanditGate(
            tmp_path,
            runner=self.make_runner(*runner_results) if runner_results else None,
        )
        result = gate.check(project_dir, self.make_ctx(tmp_path))

        tm.that(result.result.passed, eq=passed)
        tm.that(len(result.issues), eq=issues_len)

    @pytest.mark.parametrize(
        (
            "markdown_text",
            "config_text",
            "runner_result",
            "passed",
            "issues_len",
            "raw_output",
        ),
        [
            ("", None, None, True, 0, ""),
            (
                "# Test\n",
                None,
                r.ok(
                    u.Tests.stub_run(
                        stdout="README.md:1:1 error MD001 Heading level", returncode=1
                    )
                ),
                False,
                1,
                "",
            ),
            (
                "# Test\n",
                None,
                r.ok(u.Tests.stub_run(stderr="markdownlint failed", returncode=1)),
                False,
                0,
                "markdownlint failed",
            ),
        ],
    )
    def test_markdown_check(
        self,
        tmp_path: Path,
        *,
        markdown_text: str,
        config_text: str | None,
        runner_result: p.Result[p.Cli.CommandOutput] | None,
        passed: bool,
        issues_len: int,
        raw_output: str,
    ) -> None:
        """Report Markdown outcomes for absent, valid, and failed runs."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-project")
        if markdown_text:
            (project_dir / "README.md").write_text(markdown_text, encoding="utf-8")
        if config_text is not None:
            (project_dir / ".markdownlint.json").write_text(
                config_text, encoding="utf-8"
            )

        gate = FlextInfraMarkdownGate(
            tmp_path,
            runner=self.make_runner(runner_result)
            if runner_result is not None
            else None,
        )
        result = gate.check(project_dir, self.make_ctx(tmp_path))

        tm.that(result.result.passed, eq=passed)
        tm.that(len(result.issues), eq=issues_len)
        if raw_output:
            tm.that(result.raw_output, contains=raw_output)

    def test_markdown_prefers_local_config_when_root_is_missing(
        self, tmp_path: Path
    ) -> None:
        """Use a project-local Markdown config when the root config is absent."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-settings-project")
        (project_dir / "README.md").write_text("# Test\n", encoding="utf-8")
        (project_dir / ".markdownlint.json").write_text("{}", encoding="utf-8")
        runner = self.make_runner(r.ok(u.Tests.stub_run()))

        gate = FlextInfraMarkdownGate(tmp_path, runner=runner)
        _ = gate.check(project_dir, self.make_ctx(tmp_path))

        tm.that(runner.commands[0], has="--config")


__all__: t.StrSequence = []
