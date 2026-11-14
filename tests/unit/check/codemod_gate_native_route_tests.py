"""The codemod gate reads findings through the shared native scan route.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import r, u as infra_u
from flext_infra.gates import FlextInfraGatesCodemod
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodemodGateNativeRoute:
    """Cached and stopped native scans keep the gate's verdict exact."""

    @staticmethod
    def test_changed_utility_invalidates_every_cached_finding(
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """A rule matching through a utility follows the utility's new bytes."""
        project = u.Tests.scanner_contract_project(
            tmp_path, installed_dependency_path, session_runtime
        )
        catalog = (project / c.Infra.CODEMOD_CONFIG_RELPATH).parent
        utility = catalog / "utils" / "callee.yml"
        tm.ok(u.Cli.ensure_dir(utility.parent))
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalog / c.Infra.CODEMOD_CONFIG_FILENAME,
                f"{c.Infra.CODEMOD_SCOPE_KEY}: {c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n"
                f"ruleDirs:\n  - {c.Cli.RULES_DIR_NAME}\n"
                "utilDirs:\n  - utils\ntestConfigs: []\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalog / c.Cli.RULES_DIR_NAME / "second.yml",
                "id: contract-second\nlanguage: Python\nseverity: error\n"
                "message: Observed second\nrule:\n  matches: callee\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                utility,
                "id: callee\nlanguage: Python\nrule:\n  pattern: second($VALUE)\n",
            )
        )
        (project / "src" / "subject.py").write_text("second(1)\n", encoding="utf-8")
        matched = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
        tm.that(
            [
                issue.code
                for issue in matched.issues
                if issue.code.startswith("contract-")
            ],
            eq=["contract-second"],
            msg=matched.raw_output,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                utility,
                "id: callee\nlanguage: Python\nrule:\n  pattern: third($VALUE)\n",
            )
        )
        cleared = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
        tm.that(
            [
                issue.code
                for issue in cleared.issues
                if issue.code.startswith("contract-")
            ],
            empty=True,
            msg=cleared.raw_output,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("truncated", [False, True])
    def test_timed_out_scan_reports_every_published_finding(
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        truncated: bool,
    ) -> None:
        """Measure the records a stopped scan published instead of counting it once.

        The real scanner publishes its records and then reaches its deadline:
        the gate reports each published rule/file and the true policy-finding
        total while the native timeout stays blocking. A killed scanner can
        also leave its last record cut; the complete records before the cut
        are still the native measurement.
        """
        project = u.Tests.scanner_contract_project(
            tmp_path, installed_dependency_path, session_runtime
        )
        for name in ("first", "second"):
            (project / "src" / f"{name}.py").write_text(
                f"{name}(1)\n", encoding="utf-8"
            )

        class _TimedOutScan(infra_u.Cli):
            """The real native scan, reported as stopped at its deadline."""

            cut: ClassVar[bool] = False
            kept: ClassVar[int] = 0

            @classmethod
            @override
            def run_to_file(
                cls,
                cmd: Sequence[str],
                output_file: t.Cli.TextPath,
                cwd: t.Cli.TextPath | None = None,
                timeout: int | None = None,
                *,
                options: p.Cli.ProcessOptions | None = None,
            ) -> p.Result[p.Cli.ProcessOutcome]:
                tm.ok(
                    infra_u.Cli.run_to_file(
                        cmd, output_file, cwd, timeout, options=options
                    )
                )
                records = Path(output_file).read_text(encoding="utf-8").splitlines()
                cls.kept = len(records) - 1 if cls.cut else len(records)
                if cls.cut:
                    Path(output_file).write_text(
                        "".join(f"{record}\n" for record in records[:-1])
                        + records[-1][: len(records[-1]) // 2],
                        encoding="utf-8",
                    )
                return r[p.Cli.ProcessOutcome].ok(
                    m.Cli.ProcessOutcome(
                        raw_return_code=-2, timed_out=True, forwarded_signal=None
                    )
                )

        _TimedOutScan.cut = truncated
        execution = FlextInfraGatesCodemod(tmp_path, runner=_TimedOutScan).check(
            project, u.Tests.gate_context(tmp_path)
        )

        tm.fail(execution.result.passed)
        tm.that(
            execution.raw_output,
            has=f"{_TimedOutScan.kept} policy findings; 1 native failures",
        )
        if not truncated:
            tm.that(
                sorted(
                    (issue.code, Path(issue.file).name)
                    for issue in execution.issues
                    if issue.code.startswith("contract-")
                ),
                eq=[("contract-first", "first.py"), ("contract-second", "second.py")],
                msg=execution.raw_output,
            )
        tm.that(
            tuple(
                issue.message
                for issue in execution.issues
                if issue.code == c.Infra.ToolOutcome.ERROR.value
            ),
            eq=(
                (
                    f"{c.Infra.SG} exited with code -2 "
                    "timed_out=True forwarded_signal=None"
                ),
            ),
        )


__all__: list[str] = ["TestsFlextInfraCodemodGateNativeRoute"]
