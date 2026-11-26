"""A native scan never reuses findings cached for different source bytes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, tm, u

pytestmark = c.Tests.MARK.slow


class TestsFlextInfraCodemodScanCacheContentKey:
    """The scan cache key authenticates the content of every scanned source."""

    @staticmethod
    def _project(root: Path) -> tuple[Path, Path, tuple[str, ...]]:
        """Build a scannable project and elect its deep-import rule partition.

        Returns:
            The project root, its consumer test module and the elected rules.

        """
        package = root / c.Infra.DEFAULT_SRC_DIR / "flext_demo"
        tests_root = root / c.Infra.DIR_TESTS
        consumer = tests_root / "unit" / "test_client.py"
        sources = {
            package / c.Infra.INIT_PY: (
                "from flext_demo.client import Client\n__all__ = ['Client']\n"
            ),
            package / "client.py": "class Client:\n    pass\n",
            tests_root / c.Infra.INIT_PY: "",
            tests_root / "unit" / c.Infra.INIT_PY: "",
            consumer: "from flext_demo.client import Client\nPARTS = (Client,)\n",
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
        return root, consumer, selection

    @classmethod
    def test_rescan_after_repair_reports_no_stale_finding(
        cls, duplicate_project: Path
    ) -> None:
        """A repaired source scanned again at the same path reports nothing."""
        root, consumer, selection = cls._project(duplicate_project)
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
                consumer, "from flext_demo import Client\nPARTS = (Client,)\n"
            )
        )
        after = tm.ok(
            FlextInfraModGateEngine.scan(
                root, fix=False, selection=selection, source_files=(consumer,)
            )
        )
        tm.that(len(after.entries), eq=0)

    @classmethod
    def test_scan_resolves_tools_from_the_invocation_not_the_scanned_root(
        cls, duplicate_project: Path
    ) -> None:
        """A scanned root whose own manifest lacks ast-grep still scans.

        A linked worktree stages its preview under the primary checkout's Git
        directory, whose manifest need not declare the invocation's tools; the
        scan-cache key resolves ast-grep from the invocation owner, like the run.
        """
        root, consumer, selection = cls._project(duplicate_project)
        tm.ok(
            u.Cli.atomic_write_text_file(root / c.Infra.MISE_TOML_FILENAME, "[tools]\n")
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                root, fix=False, selection=selection, source_files=(consumer,)
            )
        )
        tm.that(
            {u.Infra.codemod_source_path(root, row.file) for row in report.entries},
            eq={consumer.resolve()},
        )

    @classmethod
    def test_unchanged_rescan_hits_and_one_change_rescans_one_source(
        cls, duplicate_project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An unchanged rescan is served whole; one edit rescans one source."""
        root, consumer, selection = cls._project(duplicate_project)
        package = root / c.Infra.DEFAULT_SRC_DIR / "flext_demo"
        first = tm.ok(
            FlextInfraModGateEngine.scan(root, fix=False, selection=selection)
        )
        capsys.readouterr()
        second = tm.ok(
            FlextInfraModGateEngine.scan(root, fix=False, selection=selection)
        )
        tm.that(capsys.readouterr().err, has=" miss=0\n")
        tm.that(len(second.entries), eq=len(first.entries))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "client.py", "class Client:\n    value = 1\n"
            )
        )
        third = tm.ok(
            FlextInfraModGateEngine.scan(root, fix=False, selection=selection)
        )
        tm.that(capsys.readouterr().err, has=" miss=1\n")
        tm.that(
            {u.Infra.codemod_source_path(root, row.file) for row in third.entries},
            eq={consumer.resolve()},
        )


__all__: list[str] = ["TestsFlextInfraCodemodScanCacheContentKey"]
