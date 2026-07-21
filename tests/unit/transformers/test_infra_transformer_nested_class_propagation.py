"""Unit tests for nested class propagation transformer behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import u
from flext_infra.transformers.nested_class_propagation import (
    FlextInfraNestedClassPropagationTransformer,
)

if TYPE_CHECKING:
    from pathlib import Path


def _transform_source(tmp_path: Path, source: str) -> str:
    file_path = tmp_path / "nested_class_propagation.py"
    file_path.write_text(source, encoding="utf-8")
    transformer = FlextInfraNestedClassPropagationTransformer({
        "TimeoutEnforcer": "FlextDispatcher.TimeoutEnforcer",
    })
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


class TestsFlextInfraTransformersInfraTransformerNestedClassPropagation:
    """Behavior contract for test_infra_transformer_nested_class_propagation."""

    def test_nested_class_propagation_updates_import_annotations_and_calls(
        self,
        tmp_path: Path,
    ) -> None:
        source = "from pkg import TimeoutEnforcer\n\nclass Child(TimeoutEnforcer):\n    pass\n\ndef validate(x: TimeoutEnforcer) -> bool:\n    if isinstance(x, TimeoutEnforcer):\n        y = TimeoutEnforcer()\n        return isinstance(y, pkg.TimeoutEnforcer)\n    return False\n"
        code = _transform_source(tmp_path, source)
        tm.that(code, has="from pkg import FlextDispatcher")
        tm.that(code, has="class Child(FlextDispatcher.TimeoutEnforcer):")
        tm.that(code, has="def validate(x: FlextDispatcher.TimeoutEnforcer) -> bool:")
        tm.that(code, has="if isinstance(x, FlextDispatcher.TimeoutEnforcer):")
        tm.that(code, has="y = FlextDispatcher.TimeoutEnforcer()")
        tm.that(code, has="isinstance(y, pkg.FlextDispatcher.TimeoutEnforcer)")

    def test_nested_class_propagation_preserves_asname_and_rewrites_alias_usage(
        self,
        tmp_path: Path,
    ) -> None:
        source = "from pkg import TimeoutEnforcer as TE\n\nvalue = TE()\n"
        code = _transform_source(tmp_path, source)
        tm.that(code, has="from pkg import FlextDispatcher as TE")
        tm.that(code, has="value = TE.TimeoutEnforcer()")
