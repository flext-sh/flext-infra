"""Import-cycle admission and scan targets honor the source scan's ignored trees.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from flext_infra.validate import FlextInfraNamespaceValidator
from tests import c, m, tm, u


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

    @staticmethod
    @pytest.mark.parametrize("git_project", [False, True])
    def test_active_sources_share_one_inventory(
        tmp_path: Path,
        git_project: bool,
    ) -> None:
        """Root modules and arbitrary tiers cannot disappear behind configured roots."""
        project = u.Tests.mk_project(
            tmp_path,
            "inventory",
            pyproject=(
                '[project]\nname = "inventory"\nversion = "0.1.0"\n'
                '[tool.flext.namespace]\nscan_dirs = ["src"]\n'
            ),
            with_src=True,
        ).resolve()
        if git_project:
            u.Tests.initialize_git_repo(project)
        live_paths = (
            project / "root.py",
            project / "arbitrary" / "deep" / "tier" / "worker.py",
            project / "arbitrary" / "deep" / "tier" / "__init__.py",
        )
        for path in live_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("value = 1\n", encoding="utf-8")
        stub = live_paths[1].with_suffix(".pyi")
        stub.write_text("value: int\n", encoding="utf-8")
        root_stub = live_paths[0].with_suffix(".pyi")
        root_stub.write_text("value: int\n", encoding="utf-8")
        foreign = u.Tests.git_repository(project / "arbitrary", "foreign")
        isolated = project / "arbitrary" / "independent"
        isolated.mkdir()
        (isolated / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "independent"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        unmanaged = project / "arbitrary" / "unmanaged"
        (project / c.Infra.GITMODULES).write_text(
            '[submodule "unmanaged"]\npath = arbitrary/unmanaged\n'
            "url = https://example.invalid/unmanaged.git\nflext-managed = false\n",
            encoding="utf-8",
        )
        outsiders = (
            foreign / "foreign.py",
            isolated / "independent.py",
            unmanaged / "unmanaged.py",
            project / ".historical" / "retired.py",
            project / "arbitrary" / ".hidden" / "retired.py",
            *(
                project / "arbitrary" / name / "ignored.py"
                for name in config.Infra.codegen.source_scan_ignored
            ),
        )
        for path in outsiders:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("value = 2\n", encoding="utf-8")

        targets = u.Infra.ast_grep_scan_targets(
            project,
            refactor_config=m.Infra.RefactorConfigSpec(project_scan_dirs=("src",)),
        )
        target_paths = {project / target for target in targets}
        discovered = set(
            u.Infra.discover_python_files(
                project, workspace_excluded_top_dirs=frozenset()
            )
        )
        iterated = set(
            tm.ok(
                u.Infra.iter_python_files(
                    m.Infra.SourceScanRequest(project_roots=(project,))
                )
            )
        )
        inventory = FlextInfraCodemodSemanticApply.source_inventory(
            project,
            m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence](
                files=frozenset(), entries=()
            ),
        )

        tm.that(set(live_paths) <= target_paths, eq=True)
        tm.that(target_paths, has=stub)
        tm.that(target_paths, has=root_stub)
        tm.that(target_paths, eq=discovered)
        tm.that(set(outsiders).isdisjoint(target_paths), eq=True)
        python_targets = {
            path for path in target_paths if path.suffix == c.Infra.EXT_PYTHON
        }
        tm.that(iterated, eq=python_targets)
        tm.that(set(inventory), eq=target_paths)
        analyzer_roots = u.Infra.analyzer_python_roots(
            project, ("src",), workspace_excluded_top_dirs=frozenset()
        )
        tm.that(analyzer_roots[0], eq="src")
        for target in ("arbitrary", live_paths[0].name, root_stub.name):
            tm.that(analyzer_roots, has=target)
            tm.that(u.Infra.namespace_scan_dirs(project), has=target)
        with pytest.raises(ValueError, match="outside governed inventory"):
            u.Infra.ast_grep_scan_targets(project, source_files=(outsiders[0],))

    @staticmethod
    def test_unreadable_source_subtree_preserves_native_failure(tmp_path: Path) -> None:
        """Discovery cannot return a partial inventory after a native walk failure."""
        if os.name != "posix":
            pytest.skip("NOT EXECUTED: POSIX directory permissions are required")
        project = u.Tests.mk_project(
            tmp_path,
            "unreadable-inventory",
            pyproject='[project]\nname = "unreadable-inventory"\nversion = "0.1.0"\n',
        ).resolve()
        blocked = project / "arbitrary" / "unreadable"
        blocked.mkdir(parents=True)
        (blocked / "worker.py").write_text("value = 1\n", encoding="utf-8")
        original_mode = blocked.stat().st_mode
        blocked.chmod(0)
        try:
            if os.access(blocked, os.R_OK | os.X_OK):
                pytest.skip(
                    "NOT EXECUTED: current identity can traverse "
                    "chmod-inaccessible trees"
                )
            with pytest.raises(PermissionError) as discovery_error:
                u.Infra.discover_python_files(
                    project, workspace_excluded_top_dirs=frozenset()
                )
            tm.that(discovery_error.value.filename, eq=str(blocked))
            tm.that(discovery_error.value.errno, eq=errno.EACCES)
            result = u.Infra.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(project,))
            )
            tm.that(result.failure, eq=True)
            exception = result.exception
            assert isinstance(exception, PermissionError)
            tm.that(exception.filename, eq=str(blocked))
            tm.that(exception.errno, eq=errno.EACCES)
            with pytest.raises(RuntimeError) as unwrap_error:
                result.unwrap()
            tm.that(unwrap_error.value.__cause__ is exception, eq=True)
        finally:
            blocked.chmod(original_mode)

    @staticmethod
    def test_namespace_declarations_do_not_suppress_active_source_findings(
        tmp_path: Path,
    ) -> None:
        """Namespace validation reports arbitrary and root modules.

        Reported despite src-only config.
        """
        project = u.Tests.mk_project(
            tmp_path,
            "namespace-inventory",
            pyproject=(
                '[project]\nname = "namespace-inventory"\nversion = "0.1.0"\n'
                '[tool.flext.namespace]\nscan_dirs = ["src"]\n'
            ),
            with_src=True,
        )
        config_path = project / c.Infra.CODEMOD_CONFIG_RELPATH
        rules = config_path.parent / c.Cli.RULES_DIR_NAME
        rules.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            f"ruleDirs: [{c.Cli.RULES_DIR_NAME}]\n", encoding="utf-8"
        )
        rule_id = "active-source-probe"
        (rules / "active-source.yml").write_text(
            f"id: {rule_id}\nlanguage: Python\nseverity: error\n"
            "message: Active source finding\nrule:\n  pattern: probe($VALUE)\n",
            encoding="utf-8",
        )
        paths = (project / "root.py", project / "arbitrary" / "deep" / "worker.py")
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("probe(1)\n", encoding="utf-8")
        u.Tests.copy_tracked_mise_seeds(project)

        report = tm.ok(
            FlextInfraNamespaceValidator(repository_root=project).build_report()
        )

        tm.that(report.passed, eq=False)
        for path in paths:
            tm.that(
                any(
                    f"[{rule_id}] {path.relative_to(project).as_posix()}:" in violation
                    for violation in report.violations
                ),
                eq=True,
            )
