"""Tests for Rule 1: Constants facade validation."""

from __future__ import annotations

from pathlib import Path

from ._fixtures import (
    TestsFlextInfraNamespaceProjectFixture,
    TestsFlextInfraValidateNamespaceBase,
)


class TestsFlextInfraRule1ConstantsFacade(TestsFlextInfraValidateNamespaceBase):
    """Test suite for namespace validator Rule 1 (constants facade)."""

    def test_rule1_valid_constants_passes(self, tmp_path: Path) -> None:
        fixture = TestsFlextInfraNamespaceProjectFixture()
        root = fixture.create_project(
            tmp_path,
            module_source=fixture.valid_constants_module(),
            module_name="constants.py",
        )
        self._assert_valid(root)


__all__: list[str] = ["TestsFlextInfraRule1ConstantsFacade"]
