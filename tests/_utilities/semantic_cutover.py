"""Test-only helpers for the semantic cutover planners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import infra, p, u as flext_infra_u
from tests import c, m


class TestsFlextInfraUtilitiesSemanticCutover:
    """Render J2 scenarios and plan semantic cutovers from test code."""

    @classmethod
    def semantic_cutover_import(cls, name: str) -> str:
        """Render one reusable import-law J2 scenario.

        Returns:
            The rendered and syntax-checked test module source.

        """
        scenario = m.Tests.SemanticCutoverScenario.model_validate(
            c.Tests.SEMANTIC_IMPORT_SCENARIOS[name]
        )
        return cls.semantic_cutover_render(scenario)

    @classmethod
    def semantic_cutover_assertion(cls, name: str) -> str:
        """Render one reusable assertion-law J2 scenario.

        Returns:
            The rendered and syntax-checked test module source.

        """
        scenario = m.Tests.SemanticCutoverScenario.model_validate(
            c.Tests.SEMANTIC_ASSERT_SCENARIOS[name]
        )
        return cls.semantic_cutover_render(scenario)

    @staticmethod
    def semantic_cutover_render(scenario: m.Tests.SemanticCutoverScenario) -> str:
        """Render one scenario through the flext-cli J2 engine.

        Returns:
            The rendered and syntax-checked source.

        """
        template = c.Tests.SEMANTIC_CUTOVER_TEMPLATES[scenario.template]
        path = (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / c.Tests.SEMANTIC_CUTOVER_TEMPLATE_DIRECTORY
            / template
        )
        source = flext_infra_u.Cli.template_render(path, scenario).unwrap()
        ast.parse(source, filename=str(path))
        return source

    @staticmethod
    def semantic_cutover_finding(
        module_path: Path,
        repository_root: Path,
        source: str,
        phase: c.Infra.SemanticCutoverPhase,
    ) -> p.Infra.ModOccurrence:
        """Build the finding that selects one semantic phase.

        Returns:
            The resulting ``m.Infra.ModOccurrence``.

        """
        rule_id = c.Infra.SEMANTIC_CUTOVER_RULE_IDS[phase][0]
        return m.Infra.ModOccurrence(
            rule_file=f"{rule_id}.yml",
            rule_id=rule_id,
            repository="flext-sample",
            file=module_path.relative_to(repository_root),
            range={},
            text=source,
            actionable=True,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

    @classmethod
    def semantic_cutover_plan(
        cls,
        phase: c.Infra.SemanticCutoverPhase,
        repository_root: Path,
        relative: str,
        source: str,
    ) -> p.ResultView[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan one semantic cutover for a synthetic test module.

        Returns:
            The planner's semantic edits.

        """
        repository_root.joinpath("pyproject.toml").write_text(
            c.Tests.SEMANTIC_CUTOVER_PYPROJECT,
            encoding=c.DEFAULT_ENCODING,
        )
        module_path = repository_root / relative
        module_path.parent.mkdir(parents=True, exist_ok=True)
        finding = cls.semantic_cutover_finding(
            module_path,
            repository_root,
            source,
            phase,
        )
        return flext_infra_u.Infra.plan_semantic_cutover(
            phase,
            rope_workspace=infra.rope_workspace(repository_root),
            sources={module_path: source},
            findings=(finding,),
        )

    @classmethod
    def semantic_cutover_source(
        cls,
        phase: c.Infra.SemanticCutoverPhase,
        repository_root: Path,
        relative: str,
        source: str,
    ) -> str:
        """Return the rewritten source for one semantic cutover.

        Returns:
            The resulting test module source.

        """
        planned = cls.semantic_cutover_plan(phase, repository_root, relative, source)
        return planned.value[0].updated_source


__all__: list[str] = ["TestsFlextInfraUtilitiesSemanticCutover"]
