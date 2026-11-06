"""Verify the authored setup/upg lease with actual isolated native workflows.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time

from tests import c, tm, u
from tests.unit.codegen.conftest import NativeLifecycle


class TestsNativeLifecycleLock:
    """Protect full setup/upg sequences without claiming to lease direct UV."""

    @staticmethod
    @c.Tests.MARK.parametrize("second_goal", ["setup", "upg"])
    def test_competing_workflows_do_not_interleave(
        native_lifecycle: NativeLifecycle,
        second_goal: str,
    ) -> None:
        """Hold an actual setup open while a second real workflow waits."""
        runtime = native_lifecycle
        barrier = runtime.root / "barrier"
        os.mkfifo(barrier)
        first = runtime.launch("setup", "first", LEASE_BARRIER=str(barrier))
        runtime.wait_ready(barrier, first)
        second = runtime.launch(second_goal, "second")
        time.sleep(0.1)
        tm.that(second.poll() is None)
        events = runtime.root / "events"
        tm.that(events.read_text().splitlines() == ["first begin"])
        barrier.write_text("release\n", encoding="utf-8")
        runtime.finish(first)
        runtime.finish(second)
        tm.that(
            events.read_text().splitlines()
            == [
                "first begin",
                "first end",
                "second begin",
                "second end",
            ]
        )

    @staticmethod
    def test_native_recursive_workflow_reuses_inherited_descriptor(
        native_lifecycle: NativeLifecycle,
    ) -> None:
        """A real nested Make invocation retains its parent's exclusive lease."""
        runtime = native_lifecycle
        runtime.finish(runtime.launch("setup", "recursive", LEASE_REENTER="yes"))
        tm.that(
            (runtime.root / "events").read_text().splitlines()
            == [
                "recursive begin",
                "recursive.nested begin",
                "recursive.nested end",
                "recursive end",
            ]
        )

    @staticmethod
    def test_forged_inheritance_without_descriptor_is_rejected(
        native_lifecycle: NativeLifecycle,
    ) -> None:
        """Environment metadata alone cannot authorize entry to the workflow."""
        runtime = native_lifecycle
        state = (runtime.root / ".state/.venv.lifecycle.lock").stat()
        output = runtime.finish(
            runtime.launch(
                "setup",
                "invalid",
                FLEXT_NATIVE_LIFECYCLE_LEASES=f"{state.st_dev}:{state.st_ino}",
            ),
            failure=True,
        )
        tm.that("lost its native lease descriptor" in output)
        tm.that(not (runtime.root / "events").read_text())

    @staticmethod
    def test_closed_inherited_descriptor_fails_without_deadlock(
        native_lifecycle: NativeLifecycle,
    ) -> None:
        """A real subprocess closing inherited descriptors fails before waiting."""
        runtime = native_lifecycle
        output = runtime.finish(
            runtime.launch(
                "setup",
                "closed",
                LEASE_CLOSE_FD="yes",
            ),
            failure=True,
        )
        tm.that("lost its native lease descriptor" in output)
        tm.that((runtime.root / "events").read_text().splitlines() == ["closed begin"])

    @staticmethod
    def test_uv_failure_releases_lease_and_preserves_physical_environment(
        native_lifecycle: NativeLifecycle,
    ) -> None:
        """A native failure propagates and a later actual UV operation succeeds."""
        runtime = native_lifecycle
        output = runtime.finish(runtime.launch("fail", "intermediate"), failure=True)
        tm.that("error:" in output.lower())
        runtime.finish(runtime.launch("upg", "recovery"))
        check = tm.ok(
            u.Cli.run_raw(
                (
                    str(runtime.root / ".venv/bin/python"),
                    "-I",
                    "-c",
                    "import pathlib,sys;print(pathlib.Path(sys.prefix).resolve())",
                ),
            )
        )
        tm.that(check.exit_code == 0, msg=check.stderr)
        tm.that(check.stdout.strip() == str(runtime.root / ".venv"))
        tm.that(
            (runtime.root / "events").read_text().splitlines()
            == [
                "intermediate begin",
                "recovery begin",
                "recovery end",
            ]
        )
