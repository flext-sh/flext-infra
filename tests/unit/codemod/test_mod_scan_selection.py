"""One native scanner selection preserves lexical ownership and collisions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraModScanSelection:
    """Exercise actual native findings through the public scanner boundary."""

    @staticmethod
    def test_native_selection_respects_binding_and_collision(
        mod_workspace: Path,
    ) -> None:
        """Admit each project's actual stable owner from one native capture."""
        cases = [
            (
                (
                    "from flext_infra.codemod.batch_gates import "
                    "FlextInfraModGateEngine as Engine\n"
                    "Engine.scan(root, fix=False, rule_ids=rules)\n"
                ),
                1,
                0,
            ),
            (
                (
                    "import flext_infra.codemod.batch_gates as native\n"
                    "native.FlextInfraModGateEngine.scan(root, fix=False, plan=plan)\n"
                ),
                1,
                0,
            ),
            (
                (
                    "from flext_infra.codemod.batch_gates import "
                    "FlextInfraModGateEngine as Engine\n"
                    "def use(Engine):\n"
                    "    Engine.scan(root, fix=False, rule_ids=rules)\n"
                ),
                0,
                0,
            ),
            (
                (
                    "from flext_infra.codemod.batch_gates import "
                    "FlextInfraModGateEngine as Engine\n"
                    "original = Engine\nEngine = independent\n"
                    "Engine.scan(root, fix=False, rule_ids=rules)\n"
                    "Engine = original\n"
                ),
                0,
                0,
            ),
            (
                (
                    "from flext_infra.codemod.batch_gates import "
                    "FlextInfraModGateEngine as Engine\n"
                    "Engine.scan(root, fix=False, selection=other(rule_ids=rules))\n"
                ),
                0,
                0,
            ),
            (
                (
                    "from flext_infra.codemod.batch_gates import "
                    "FlextInfraModGateEngine as Engine\n"
                    "Engine.scan(root, fix=False, rule_ids=rules, plan=plan)\n"
                ),
                0,
                1,
            ),
            (
                (
                    "from flext_infra.codemod.batch_gates import "
                    "FlextInfraModGateEngine as Engine\n"
                    "Engine.scan(root, fix=False, plan=plan, selection=plan)\n"
                ),
                0,
                1,
            ),
        ]
        projects = tuple(
            u.Tests.mk_project(
                mod_workspace,
                f"consumer-{index}",
                pyproject=(
                    f'[project]\nname = "consumer-{index}"\nversion = "0.1.0"\n'
                    "dependencies = []\n"
                ),
                with_src=True,
            )
            for index in range(len(cases))
        )
        for project, (source, _actionable, _conflicts) in zip(
            projects, cases, strict=True
        ):
            u.Tests.initialize_git_repo(project)
            (project / "consumer.py").write_text(source, encoding="utf-8")
        u.Tests.declare_workspace_projects(
            mod_workspace, tuple(project.name for project in projects)
        )
        rules = ("rewire-mod-scan-selection", "mod-scan-selection-conflict")
        report = tm.ok(
            FlextInfraModGateEngine.scan(mod_workspace, fix=False, selection=rules)
        )
        for project, (_source, actionable, conflicts) in zip(
            projects, cases, strict=True
        ):
            entries = tuple(
                entry for entry in report.entries if entry.repository == project.name
            )
            tm.that(sum(entry.actionable for entry in entries), eq=actionable)
            tm.that(sum(entry.rule_id == rules[1] for entry in entries), eq=conflicts)
            tm.that(len(entries), eq=actionable + conflicts)
