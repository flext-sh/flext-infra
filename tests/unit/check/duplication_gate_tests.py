"""Fail-closed public behavior for the jscpd duplication gate."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c
<<<<<<< HEAD
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
=======
from flext_infra.check import FlextInfraGateRegistry
>>>>>>> origin/0.12.0-dev
from flext_infra.gates.duplication import FlextInfraDuplicationGate
from flext_tests import tm
from tests import m, u
from tests.unit.workspace import WorktreeFixture

_DUPLICATED_MODULE = """\
def normalize_records(records: list[str]) -> tuple[str, ...]:
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


def _ctx(root: Path) -> m.Infra.GateContext:
    return m.Infra.GateContext(workspace=root, reports_dir=root / "reports")


class TestDuplicationGate:
    """Exercise observable gate behavior with the real setup-provisioned tool."""

    def test_registry_exposes_the_canonical_gate(self) -> None:
<<<<<<< HEAD
        gate = FlextInfraGateRegistry.default().create("duplication", Path.cwd())
        tm.that(isinstance(gate, FlextInfraDuplicationGate), eq=True)
=======
        gate = FlextInfraGateRegistry.default().get(FlextInfraDuplicationGate.gate_id)
        tm.that(gate is FlextInfraDuplicationGate, eq=True)
>>>>>>> origin/0.12.0-dev

    def test_empty_workspace_scope_is_a_blocking_failure(self, tmp_path: Path) -> None:
        project = tmp_path / "missing-project"
        project.mkdir()

        execution = FlextInfraDuplicationGate(tmp_path).check(project, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that(execution.issues[0].message, has="empty JSON report")
        tm.that(execution.issues[0].severity, eq=str(c.Infra.GateSeverity.ERROR.value))

    @staticmethod
    def _governed_with_declared_trees(tmp_path: Path, *, declare_trees: bool) -> Path:
        """One governed checkout whose clones live only inside charts/."""
        root = tmp_path / "governed-duplication"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-duplication",
            workspace="duplication-workspace",
            database="duplication-database",
            issue_prefix="duplication-prefix",
        )
        package = root / "src" / "fixture_duplication"
        package.mkdir(parents=True, exist_ok=True)
        (root / "src" / "fixture_duplication" / "unique.py").write_text(
            "UNIQUE_MODULE_MARKER = 'canonical-scope-only'\n", encoding="utf-8"
        )
        (root / "charts").mkdir()
        chart_block = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            "  name: fixture-duplication\n"
            "  labels:\n"
            "    app: fixture\n"
            "spec:\n"
            "  replicas: 3\n"
            "  selector:\n"
            "    matchLabels:\n"
            "      app: fixture\n"
            "  template:\n"
            "    metadata:\n"
            "      labels:\n"
            "        app: fixture\n"
        )
        (root / "charts" / "values.yaml").write_text(
            chart_block + "\n---\n" + chart_block, encoding="utf-8"
        )
        if declare_trees:
            manifest = root / "config" / "workspace.yaml"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            provider = u.Tests.provider()
            manifest.write_text(
                "version: 3\n"
                "name: duplication-workspace\n"
                "repository:\n"
                "  name: fixture-duplication\n"
                "  distribution: fixture-duplication\n"
                f"  provider: {provider.name}\n"
                f"  url: {WorktreeFixture.governed_repository_url('fixture-duplication')}\n"
                "  path: .\n"
                "  role: standalone\n"
                "  state: active\n"
                "  checkout: root\n"
                "  codegen: none\n"
                "  package: true\n"
                "  editable: true\n"
                "  read_only: false\n"
                "  duplication_trees: [charts]\n",
                encoding="utf-8",
            )
        return root

    def test_declared_trees_enter_the_scan_and_fail_on_clones(
        self, tmp_path: Path
    ) -> None:
        """A declared project tree joins the scan and its clones are findings."""
        root = self._governed_with_declared_trees(tmp_path, declare_trees=True)

        execution = FlextInfraDuplicationGate(root).check(root, _ctx(root))

        tm.that(execution.result.passed, eq=False)
        tm.that(
            tuple(issue.file for issue in execution.issues), has="charts/values.yaml"
        )

    def test_undeclared_trees_stay_outside_the_scan(self, tmp_path: Path) -> None:
        """Without a declaration the canonical Python discovery owns the scope."""
        root = self._governed_with_declared_trees(tmp_path, declare_trees=False)

        execution = FlextInfraDuplicationGate(root).check(root, _ctx(root))

        tm.that(execution.result.passed, eq=True)
        tm.that(execution.issues, eq=())
