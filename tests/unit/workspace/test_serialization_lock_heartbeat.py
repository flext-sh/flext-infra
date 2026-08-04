"""Lock-wait heartbeat progress for serialized Make ownership."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from filelock import FileLock
from flext_core import r
from flext_infra import p
from flext_infra.workspace.serialization_lock import FlextInfraSerializationLockOwner
from flext_tests import tm


class TestsFlextInfraSerializationLockHeartbeat:
    """Prove waiters emit stage progress instead of silent blocking."""

    def test_wait_progress_emits_heartbeat_while_lock_held(
        self, tmp_path: Path
    ) -> None:
        """A contended lock must heartbeat before the waiter proceeds."""
        lock_path = tmp_path / "make-single-flight.lock"
        held = Event()
        release = Event()
        heartbeats: list[tuple[Path, float]] = []

        def hold_lock() -> None:
            with FileLock(lock_path, timeout=1):
                held.set()
                tm.that(release.wait(timeout=15), where=bool)

        def waiter() -> p.Result[str]:
            return FlextInfraSerializationLockOwner.execute(
                (lock_path,),
                timeout_seconds=10,
                operation=lambda: r[str].ok("acquired"),
                timeout_failure=lambda path, seconds: r[str].fail(
                    f"timeout {path} {seconds}"
                ),
                acquisition_failure=lambda detail: r[str].fail(detail),
                wait_heartbeat_seconds=1,
                wait_progress=lambda path, waited: heartbeats.append((path, waited)),
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            holder_future = pool.submit(hold_lock)
            tm.that(held.wait(timeout=5), where=bool)
            waiter_future = pool.submit(waiter)
            deadline = time.monotonic() + 8
            while not heartbeats and time.monotonic() < deadline:
                time.sleep(0.05)
            tm.that(len(heartbeats) >= 1, where=bool, msg=str(heartbeats))
            tm.that(heartbeats[0][0], eq=lock_path)
            tm.that(heartbeats[0][1], gt=0.0)
            release.set()
            result = waiter_future.result(timeout=10)
            holder_future.result(timeout=5)

        tm.that(result.failure, eq=False, msg=result.error or "")
        tm.that(result.value, eq="acquired")
