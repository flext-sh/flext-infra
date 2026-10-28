"""Fail-closed public behavior for the jscpd duplication gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.check import FlextInfraGateRegistry
from flext_infra.gates import FlextInfraDuplicationGate
from tests import c, m, tm, u


@pytest.mark.usefixtures("_ci_context")
class TestsFlextInfraDuplicationGate:
    """Exercise observable gate behavior with the real setup-provisioned tool.

    Every scan runs in the declared CI context: the embedding pass needs a
    host a unit test never reaches, so it is typed NOT EXECUTED there.
    """

    @staticmethod
    @pytest.fixture
    def _ci_context() -> Generator[None]:
        ci = config.Infra.codegen.make.ci
        with u.Tests.env_vars_context({ci.variable: ci.value}):
            yield

    _DUPLICATED_MODULE = """\
def normalize_records(records: list[str]) -> t.VariadicTuple[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for record in records:
        candidate = record.strip().casefold()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return tuple(sorted(normalized))
"""

    @staticmethod
    def _ctx(root: Path) -> m.Infra.GateContext:
        return m.Infra.GateContext(repository_root=root, reports_dir=root / "reports")

    @staticmethod
    def test_registry_exposes_the_canonical_gate() -> None:
        """Test registry exposes the canonical gate."""
        gate = FlextInfraGateRegistry.default().create("duplication", Path.cwd())
        tm.ok(isinstance(gate, FlextInfraDuplicationGate))

    def test_empty_workspace_scope_is_a_blocking_failure(self, tmp_path: Path) -> None:
        """Test empty workspace scope is a blocking failure."""
        project = tmp_path / "missing-project"
        project.mkdir()

        execution = FlextInfraDuplicationGate(tmp_path).check(
            project,
            self._ctx(tmp_path),
        )

        tm.fail(execution.result.passed)
        tm.that(len(execution.issues), eq=1)
        tm.that(
            execution.issues[0].message,
            has=(
                "duplication scan did not produce its required JSON report "
                "for project missing-project"
            ),
        )
        tm.that(execution.issues[0].severity, eq=str(c.Infra.GateSeverity.ERROR.value))

    @staticmethod
    def _governed_with_declared_trees(tmp_path: Path, *, declare_trees: bool) -> Path:
        """One governed checkout whose clones live only inside charts/.

        Returns:
            The resulting ``Path``.

        """
        root = tmp_path / "governed-duplication"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-duplication",
            beads=u.Tests.BeadsIdentity(
                workspace="duplication-workspace",
                database="duplication-database",
                issue_prefix="duplication-prefix",
            ),
        )
        package = root / "src" / "fixture_duplication"
        package.mkdir(parents=True, exist_ok=True)
        (root / "src" / "fixture_duplication" / "unique.py").write_text(
            "UNIQUE_MODULE_MARKER = 'canonical-scope-only'\n",
            encoding="utf-8",
        )
        (root / "charts").mkdir()
        # The clone must clear BOTH typed gate floors (lines and tokens); a
        # block under the token floor is skipped by the scanner, never a clone.
        chart_block = "apiVersion: apps/v1\nkind: Deployment\nenv:\n" + "".join(
            f"  - name: FIXTURE_SETTING_{index}\n    value: fixture-value-{index}\n"
            for index in range(max(c.Infra.JSCPD_MIN_LINES, c.Infra.JSCPD_MIN_TOKENS))
        )
        (root / "charts" / "values.yaml").write_text(chart_block, encoding="utf-8")
        nested = root / "charts" / "workers" / "prod"
        nested.mkdir(parents=True)
        (nested / "values.yaml").write_text(chart_block, encoding="utf-8")
        if declare_trees:
            manifest = root / "config" / "workspace.yaml"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            provider = u.Tests.provider()
            url = u.Tests.WorktreeFixture.governed_repository_url("fixture-duplication")
            manifest.write_text(
                "version: 3\n"
                "name: duplication-workspace\n"
                "repository:\n"
                "  name: fixture-duplication\n"
                "  distribution: fixture-duplication\n"
                f"  provider: {provider.name}\n"
                f"  url: {url}\n"
                "  path: .\n"
                "  role: standalone\n"
                "  state: active\n"
                "  kind: internal_flext\n"
                "  checkout: root\n"
                "  codegen: none\n"
                "  package: true\n"
                "  editable: true\n"
                "  read_only: false\n",
                encoding="utf-8",
            )
            (root / "config" / "codegen.yaml").write_text(
                "Infra:\n"
                "  codegen:\n"
                "    repository:\n"
                "      duplication_trees: [charts]\n",
                encoding="utf-8",
            )
        return root

    def test_declared_trees_enter_the_scan_and_fail_on_clones(
        self,
        tmp_path: Path,
    ) -> None:
        """A declared project tree joins the scan and its clones are findings."""
        root = self._governed_with_declared_trees(tmp_path, declare_trees=True)

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.fail(execution.result.passed)
        tm.that(
            tuple(issue.file for issue in execution.issues),
            has="charts/values.yaml",
        )

    def test_undeclared_trees_stay_outside_the_scan(self, tmp_path: Path) -> None:
        """Without a declaration the canonical Python discovery owns the scope."""
        root = self._governed_with_declared_trees(tmp_path, declare_trees=False)

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.ok(execution.result.passed)
        tm.that(execution.issues, eq=())

    @staticmethod
    def _sibling_prefix_workspace(tmp_path: Path) -> Path:
        """One workspace whose member directories prefix each other.

        ``fixture-dup`` and ``fixture-dup-extra`` share a string prefix but are
        distinct projects; a clone between them must never be attributed to the
        shorter one.

        Returns:
            The resulting ``Path``.

        """
        root = tmp_path / "sibling-workspace"
        root.mkdir()
        module = "".join(
            f"def helper_{index}(value: int) -> int:\n    return value + {index}\n\n"
            for index in range(12)
        )
        for name in ("fixture-dup", "fixture-dup-extra"):
            member = root / name
            member.mkdir()
            u.Tests.WorktreeFixture.initialize_governed_project(
                member,
                name,
                beads=u.Tests.BeadsIdentity(
                    workspace="sibling-workspace",
                    database="sibling_workspace",
                    issue_prefix="sibling",
                ),
            )
            package = member / "src" / name.replace("-", "_")
            package.mkdir(parents=True, exist_ok=True)
            (package / "duplicated.py").write_text(module, encoding="utf-8")
        u.Tests.write_workspace_manifest(
            root,
            "sibling-workspace",
            role=c.Infra.MakeProfile.WORKSPACE,
        )
        u.Tests.declare_workspace_projects(root, ("fixture-dup", "fixture-dup-extra"))
        return root

    def test_project_scan_never_reaches_a_prefix_named_sibling(
        self,
        tmp_path: Path,
    ) -> None:
        """A project evaluates only itself, locally exactly as in CI.

        Both members carry the same module, yet the gate for ``fixture-dup``
        scans only its own tree: the sibling whose name it prefixes is a
        library, never scanned, so no cross-project clone is reported.
        """
        root = self._sibling_prefix_workspace(tmp_path)
        own = root / "fixture-dup"

        execution = FlextInfraDuplicationGate(root).check(own, self._ctx(root))

        tm.ok(execution.result.passed)
        tm.that(execution.issues, eq=())

    _PYTHON_BEHAVIOR_BLOCK = """\
def normalize_records(records: list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for record in records:
        candidate = record.strip().casefold()
        if not candidate:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    ordered = sorted(normalized)
    return tuple(ordered)
"""

    @staticmethod
    def _governed_with_python_clone(tmp_path: Path, *, same_file: bool) -> Path:
        """One governed checkout whose only duplication is Python behavior.

        Returns:
            The resulting ``Path``.

        """
        root = tmp_path / "python-clone"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-python-clone",
            beads=u.Tests.BeadsIdentity(
                workspace="python-clone-workspace",
                database="python_clone_database",
                issue_prefix="python-clone",
            ),
        )
        package = root / "src" / "fixture_python_clone"
        package.mkdir(parents=True, exist_ok=True)
        block = TestsFlextInfraDuplicationGate._PYTHON_BEHAVIOR_BLOCK
        if same_file:
            (package / "duplicated.py").write_text(
                f"{block}\n\n{block}",
                encoding="utf-8",
            )
        else:
            (package / "first.py").write_text(block, encoding="utf-8")
            (package / "second.py").write_text(block, encoding="utf-8")
        return root

    def test_overlapping_scope_never_reports_a_file_as_its_own_clone(
        self,
        tmp_path: Path,
    ) -> None:
        """Overlapping declarations never produce double-scan clone findings.

        A duplicated scope entry makes jscpd clone every file against itself,
        which is the false double-scan artifact; the union must be unique.
        """
        root = self._governed_with_declared_trees(tmp_path, declare_trees=True)
        pyproject = root / c.PYPROJECT_FILENAME
        pyproject.write_text(
            f"{pyproject.read_text(encoding='utf-8')}\n"
            "[tool.flext.project.duplication]\n"
            'scope = ["src", "charts", "charts"]\n',
            encoding="utf-8",
        )

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.fail(execution.result.passed)
        tm.that(execution.issues, empty=False)
        report = m.Infra.JscpdReport.model_validate_json(
            (
                root / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_REPORT_FILENAME
            ).read_text(encoding="utf-8"),
        )
        tm.that(report.duplicates, empty=False)
        for duplicate in report.duplicates:
            tm.fail(duplicate.first_file == duplicate.second_file)
        tm.that(
            tuple(issue.file for issue in execution.issues),
            has="charts/values.yaml",
        )

    def test_cross_file_clone_is_reported(self, tmp_path: Path) -> None:
        """A cross-file clone blocks; CI runs similarity, semantic NOT EXECUTED."""
        root = self._governed_with_python_clone(tmp_path, same_file=False)

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.fail(execution.result.passed)
        tm.ok(len(execution.issues) >= 1)
        rendered = u.Cli.json_as_mapping(
            u.Cli.json_parse(
                (
                    root / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_CONFIG_FILENAME
                ).read_text(encoding="utf-8"),
            ).unwrap(),
        )
        tm.that(
            rendered.get("similarity"),
            eq=config.Infra.tooling.tools.jscpd.similarity,
        )
        tm.that("semantic" in rendered, truth=False)
        tm.that(
            "jscpd semantic pass NOT EXECUTED" in execution.raw_output,
            truth=True,
        )

    def test_intra_file_clone_is_reported(self, tmp_path: Path) -> None:
        """A file that duplicates a block inside itself is a finding.

        The identical file/span pair from the double-scan is dropped, but a
        same-file clone with two distinct spans is genuine duplication and
        must never be hidden.
        """
        root = self._governed_with_python_clone(tmp_path, same_file=True)

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.fail(execution.result.passed)
        tm.that(
            {issue.file for issue in execution.issues},
            eq={"src/fixture_python_clone/duplicated.py"},
        )

    @staticmethod
    def _governed_with_fleet_members(
        tmp_path: Path, *, enable_fleet: bool | None
    ) -> Path:
        """One governed root plus two declared members sharing a Python block.

        Returns:
            The resulting ``Path``.

        """
        root = tmp_path / "fleet-duplication"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-fleet",
            beads=u.Tests.BeadsIdentity(
                workspace="fleet-workspace",
                database="fleet_database",
                issue_prefix="fleet",
            ),
        )
        root_package = root / "src" / "fixture_fleet"
        root_package.mkdir(parents=True, exist_ok=True)
        (root_package / "unique.py").write_text(
            "ROOT_ONLY_MARKER = 'canonical-root-only'\n",
            encoding="utf-8",
        )
        block = TestsFlextInfraDuplicationGate._PYTHON_BEHAVIOR_BLOCK
        for name in ("alpha", "beta"):
            member = root / f"peer-{name}"
            package = member / "src" / f"peer_{name}"
            package.mkdir(parents=True, exist_ok=True)
            (member / c.PYPROJECT_FILENAME).write_text(
                f'[project]\nname = "peer-{name}"\nversion = "0"\n',
                encoding="utf-8",
            )
            (package / "duplicated.py").write_text(block, encoding="utf-8")
        (root / ".gitmodules").write_text(
            '[submodule "peer-alpha"]\n'
            "\tpath = peer-alpha\n"
            "\turl = https://example.invalid/peer-alpha\n"
            '[submodule "peer-beta"]\n'
            "\tpath = peer-beta\n"
            "\turl = https://example.invalid/peer-beta\n",
            encoding="utf-8",
        )
        if enable_fleet is not None:
            pyproject = root / c.PYPROJECT_FILENAME
            pyproject.write_text(
                f"{pyproject.read_text(encoding='utf-8')}\n"
                "[tool.flext.project.duplication]\n"
                f"fleet = {str(enable_fleet).lower()}\n",
                encoding="utf-8",
            )
        return root

    def test_fleet_scope_reports_a_cross_project_clone(self, tmp_path: Path) -> None:
        """Two declared members sharing a block are one cross-project finding."""
        root = self._governed_with_fleet_members(tmp_path, enable_fleet=True)

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.fail(execution.result.passed)
        text = " ".join(f"{issue.file} {issue.message}" for issue in execution.issues)
        tm.that(text, has="peer-alpha")
        tm.that(text, has="peer-beta")

    def test_fleet_disabled_ignores_member_projects(self, tmp_path: Path) -> None:
        """An explicit fleet=false keeps member projects out of scope."""
        root = self._governed_with_fleet_members(tmp_path, enable_fleet=False)

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.that(
            execution.result.passed,
            truth=True,
            msg="; ".join(issue.formatted for issue in execution.issues),
        )

    def test_default_fleet_scope_follows_typed_overrides(self, tmp_path: Path) -> None:
        """An omitted fleet declaration follows the canonical typed default."""
        root = self._governed_with_fleet_members(tmp_path, enable_fleet=None)
        fleet = m.Infra.ProjectDuplicationOverrides().fleet

        execution = FlextInfraDuplicationGate(root).check(root, self._ctx(root))

        tm.that(execution.result.passed, eq=not fleet)
        text = " ".join(f"{issue.file} {issue.message}" for issue in execution.issues)
        tm.that("peer-alpha" in text, eq=fleet)
        tm.that("peer-beta" in text, eq=fleet)

    @staticmethod
    def _comparison_workspace(
        tmp_path: Path, *, declare_root: bool, existing: bool
    ) -> tuple[Path, Path]:
        """One governed project and one external checkout sharing a block.

        Returns:
            The resulting pair of the project and the external root paths.

        """
        project = tmp_path / "comparison-project"
        u.Tests.WorktreeFixture.initialize_governed_project(
            project,
            "fixture-comparison",
            beads=u.Tests.BeadsIdentity(
                workspace="comparison-workspace",
                database="comparison_database",
                issue_prefix="comparison",
            ),
        )
        package = project / "src" / "fixture_comparison"
        package.mkdir(parents=True, exist_ok=True)
        (package / "unique.py").write_text(
            "PROJECT_ONLY_MARKER = 'comparison-project-only'\n",
            encoding="utf-8",
        )
        block = TestsFlextInfraDuplicationGate._PYTHON_BEHAVIOR_BLOCK
        external = tmp_path / "external-library"
        if existing:
            external.mkdir(parents=True, exist_ok=True)
            (external / "shared.py").write_text(block, encoding="utf-8")
        package.mkdir(parents=True, exist_ok=True)
        (package / "duplicated.py").write_text(block, encoding="utf-8")
        if declare_root:
            pyproject = project / c.PYPROJECT_FILENAME
            pyproject.write_text(
                f"{pyproject.read_text(encoding='utf-8')}\n"
                "[tool.flext.project.duplication]\n"
                f'comparison_roots = ["{external}"]\n',
                encoding="utf-8",
            )
        return project, external

    def test_comparison_root_clone_is_a_project_finding(self, tmp_path: Path) -> None:
        """A declared external root joins the scan; the clone stays project-owned."""
        project, _external = self._comparison_workspace(
            tmp_path, declare_root=True, existing=True
        )

        execution = FlextInfraDuplicationGate(project).check(
            project, self._ctx(project)
        )

        tm.fail(execution.result.passed)
        text = " ".join(f"{issue.file} {issue.message}" for issue in execution.issues)
        tm.that(text, has="src/fixture_comparison/duplicated.py")
        tm.that(text, has="external-library")
        sarif = (
            project
            / c.Infra.JSCPD_REPORT_DIRNAME
            / f"{c.Infra.JSCPD_REPORT_FILENAME.removesuffix('.json')}.sarif"
        )
        runs = u.Cli.json_as_mapping(
            u.Cli.json_parse(sarif.read_text(encoding="utf-8")).unwrap()
        ).get("runs")
        tm.ok(isinstance(runs, list) and len(runs) >= 1)

    def test_absent_comparison_root_degrades_with_a_recorded_note(
        self, tmp_path: Path
    ) -> None:
        """A missing declared root is skipped with its typed degradation note."""
        project, _external = self._comparison_workspace(
            tmp_path, declare_root=True, existing=False
        )

        execution = FlextInfraDuplicationGate(project).check(
            project, self._ctx(project)
        )

        tm.ok(execution.result.passed)
        tm.that(execution.raw_output, has="comparison roots skipped (absent)")

    def test_undeclared_comparison_root_keeps_project_isolated(
        self, tmp_path: Path
    ) -> None:
        """Without the declaration an external checkout is never scanned.

        The project carries one copy of the block and no internal duplicate,
        so the isolated scan is clean.
        """
        project, _external = self._comparison_workspace(
            tmp_path, declare_root=False, existing=True
        )

        execution = FlextInfraDuplicationGate(project).check(
            project, self._ctx(project)
        )

        tm.ok(execution.result.passed)
        text = " ".join(f"{issue.file} {issue.message}" for issue in execution.issues)
        tm.fail("external-library" in text)

    def test_overlapping_comparison_root_never_double_scans(
        self, tmp_path: Path
    ) -> None:
        """A comparison root that aliases an internal scope adds no second view."""
        project, external = self._comparison_workspace(
            tmp_path, declare_root=False, existing=True
        )
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            f"{pyproject.read_text(encoding='utf-8')}\n"
            "[tool.flext.project.duplication]\n"
            f'comparison_roots = ["{external}", "{external.resolve()}"]\n',
            encoding="utf-8",
        )

        execution = FlextInfraDuplicationGate(project).check(
            project, self._ctx(project)
        )

        tm.fail(execution.result.passed)
        report = m.Infra.JscpdReport.model_validate_json(
            (
                project / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_REPORT_FILENAME
            ).read_text(encoding="utf-8"),
        )
        for duplicate in report.duplicates:
            tm.fail(duplicate.first_file == duplicate.second_file)
