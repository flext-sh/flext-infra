"""Public snapshot reconciliation for complete ast-grep YAML streams.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraCodemodSnapshotReconciler
from tests import c, tm, u


class TestsFlextInfraSnapshotDocuments:
    """Every declared document contributes its cases to the same owner."""

    @staticmethod
    @pytest.mark.parametrize("empty_stream", [None, "", "# no documents\n"])
    @pytest.mark.parametrize(
        ("block_header", "padding", "second_case"),
        [
            ("|", "", "second_case\n"),
            ("|-", "", "second_case"),
            ("|+", "\n", "second_case\n\n"),
        ],
    )
    def test_all_documents_and_repeated_ids_contribute_snapshot_cases(
        tmp_path: Path,
        empty_stream: str | None,
        block_header: str,
        padding: str,
        second_case: str,
    ) -> None:
        """Native YAML block contents survive document and repeated-ID boundaries."""
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
                f"---\nid: second-probe\ninvalid:\n  - {block_header}\n"
                f"    second_case\n{padding}"
                "---\nid: first-probe\ninvalid: [additional_case]\n"
                if empty_stream is None
                else empty_stream
            ),
            encoding="utf-8",
        )
        for rule_id, cases in (
            ("first-probe", ("first_case", "additional_case")),
            ("second-probe", (second_case,)),
        ):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rules / f"{rule_id}{c.Infra.CODEMOD_RULE_SUFFIX}",
                    f"id: {rule_id}\nlanguage: Python\nrule:\n  pattern: $VALUE\n",
                ),
            )
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
                    tmp_path,
                )
            return
        tm.that(
            FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                tmp_path,
            ),
            empty=True,
        )
