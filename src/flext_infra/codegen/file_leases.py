"""Physical destination leases for recoverable file publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator, MutableMapping
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen import FlextInfraMiseArtifactsFiles

if TYPE_CHECKING:
    from collections.abc import Callable

    from flext_infra import p

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenFileLeases:
    """Hold destination identities for the lifetime of one transaction."""

    @staticmethod
    def prepare_source_controlplanes(roots: t.SequenceOf[Path]) -> p.Result[bool]:
        """Initialize native control planes before electing a source epoch.

        Persistent directories and their native lease identities become original
        source observations, not exceptions to a captured membership receipt.
        Never use this operation to repair a rejected persisted source epoch.

        Returns:
            Success after each physical root's guarded control-plane creation.

        """
        for root in dict.fromkeys(roots):
            try:
                FlextInfraMiseArtifactsFiles.physical_directory_identity(root).unwrap()
                plan = u.Cli.atomic_plan_directory_chain(
                    root / c.Infra.TRANSACTION_STATE_DIRNAME
                ).unwrap()
                u.Cli.atomic_create_directory_chain_guarded(
                    plan,
                    permission_mode=config.Infra.codegen.modes.directory_private,
                ).unwrap()
            except c.EXC_BROAD_RUNTIME_OS as exc:
                return r[bool].fail(str(exc), exception=exc)
            journal = plan.target / c.Infra.JOURNAL_NAME
            lock = journal.with_name(f"{journal.name}.lock")
            observed = u.Cli.atomic_read_binary_file_state(lock, required=False)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value.content is None:
                try:
                    with u.Infra.codegen_transaction_lease(journal):
                        u.Cli.atomic_read_binary_file_state(
                            lock, required=True
                        ).unwrap()
                except c.EXC_BROAD_RUNTIME_OS as exc:
                    return r[bool].fail(str(exc), exception=exc)
        return r[bool].ok(value=True)

    @staticmethod
    @contextmanager
    def mutation_lease(root: Path) -> Generator[None]:
        """Serialize one nontransactional writer with its canonical scope owner.

        Raises:
            ValueError: If mutation root changed before lease acquisition; or if
                mutation Git ownership changed before lease acquisition.

        """
        scope = u.Infra.git_mutation_scope(
            m.Infra.GitRepoRequest(repo_root=root),
        ).unwrap()
        physical = FlextInfraMiseArtifactsFiles.physical_directory_identity(
            scope.root
        ).unwrap()
        lease_directory = (
            scope.git_dir
            if scope.git_dir is not None
            else scope.root / c.Infra.TRANSACTION_STATE_DIRNAME
        )
        if lease_directory.is_symlink() or lease_directory.exists():
            FlextInfraMiseArtifactsFiles.physical_directory_identity(
                lease_directory
            ).unwrap()
        journal = lease_directory / c.Infra.JOURNAL_NAME
        u.Cli.atomic_read_binary_file_state(
            journal.with_name(f"{journal.name}.lock"),
            required=False,
        ).unwrap()
        with u.Infra.codegen_transaction_lease(journal):
            FlextInfraMiseArtifactsFiles.physical_directory_identity(
                lease_directory
            ).unwrap()
            if (
                FlextInfraMiseArtifactsFiles.physical_directory_identity(
                    scope.root
                ).unwrap()
                != physical
            ):
                msg = f"mutation root changed before lease acquisition: {scope.root}"
                raise ValueError(msg)
            if (
                u.Infra.git_mutation_scope(
                    m.Infra.GitRepoRequest(repo_root=scope.root),
                ).unwrap()
                != scope
            ):
                msg = (
                    f"mutation Git ownership changed before lease "
                    f"acquisition: {scope.root}"
                )
                raise ValueError(msg)
            yield

    def __init__(
        self,
        participant_policy: p.Infra.CodegenParticipantPolicy | None = None,
    ) -> None:
        """Start without borrowed destination capabilities."""
        self._file_leases: MutableMapping[Path, m.Infra.CodegenFileParticipant] = {}
        self._participant_policy = (
            None
            if participant_policy is None
            else m.Infra.CodegenParticipantPolicy.model_validate(
                participant_policy,
                from_attributes=True,
            )
        )

    def _authorize_roots(
        self,
        roots: t.VariadicTuple[Path],
        paths: t.VariadicTuple[Path] = (),
    ) -> p.Result[bool]:
        """Reauthenticate injected capabilities before any destination effect.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        policy = self._participant_policy
        if policy is None:
            return r[bool].ok(value=True)
        authorized = {root.target: root for root in policy.roots}
        for root in dict.fromkeys((policy.scope_root, *roots)):
            expected = authorized.get(root)
            if expected is None:
                return r[bool].fail(
                    f"generation participant is outside authorized roots: {root}; "
                    "pending journal preserved",
                )
            observed = u.Cli.atomic_plan_directory_chain(root)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != expected:
                return r[bool].fail(f"generation authorized root changed: {root}")
        for path in paths:
            if (
                not path.is_absolute()
                or ".." in path.parts
                or not any(path.is_relative_to(root) for root in roots)
                or path.resolve() != path
            ):
                return r[bool].fail(
                    f"generation effect is outside authorized participants: {path}; "
                    "pending journal preserved",
                )
        return r[bool].ok(value=True)

    def _prepare_source_controlplanes(
        self,
        roots: t.MappingKV[str, Path],
        created: t.MutableSequenceOf[m.Cli.AtomicDirectoryState],
    ) -> None:
        """Create only authenticated native control planes under existing leases.

        Raises:
            ValueError: A participant is absent or its physical identity changed.

        """
        for root in dict.fromkeys(roots.values()):
            participant = self._file_leases.get(root)
            if participant is None:
                message = f"source preview participant has no native lease: {root}"
                raise ValueError(message)
            physical = FlextInfraMiseArtifactsFiles.physical_directory_identity(
                root
            ).unwrap()
            if physical != (participant.device, participant.inode):
                message = f"source preview participant changed before capture: {root}"
                raise ValueError(message)
            control = root / c.Infra.TRANSACTION_STATE_DIRNAME
            self._authorize_roots((root,), (control,)).unwrap()
            plan = u.Cli.atomic_plan_directory_chain(control).unwrap()
            created.extend(
                u.Cli.atomic_create_directory_chain_guarded(
                    plan,
                    permission_mode=config.Infra.codegen.modes.directory_private,
                ).unwrap()
            )

    @staticmethod
    def _source_controlplane_cleanup(
        created: t.SequenceOf[m.Cli.AtomicDirectoryState],
    ) -> p.Result[bool]:
        """Remove only the exact empty control-plane directories this run created.

        Returns:
            Success or the first native identity/emptiness refusal.

        """
        failure: p.Result[bool] | None = None
        for state in reversed(created):
            cleaned = u.Cli.atomic_delete_empty_directory_guarded(state)
            if failure is None and cleaned.failure:
                failure = cleaned
        return failure if failure is not None else r[bool].ok(value=True)

    def _source_controlplane_operation[T](
        self,
        roots: t.MappingKV[str, Path],
        operation: Callable[[], p.Result[T]],
        identities: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan],
    ) -> p.Result[T]:
        """Keep native preparation outside the source epoch and retain first failure.

        Args:
            roots: The original capability roots held by native file leases.
            operation: Source capture and validation within those roots.
            identities: Original participant directory witnesses checked first.

        Returns:
            The operation result, with any native cleanup refusal attached.

        """
        for identity in identities:
            observed = u.Cli.atomic_plan_directory_chain(identity.target)
            if observed.failure:
                return r[T].from_failure(observed)
            if observed.value != identity:
                return r[T].fail(
                    "source preview participant changed before capture: "
                    f"{identity.target}"
                )
        created: list[m.Cli.AtomicDirectoryState] = []
        try:
            self._prepare_source_controlplanes(roots, created)
            outcome = operation()
        except Exception as exception:
            cleaned = self._source_controlplane_cleanup(created)
            if cleaned.failure:
                exception.add_note(
                    cleaned.error or "source control-plane cleanup failed"
                )
            raise
        cleaned = self._source_controlplane_cleanup(created)
        if cleaned.failure:
            if outcome.failure:
                return r[T].fail(
                    outcome.error or "source preview failed",
                    error_code=outcome.error_code,
                    exception=outcome.exception,
                    error_data={
                        **(outcome.error_data or {}),
                        "controlplane_cleanup_error": cleaned.error,
                    },
                )
            return r[T].from_failure(cleaned)
        return outcome

    @contextmanager
    def _lease_file_participants(
        self,
        participants: t.VariadicTuple[m.Infra.CodegenFileParticipant],
    ) -> Generator[None]:
        """Serialize every destination through its own participant lease.

        The journal lease anchors one repository's recovery authority only; each
        written root, the run's own repository included, holds its participant
        lease so a workspace run and a member run never publish concurrently.

        Raises:
            ValueError: If file publication root changed before lease; or if file
                publication root changed during lease.

        """
        self._authorize_roots(
            tuple(participant.root for participant in participants),
            tuple(participant.transaction_root for participant in participants),
        ).unwrap()
        for participant in participants:
            physical = FlextInfraMiseArtifactsFiles.physical_directory_identity(
                participant.root
            ).unwrap()
            if physical != (participant.device, participant.inode):
                msg = f"file publication root changed before lease: {participant.root}"
                raise ValueError(msg)
        acquired: set[Path] = set()
        try:
            with ExitStack() as stack:
                for participant in sorted(
                    participants,
                    key=lambda item: str(item.root),
                ):
                    if participant.root in self._file_leases:
                        continue
                    lease_directory = (
                        participant.root / c.Infra.TRANSACTION_STATE_DIRNAME
                    )
                    if lease_directory.is_symlink() or lease_directory.exists():
                        FlextInfraMiseArtifactsFiles.physical_directory_identity(
                            lease_directory
                        ).unwrap()
                    lease_path = lease_directory / c.Infra.JOURNAL_NAME
                    u.Cli.atomic_read_binary_file_state(
                        lease_path.with_name(f"{lease_path.name}.lock"),
                        required=False,
                    ).unwrap()
                    stack.enter_context(u.Infra.codegen_transaction_lease(lease_path))
                    FlextInfraMiseArtifactsFiles.physical_directory_identity(
                        lease_directory
                    ).unwrap()
                    acquired.add(participant.root)
                    self._file_leases[participant.root] = participant
                    physical = FlextInfraMiseArtifactsFiles.physical_directory_identity(
                        participant.root,
                    ).unwrap()
                    if physical != (participant.device, participant.inode):
                        msg = (
                            f"file publication root changed during lease: "
                            f"{participant.root}"
                        )
                        raise ValueError(msg)
                yield
        finally:
            for root in acquired:
                self._file_leases.pop(root)


__all__: list[str] = ["FlextInfraCodegenFileLeases"]
