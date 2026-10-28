"""Public contracts for declarative intra-file duplicate extraction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flext_infra.codemod import FlextInfraCodemodExtractDuplicate
from tests import c, m, t, tm, u

_SAFE_SOURCE = (
    "CONSTANT = 2\n"
    "\n"
    "\n"
    "class Sample:\n"
    '    """Sample holder."""\n'
    "\n"
    "    @staticmethod\n"
    "    def demo(seed: int, bucket: list[int]) -> int:\n"
    '        """Append the repeated block twice and sum the bucket."""\n'
    "        bucket.append(seed + CONSTANT)\n"
    "        bucket.extend([seed, CONSTANT])\n"
    "        bucket.append(seed + CONSTANT)\n"
    "        bucket.extend([seed, CONSTANT])\n"
    "        return sum(bucket)\n"
)

_SAFE_BLOCK = (
    "        bucket.append(seed + CONSTANT)\n        bucket.extend([seed, CONSTANT])\n"
)

_UNSAFE_SOURCE = (
    "def resolve(flag: bool, value: int) -> int:\n"
    '    """Resolve a value twice with a return inside the repeated block."""\n'
    "    if flag:\n"
    "        return value + 1\n"
    "        raise AssertionError(value)\n"
    "    if flag:\n"
    "        return value + 1\n"
    "        raise AssertionError(value)\n"
    "    return value\n"
)

_UNSAFE_BLOCK = (
    "    if flag:\n        return value + 1\n        raise AssertionError(value)\n"
)


class TestsFlextInfraExtractDuplicate:
    """Prove extraction rewires safe blocks and skips unsafe ones."""

    @staticmethod
    def _block_span(source: str, block: str) -> tuple[int, int, int, int]:
        """Locate the two exact occurrences of a contiguous block.

        Returns:
            The four reported line numbers (first start/end, second start/end).

        """
        lines = source.splitlines(keepends=True)
        block_lines = block.splitlines(keepends=True)
        width = len(block_lines)
        starts = [
            index
            for index in range(len(lines) - width + 1)
            if lines[index : index + width] == block_lines
        ]
        tm.that(starts, length=2)
        first, second = starts
        return (first + 1, first + width, second + 1, second + width)

    @staticmethod
    def _run_module(root: Path, probe: str) -> str:
        """Execute a probe against a written module in a fresh interpreter.

        Returns:
            The probe's stripped standard output.

        """
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([str(root), *sys.path])
        outcome = tm.ok(
            u.Cli.run(
                [sys.executable, "-c", probe],
                cwd=root,
                options=m.Cli.ProcessOptions(env=env),
            ),
        )
        return outcome.stdout.strip()

    def test_safe_block_is_extracted_without_changing_behavior(
        self,
        tmp_path: Path,
    ) -> None:
        """A repeated side-effect block is hoisted and rewired byte-safely."""
        span = self._block_span(_SAFE_SOURCE, _SAFE_BLOCK)
        updated = tm.not_none(
            FlextInfraCodemodExtractDuplicate.plan_source(_SAFE_SOURCE, (span,)),
        )
        tm.that(updated, has="def _flext_extract_")
        tm.that(updated, has="Sample._flext_extract_")
        tm.that(updated.count("bucket.extend([seed, CONSTANT])"), eq=1)
        tm.that(
            FlextInfraCodemodExtractDuplicate.plan_source(updated, (span,)),
            eq=None,
        )
        module = tmp_path / "sample.py"
        (tmp_path / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        module.write_text(_SAFE_SOURCE, encoding=c.DEFAULT_ENCODING)
        original = self._run_module(
            tmp_path,
            "import sample\nprint(sample.Sample.demo(3, []))\n",
        )
        module.write_text(updated, encoding=c.DEFAULT_ENCODING)
        extracted = self._run_module(
            tmp_path,
            "import sample\nprint(sample.Sample.demo(3, []))\n",
        )
        tm.that(extracted, eq=original)

    def test_unsafe_block_is_skipped(self) -> None:
        """A block whose return crosses the boundary is never extracted."""
        span = self._block_span(_UNSAFE_SOURCE, _UNSAFE_BLOCK)
        tm.that(
            FlextInfraCodemodExtractDuplicate.plan_source(_UNSAFE_SOURCE, (span,)),
            eq=None,
        )

    def test_plan_project_reads_report_and_is_idempotent(self, tmp_path: Path) -> None:
        """The phase consumes the truthful report and reaches a fixed point."""
        span = self._block_span(_SAFE_SOURCE, _SAFE_BLOCK)
        module = tmp_path / "sample.py"
        module.write_text(_SAFE_SOURCE, encoding=c.DEFAULT_ENCODING)
        report_dir = tmp_path / c.Infra.JSCPD_REPORT_DIRNAME
        report_dir.mkdir(parents=True)
        report: t.JsonDict = {
            "duplicates": [
                {
                    "format": "python",
                    "firstFile": {
                        "name": str(module.resolve()),
                        "startLoc": {"line": span[0]},
                        "endLoc": {"line": span[1]},
                    },
                    "secondFile": {
                        "name": str(module.resolve()),
                        "startLoc": {"line": span[2]},
                        "endLoc": {"line": span[3]},
                    },
                    "lines": span[1] - span[0] + 1,
                    "tokens": 40,
                },
            ],
            "statistics": {"clones": 1},
        }
        (report_dir / c.Infra.JSCPD_REPORT_FILENAME).write_text(
            tm.ok(u.Cli.json_dumps(report)),
            encoding=c.DEFAULT_ENCODING,
        )
        edits = tm.ok(FlextInfraCodemodExtractDuplicate.plan_project(tmp_path))
        tm.that(edits, length=1)
        tm.that(edits[0].file_path, eq=module.resolve())
        module.write_text(edits[0].updated_source, encoding=c.DEFAULT_ENCODING)
        tm.that(
            tm.ok(FlextInfraCodemodExtractDuplicate.plan_project(tmp_path)),
            empty=True,
        )
