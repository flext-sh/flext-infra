"""Native checker progress retains ordered physical project identities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import check, config
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCheckReportProgress:
    """Observe real native receipts and interrupted aggregate reports."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "first_has_python",
        [True, False],
        ids=["completed-first", "zero-applicable-first"],
    )
    @pytest.mark.parametrize(
        "typed_targets",
        [False, True],
        ids=["string-projects", "typed-targets"],
    )
    def test_audit_refusal_preserves_ordered_project_progress(
        tmp_path: Path,
        *,
        first_has_python: bool,
        typed_targets: bool,
    ) -> None:
        """Equal basenames never transfer a reached result to an unreached root."""
        workspace = u.Tests.mk_project(tmp_path, "workspace")
        first = u.Tests.mk_project(
            workspace / "left",
            "shared-name",
            with_src=first_has_python,
        )
        second = u.Tests.mk_project(
            workspace / "right",
            first.name,
            with_src=True,
        )
        python_projects = (first, second) if first_has_python else (second,)
        for project in python_projects:
            (project / c.Infra.DEFAULT_SRC_DIR / "values.py").write_text(
                "def increment(value: int) -> int:\n    return value + 1\n",
                encoding=c.DEFAULT_ENCODING,
            )
        reports = workspace / "reports"
        refusal = "The consumer audit policy refuses the second Bandit launch"
        consumer = TestsFlextInfraCheckReportProgress._consumer_script(
            workspace, typed_targets=typed_targets
        )

        process = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    str(consumer),
                    str(workspace),
                    str(first),
                    str(second),
                    str(reports),
                    refusal,
                ),
                cwd=workspace,
                timeout=config.Infra.tooling.tools.pytest.run_timeout_seconds,
            ),
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        tm.fail(process.outcome.timed_out)
        tm.that(process.outcome.forwarded_signal, none=True)
        tm.that(process.stderr, has="Traceback (most recent call last):")
        tm.ok(process.stderr.rstrip().endswith(f"CheckAuditRefusal: {refusal}"))
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        sarif = m.Infra.SarifReport.model_validate_json(report_path.read_bytes())
        summary = tm.not_none(sarif.properties)
        tm.fail(summary.complete)
        tm.that(
            tuple(target.path for target in summary.targets),
            eq=(first.resolve(), second.resolve()),
        )
        tm.that(
            tuple(target.name for target in summary.targets),
            eq=(first.name, second.name),
        )
        tm.that(summary.results, length=1)
        attempted = summary.results[0]
        tm.that(attempted.project, eq=first.name)
        tm.that(summary.targets[1].applicable_gates, eq=(c.Infra.SECURITY,))
        if first_has_python:
            tm.that(summary.targets[0].applicable_gates, eq=(c.Infra.SECURITY,))
            tm.that(tuple(attempted.gates), eq=(c.Infra.SECURITY,))
            execution = attempted.gates[c.Infra.SECURITY]
            tm.ok(execution.result.passed)
            tm.that(execution.outcome, eq=c.Infra.ToolOutcome.CLEAN)
            native = tm.not_none(execution.raw_receipt)
            bandit = m.Infra.BanditReport.model_validate_json(native.read_bytes())
            tm.that(bandit.results, empty=True)
            tm.that(bandit.errors, empty=True)
            tm.that(native.parent.name, eq=first.name)
            tm.that(native.parent.parent.name, eq=first.parent.name)
        else:
            tm.that(summary.targets[0].applicable_gates, empty=True)
            tm.that(attempted.gates, empty=True)
            tm.fail(attempted.passed)
        TestsFlextInfraCheckReportProgress._assert_markdown(
            report_path, first, second, first_has_python=first_has_python
        )
        tm.that(
            tm.ok(
                u.Infra.check_report_findings(
                    workspace,
                    reports_dir=report_path.parent,
                ),
            ),
            empty=True,
        )

    @staticmethod
    def _consumer_script(workspace: Path, *, typed_targets: bool) -> Path:
        """Write the real consumer that denies the second native Bandit launch.

        Returns:
            The path of the executable consumer script.

        """
        consumer = workspace / "check_report_consumer.py"
        consumer.write_text(
            "import sys\n"
            "from pathlib import Path\n\n"
            "from flext_infra import c, check, infra, m\n\n"
            "class CheckAuditRefusal(RuntimeError):\n"
            '    """The real consumer denies one native child launch."""\n\n'
            "root = Path(sys.argv[1])\n"
            "first = Path(sys.argv[2])\n"
            "second = Path(sys.argv[3])\n"
            "reports = Path(sys.argv[4])\n"
            "refusal = sys.argv[5]\n"
            f"typed_targets = {typed_targets!r}\n\n"
            "def enforce_audit_policy(event, arguments):\n"
            "    if event != 'subprocess.Popen':\n"
            "        return\n"
            "    _executable, command, cwd, _environment = arguments\n"
            "    if (cwd is not None and Path(cwd).resolve() == second.resolve()\n"
            "            and tuple(command[:3]) == "
            "(sys.executable, '-m', c.Infra.BANDIT)):\n"
            "        raise CheckAuditRefusal(refusal)\n\n"
            "sys.addaudithook(enforce_audit_policy)\n"
            "if typed_targets:\n"
            "    check.FlextInfraWorkspaceChecker(repository_root=root)"
            ".run_projects_report(\n"
            "        projects=tuple(m.Infra.CheckProjectTarget("
            "name=path.name, path=path) for path in (first, second)),\n"
            "        gates=(c.Infra.SECURITY,),\n"
            "        reports_dir=reports,\n"
            "    ).unwrap()\n"
            "else:\n"
            "    infra.check_report(m.Infra.RunCommand(\n"
            "        repository_root=root,\n"
            "        projects=(first.relative_to(root).as_posix(),\n"
            "                  second.relative_to(root).as_posix()),\n"
            "        gates=(c.Infra.SECURITY,),\n"
            "        reports_dir=str(reports),\n"
            "    )).unwrap()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        return consumer

    @staticmethod
    def _assert_markdown(
        report_path: Path,
        first: Path,
        second: Path,
        *,
        first_has_python: bool,
    ) -> None:
        """Require each root and its completion state in the Markdown report."""
        markdown = (
            report_path.parent / c.Infra.CHECK_REPORT_MARKDOWN_FILENAME
        ).read_text(encoding=c.DEFAULT_ENCODING)
        for target in (first, second):
            tm.that(markdown, has=f"Root: `{target.resolve()}`")
        _, _, second_details = markdown.partition(f"Root: `{second.resolve()}`")
        second_details = second_details.partition("\n### ")[0]
        tm.that(second_details, has="NOT COMPLETED", lacks="PASS")
        _, _, first_details = markdown.partition(f"Root: `{first.resolve()}`")
        first_details = first_details.partition("\n### ")[0]
        tm.that(
            first_details,
            has=f"{c.Infra.SECURITY}: PASS" if first_has_python else "INCOMPLETE",
        )

    @staticmethod
    @pytest.mark.slow
    def test_root_and_same_named_member_keep_distinct_native_receipts(
        tmp_path: Path,
    ) -> None:
        """A completed root and its same-named member retain separate Bandit facts."""
        root = u.Tests.mk_project(tmp_path, "shared-name", with_src=True)
        member = u.Tests.mk_project(root, root.name, with_src=True)
        projects = (root, member)
        for project in projects:
            (project / c.Infra.DEFAULT_SRC_DIR / "values.py").write_text(
                "def increment(value: int) -> int:\n    return value + 1\n",
                encoding=c.DEFAULT_ENCODING,
            )
        reports = root / "reports"

        summary = tm.ok(
            check.FlextInfraWorkspaceChecker(
                repository_root=root,
            ).run_projects_report(
                projects=tuple(
                    m.Infra.CheckProjectTarget(name=project.name, path=project)
                    for project in projects
                ),
                gates=(c.Infra.SECURITY,),
                reports_dir=reports,
            ),
        )

        tm.ok(summary.complete)
        tm.that(summary.results, length=len(projects))
        tm.that(
            tuple(target.path for target in summary.targets),
            eq=tuple(project.resolve() for project in projects),
        )
        receipts = tuple(
            tm.not_none(result.gates[c.Infra.SECURITY].raw_receipt)
            for result in summary.results
        )
        tm.that(set(receipts), length=len(projects))
        root_receipt, member_receipt = receipts
        tm.that(root_receipt.parent.name, eq=root.name)
        tm.that(member_receipt.parent.name, eq=member.name)
        tm.that(member_receipt.parent.parent, eq=root_receipt.parent)
        for result, receipt in zip(summary.results, receipts, strict=True):
            execution = result.gates[c.Infra.SECURITY]
            tm.ok(execution.result.passed)
            tm.that(execution.outcome, eq=c.Infra.ToolOutcome.CLEAN)
            bandit = m.Infra.BanditReport.model_validate_json(receipt.read_bytes())
            tm.that(bandit.results, empty=True)
            tm.that(bandit.errors, empty=True)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        persisted = m.Infra.SarifReport.model_validate_json(report_path.read_bytes())
        tm.that(tm.not_none(persisted.properties), eq=summary)
