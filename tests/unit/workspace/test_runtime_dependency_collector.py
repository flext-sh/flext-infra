"""Verify dependency provenance through the native installed environment.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra.workspace import FlextInfraRuntimeDependencyCollector
from tests import c, m, tm, u


class TestsFlextInfraRuntimeDependencyCollector:
    """Installed vendor metadata must not compete with its owning distribution."""

    @staticmethod
    def test_collect_native_dependency_suppliers(tmp_path: Path) -> None:
        """The public collector accepts the current real wheel inventories."""
        root = tm.ok(
            u.Infra.git_repository_root(
                m.Infra.GitRepoRequest(repo_root=Path(__file__).parent),
            ),
        ).repository_root
        scan = tm.ok(
            u.Infra.capture_deptry_scan(
                root,
                Path(sys.executable).parent,
                config_path=root / c.PYPROJECT_FILENAME,
                json_output_path=tmp_path / "deptry.json",
            ),
        )
        tm.ok(
            FlextInfraRuntimeDependencyCollector(
                python=Path(sys.executable),
                development_only=(),
            )(root, scan),
        )

    @staticmethod
    def test_console_script_reference_is_usage_evidence(tmp_path: Path) -> None:
        """A Make recipe running a script elects its distribution.

        A script name that is only a prefix of the invoked one (``ansible`` in
        ``ansible-galaxy``) elects nothing, and removing the recipe removes it.
        """
        root = tmp_path / "consumer"
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        (root / "custom.mk").write_text(
            "galaxy:\n\t$(VIRTUAL_ENV)/bin/ansible-galaxy install -r req.yml\n",
            encoding="utf-8",
        )
        distributions = {
            "ansible-core": ("ansible-galaxy", "ansible-playbook"),
            "other": ("ansible",),
        }
        tm.that(
            tm.ok(
                FlextInfraRuntimeDependencyCollector.invoked_console_scripts(
                    root, distributions
                )
            ),
            eq=("ansible-core",),
        )
        (root / "custom.mk").write_text("galaxy:\n\t@true\n", encoding="utf-8")
        tm.that(
            tm.ok(
                FlextInfraRuntimeDependencyCollector.invoked_console_scripts(
                    root, distributions
                )
            ),
            eq=(),
        )
