"""Failed codemod passes retain accepted writes for fix-forward.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraCodemodAstScan, FlextInfraCodemodSemanticApply
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import m, tm, u


class TestsFlextInfraFailedInvocationProgress:
    """Failures preserve accepted progress and newer independent source states."""

    @staticmethod
    @pytest.mark.slow
    def test_failed_mechanical_cycle_retains_accepted_rewrite(
        mod_workspace: Path,
    ) -> None:
        """A real syntax cycle fails without restoring its initial source."""
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                name: (
                    f"id: {name}\nlanguage: Python\nseverity: warning\n"
                    "rule:\n"
                    f"  pattern: value = {before}()\n"
                    f"fix: value = {after}()\n"
                )
                for name, before, after in (
                    ("start", "dict", "list"),
                    ("forward", "list", "tuple"),
                    ("cycle", "tuple", "list"),
                )
            },
        )
        module = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(module, "value = dict()\n"))

        outcome = FlextInfraCodemodAstScan(
            repository_root=mod_workspace,
            apply_changes=True,
        ).execute()

        tm.fail(outcome, has="made no progress")
        retained = module.read_text(encoding="utf-8")
        tm.that(retained, lacks="value = dict()")
        tm.that(retained, has="value = list()")

    @staticmethod
    def test_failed_publication_preserves_progress_and_newer_source(
        mod_workspace: Path,
    ) -> None:
        """A stale next batch cannot undo an accepted batch or a newer edit."""
        accepted = mod_workspace / "accepted.py"
        unrelated = mod_workspace / "unrelated.py"
        for path in (accepted, unrelated):
            tm.ok(u.Cli.atomic_write_text_file(path, 'value = "original"\n'))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(accepted, required=True))
        stale = tm.ok(u.Cli.atomic_read_binary_file_state(unrelated, required=True))
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (
                    m.Infra.SemanticFilePlan(
                        project=mod_workspace,
                        path=accepted,
                        before=before,
                        desired_content=b'value = "accepted"\n',
                        desired_mode=before.mode,
                    ),
                ),
                repository_root=mod_workspace,
            ),
        )
        newer = 'value = "newer independent edit"\n'
        tm.ok(u.Cli.atomic_write_text_file(unrelated, newer))
        published = accepted.read_bytes()
        next_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(accepted, required=True),
        )

        outcome = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=accepted,
                    before=next_before,
                    desired_content=b'value = "next pass"\n',
                    desired_mode=next_before.mode,
                ),
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=unrelated,
                    before=stale,
                    desired_content=b'value = "stale replacement"\n',
                    desired_mode=stale.mode,
                ),
            ),
            repository_root=mod_workspace,
        )

        tm.fail(outcome)
        tm.that(accepted.read_bytes(), eq=published)
        tm.that(unrelated.read_text(encoding="utf-8"), eq=newer)

    @staticmethod
    def test_formatter_exception_preserves_preexisting_accepted_progress(
        mod_workspace: Path,
    ) -> None:
        """A later formatter failure leaves accepted and unrelated files intact."""
        accepted = mod_workspace / "accepted.py"
        unrelated = mod_workspace / "unrelated.py"
        source = 'value = "accepted"\n'
        newer = 'value = "newer independent edit"\n'
        tm.ok(u.Cli.atomic_write_text_file(accepted, source))
        tm.ok(u.Cli.atomic_write_text_file(unrelated, newer))

        with pytest.raises(RuntimeError, match="failed"):
            FlextInfraCodemodSemanticApply.apply_transaction_paths(
                mod_workspace,
                (
                    m.Infra.SemanticMigrationEdit(
                        file_path=accepted,
                        original_source=source,
                        updated_source="value = (\n",
                        changes=("real formatter rejection",),
                    ),
                ),
            )

        tm.that(accepted.read_text(encoding="utf-8"), eq=source)
        tm.that(unrelated.read_text(encoding="utf-8"), eq=newer)
