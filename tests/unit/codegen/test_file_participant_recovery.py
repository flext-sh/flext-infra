"""Public recovery behavior for file-only transaction participants."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_core import r
from flext_infra import u
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from tests import u as test_u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFileParticipantRecovery:
    """Recover prepared file-only journals through their physical owners."""

    def test_recovers_external_only_prepared_journal(self, tmp_path: Path) -> None:
        workspace = test_u.Tests.create_docs_workspace(tmp_path, project_names=())
        docs_root = tmp_path / "published-docs"
        docs_root.mkdir()
        roots = {"@docs-0": docs_root}
        source = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                workspace / "README.md", required=True
            )
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=workspace)
        )

        prepared = transaction.run_files_locked(
            roots,
            lambda scope_root: transaction.begin_files_locked(
                scope_root, roots, (source,)
            ),
        )
        tm.ok(prepared)

        recovered = transaction.run_files_locked(
            roots, lambda _scope_root: r[bool].ok(True)
        )

        tm.ok(recovered)
        tm.that(recovered.value, eq=True)


__all__ = ["TestsFlextInfraFileParticipantRecovery"]
