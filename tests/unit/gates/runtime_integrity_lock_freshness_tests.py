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

pytestmark = c.Tests.MARK.slow

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

    @c.Tests.MARK.parametrize(
        "provisioned_infra_checkout", ["lock-freshness-native"], indirect=True
    )
    def test_a_fresh_lock_passes(
        self, provisioned_infra_checkout: tuple[str, Path]
    ) -> None:
        """The provisioned checkout's own lock matches its manifest."""
        _, project = provisioned_infra_checkout
        tm.ok(self._lock_freshness(project).result.passed)

    @c.Tests.MARK.parametrize(
        "provisioned_infra_checkout", ["lock-freshness-manifest"], indirect=True
    )
    def test_a_manifest_changed_without_relock_fails(
        self, provisioned_infra_checkout: tuple[str, Path]
    ) -> None:
        """A dependency declared after locking leaves the lock stale and red."""
        _, root = provisioned_infra_checkout
        lock = root / c.Infra.UV_LOCK_FILENAME
        before = lock.read_bytes()
        manifest = root / c.PYPROJECT_FILENAME
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
        tm.fail(self._lock_freshness(root).result.passed)
        tm.that(lock.read_bytes(), eq=before)
