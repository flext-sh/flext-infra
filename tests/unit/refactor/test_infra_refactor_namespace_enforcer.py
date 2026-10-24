"""Unit tests for the namespace enforcer's rule-catalog relocations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from flext_infra import m
from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer:
    """Behavior contract for test_infra_refactor_namespace_enforcer."""

    @staticmethod
    def test_selected_module_normalizes_alias_without_rewriting_sibling(
        tmp_path: Path,
    ) -> None:
        """The public dotted module selection bounds the actual repair effects."""
        workspace, project, pkg = u.Tests.namespace_workspace(tmp_path)
        (pkg / "helper.py").write_text(
            "from __future__ import annotations\n"
            "class SampleHelper:\n    value = 'published'\n"
            "__all__ = ['SampleHelper']\n",
            encoding="utf-8",
        )
        source = (
            "from __future__ import annotations\n"
            f"from {pkg.name}.helper import SampleHelper as files\n"
            "value = files.value\n"
        )
        target = pkg / "consumer.py"
        sibling = pkg / "sibling.py"
        target.write_text(source, encoding="utf-8")
        sibling.write_text(source, encoding="utf-8")
        u.Tests.provision_checkout(workspace)
        before = sibling.read_bytes()
        FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=True,
            module=u.Infra.module_name_for_file(target, project_root=project),
        )
        tm.that(target.read_text(encoding="utf-8"), lacks="as files")
        tm.that(target.read_text(encoding="utf-8"), has="value = SampleHelper.value")
        tm.that(sibling.read_bytes(), eq=before)

    @staticmethod
    def test_unknown_module_fails_before_repair(tmp_path: Path) -> None:
        """An unresolved selector cannot silently expand to the whole project."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        target = pkg / "consumer.py"
        source = b"from __future__ import annotations\nimport os as operating\n"
        target.write_bytes(source)
        with pytest.raises(ValueError, match="requires one owned module"):
            FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
                apply=True,
                module=f"{pkg.name}.missing",
            )
        tm.that(target.read_bytes(), eq=source)

    @staticmethod
    def test_namespace_enforcer_apply_moves_manual_protocol_to_protocols_file(
        tmp_path: Path,
    ) -> None:
        """Move a manual protocol into the canonical protocols module."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n\n"
            "class ServiceImpl:\n"
            "    def run(self) -> str:\n"
            "        return 'ok'",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=True,
        )

        tm.that(report.projects[0].relocation_findings, eq=0)
        protocols_file = pkg / "protocols.py"
        tm.ok(protocols_file.exists())

        protocols_source = protocols_file.read_text(encoding="utf-8")
        tm.that(protocols_source, has="class ServiceContract(Protocol):")
        tm.that(protocols_source, has="from __future__ import annotations")
        tm.that(protocols_source, has="from typing import Protocol")

    @staticmethod
    @pytest.mark.slow
    def test_namespace_enforcer_apply_keeps_autofixes_when_other_violations_remain(
        tmp_path: Path,
    ) -> None:
        """Relocate what a rule repairs and leave the detection-only finding."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\n"
            "import logging\n"
            "from typing import Protocol\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=True,
        )

        tm.that(report.projects[0].relocation_findings, eq=0)
        tm.that(service_file.read_text(encoding="utf-8"), has="logger = ")
        tm.ok((pkg / "protocols.py").exists())
        tm.that(
            (pkg / "protocols.py").read_text(encoding="utf-8"),
            has="class ServiceContract(Protocol):",
        )
        tm.that(
            service_file.read_text(encoding="utf-8"),
            lacks="class ServiceContract(Protocol):",
        )

    @staticmethod
    def test_namespace_enforcer_keeps_active_sources_beyond_declared_scan_dirs(
        tmp_path: Path,
    ) -> None:
        """A declared source root cannot hide active example declarations."""
        workspace, project, _pkg = u.Tests.namespace_workspace(
            tmp_path,
            pyproject=(
                "[project]\nname='sample'\nversion='1.0.0'\n\n"
                "[tool.flext.namespace]\nscan_dirs = ['src']\n"
            ),
        )
        examples_dir = project / "examples"
        examples_dir.mkdir(parents=True)
        _ = (examples_dir / "constants.py").write_text(
            "from __future__ import annotations\n\nclass DemoConstants:\n    pass\n",
            encoding="utf-8",
        )
        alias_file = examples_dir / "aliases.py"
        alias_source = "from __future__ import annotations\n\ntype LocalAlias = str\n"
        _ = alias_file.write_text(alias_source, encoding="utf-8")

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=False,
        )

        tm.that(report.projects, empty=False)
        tm.ok(report.projects[0].relocation_findings > 0)
        tm.that(alias_file.read_text(encoding="utf-8"), eq=alias_source)

    @staticmethod
    def test_namespace_enforcer_includes_discovered_python_tiers(
        tmp_path: Path,
    ) -> None:
        """Discover Python declarations without an allowlist of tier names."""
        workspace, project, _pkg = u.Tests.namespace_workspace(tmp_path)
        docs_dir = project / "docs"
        docs_dir.mkdir(parents=True)
        _ = (docs_dir / "contracts.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class HiddenContract(Protocol):\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=False,
        )

        tm.ok(report.projects[0].relocation_findings > 0)

    @staticmethod
    def test_namespace_enforcer_apply_keeps_script_shebang_when_adding_future(
        tmp_path: Path,
    ) -> None:
        """Preserve a script shebang while adding the future import."""
        workspace, project, _pkg = u.Tests.namespace_workspace(tmp_path)
        scripts_dir = project / "scripts"
        scripts_dir.mkdir(parents=True)
        script_file = scripts_dir / "run.py"
        _ = script_file.write_text(
            "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nu.Cli.print('ok')\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        _ = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(apply=True)

        rewritten_lines = script_file.read_text(encoding="utf-8").splitlines()
        tm.that(rewritten_lines[0], eq="#!/usr/bin/env python3")
        tm.that(rewritten_lines[1], eq="# -*- coding: utf-8 -*-")
        tm.that(rewritten_lines, has="from __future__ import annotations")

    @staticmethod
    def test_namespace_enforcer_apply_inserts_future_after_single_line_module_docstring(
        tmp_path: Path,
    ) -> None:
        """Insert the future import after a one-line module docstring."""
        workspace, project, _pkg = u.Tests.namespace_workspace(tmp_path)
        scripts_dir = project / "scripts"
        scripts_dir.mkdir(parents=True)
        target_file = scripts_dir / "base_improved.py"
        _ = target_file.write_text(
            '"""Improved test base with high automation and real functionality."""\n'
            "from pathlib import Path\n"
            "\n"
            "class DemoMigrationTestBase:\n"
            '    """Highly automated test base with real functionality patterns."""\n'
            "    temp_dir: Path\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        _ = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(apply=True)

        rewritten_lines = target_file.read_text(encoding="utf-8").splitlines()
        tm.ok(rewritten_lines[0].startswith('"""Improved test base'))
        future_index = rewritten_lines.index("from __future__ import annotations")
        import_index = rewritten_lines.index("from pathlib import Path")
        tm.ok(future_index > 0)
        tm.ok(future_index < import_index)

    @staticmethod
    def test_namespace_enforcer_does_not_rewrite_indented_import_aliases(
        tmp_path: Path,
    ) -> None:
        """Leave indented import aliases unchanged."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path, declare=False)
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\n\n"
            "def runner() -> None:\n"
            "    from flext_core import System\n"
            "    _ = System\n",
            encoding="utf-8",
        )

        _ = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(apply=True)

        service_source = service_file.read_text(encoding="utf-8")
        tm.that(service_source, has="    from flext_core import System")

    @staticmethod
    def test_namespace_enforcer_does_not_rewrite_multiline_import_alias_blocks(
        tmp_path: Path,
    ) -> None:
        """Leave multiline import alias blocks unchanged."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path, declare=False)
        module_file = pkg / "constants.py"
        _ = module_file.write_text(
            "from __future__ import annotations\n"
            "from flext_infra import (\n"
            "    FlextInfraConstantsCore,\n"
            "    FlextInfraConstantsSharedInfra,\n"
            ")\n"
            "\n"
            "class DemoConstants:\n"
            "    CORE = FlextInfraConstantsCore\n"
            "    SHARED = FlextInfraConstantsSharedInfra\n",
            encoding="utf-8",
        )

        _ = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(apply=True)

        module_source = module_file.read_text(encoding="utf-8")
        tm.that(module_source, has="from flext_infra import (")
        tm.that(module_source, has="FlextInfraConstantsCore")
        tm.that(module_source, has="FlextInfraConstantsSharedInfra")
        tm.that(module_source, has="CORE = FlextInfraConstantsCore")
        tm.that(module_source, has="SHARED = FlextInfraConstantsSharedInfra")

    @staticmethod
    def test_namespace_enforcer_apply_is_idempotent_on_the_second_pass(
        tmp_path: Path,
    ) -> None:
        """A second apply over the enforced tree relocates nothing new."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)
        enforcer = FlextInfraNamespaceEnforcer(repository_root=workspace)

        _first = enforcer.enforce(apply=True)
        enforced_sources = {
            path: path.read_text(encoding="utf-8") for path in sorted(pkg.rglob("*.py"))
        }

        second = enforcer.enforce(apply=True)

        tm.that(second.projects[0].relocation_findings, eq=0)
        tm.that(second.projects[0].relocation_resolved, eq=0)
        tm.that(second.projects[0].relocation_persisted, eq=0)
        tm.that(second.projects[0].relocation_introduced, eq=0)
        tm.that(
            second.projects[0].before_rule_counts,
            eq=second.projects[0].after_rule_counts,
        )
        for path, source in enforced_sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_namespace_enforcer_publishes_the_report_receipt(
        tmp_path: Path,
    ) -> None:
        """The command payload publishes the structured receipt under ``.reports``."""
        workspace, _project, _pkg = u.Tests.namespace_workspace(tmp_path)
        u.Tests.provision_checkout(workspace)

        result = FlextInfraNamespaceEnforcer.execute_command(
            m.Infra.RefactorNamespaceEnforceInput(repository_root=workspace),
        )

        receipt = (workspace / c.Infra.NAMESPACE_ENFORCE_REPORT_RELATIVE_PATH).resolve()
        tm.ok(receipt.exists())
        published = json.loads(receipt.read_text(encoding="utf-8"))
        tm.that(published["workspace"], eq=str(workspace))
        tm.that(published["projects"], empty=False)
        tm.that(result.failure, eq=published["has_violations"])

    @staticmethod
    def test_namespace_enforcer_report_mode_fails_on_findings_after_publishing(
        tmp_path: Path,
    ) -> None:
        """Remaining catalog findings fail the verdict; the receipt is published.

        A gate fails on every finding it counts: the report pass publishes the
        structured receipt first, then returns the failure naming the
        violations instead of a green verdict carrying them.
        """
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract awaiting relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        result = FlextInfraNamespaceEnforcer.execute_command(
            m.Infra.RefactorNamespaceEnforceInput(repository_root=workspace),
        )

        tm.fail(result, has="Namespace violations found")
        receipt = (workspace / c.Infra.NAMESPACE_ENFORCE_REPORT_RELATIVE_PATH).resolve()
        published = json.loads(receipt.read_text(encoding="utf-8"))
        tm.ok(published["projects"][0]["relocation_findings"] > 0)
        tm.ok(published["has_violations"])

    @staticmethod
    def test_namespace_enforcer_reports_detection_only_findings_separately(
        tmp_path: Path,
    ) -> None:
        """Detection-only residue remains visible without inflating relocations."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\n"
            "import logging\n"
            "from typing import Protocol\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=True,
        )

        tm.that(report.projects[0].relocation_findings, eq=0)
        tm.ok(report.projects[0].has_violations)
        tm.ok(any(row.after for row in report.projects[0].rule_deltas))
        tm.ok((pkg / "protocols.py").exists())

    @staticmethod
    def test_namespace_enforcer_apply_clears_the_pending_relocations(
        tmp_path: Path,
    ) -> None:
        """The apply pass performs the relocations the report pass counted."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)
        enforcer = FlextInfraNamespaceEnforcer(repository_root=workspace)

        pending = enforcer.enforce(apply=False)
        applied = enforcer.enforce(apply=True)

        tm.ok(pending.projects[0].relocation_findings > 0)
        tm.that(applied.projects[0].relocation_findings, eq=0)
        tm.ok((pkg / "protocols.py").exists())

    @staticmethod
    def test_namespace_enforcer_invalid_declaration_fails_before_any_effect(
        tmp_path: Path,
    ) -> None:
        """An invalid namespace declaration escapes loud; no project is touched.

        Project resolution validates every declaration before the first
        relocation, so the healthy project keeps its source untouched.
        """
        workspace = tmp_path / "workspace"
        _healthy, healthy_pkg = u.Tests.demo_project(workspace, name="healthy-proj")
        _ = (healthy_pkg / "service.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        broken, _broken_pkg = u.Tests.demo_project(workspace, name="broken-proj")
        _ = (broken / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='broken-proj'\n\n"
            "[tool.flext.namespace]\nenabled = 'yes'\n",
            encoding="utf-8",
        )
        u.Tests.declare_workspace_projects(workspace, ("healthy-proj", "broken-proj"))
        u.Tests.provision_checkout(workspace)

        with pytest.raises(TypeError, match="must be a boolean"):
            FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(apply=True)

        tm.fail((healthy_pkg / "protocols.py").exists())

    @staticmethod
    def test_namespace_enforcer_render_text_reports_the_totals(
        tmp_path: Path,
    ) -> None:
        """The text report carries the aggregate counters the operator reads."""
        workspace, _project, pkg = u.Tests.namespace_workspace(tmp_path)
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\n"
            "import logging\n"
            "from typing import Protocol\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Service contract under relocation."""\n'
            "\n"
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=True,
        )
        rendered = FlextInfraNamespaceEnforcer.render_text(report)

        tm.that(rendered, has="Violations: YES")
        tm.that(rendered, has="Relocation findings: 0")
        tm.that(rendered, has="Catalog findings:")
        tm.that(rendered, has="Introduced occurrences:")
        tm.that(
            rendered,
            has=f"Relocation files scanned: {report.projects[0].files_scanned}",
        )

    @staticmethod
    def test_namespace_report_retains_full_catalog_and_zero_count_rows(
        tmp_path: Path,
    ) -> None:
        """Report mode compares every elected rule against the real native scan."""
        workspace, project, pkg = u.Tests.namespace_workspace(tmp_path)
        source = (
            "from __future__ import annotations\nimport logging\n"
            "logger = logging.getLogger(__name__)\n"
        )
        (pkg / "service.py").write_text(source, encoding="utf-8")
        u.Tests.provision_checkout(workspace)
        expected = tm.ok(FlextInfraModGateEngine.scan(project, fix=False))
        plan = tm.ok(u.Infra.codemod_rule_plan(project))

        result = FlextInfraNamespaceEnforcer.execute_command(
            m.Infra.RefactorNamespaceEnforceInput(repository_root=workspace),
        )
        tm.fail(result, has="Namespace violations found")
        receipt = workspace / c.Infra.NAMESPACE_ENFORCE_REPORT_RELATIVE_PATH
        report = m.Infra.WorkspaceEnforcementReport.model_validate_json(
            receipt.read_bytes(),
        ).projects[0]

        tm.that(
            {row.rule_id for row in report.rule_deltas},
            eq={rule.id for rule in plan.rules},
        )
        tm.that(report.before_rule_counts, eq=report.after_rule_counts)
        tm.that(
            all(change == 0 for change in report.cross_rule_delta.values()), eq=True
        )
        tm.that(sum(report.after_rule_counts.values()), eq=expected.findings)
        tm.ok(any(row.after == 0 for row in report.rule_deltas))
        tm.that(report.relocation_findings, eq=0)
        tm.ok(report.has_violations)
        tm.that((pkg / "service.py").read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_namespace_apply_publishes_cross_rule_regression_after_relocation(
        tmp_path: Path,
    ) -> None:
        """A successful relocation cannot conceal a new detection-only occurrence."""
        workspace, project, pkg = u.Tests.namespace_workspace(tmp_path)
        config_path = project / c.Infra.CODEMOD_CONFIG_RELPATH
        rules = config_path.parent / c.Cli.RULES_DIR_NAME
        rules.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "ruleDirs:\n  - rules\ntestConfigs: []\n", encoding="utf-8"
        )
        rule_id = "namespace-destination-contract"
        (rules / "destination.yml").write_text(
            f"id: {rule_id}\nlanguage: Python\n"
            "rule:\n  pattern: |\n    class ServiceContract(Protocol):\n      $$$BODY\n"
            "files:\n  - '**/protocols.py'\nseverity: error\n",
            encoding="utf-8",
        )
        (pkg / "service.py").write_text(
            "from __future__ import annotations\nfrom typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            '    """Contract awaiting relocation."""\n'
            "    def run(self) -> str:\n"
            '        """Run the contract."""\n'
            "        ...\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)

        result = FlextInfraNamespaceEnforcer.execute_command(
            m.Infra.RefactorNamespaceEnforceInput(
                repository_root=workspace, apply=True
            ),
        )

        tm.fail(result, has="Namespace violations found")
        receipt = workspace / c.Infra.NAMESPACE_ENFORCE_REPORT_RELATIVE_PATH
        published = m.Infra.WorkspaceEnforcementReport.model_validate_json(
            receipt.read_bytes(),
        )
        report = published.projects[0]
        row = next(row for row in report.rule_deltas if row.rule_id == rule_id)
        tm.that((row.before, row.after, row.introduced), eq=(0, 1, 1))
        tm.that(report.cross_rule_delta[rule_id], eq=row.after - row.before)
        tm.that(report.relocation_findings, eq=0)
        tm.ok(report.relocation_resolved > 0)
        tm.that(report.relocation_introduced, eq=0)
        tm.ok(published.has_violations)
        tm.that(FlextInfraNamespaceEnforcer.render_text(published), has=rule_id)

    @staticmethod
    @pytest.mark.slow
    def test_namespace_workspace_counts_bracket_all_projects_without_double_counting(
        tmp_path: Path,
    ) -> None:
        """Every project compares the same initial and final workspace observations."""
        workspace, first, _pkg = u.Tests.namespace_workspace(tmp_path)
        second, _second_pkg = u.Tests.demo_project(workspace, name="another-project")
        for project in (first, second):
            scripts = project / "scripts"
            scripts.mkdir()
            (scripts / "run.py").write_text(
                '"""Governed script."""\nvalue = 1\n', encoding="utf-8"
            )
        u.Tests.declare_workspace_projects(workspace, (first.name, second.name))
        u.Tests.provision_checkout(workspace)
        before = tm.ok(FlextInfraModGateEngine.scan(workspace, fix=False))

        report = FlextInfraNamespaceEnforcer(repository_root=workspace).enforce(
            apply=True,
        )

        after = tm.ok(FlextInfraModGateEngine.scan(workspace, fix=False))
        tm.that(
            {project.project for project in report.projects},
            eq={first.name, second.name},
        )
        for project in report.projects:
            tm.that(
                {row.repository for row in project.rule_deltas}, eq={project.project}
            )
            for counts, snapshot in (
                (project.before_rule_counts, before),
                (project.after_rule_counts, after),
            ):
                tm.that(
                    counts,
                    eq={
                        rule_id: sum(
                            entry.repository == project.project
                            and entry.rule_id == rule_id
                            for entry in snapshot.entries
                        )
                        for rule_id in counts
                    },
                )
            tm.ok(project.relocation_resolved > 0)
