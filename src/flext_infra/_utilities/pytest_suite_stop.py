"""Runner suite-stop hook: end the pytest session at the derived stop instant.

The controller stops dispatch through the same path as max-failures: xdist
queues the shutdown marker, so each worker's final item runs with no successor
and pytest-testmon flushes every batched result. A stop therefore never waits
for a flushed batch: testmon flushes only at its batch size or on an item with
no successor, so waiting for one lets the run reach the process deadline,
whose SIGTERM discards every unflushed batch and every later run restarts from
the same prefix. A single-process session has no shutdown marker: the item
after the instant becomes the session's last item, testmon flushes on its
teardown, and the stop is requested there.

When every collected item has already completed, nothing is left to stop and
the stop request would only recolor a finished green suite red, so the request
is suppressed at that boundary.

An item still in flight at the process deadline (a class fixture is not
bounded by the per-item ``timeout_func_only`` budget) receives the runner's
SIGTERM. The controller turns it into pytest's own interruption, so testmon
saves its unflushed batch and the session still writes its junit, report log
and durations inside the termination grace instead of dying with
``executed=unknown``. Once pytest is already unwinding from an interruption, a
later deadline signal is ignored: a second signal must never kill the
finalization that publishes the executed prefix.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import signal
import time
from types import FrameType

from flext_infra import p, t, u
from flext_infra._utilities import FlextInfraUtilitiesPytest


class FlextInfraUtilitiesPytestSuiteStop:
    """The runner's single graceful suite-stop and deadline-interruption owner."""

    class SuiteStop:
        """End the session gracefully at the runner's derived stop instant."""

        def __init__(self, *, stop_at_monotonic: float) -> None:
            self.stop_at_monotonic = stop_at_monotonic
            self.session: t.Infra.Pytest.Session | None = None
            self.completed_items: set[str] = set()
            self.selected_count = 0
            self.stopping = False
            self.previous_sigint: t.Infra.SignalHandler = signal.SIG_DFL
            self.previous_sigterm: t.Infra.SignalHandler = signal.SIG_DFL

        def pytest_sessionstart(self, session: t.Infra.Pytest.Session) -> None:
            """Bind the controller session and its graceful wall interruption."""
            self.session = session
            self.previous_sigint = signal.signal(signal.SIGINT, self._interrupt)
            self.previous_sigterm = signal.signal(signal.SIGTERM, self._interrupt)

        def pytest_keyboard_interrupt(
            self,
            excinfo: t.Infra.Pytest.ExceptionInfo[BaseException],
        ) -> None:
            """Keep the announced interruption terminal for the rest of the process."""
            del excinfo
            self.stopping = True

        def pytest_unconfigure(self) -> None:
            """Restore the signal actions, or ignore them after an interruption."""
            actions = (
                (signal.SIGINT, self.previous_sigint),
                (signal.SIGTERM, self.previous_sigterm),
            )
            for number, previous in actions:
                if signal.getsignal(number) == self._interrupt:
                    signal.signal(
                        number,
                        signal.SIG_IGN if self.stopping else previous,
                    )

        def _interrupt(self, _signum: int, _frame: FrameType | None) -> None:
            """Unwind the session once through pytest's native interruption path.

            The soft SIGINT marks the interruption before pytest runs any
            ``pytest_keyboard_interrupt`` hook, so the deadline SIGTERM that
            lands inside a slow hook (testmon's coverage flush) is ignored
            instead of raising a second KeyboardInterrupt.

            Raises:
                KeyboardInterrupt: Until the first interruption is recorded.

            """
            if self.stopping:
                return
            self.stopping = True
            raise KeyboardInterrupt

        @FlextInfraUtilitiesPytest.Pytest.hookimpl(trylast=True)
        def pytest_collection_finish(self, session: t.Infra.Pytest.Session) -> None:
            """Record the selected population before any stop shortens it."""
            self.selected_count = len(session.items)

        def pytest_runtest_logreport(self, report: t.Infra.Pytest.TestReport) -> None:
            """Request the stop once a completed item crosses the instant.

            The request is suppressed when this item was the last one still
            pending: a suite that already finished must end green instead of
            being interrupted after its own final result.

            Raises:
                TypeError: If the native distributed controller has no stop port.

            """
            session = self.session
            if session is None or report.when != "teardown":
                return
            self.completed_items.add(report.nodeid)
            # The instant is computed in the runner parent and handed to this
            # process as a CLI option; a clock skew between the two (or a
            # stale parent clock) must never stop a suite whose deadline has
            # not actually passed on this process's own monotonic clock.
            if time.monotonic() < self.stop_at_monotonic:
                return
            total_items = self.selected_count or len(session.items)
            if total_items and len(self.completed_items) >= total_items:
                return
            reason = f"suite stop instant {self.stop_at_monotonic:.3f} reached"
            controller = session.config.pluginmanager.getplugin("dsession")
            if controller is None:
                # pytest's loop reads ``session.items`` for each successor, so
                # the next item runs with none and testmon flushes on its
                # teardown; the stop is requested on that final teardown.
                position = next(
                    index
                    for index, item in enumerate(session.items)
                    if item.nodeid == report.nodeid
                )
                if position + 2 < len(session.items):
                    del session.items[position + 2 :]
                elif position + 1 == len(session.items) and not session.shouldstop:
                    session.shouldstop = reason
                return
            if not isinstance(controller, p.Infra.PytestStopController):
                msg = "native distributed pytest controller has no stop port"
                raise TypeError(msg)
            shouldstop = u.type_adapter(bool | str).validate_python(
                controller.shouldstop,
                strict=True,
            )
            if not shouldstop:
                controller.shouldstop = reason


__all__ = ["FlextInfraUtilitiesPytestSuiteStop"]
