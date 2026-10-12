"""Public snapshot reconciliation for complete ast-grep YAML streams.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler
from tests import c, tm, u


class TestsFlextInfraSnapshotDocuments:
    """Every declared document contributes its cases to the same owner."""

    @staticmethod
    @pytest.mark.parametrize("empty_stream", [None, "", "# no documents\n"])
    def test_all_documents_and_repeated_ids_contribute_snapshot_cases(
        tmp_path: Path,
        empty_stream: str | None,
    ) -> None:
        """Snapshots from later documents and repeated IDs remain valid."""
        rules = tmp_path / "rule-inputs"
        tests = tmp_path / "fixture-inputs"
        snapshots = tests / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
        rules.mkdir()
        snapshots.mkdir(parents=True)
        tm.ok(
            u.Cli.yaml_dump(
                tmp_path / c.Infra.CODEMOD_CONFIG_FILENAME,
                {
                    c.Infra.CODEMOD_RULE_DIRS_KEY: [rules.name],
                    c.Infra.CODEMOD_TEST_CONFIGS_KEY: [
                        {c.Infra.CODEMOD_TEST_DIR_KEY: tests.name}
                    ],
                },
            )
        )
        (tests / f"cases{c.Infra.CODEMOD_RULE_SUFFIX}").write_text(
            (
                "id: first-probe\ninvalid: [first_case]\n"
                "---\nid: second-probe\ninvalid: [second_case]\n"
                "---\nid: first-probe\ninvalid: [additional_case]\n"
                if empty_stream is None
                else empty_stream
            ),
            encoding="utf-8",
        )
        for rule_id, cases in (
            ("first-probe", ("first_case", "additional_case")),
            ("second-probe", ("second_case",)),
        ):
            tm.ok(
                u.Cli.yaml_dump(
                    snapshots / f"{rule_id}{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}",
                    {
                        c.Infra.CODEMOD_RULE_TEST_ID_KEY: rule_id,
                        c.Infra.CODEMOD_SNAPSHOTS_KEY: {
                            case: {
                                "labels": [
                                    {
                                        "source": case,
                                        "style": "primary",
                                        "start": 0,
                                        "end": len(case),
                                    }
                                ]
                            }
                            for case in cases
                        },
                    },
                )
            )
        if empty_stream is not None:
            with pytest.raises(TypeError, match="empty ast-grep rule-test"):
                FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                    tmp_path, frozenset(("first-probe", "second-probe"))
                )
            return
        tm.that(
            FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                tmp_path, frozenset(("first-probe", "second-probe"))
            ),
            empty=True,
        )
