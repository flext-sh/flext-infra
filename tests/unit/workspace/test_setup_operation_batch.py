"""Exercise setup batches through original validators.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraCli
from tests import c, m, tm, u


class TestsFlextInfraSetupOperationBatch:
    """Repository scopes retain independent failures and successful real effects."""

    @staticmethod
    def _workspace(root: Path) -> tuple[Path, Path, Path]:
        """Compose two independent consumer repositories using the Git owner.

        Returns:
            The workspace root and its two declared member roots.

        """
        first = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        second = u.Tests.WorktreeFixture.self_named_project(
            root / "second-consumer",
            "second-consumer",
        )
        u.Tests.WorktreeFixture.write_gitmodules(
            root,
            (first.relative_to(root).as_posix(), second.relative_to(root).as_posix()),
        )
        return root, first, second

    @staticmethod
    def _report(root: Path, operation: str) -> m.Infra.WorkspaceOperationReport:
        """Read the operation's published typed receipt.

        Returns:
            The operation's published typed receipt.

        """
        return m.Infra.WorkspaceOperationReport.model_validate_json(
            (
                root
                / c.Infra.WORKSPACE_OPERATION_REPORT_DIRECTORY
                / f"{operation}.json"
            ).read_bytes(),
        )

    @staticmethod
    def _validate(root: Path, scope: c.Infra.CodegenConformScope) -> int:
        """Invoke the public offline validation route.

        Returns:
            The public validation route's exit status.

        """
        return FlextInfraCli.infra_main([
            c.Infra.CLI_GROUP_CODEGEN,
            "mise-artifacts",
            "--repository-root",
            str(root),
            "--config-only",
            "--scope",
            scope.value,
        ])

    def test_all_validation_reaches_both_members_after_a_native_middle_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Invalid TOML stays red while later declared roots are still validated."""
        root, first, second = self._workspace(tmp_path / "workspace")
        invalid = first / c.Infra.CONFIG_SPEC[0]
        invalid.write_text("[tools\n", encoding=c.DEFAULT_ENCODING)

        tm.ok(self._validate(root, c.Infra.CodegenConformScope.ALL) != 0)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root, first, second))
        tm.that(tuple(row.root for row in report.receipts), eq=report.scope)
        tm.ok(all(row.executed for row in report.receipts))
        tm.that(
            tuple(row.outcome for row in report.receipts),
            eq=(
                c.Infra.ToolOutcome.CLEAN,
                c.Infra.ToolOutcome.ERROR,
                c.Infra.ToolOutcome.CLEAN,
            ),
        )
        tm.that(report.receipts[1].issues[0].file, eq=str(first))
        tm.that(
            report.receipts[2].files,
            eq=(second / c.Infra.CONFIG_SPEC[0],),
        )
        tm.that(invalid.read_text(encoding=c.DEFAULT_ENCODING), eq="[tools\n")

    def test_self_validation_does_not_attempt_other_declared_roots(
        self,
        tmp_path: Path,
    ) -> None:
        """The standalone/member scope never expands into sibling operations."""
        root, first, _ = self._workspace(tmp_path / "workspace")
        (first / c.Infra.CONFIG_SPEC[0]).write_text(
            "[tools\n",
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(self._validate(root, c.Infra.CodegenConformScope.SELF), eq=0)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root,))
        tm.that(report.receipts[0].outcome, eq=c.Infra.ToolOutcome.CLEAN)

    def test_scaffold_validation_needs_no_git_checkout(
        self,
        tmp_path: Path,
    ) -> None:
        """A new declaration can be validated before scaffold Git initialization."""
        root = tmp_path / "scaffold"
        root.mkdir()
        u.Tests.copy_tracked_mise_seeds(root)

        tm.that(self._validate(root, c.Infra.CodegenConformScope.SELF), eq=0)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root,))
        tm.that(
            report.receipts[0].files,
            eq=(root / c.Infra.CONFIG_SPEC[0],),
        )

    def test_git_unmanaged_member_is_reported_without_validation_or_success(
        self,
        tmp_path: Path,
    ) -> None:
        """An explicit Git policy remains visible instead of being silently omitted."""
        root, first, second = self._workspace(tmp_path / "workspace")
        u.Tests.git_run(
            root,
            "config",
            "--file",
            c.Infra.GITMODULES,
            f"submodule.{first.name}.{c.Infra.GITMODULE_MANAGED_KEY}",
            c.ParserBooleanToken.FALSE,
        )
        (first / c.Infra.CONFIG_SPEC[0]).write_text(
            "[tools\n",
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(self._validate(root, c.Infra.CodegenConformScope.ALL), eq=0)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root, first, second))
        inactive = report.receipts[1]
        tm.fail(inactive.executed)
        tm.that(inactive.outcome, eq=None)
        tm.ok(bool(inactive.applicability))

    def test_required_missing_member_is_an_unexecuted_native_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Git-declared missing checkouts remain in the failed report inventory."""
        root, first, second = self._workspace(tmp_path / "workspace")
        missing = root / "absent-consumer"
        u.Tests.WorktreeFixture.write_gitmodules(
            root,
            (first.name, second.name, missing.name),
        )

        tm.ok(self._validate(root, c.Infra.CodegenConformScope.ALL) != 0)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root, first, second, missing))
        unavailable = report.receipts[-1]
        tm.that(unavailable.root, eq=missing)
        tm.fail(unavailable.executed)
        tm.that(unavailable.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(unavailable.issues[0].file, eq=str(missing))
        tm.fail(missing.exists())
