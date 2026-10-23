"""Public recovery of native journal witnesses after a physical scope move.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import codegen
from tests import c, m, p, r, tm, u


class TestsFlextInfraJournalRelocation:
    """Keep staged authority and live destination bytes through native recovery."""

    @staticmethod
    def _interrupted_staging(
        root: Path,
        *,
        materialized: bool,
    ) -> m.Infra.CodegenTransactionSession:
        """Persist write-ahead authority with optional real staging bytes.

        Returns:
            The session left for the next public recovery invocation.

        """
        owner = codegen.FlextInfraCodegenTransaction(
            codegen.FlextInfraCodegenMiseArtifacts(repository_root=root),
        )

        def interrupt(scope: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope, {"@docs-0": root}, ()))
            planned = m.Infra.CodegenFilePlan(
                project=root,
                path=root / "generated.md",
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(
                        root / "generated.md", required=True,
                    ),
                ),
                desired_content=b"generated document\n",
                desired_mode=session.journal_state.mode,
                owner="docs",
            )
            prepared = tm.ok(
                owner.prepare_phase_staging_locked(session, "docs", (planned,)),
            )
            if materialized:
                for intent in prepared.journal.staging_intents:
                    tm.ok(
                        u.Cli.atomic_write_binary_file_guarded(
                            intent.before,
                            tm.not_none(planned.desired_content),
                            permission_mode=intent.mode,
                        ),
                    )
            return r[m.Infra.CodegenTransactionSession].ok(prepared)

        return tm.ok(owner.run_files_locked({"@docs-0": root}, interrupt))

    @staticmethod
    @pytest.mark.parametrize("materialized", [False, True])
    @pytest.mark.parametrize("relocated", [False, True])
    def test_first_use_journal_staging_and_relocated_recovery(
        tmp_path: Path,
        *,
        materialized: bool,
        relocated: bool,
    ) -> None:
        """Retire only owned staging without publishing interrupted live bytes."""
        root = u.Tests.git_repository(tmp_path)
        (root / "generated.md").write_bytes(b"original document\n")
        prepared = TestsFlextInfraJournalRelocation._interrupted_staging(
            root, materialized=materialized,
        )
        if relocated:
            root = root.rename(root.with_name("relocated-repository"))
        layout = tm.ok(
            codegen.FlextInfraMiseWorkspacePlanner(
                codegen.FlextInfraCodegenMiseArtifacts(repository_root=root),
            ).file_layout(
                root,
                {"@docs-0": root},
                transaction_id=prepared.journal.transaction_id,
            ),
        )
        rebound, original_state = tm.ok(
            codegen.FlextInfraMiseArtifactsJournal.read(layout),
        )
        tm.that(rebound.transaction_id, eq=prepared.journal.transaction_id)
        tm.that(rebound.state, eq=prepared.journal.state)
        tm.that(rebound.entries, eq=prepared.journal.entries)
        tm.that(len(rebound.staging_intents), eq=len(prepared.journal.staging_intents))
        if relocated:
            tm.ok(rebound.file_participants[0] is layout.file_participants[0])
        for directory in rebound.directories:
            if directory.manifest is not None:
                tm.ok(directory.manifest.root.path.is_relative_to(root))
                tm.ok(all(entry.path.is_relative_to(root) for entry in directory.manifest.entries))
        for intent in rebound.staging_intents:
            tm.ok(intent.before.path.is_relative_to(root))
        tm.ok(
            codegen.FlextInfraMiseArtifactsJournal.write(
                layout, rebound, expected=original_state,
            ),
        )
        tm.ok(
            codegen.FlextInfraCodegenTransaction(
                codegen.FlextInfraCodegenMiseArtifacts(repository_root=root),
            ).run_files_locked({"@docs-0": root}, r[Path].ok),
        )
        tm.that((root / "generated.md").read_bytes(), eq=b"original document\n")
        tm.fail(tm.not_none(layout.file_participants[0].transaction_root).exists())

    @staticmethod
    def test_journal_read_rejects_foreign_scope_before_staging_effects(
        tmp_path: Path,
    ) -> None:
        """Keep physical-scope refusal and untrusted JSON ingress authoritative."""
        root = u.Tests.git_repository(tmp_path)
        (root / "generated.md").write_bytes(b"original document\n")
        prepared = TestsFlextInfraJournalRelocation._interrupted_staging(
            root, materialized=True,
        )
        layout = prepared.plan.layout
        payload = u.json_dict_adapter().validate_json(
            prepared.journal.model_dump_json(),
        )
        payload["scope_inode"] = prepared.journal.scope_inode + 1
        layout.journal_path.write_text(u.json_dumps(payload), encoding=c.DEFAULT_ENCODING)
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(layout.journal_path, required=True),
        )
        tm.fail(
            codegen.FlextInfraMiseArtifactsJournal.read(layout),
            has="another physical scope",
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(layout.journal_path, required=True)),
            eq=before,
        )
        tm.that((root / "generated.md").read_bytes(), eq=b"original document\n")
