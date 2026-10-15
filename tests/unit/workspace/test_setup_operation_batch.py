"""Exercise setup batches through original validators and environment writers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import main
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentMixin
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
        return main([
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

        tm.that(self._validate(root, c.Infra.CodegenConformScope.ALL) != 0, eq=True)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root, first, second))
        tm.that(tuple(row.root for row in report.receipts), eq=report.scope)
        tm.that(all(row.executed for row in report.receipts), eq=True)
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
            "false",
        )
        (first / c.Infra.CONFIG_SPEC[0]).write_text(
            "[tools\n",
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(self._validate(root, c.Infra.CodegenConformScope.ALL), eq=0)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root, first, second))
        inactive = report.receipts[1]
        tm.that(inactive.executed, eq=False)
        tm.that(inactive.outcome, eq=None)
        tm.that(bool(inactive.applicability), eq=True)

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

        tm.that(self._validate(root, c.Infra.CodegenConformScope.ALL) != 0, eq=True)

        report = self._report(root, "mise-artifacts")
        tm.that(report.scope, eq=(root, first, second, missing))
        unavailable = report.receipts[-1]
        tm.that(unavailable.root, eq=missing)
        tm.that(unavailable.executed, eq=False)
        tm.that(unavailable.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(unavailable.issues[0].file, eq=str(missing))
        tm.that(missing.exists(), eq=False)

    def test_read_only_member_policy_prevents_environment_effects(
        self,
        tmp_path: Path,
    ) -> None:
        """The original member's own policy governs writes without a root roster."""
        root, first, second = self._workspace(tmp_path / "workspace")
        manifest = tm.ok(u.Infra.load_workspace_manifest(first))[0]
        policy = manifest.model_copy(
            update={
                "repository": manifest.repository.model_copy(
                    update={"read_only": True},
                ),
            },
        )
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(first),
                policy.model_dump(mode="json", exclude_computed_fields=True),
            ),
        )

        tm.ok(
            FlextInfraWorkspaceEnvironmentMixin.execute_request(
                m.Infra.WorkspaceEnvironmentSyncRequest(
                    repository_root=root,
                    allow_direnv=False,
                ),
                scope=c.Infra.CodegenConformScope.ALL,
            ),
        )

        report = self._report(root, "sync-environment")
        tm.that(report.scope, eq=(root, first, second))
        inactive = report.receipts[1]
        tm.that(inactive.executed, eq=False)
        tm.that(inactive.outcome, eq=None)
        tm.that(bool(inactive.applicability), eq=True)
        tm.that((first / c.Infra.ENVRC_FILENAME).exists(), eq=False)
        tm.that((second / c.Infra.ENVRC_FILENAME).is_file(), eq=True)

    def test_environment_batch_preserves_invalid_destination_and_publishes_other_roots(
        self,
        tmp_path: Path,
    ) -> None:
        """A real writer rejection preserves successful independent publications."""
        root, first, second = self._workspace(tmp_path / "workspace")
        blocked = first / c.Infra.ENVRC_FILENAME
        blocked.mkdir()
        result = FlextInfraWorkspaceEnvironmentMixin.execute_request(
            m.Infra.WorkspaceEnvironmentSyncRequest(
                repository_root=root,
                allow_direnv=False,
            ),
            scope=c.Infra.CodegenConformScope.ALL,
        )

        tm.that(result.failure, eq=True)
        report = self._report(root, "sync-environment")
        tm.that(report.scope, eq=(root, first, second))
        tm.that(all(row.executed for row in report.receipts), eq=True)
        tm.that(report.receipts[1].outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(blocked.is_dir(), eq=True)
        for index in (0, 2):
            row = report.receipts[index]
            tm.that(row.outcome, eq=c.Infra.ToolOutcome.CLEAN)
            tm.that(row.files, eq=(row.root / c.Infra.ENVRC_FILENAME,))
            tm.that(row.files[0].is_file(), eq=True)
