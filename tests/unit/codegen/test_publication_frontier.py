"""Verify ordered publication ownership with real journaled filesystem effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import infra, r
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from tests import c, m, p, t, tm, u


class TestsPublicationFrontier:
    """Historical sources advance only through actual native publication effects."""

    @staticmethod
    @pytest.mark.parametrize("external_drift", [False, True])
    def test_ordered_batches_authenticate_their_shared_destination(
        tmp_path: Path,
        external_drift: bool,
    ) -> None:
        """Ordered batches share a destination, and external drift fails it."""
        root = u.Tests.git_repository(tmp_path)
        target = root / c.Infra.MAKEFILE_FILENAME
        tm.ok(u.Cli.atomic_write_text_file(target, "VALUE := initial\n"))
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@bootstrap-0": root}
        receipts: list[m.Infra.CodegenPhaseOutcome] = []
        for value in ("first", "second"):
            if value == "second" and external_drift:
                tm.ok(u.Cli.atomic_write_text_file(target, "VALUE := external\n"))
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(target, required=True),
            )
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=before,
                desired_content=f"VALUE := {value}\n".encode(c.DEFAULT_ENCODING),
                desired_mode=tm.not_none(before.mode),
                source_states=(before,),
            )

            def publish(
                scope: Path,
                *,
                before: m.Cli.AtomicFileState = before,
                plan: m.Infra.CodegenFilePlan = plan,
            ) -> p.Result[t.VariadicTuple[Path]]:
                started = owner.begin_files_locked(scope, roots, (before,))
                if started.failure:
                    return r[t.VariadicTuple[Path]].from_failure(started)
                appended = owner.append_phase_locked(
                    started.value,
                    c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                    (plan,),
                )
                if appended.failure:
                    return r[t.VariadicTuple[Path]].from_failure(appended)
                return owner.commit_locked(
                    appended.value,
                    publication_receipts=receipts,
                )

            tm.ok(owner.run_files_locked(roots, publish))
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )

        composed = owner.publish_operation_receipt(
            request,
            tuple(receipts),
            scope_roots=(root,),
            completed=True,
        )

        if external_drift:
            tm.that(composed.failure, eq=True)
            tm.that(composed.error or "", has="differs from preceding output")
        else:
            tm.ok(composed)
            tm.that(
                target.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE := second\n"
            )
            tm.ok(
                infra.codegen_conform(
                    request.model_copy(
                        update={"mode": c.Infra.CodegenConformMode.CHECK}
                    ),
                ),
            )
            tm.that(
                receipts[0].sources[0].sha256,
                eq=u.Cli.sha256_bytes(b"VALUE := initial\n"),
            )
