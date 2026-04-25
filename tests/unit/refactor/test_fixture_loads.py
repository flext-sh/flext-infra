"""Smoke checks for the 9 edge-case fixtures (Task 0.7).

Each test resolves a single ``edge_case_<a..i>`` fixture and asserts:
  * the workspace_root tmp dir exists and contains the project subdirectory
  * every declared target file exists, is non-empty, and is contained
    inside the workspace_root
  * the file's signature pattern (the canonical line that proves the edge
    case) is present in source — guards against silent fixture rot if a
    handler refactors one of these prototypes by accident
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from tests.unit.refactor.conftest import EdgeCaseFixture

# Fixture letter → marker substring that must appear in at least one
# of the fixture's target files. Centralised so adding/removing an
# edge case stays a single-row update.
_EDGE_CASE_MARKERS: Mapping[str, str] = {
    "a": "class FlextAlphaProtocols(_MeltanoProtocols, _BaseProtocols)",
    "b": "_LAZY_IMPORTS",
    "c": "FlextModelsPydantic as mp",
    "d": "class TestsFlextAlphaModels",
    "e": "class ExamplesFlextAlphaSample",
    "f": "class FlextAlphaServicesAlpha",
    "g": "@auto_register",
    "h": "@field_validator",
    "i": "@override",
}


class TestsFlextInfraRefactorEdgeCaseFixtures:
    """Behavior contract for the rule-lifecycle edge-case fixture set."""

    @staticmethod
    def _assert_fixture(letter: str, fixture: EdgeCaseFixture) -> None:
        workspace_root, target_files = fixture
        assert workspace_root.is_dir()
        assert target_files, f"edge case {letter}: no target files"
        marker = _EDGE_CASE_MARKERS[letter]
        joined_source = ""
        for file in target_files:
            assert isinstance(file, Path)
            assert file.exists(), f"edge case {letter}: {file} not on disk"
            assert file.is_relative_to(workspace_root)
            content = file.read_text(encoding="utf-8")
            assert content.strip(), f"edge case {letter}: {file} is empty"
            joined_source += content
        assert marker in joined_source, (
            f"edge case {letter}: expected marker {marker!r} in fixture source"
        )

    def test_edge_case_a_dual_mro(self, edge_case_a: EdgeCaseFixture) -> None:
        self._assert_fixture("a", edge_case_a)

    def test_edge_case_b_lazy_init(self, edge_case_b: EdgeCaseFixture) -> None:
        self._assert_fixture("b", edge_case_b)

    def test_edge_case_c_bootstrap_aliases(self, edge_case_c: EdgeCaseFixture) -> None:
        self._assert_fixture("c", edge_case_c)

    def test_edge_case_d_tests_tier_facade(self, edge_case_d: EdgeCaseFixture) -> None:
        self._assert_fixture("d", edge_case_d)

    def test_edge_case_e_examples_scripts_tiers(
        self, edge_case_e: EdgeCaseFixture
    ) -> None:
        self._assert_fixture("e", edge_case_e)

    def test_edge_case_f_services_mixin_tree(
        self, edge_case_f: EdgeCaseFixture
    ) -> None:
        self._assert_fixture("f", edge_case_f)

    def test_edge_case_g_settings_auto_register(
        self, edge_case_g: EdgeCaseFixture
    ) -> None:
        self._assert_fixture("g", edge_case_g)

    def test_edge_case_h_pydantic_validators(
        self, edge_case_h: EdgeCaseFixture
    ) -> None:
        self._assert_fixture("h", edge_case_h)

    def test_edge_case_i_override_final_decorators(
        self, edge_case_i: EdgeCaseFixture
    ) -> None:
        self._assert_fixture("i", edge_case_i)

    @pytest.mark.parametrize("letter", sorted(_EDGE_CASE_MARKERS))
    def test_marker_table_covers_every_letter(self, letter: str) -> None:
        # Defensive: catalog the complete a..i alphabet so removing a
        # fixture doesn't silently leave a stale table entry.
        assert letter in _EDGE_CASE_MARKERS
        assert _EDGE_CASE_MARKERS[letter]

    def test_marker_table_is_exactly_a_through_i(self) -> None:
        assert sorted(_EDGE_CASE_MARKERS) == list("abcdefghi")
