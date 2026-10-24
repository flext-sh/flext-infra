"""Shared Ruff exemptions compose with isolated repository-owned additions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config, m, t
from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRuffProjectExemptions:
    """A project inherits exactly the declared fleet exemptions."""

    @staticmethod
    def _project(
        phase: FlextInfraEnsureRuffConfigPhase,
        tmp_path: Path,
        name: str,
    ) -> t.Pair[t.MutableJsonMapping, t.MutableJsonMapping | None]:
        """Project the phase onto a fresh payload.

        Returns:
            The payload and its projected per-file-ignores table.

        """
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(f'[project]\nname = "{name}"\n'),
        )
        phase.apply_payload(
            payload,
            path=tmp_path / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        return payload, u.Cli.toml_mapping_path(
            payload,
            (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION, "per-file-ignores"),
        )

    @staticmethod
    def test_project_map_is_the_fleet_map(tmp_path: Path) -> None:
        """The projected per-file-ignores equal the fleet map, unfiltered."""
        fleet = config.Infra.tooling.tools.ruff.lint.per_file_ignores
        _, projected = TestsFlextInfraRuffProjectExemptions._project(
            FlextInfraEnsureRuffConfigPhase(
                config.Infra.tooling,
                u.Infra.empty_snapshot().resolution.artifacts.Ruff,
            ),
            tmp_path,
            "fleet-exemptions",
        )
        projected_rules: t.MutableMappingKV[str, t.VariadicTuple[str]] = {}
        for pattern, rules in dict(projected or {}).items():
            entries = rules if isinstance(rules, list) else ()
            projected_rules[pattern] = tuple(
                rule for rule in entries if isinstance(rule, str)
            )
        tm.that(
            projected_rules,
            eq={pattern: tuple(sorted(rules)) for pattern, rules in fleet.items()},
        )

    @staticmethod
    def test_project_additions_do_not_change_shared_policy(tmp_path: Path) -> None:
        """One project keeps its scoped additions without leaking to the next."""
        shared = config.Infra.tooling.tools.ruff.lint.per_file_ignores
        pattern = "src/project_owned.py"
        local = m.Infra.ProjectRuffConfig(
            per_file_ignores={pattern: ("invalid-function-name",)},
        )
        phase = FlextInfraEnsureRuffConfigPhase(config.Infra.tooling, local)
        payload, projected = TestsFlextInfraRuffProjectExemptions._project(
            phase,
            tmp_path,
            "project-exemptions",
        )
        tm.that(projected is not None, eq=True)
        assert projected is not None
        tm.that(projected[pattern], eq=list(local.per_file_ignores[pattern]))
        tm.that(
            phase.apply_payload(
                payload,
                path=tmp_path / c.PYPROJECT_FILENAME,
                analysis_exclusions=(),
            ),
            empty=True,
        )
        empty = u.Infra.empty_snapshot().resolution.artifacts.Ruff
        tm.that(
            u.Infra.compose_ruff_per_file_ignores(config.Infra.tooling, empty),
            eq=shared,
        )

    @staticmethod
    def test_matching_pattern_retains_both_owners() -> None:
        """Local additions cannot erase the rules declared by shared policy."""
        shared = config.Infra.tooling.tools.ruff.lint.per_file_ignores
        pattern = next(iter(shared))
        local = m.Infra.ProjectRuffConfig(
            per_file_ignores={pattern: ("invalid-function-name",)},
        )
        composed = u.Infra.compose_ruff_per_file_ignores(config.Infra.tooling, local)
        tm.that(
            composed[pattern],
            eq=tuple(
                sorted(set(shared[pattern]) | set(local.per_file_ignores[pattern]))
            ),
        )
