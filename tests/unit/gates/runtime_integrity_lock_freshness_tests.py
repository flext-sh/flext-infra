"""Runtime integrity proves the committed uv.lock matches its manifest.

A declaration can reach a checkout without any lock write, for example
through a merge. The gate must then report the stale lock instead of
installing and accepting the old resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.gates import FlextInfraGatesRuntimeIntegrity
from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRuntimeIntegrityLockFreshness:
    """The lock-freshness component follows the native ``uv lock --check``."""

    @staticmethod
    def _lock_freshness(project: Path) -> p.Infra.GateExecution:
        """Run the gate over the real consumer and select its lock component.

        Returns:
            The lock-freshness component execution.

        """
        context = m.Infra.GateContext(
            repository_root=project,
            reports_dir=project / ".reports",
        )
        gate = FlextInfraGatesRuntimeIntegrity(repository_root=project)
        execution = gate.check(project, context)
        tm.that(execution.requested_components, has=c.Infra.LOCK_FRESHNESS)
        return execution.components[c.Infra.LOCK_FRESHNESS]

    def test_a_fresh_lock_passes(self, duplicate_project: Path) -> None:
        """The provisioned consumer's own lock matches its manifest."""
        tm.ok(self._lock_freshness(duplicate_project).result.passed)

    def test_a_manifest_changed_without_relock_fails(
        self, duplicate_project: Path
    ) -> None:
        """A dependency declared after locking leaves the lock stale and red."""
        lock = duplicate_project / c.Infra.UV_LOCK_FILENAME
        before = lock.read_bytes()
        manifest = duplicate_project / c.PYPROJECT_FILENAME
        payload = u.Tests.toml_payload(manifest.read_text(encoding="utf-8"))
        project = u.Tests.toml_mapping(payload["project"])
        dependencies = u.Tests.toml_strings(project["dependencies"])
        tm.ok(
            u.Cli.toml_write_mapping(
                manifest,
                {
                    **payload,
                    "project": {**project, "dependencies": list(dependencies[1:])},
                },
            )
        )
        tm.fail(self._lock_freshness(duplicate_project).result.passed)
        tm.that(lock.read_bytes(), eq=before)
