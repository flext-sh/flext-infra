"""A native scan never reuses findings cached for different source bytes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodemodScanCacheContentKey:
    """The scan cache key authenticates the content of every scanned source."""

    @staticmethod
    def test_rescan_after_repair_reports_no_stale_finding(tmp_path: Path) -> None:
        """A repaired source scanned again at the same path reports nothing."""
        root = u.Tests.mk_project(
            tmp_path,
            "scan-cache",
            pyproject='[project]\nname = "scan-cache"\nversion = "0.1.0"\n',
            with_src=True,
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / "scan_cache"
        tests_root = root / c.Infra.DIR_TESTS
        consumer = tests_root / "unit" / "test_client.py"
        sources = {
            package / c.Infra.INIT_PY: (
                "from scan_cache.client import Client\n__all__ = ['Client']\n"
            ),
            package / "client.py": "class Client:\n    pass\n",
            tests_root / c.Infra.INIT_PY: "",
            tests_root / "unit" / c.Infra.INIT_PY: "",
            consumer: "from scan_cache.client import Client\nPARTS = (Client,)\n",
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            plan = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        selection = tuple(
            rule.id
            for rule in plan.rules
            if rule.partition_of == "rewire-deep-import-to-package"
        )
        before = tm.ok(
            FlextInfraModGateEngine.scan(
                root, fix=False, selection=selection, source_files=(consumer,)
            )
        )
        tm.that(
            {u.Infra.codemod_source_path(root, row.file) for row in before.entries},
            eq={consumer.resolve()},
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                consumer, "from scan_cache import Client\nPARTS = (Client,)\n"
            )
        )
        after = tm.ok(
            FlextInfraModGateEngine.scan(
                root, fix=False, selection=selection, source_files=(consumer,)
            )
        )
        tm.that(len(after.entries), eq=0)


__all__: list[str] = ["TestsFlextInfraCodemodScanCacheContentKey"]
