"""Drifted sources defer with receipts and never receive engine rewrites.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, t
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from tests import c, tm, u


class TestsFlextInfraBatchGateSourceDrift:
    """The always-reducing sweep stays live under concurrent fleet lanes."""

    @staticmethod
    def _finding(
        path: Path,
        state: m.Cli.AtomicFileState | None,
        *,
        actionable: bool,
    ) -> m.Infra.ModOccurrence:
        start = b'value = "before"'.index(b"before")
        offsets: t.JsonDict = {"start": start, "end": start + len(b"before")}
        return m.Infra.ModOccurrence(
            rule_file=str(path.parent / "rule.yaml"),
            rule_id="fixture-rewrite",
            repository=path.parent.name,
            file=path,
            source_state=state,
            range={"byteOffset": offsets},
            text="before",
            replacement="after",
            actionable=actionable,
            classification=(
                c.Infra.ModScanFindingClass.ACTIONABLE
                if actionable
                else c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT
            ),
            replacement_offsets=m.Infra.ModReplacementOffsets.model_validate(offsets),
        )

    @staticmethod
    def _repository(path: Path) -> None:
        policy = path / c.PYPROJECT_FILENAME
        if not policy.exists():
            policy.write_text(
                "[project]\nname = 'sample'\nversion = '1.0.0'\n"
                "[tool.ruff.lint]\nselect = ['F401', 'F821']\n",
            )

    def test_recounted_defers_drifted_class_without_actionable_count(
        self,
        tmp_path: Path,
    ) -> None:
        """Test recounted defers drifted class without actionable count."""
        root = u.Tests.git_repository(tmp_path)
        self._repository(root)
        path = root / "subject.py"
        path.write_bytes(b'value = "before"\n')
        entry = self._finding(path, None, actionable=False)
        report = m.Infra.ModOccurrenceReport(entries=(entry,), files=frozenset({path}))
        tm.that(report.findings, eq=1)
        tm.that(report.deferred, eq=1)
        tm.that(report.actionable, eq=0)
        tm.that(
            report.entries[0].classification,
            eq=c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT,
        )

    def test_publish_applies_actionable_and_ignores_deferred(
        self,
        tmp_path: Path,
    ) -> None:
        """Test publish applies actionable and ignores deferred."""
        root = u.Tests.git_repository(tmp_path)
        self._repository(root)
        path = root / "subject.py"
        original = b'value = "before"\n'
        path.write_bytes(original)
        state = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
        report = m.Infra.ModOccurrenceReport(
            entries=(
                self._finding(path, state, actionable=True),
                self._finding(path, None, actionable=False),
            ),
            files=frozenset({path}),
        )
        tm.that(report.actionable, eq=1)
        tm.that(report.deferred, eq=1)
        tm.ok(FlextInfraModReplacements.publish(root, report))
        tm.that(path.read_bytes(), eq=original.replace(b"before", b"after"))
