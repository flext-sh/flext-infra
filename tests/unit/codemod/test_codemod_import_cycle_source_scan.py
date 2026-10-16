"""Import-cycle admission and scan targets honor the source scan's ignored trees.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m
from tests import tm, u


class TestsFlextInfraCodemodImportCycleSourceScan:
    """A source-scan-ignored tree is not a missing production module."""

    @staticmethod
    def _cycle_rule() -> m.Infra.CodemodRule:
        """Return a probe rule whose only predicate is the import cycle.

        Returns:
            A probe rule whose only predicate is the import cycle.

        """
        return m.Infra.CodemodRule(
            id="import-cycle-probe",
            digest="probe",
            provider="probe",
            resource=Path("probe.yml"),
            fixable=False,
            context=(
                m.Infra.CodemodContextCondition(
                    variable="MODULE",
                    predicate=c.Infra.CodemodContextPredicate.IMPORT_CYCLE,
                    holds=True,
                    of="NAME",
                ),
            ),
        )

    def test_import_graph_uses_governed_workspace_sources(self, tmp_path: Path) -> None:
        """Keep live roots and member cycles, never historical or foreign trees."""
        root, member, package = u.Tests.namespace_workspace(
            tmp_path,
            project_name="fleet-member",
            package_name="fleet_member",
        )
        entry = root / "entry.py"
        entry.write_text("import fleet_member.live\n", encoding="utf-8")
        live = package / "live.py"
        live.write_text("import entry\n", encoding="utf-8")
        expected = {entry.resolve(), live.resolve()}
        for index, directory in enumerate(config.Infra.source_scan.roots):
            surface = root / directory / f"surface_{index}.py"
            surface.parent.mkdir(parents=True, exist_ok=True)
            surface.write_text("import entry\n", encoding="utf-8")
            expected.add(surface.resolve())
        foreign = u.Tests.git_repository(
            root / config.Infra.source_scan.roots[0],
            "foreign",
        )
        outsiders = (
            root / ".gc" / "worktrees" / "historical" / "retired.py",
            root / ".agents-sync-home" / "provider" / "hook.py",
            foreign / "retired.py",
        )
        for path in outsiders:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("import entry\n", encoding="utf-8")
        u.Tests.initialize_git_repo(member)

        facts = u.Infra.codemod_project_facts(root, (self._cycle_rule(),))

        tm.that(expected <= facts.import_modules.keys(), eq=True)
        tm.that(
            set(outsiders).isdisjoint(facts.import_modules),
            eq=True,
        )
        tm.that(facts.import_modules[live.resolve()], eq="fleet_member.live")
        tm.that(facts.import_graph["entry"], has="fleet_member.live")
        tm.that(facts.import_cycles["entry"], has="fleet_member.live")

    @staticmethod
    def test_snapshot_graph_keeps_its_proposed_source_inventory(tmp_path: Path) -> None:
        """Live scan bounds never remove captured modules from semantic snapshots."""
        project = u.Tests.mk_project(
            tmp_path,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "0.1.0"\n',
            with_src=True,
        )
        dependency = project / "captured_dependency" / "provider.py"
        dependency.parent.mkdir()
        (dependency.parent / "__init__.py").write_text("", encoding="utf-8")
        dependency.write_text("value = 1\n", encoding="utf-8")
        entry = project / "entry.py"
        entry.write_text("value = 1\n", encoding="utf-8")
        with u.Infra.open_project(project) as rope:
            snapshot = u.Infra.snapshot_project(
                rope,
                {entry: "import captured_dependency.provider\n"},
            )
            try:
                graph, modules = u.Infra.snapshot_import_graph(snapshot)
            finally:
                snapshot.close()

        tm.that(modules, has=dependency.resolve())
        tm.that(graph[modules[entry.resolve()]], has=modules[dependency.resolve()])

    def test_legado_is_outside_the_scanned_import_graph(
        self,
        tmp_path: Path,
    ) -> None:
        """A source-scan-ignored legado module is not a missing graph node."""
        project = u.Tests.mk_project(
            tmp_path,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "0.1.0"\n',
            with_src=True,
        )
        legado = project / "src" / "demo" / "legado" / "app_recovery.py"
        legado.parent.mkdir(parents=True)
        legado.write_text("from demo.live import value\n", encoding="utf-8")
        live = project / "src" / "demo" / "live.py"
        live.write_text("value = 1\n", encoding="utf-8")
        rule = self._cycle_rule()
        facts = u.Infra.codemod_project_facts(project, (rule,))

        verdict = u.Infra.codemod_context_admits(
            m.Infra.CodemodAdmission(
                root=project,
                rule=rule,
                file_path=legado,
                captures={
                    "MODULE": {"text": "demo.live"},
                    "NAME": {"text": "value"},
                },
                facts=facts,
            ),
        )
        tm.that(verdict, eq=False)
        late = live.with_name("late.py")
        late.write_text("from demo.live import value\n", encoding="utf-8")
        with pytest.raises(ValueError, match="absent from the project import graph"):
            u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=project,
                    rule=rule,
                    file_path=late,
                    captures={
                        "MODULE": {"text": "demo.live"},
                        "NAME": {"text": "value"},
                    },
                    facts=facts,
                ),
            )

    @staticmethod
    @pytest.mark.parametrize("reuse_config", [False, True])
    def test_generated_source_tree_is_outside_the_scan_targets(
        tmp_path: Path,
        reuse_config: bool,
    ) -> None:
        """`make mod` targets only the inventory its semantic phases index.

        Premise (flext-gknfx): the scan reached a generated protoc module the
        Rope inventory ignores, and the private-import phase then failed with
        "private import source missing from inventory".
        """
        names = config.Infra.codegen.generated_sources
        tm.that(names, empty=False)
        project = u.Tests.mk_project(
            tmp_path,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "0.1.0"\n',
            with_src=True,
        ).resolve()
        live = project / "src" / "demo" / "live.py"
        live.write_text("value = 1\n", encoding="utf-8")
        generated = project / "src" / "demo" / names[0] / "wire_pb2_grpc.py"
        generated.parent.mkdir(parents=True)
        generated.write_text("from grpc import _utilities\n", encoding="utf-8")

        targets = u.Infra.ast_grep_scan_targets(
            project,
            refactor_config=(
                u.Infra.load_refactor_config(project) if reuse_config else None
            ),
        )

        tm.that(targets, has=live.relative_to(project).as_posix())
        tm.that(targets, lacks=generated.relative_to(project).as_posix())
