"""Lock-artifact lifecycle contract for the canonical serialization owner.

A serialized Make verb reuses its per-checkout lock across invocations, so the
lock file is durable state that must survive. An isolated worktree transaction
is ephemeral by contract: everything it creates inside the sandbox and the
source checkout is torn down when the transaction ends, so a retained lock file
is leaked state. One owner serves both, therefore retention is a declared
parameter of the operation, never a hardcoded engine default.
"""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import p, u
from flext_tests import tm


def _noop() -> p.Result[bool]:
    return r[bool].ok(True)


def _timeout_failure(lock_path: Path, timeout_seconds: int) -> p.Result[bool]:
    return r[bool].fail(f"timeout on {lock_path} after {timeout_seconds}s")


def _acquisition_failure(error: str) -> p.Result[bool]:
    return r[bool].fail(f"acquisition failed: {error}")


class TestsSerializationLockLifecycle:
    """Prove the owner honours both durable and ephemeral lock lifecycles."""

    def test_durable_lock_artifact_survives_for_reuse(self, tmp_path: Path) -> None:
        """A serialized Make verb keeps its lock file for the next invocation."""
        lock_path = tmp_path / ".reports" / "locks" / "make-validation.lock"
        lock_path.parent.mkdir(parents=True)

        tm.ok(
            u.Infra.serialization_lock_execute(
                (lock_path,),
                1,
                _noop,
                timeout_failure=_timeout_failure,
                acquisition_failure=_acquisition_failure,
            )
        )

        tm.that(lock_path.exists(), eq=True)

    def test_ephemeral_lock_artifact_leaves_no_state_behind(
        self, tmp_path: Path
    ) -> None:
        """An isolated transaction leaves neither the lock nor its state root."""
        state_root = tmp_path / ".reports"
        lock_path = state_root / "flext-infra" / "make-validation.lock"
        lock_path.parent.mkdir(parents=True)

        tm.ok(
            u.Infra.serialization_lock_execute(
                (lock_path,),
                1,
                _noop,
                timeout_failure=_timeout_failure,
                acquisition_failure=_acquisition_failure,
                ephemeral=True,
            )
        )

        tm.that(lock_path.exists(), eq=False)
        tm.that(state_root.exists(), eq=False)

    def test_ephemeral_teardown_preserves_unrelated_state_siblings(
        self, tmp_path: Path
    ) -> None:
        """Teardown removes only the directories the lock itself created."""
        state_root = tmp_path / ".reports"
        lock_path = state_root / "flext-infra" / "make-validation.lock"
        lock_path.parent.mkdir(parents=True)
        sibling = state_root / "other-owner" / "keep.txt"
        sibling.parent.mkdir(parents=True)
        sibling.write_text("durable\n", encoding="utf-8")

        tm.ok(
            u.Infra.serialization_lock_execute(
                (lock_path,),
                1,
                _noop,
                timeout_failure=_timeout_failure,
                acquisition_failure=_acquisition_failure,
                ephemeral=True,
            )
        )

        tm.that(lock_path.exists(), eq=False)
        tm.that(sibling.exists(), eq=True)
        tm.that(state_root.exists(), eq=True)
