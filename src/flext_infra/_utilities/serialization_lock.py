"""Public utility composition for the canonical serialization lock owner."""

from __future__ import annotations

from pathlib import Path

from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.workspace.serialization_lock import FlextInfraSerializationLockOwner


class FlextInfraUtilitiesSerializationLock:
    """Expose deterministic lock ownership through ``u.Infra``."""

    @staticmethod
    def serialization_lock_execute[TValue](
        lock_paths: t.SequenceOf[Path],
        timeout_seconds: int,
        operation: p.Infra.ResultOperation[TValue],
        *,
        timeout_failure: p.Infra.LockTimeoutFailure[TValue],
        acquisition_failure: p.Infra.LockAcquisitionFailure[TValue],
        ephemeral: bool = False,
    ) -> p.Result[TValue]:
        """Delegate one typed operation to the sole native lock engine."""
        return FlextInfraSerializationLockOwner.execute(
            lock_paths,
            timeout_seconds,
            operation,
            timeout_failure=timeout_failure,
            acquisition_failure=acquisition_failure,
            ephemeral=ephemeral,
        )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesSerializationLock",)
