"""The runner's single graceful suite-stop and deadline-interruption owner.

Under xdist the controller stops dispatch through the same shutdown path as
max-failures, so testmon flushes every batched result; a single-process session
instead removes the items after the stop instant. A deadline SIGTERM unwinds
the suite through pytest's own interruption once, so JUnit, report log and
testmon still publish the executed prefix; later signals never kill that
finalization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import signal
import time
from types import FrameType

from flext_infra import c, p, t, u
from flext_infra._utilities import FlextInfraUtilitiesPytest


class FlextInfraUtilitiesPytestSuiteStop:
    """End the session at the runner's derived stop instant."""

    class SuiteStop:
        """The stop instant, the deadline interruption and their terminal state."""

        def __init__(self, *, stop_at_monotonic: float) -> None:
            self.stop_at_monotonic = stop_at_monotonic
            self.session: t.Infra.Pytest.Session | None = None
            self.completed_items: set[str] = set()
            self.selected_count = 0
            self.stopping = False
            self.previous_sigterm: t.Infra.SignalHandler = signal.SIG_DFL

        def pytest_sessionstart(self, session: t.Infra.Pytest.Session) -> None:
            """Bind the session and its graceful wall interruption."""
            self.session = session
            self.previous_sigterm = signal.signal(signal.SIGTERM, self._interrupt)

        def pytest_keyboard_interrupt(
            self,
            excinfo: t.Infra.Pytest.ExceptionInfo[BaseException],
        ) -> None:
            """Keep the announced interruption terminal for the process."""
            del excinfo
            self.stopping = True

        def pytest_unconfigure(self) -> None:
            """Restore the SIGTERM action, or ignore it after an interruption."""
            if signal.getsignal(signal.SIGTERM) == self._interrupt:
                signal.signal(
                    signal.SIGTERM,
                    signal.SIG_IGN if self.stopping else self.previous_sigterm,
                )

        def _interrupt(self, _signum: int, _frame: FrameType | None) -> None:
            """Unwind the session through pytest's native interruption path.

            Raises:
                KeyboardInterrupt: Until pytest has caught the interruption, so
                    it runs its interrupt hooks; later signals only skip.

            """
            if not self.stopping:
                raise KeyboardInterrupt

        @FlextInfraUtilitiesPytest.Pytest.hookimpl(trylast=True)
        def pytest_collection_finish(self, session: t.Infra.Pytest.Session) -> None:
            """Record the selected population before any stop shortens it."""
            self.selected_count = len(session.items)

        def pytest_runtest_logreport(self, report: t.Infra.Pytest.TestReport) -> None:
            """Request the stop once a completed item crosses the instant.

            A suite whose every item completed is never recolored red.

            Raises:
                TypeError: If the native distributed controller has no stop port.

            """
            session = self.session
            if session is None or report.when != c.Infra.PYTEST_TEARDOWN_PHASE:
                return
            self.completed_items.add(report.nodeid)
            if time.monotonic() < self.stop_at_monotonic:
                return
            total = self.selected_count or len(session.items)
            if total and len(self.completed_items) >= total:
                return
            reason = c.Infra.PYTEST_SUITE_STOP_REASON.format(
                instant=self.stop_at_monotonic,
            )
            controller = session.config.pluginmanager.getplugin(
                c.Infra.PYTEST_DISTRIBUTED_PLUGIN,
            )
            if controller is None:
                self._stop_local(session, report, reason)
                return
            if not isinstance(controller, p.Infra.PytestStopController):
                msg = "native distributed pytest controller has no stop port"
                raise TypeError(msg)
            if not u.type_adapter(bool | str).validate_python(
                controller.shouldstop,
                strict=True,
            ):
                controller.shouldstop = reason

        @staticmethod
        def _stop_local(
            session: t.Infra.Pytest.Session,
            report: t.Infra.Pytest.TestReport,
            reason: str,
        ) -> None:
            """Make the item after the instant the session's last item."""
            position = next(
                index
                for index, item in enumerate(session.items)
                if item.nodeid == report.nodeid
            )
            if position + 2 < len(session.items):
                del session.items[position + 2 :]
            elif position + 1 == len(session.items) and not session.shouldstop:
                session.shouldstop = reason


__all__: list[str] = ["FlextInfraUtilitiesPytestSuiteStop"]
