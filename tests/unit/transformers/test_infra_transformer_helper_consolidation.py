"""Tests for FlextInfraHelperConsolidationTransformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.helper_consolidation import (
    FlextInfraHelperConsolidationTransformer,
)
from tests import u
from flext_tests import tm

from pathlib import Path

from tests import p, t



def _transform_source(
    tmp_path: Path, source: str, mappings: t.MappingKV[str, str]
) -> str:
    file_path = tmp_path / "helper_consolidation.py"
    file_path.write_text(source, encoding="utf-8")
    transformer = FlextInfraHelperConsolidationTransformer(mappings)
    rope_project = u.Infra.init_rope_project(tmp_path)
    try:
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            raise FileNotFoundError(file_path)
        transformed, _ = transformer.transform(rope_project, resource)
        transformed_source: str = transformed
        return transformed_source
    finally:
        rope_project.close()


class TestsFlextInfraTransformersInfraTransformerHelperConsolidation:
    """Test suite for helper consolidation transformer."""

    def test_helper_becomes_staticmethod(self, tmp_path: Path) -> None:
        """Test that loose function becomes @staticmethod."""
        source = '\ndef util_helper(x: int) -> int:\n    """Helper docstring."""\n    return x * 2\n'
        mappings = {"util_helper": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified, has="@staticmethod")
        tm.that(modified, has="class FlextUtilities:")
        tm.that(modified, has="def util_helper")

    def test_helper_type_hints_preserved(self, tmp_path: Path) -> None:
        """Test that type hints are preserved."""
        source = "\ndef typed_helper(x: int, y: str) -> bool:\n    return True\n"
        mappings = {"typed_helper": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified, has="x: int")
        tm.that(modified, has="y: str")
        tm.that(modified, has="-> bool")

    def test_helper_docstring_preserved(self, tmp_path: Path) -> None:
        """Test that docstrings are preserved."""
        source = '\ndef documented_helper():\n    """This is a documented helper."""\n    pass\n'
        mappings = {"documented_helper": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified, has="This is a documented helper")

    def test_multiple_helpers_same_namespace(self, tmp_path: Path) -> None:
        """Test multiple helpers consolidated into same namespace."""
        source = "\ndef helper_one():\n    pass\n\ndef helper_two():\n    pass\n"
        mappings = {"helper_one": "FlextUtilities", "helper_two": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified.count("def helper_"), eq=2)
        tm.that(modified, has="class FlextUtilities:")

    def test_unmapped_helper_preserved(self, tmp_path: Path) -> None:
        """Test that unmapped helpers stay at module level."""
        source = (
            "\ndef mapped_helper():\n    pass\n\ndef unmapped_helper():\n    pass\n"
        )
        mappings = {"mapped_helper": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified, has="def unmapped_helper()")
        lines = modified.strip().split("\n")
        unmapped_line = next(line for line in lines if "unmapped_helper" in line)
        assert not unmapped_line.startswith(" ")

    def test_existing_namespace_extended(self, tmp_path: Path) -> None:
        """Test that existing namespace class is extended."""
        source = "\nclass FlextUtilities:\n    pass\n\ndef new_helper():\n    pass\n"
        mappings = {"new_helper": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified.count("class FlextUtilities:"), eq=1)
        tm.that(modified, has="def new_helper")

    def test_helper_call_references_updated(self, tmp_path: Path) -> None:
        """Test that internal calls to helpers are updated."""
        source = "\ndef helper():\n    pass\n\ndef caller():\n    helper()\n"
        mappings = {"helper": "FlextUtilities"}
        modified = _transform_source(tmp_path, source, mappings)
        tm.that(modified, has="FlextUtilities.helper()")
