"""Thin transaction coordinator for newest Mise artifact publication."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from filelock import FileLock, Timeout
from flext_core import r
from flext_infra import m, settings
from flext_infra.codegen import _mise_artifacts_files as files
from flext_infra.codegen import _mise_artifacts_journal as journal_io
from flext_infra.codegen import _mise_artifacts_publication as publication
from flext_infra.codegen import _mise_artifacts_state as state
from flext_infra.codegen import _mise_artifacts_verification as verify
from flext_infra.codegen._codegen_file_staging import FlextInfraCodegenFileStaging
from flext_infra.codegen._mise_artifacts_recovery import FlextInfraMiseRecovery
from flext_infra.codegen._mise_artifacts_staging import FlextInfraMiseStaging
from flext_infra.codegen._mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenMiseArtifactTransaction:
    """Coordinate one workspace-wide transaction through focused owners."""

    def __init__(self, owner: p.Infra.MiseArtifactsOwner) -> None:
        self._owner = owner
        self._planner = FlextInfraMiseWorkspacePlanner(owner)
        self._recovery = FlextInfraMiseRecovery()
        self._staging = FlextInfraMiseStaging(owner)
        self._file_staging = FlextInfraCodegenFileStaging()

    def validate(
        self, config_plans: tuple[m.Infra.CodegenFilePlan, ...] = ()
    ) -> p.Result[bool]:
        """Validate one coherent live snapshot under the existing lock."""
        return self.run_locked(
            prepare=False,
            operation=lambda scope_root: self.validate_locked(scope_root, config_plans),
        )

    def validate_locked(
        self, scope_root: Path, config_plans: tuple[m.Infra.CodegenFilePlan, ...] = ()
    ) -> p.Result[bool]:
        """Validate a plan while the generation owner holds the workspace lock."""
        layout_result = (
            self._planner.layout_for_config_plans(scope_root, config_plans)
            if config_plans
            else self._planner.layout(scope_root)
        )
        if layout_result.failure:
            return r[bool].from_failure(layout_result)
        selected = self._planner.select_layout(layout_result.value, config_plans)
        if selected.failure:
            return r[bool].from_failure(selected)
        layout = selected.value
        journal = state.journal_state(layout)
        if journal.failure:
            return r[bool].from_failure(journal)
        if journal.value.content is not None:
            return r[bool].fail("pending Mise transaction requires apply-mode recovery")
        residue = state.transaction_residue(layout)
        if residue:
            return r[bool].fail(
                f"unpublished Mise staging requires apply-mode cleanup: {residue[0]}"
            )
        plan = self._planner.snapshot(layout, config_plans)
        if plan.failure:
            return r[bool].from_failure(plan)
        return verify.live(self._owner, plan.value)

    def execute(
        self, config_plans: tuple[m.Infra.CodegenFilePlan, ...]
    ) -> p.Result[bool]:
        """Recover if necessary, then publish one locked atomic workspace set."""
        published = self.run_locked(
            prepare=True,
            operation=lambda scope_root: self.publish_locked(scope_root, config_plans),
        )
        if published.failure:
            return r[bool].from_failure(published)
        return r[bool].ok(True)

    def run_locked[T](
        self, *, prepare: bool, operation: Callable[[Path], p.Result[T]]
    ) -> p.Result[T]:
        """Run one generation operation under the stable workspace lock."""
        scope_root = self._planner.scope_root()
        if scope_root.failure:
            return r[T].from_failure(scope_root)
        state_root = self._planner.state_root(scope_root.value)
        if state_root.failure:
            return r[T].from_failure(state_root)
        # The coordination root is transaction state, never a managed write, and
        # it is gitignored: a fresh clone has none. Creating it before the lock
        # in every mode is what lets `gen check` serialize against a concurrent
        # publisher on a checkout that has never published.
        prepared = state.prepare_common_state_root(scope_root.value, state_root.value)
        if prepared.failure:
            return r[T].from_failure(prepared)
        lock_path = state.validate_lock_path(state_root.value, require_existing=False)
        if lock_path.failure:
            return r[T].from_failure(lock_path)
        try:
            with FileLock(str(lock_path.value), timeout=0):
                return self._run_authenticated(
                    scope_root.value,
                    state_root.value,
                    prepare=prepare,
                    operation=operation,
                )
        except Timeout:
            holder = state.lock_holder(lock_path.value)
            if holder.failure:
                return r[T].fail(
                    "another Mise artifact transaction owns the workspace: "
                    f"{lock_path.value}; holder inspection failed: {holder.error}"
                )
            return r[T].fail(
                "another Mise artifact transaction owns the workspace: "
                f"{lock_path.value}; {holder.value}"
            )
        except OSError as exc:
            return r[T].fail_op("execute Mise toolchain transaction", exc)

    def _run_authenticated[T](
        self,
        scope_root: Path,
        state_root: Path,
        *,
        prepare: bool,
        operation: Callable[[Path], p.Result[T]],
    ) -> p.Result[T]:
        """Authenticate lock and layout before entering caller-owned work."""
        authenticated = state.validate_lock_path(state_root, require_existing=True)
        if authenticated.failure:
            return r[T].from_failure(authenticated)
        if prepare:
            reconciled = self._reconcile(scope_root, state_root)
            if reconciled.failure:
                return r[T].from_failure(reconciled)
        return operation(scope_root)

    def publish_locked(
        self,
        scope_root: Path,
        config_plans: tuple[m.Infra.CodegenFilePlan, ...],
        managed_plans: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[tuple[Path, ...]]:
        """Publish one planned bundle while its caller holds the stable lock."""
        result_type = r[tuple[Path, ...]]
        layout_result = self._planner.layout_for_config_plans(scope_root, config_plans)
        if layout_result.failure:
            return result_type.from_failure(layout_result)
        layout = layout_result.value
        plan = self._planner.snapshot(layout, config_plans)
        if plan.failure:
            return result_type.from_failure(plan)
        source_plans = (*config_plans, *managed_plans)
        reuse_live = self._can_reuse_live(plan.value)
        credential_command = settings.Infra.mise_github_credential_command
        if not reuse_live and (
            credential_command is None or not credential_command.strip()
        ):
            return result_type.fail(
                "MISE_GITHUB_CREDENTIAL_COMMAND is required for Mise lock publication"
            )
        journal_before = state.journal_state(layout)
        if journal_before.failure:
            return result_type.from_failure(journal_before)
        if journal_before.value.content is not None:
            return result_type.fail("Mise journal appeared after locked recovery")
        roots = state.prepare_state_roots(layout)
        if roots.failure:
            return result_type.from_failure(roots)
        residue = state.transaction_residue(layout)
        if residue:
            return result_type.fail(
                f"Mise transaction residue has no journal authority: {residue[0]}"
            )
        staging_journal = journal_io.begin(
            plan.value, managed_plans, source_plans=source_plans
        )
        if staging_journal.failure:
            return result_type.from_failure(staging_journal)
        staging_topology = verify.journal_topology(layout, staging_journal.value)
        if staging_topology.failure:
            return result_type.from_failure(staging_topology)
        staging_state = journal_io.write(
            layout, staging_journal.value, expected=journal_before.value
        )
        if staging_state.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(scope_root, staging_state)
            )
        directories = files.create_directories(
            layout, staging_journal.value.created_directories
        )
        if directories.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, directories)
            )
        created = state.create_transaction_roots(layout)
        if created.failure:
            return result_type.from_failure(self._recover_failure(scope_root, created))
        managed_staged = self._file_staging.stage(plan.value, managed_plans)
        if managed_staged.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, managed_staged)
            )
        staged = self._staging.stage(
            plan.value,
            credential_command=(credential_command or "").strip(),
            reuse_live=reuse_live,
        )
        if staged.failure:
            return result_type.from_failure(self._recover_failure(scope_root, staged))
        publications = (*managed_staged.value, *staged.value)
        sources = verify.sources(plan.value, source_plans=source_plans)
        if sources.failure:
            return result_type.from_failure(self._recover_failure(scope_root, sources))
        destinations = verify.destinations(plan.value, publications)
        if destinations.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, destinations)
            )
        prepared_journal = journal_io.prepare(
            plan.value, staging_journal.value, publications
        )
        if prepared_journal.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, prepared_journal)
            )
        prepared_topology = verify.journal_topology(
            layout, prepared_journal.value, publications
        )
        if prepared_topology.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, prepared_topology)
            )
        source_barrier = verify.sources(
            plan.value, prepared_journal.value, source_plans
        )
        if source_barrier.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, source_barrier)
            )
        destination_barrier = verify.destinations(plan.value, publications)
        if destination_barrier.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, destination_barrier)
            )
        prepared_state = journal_io.write(
            layout, prepared_journal.value, expected=staging_state.value
        )
        if prepared_state.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(scope_root, prepared_state)
            )
        published = publication.publish(
            self._owner, plan.value, prepared_journal.value, publications, source_plans
        )
        if published.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, published)
            )
        precommit = verify.published(publications)
        if precommit.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, precommit)
            )
        source_commit = verify.sources(plan.value, prepared_journal.value, source_plans)
        if source_commit.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, source_commit)
            )
        committed_journal = journal_io.commit(prepared_journal.value)
        if committed_journal.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, committed_journal)
            )
        committed_state = journal_io.write(
            layout, committed_journal.value, expected=prepared_state.value
        )
        if committed_state.failure:
            return result_type.from_failure(
                self._recover_failure(scope_root, committed_state)
            )
        changed = tuple(
            item.before.path
            for item in publications
            if (
                item.before.content != item.replacement.content
                or item.before.mode != item.replacement.mode
            )
        )
        cleaned = journal_io.cleanup(layout, committed_state.value)
        if cleaned.failure:
            return result_type.from_failure(cleaned)
        return result_type.ok(changed)

    def _can_reuse_live(self, plan: m.Infra.MiseToolchainWorkspacePlan) -> bool:
        """Return whether the exact planned config already has valid live artifacts."""
        if any(
            project.config.before.content != project.config.replacement_content
            or project.config.before.mode != project.config.replacement_mode
            for project in plan.projects
        ):
            return False
        validated = verify.live(self._owner, plan)
        if validated.failure:
            return False
        return True

    def _reconcile(self, scope_root: Path, state_root: Path) -> p.Result[bool]:
        journal = state.journal_state_at(state_root)
        if journal.failure:
            return r[bool].from_failure(journal)
        if journal.value.content is not None:
            recovered = self._recover(scope_root)
            if recovered.failure:
                return recovered
        return r[bool].ok(True)

    def _handle_journal_write_failure(
        self, scope_root: Path, failure: p.FailureLike
    ) -> p.Result[bool]:
        state_root = self._planner.state_root(scope_root)
        if state_root.failure:
            return self._attach_secondary(
                failure, f"state-root inspection failed: {state_root.error}"
            )
        observed = state.journal_state_at(state_root.value)
        if observed.failure:
            return self._attach_secondary(
                failure, f"journal inspection failed: {observed.error}"
            )
        if observed.value.content is None:
            return self._attach_secondary(failure, "durable journal disappeared")
        return self._recover_failure(scope_root, failure)

    def _recover_failure(
        self, scope_root: Path, failure: p.FailureLike
    ) -> p.Result[bool]:
        recovered = self._recover(scope_root)
        if recovered.failure:
            return self._attach_secondary(
                failure, f"recovery failed: {recovered.error}"
            )
        return r[bool].from_failure(failure)

    @staticmethod
    def _attach_secondary(failure: p.FailureLike, secondary: str) -> p.Result[bool]:
        """Attach cleanup evidence without replacing the first causal failure."""
        return r[bool].fail(
            f"{failure.error or ''}; {secondary}",
            error_code=failure.error_code,
            error_data=failure.error_data,
            exception=failure.exception,
        )

    def _recover(self, scope_root: Path) -> p.Result[bool]:
        """Recover only the topology authorized by the durable common journal."""
        state_root = self._planner.state_root(scope_root)
        if state_root.failure:
            return r[bool].from_failure(state_root)
        loaded = journal_io.read_state_root(state_root.value)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        journal, journal_state = loaded.value
        layout = self._planner.layout_from_selectors(scope_root, journal.projects)
        if layout.failure:
            return r[bool].from_failure(layout)
        return self._recovery.execute(layout.value, journal, journal_state)


__all__: list[str] = ["FlextInfraCodegenMiseArtifactTransaction"]
