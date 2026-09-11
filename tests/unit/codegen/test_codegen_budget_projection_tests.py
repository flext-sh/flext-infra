"""The generator projects the budget table every registry gate requires."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c
from flext_infra.codegen import FlextInfraCodegenConform
from tests import u
from tests.unit.workspace import WorktreeFixture


def _conformed_root(tmp_path: Path) -> Path:
    """Materialize one governed project and conform it to a fixed point."""
    root = tmp_path / "repo"
    WorktreeFixture.initialize_governed_project(
        root,
        "fixture-project",
        workspace="fixture-workspace",
        database="fixture-database",
        issue_prefix="fixture-prefix",
    )
    pyproject = root / c.Infra.PYPROJECT_FILENAME
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace(
            "\n[project.urls]",
            '\ndescription = "Fixture governed project"\n\n[project.urls]',
        ),
        encoding="utf-8",
    )
    u.Tests.commit_git_changes(root, "Declare project identity")
    tm.ok(
        FlextInfraCodegenConform.execute_request(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
    )
    return root


class TestsFlextInfraBudgetProjection:
    """The codegen SSOT provisions the budget table the budget gate demands.

    flext-cpzjo.3: the budget gate requires one complete row per registry
    gate; the rows are generator output, never authorial member input, so a
    governed project reaches the gate already conformant.
    """

    def test_conformed_pyproject_covers_every_registry_gate(
        self, tmp_path: Path
    ) -> None:
        """Every ALLOWED_GATES id renders a complete positive-int budget row."""
        import tomllib

        root = _conformed_root(tmp_path)
        rendered = (root / c.Infra.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        parsed = tomllib.loads(rendered)
        table = parsed["tool"]["flext"]["project"]["budget"]

        tm.that(set(table), eq=set(c.Infra.ALLOWED_GATES))
        for row in table.values():
            for field in c.Infra.BUDGET_REQUIRED_FIELDS:
                value = row[field]
                tm.that(isinstance(value, int) and not isinstance(value, bool), eq=True)
                tm.that(value >= 1, eq=True)

    @pytest.mark.slow
    def test_budget_table_renders_identically_across_projects(
        self, tmp_path: Path
    ) -> None:
        """Two governed projects render the byte-identical budget table."""
        root_a = _conformed_root(tmp_path / "a" / "repo")
        root_b = _conformed_root(tmp_path / "b" / "repo")

        def budget_table(path: Path) -> bytes:
            rendered = path.read_bytes()
            marker = b"[tool.flext.project.budget]"
            _, _, table = rendered.partition(marker)
            return table.split(b"# [MANAGED]", 1)[0]

        tm.that(
            budget_table(root_a / c.Infra.PYPROJECT_FILENAME),
            eq=budget_table(root_b / c.Infra.PYPROJECT_FILENAME),
        )

    def test_budget_config_must_cover_the_registry(self) -> None:
        """A registry gate without a configured row fails generation loud."""
        from flext_infra import config

        budgets = {
            gate_id: row
            for gate_id, row in config.Infra.codegen.budget.items()
            if gate_id != min(c.Infra.ALLOWED_GATES)
        }
        result = FlextInfraCodegenConform._resolve_gate_budgets(budgets)

        tm.fail(result, has="budget configuration diverges from the gate registry")

    def test_unknown_budget_row_fails_loud(self) -> None:
        """A configured row outside the registry fails generation loud."""
        from flext_infra import config

        unknown = min(c.Infra.ALLOWED_GATES) + "-unknown"
        first_row = next(iter(config.Infra.codegen.budget.values()))
        result = FlextInfraCodegenConform._resolve_gate_budgets({
            **config.Infra.codegen.budget,
            unknown: first_row,
        })

        tm.fail(result, has="unknown rows=")
