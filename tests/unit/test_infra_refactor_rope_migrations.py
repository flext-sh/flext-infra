"""Tests for rope-migrated transformers: symbol_propagator, nested_class_propagation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.nested_class_propagation import (
    FlextInfraNestedClassPropagationTransformer,
)
from flext_infra.transformers.symbol_propagator import (
    FlextInfraRefactorSymbolPropagator,
)
from tests import u
from flext_tests import tm

from pathlib import Path

from tests import p, t



def _apply_transformer(
    tmp_path: Path, file_name: str, source: str, transform: t.Infra.RopeTransformFn
) -> t.Infra.TransformResult:
    file_path = tmp_path / "src" / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(source, encoding="utf-8")
    updated, changes = u.Infra.rope_apply_transformer_to_source(source, file_path, transform)
    return updated, list(changes)


def _metadata_dependency_names(subject: type) -> set[str]:
    names: set[str] = set()
    # for dep in deps:
    #     raw_name = getattr(dep, "__name__", dep.__class__.__name__)
    #     names.add(str(raw_name))
    return names


class TestsFlextInfraInfraRefactorRopeMigrations:
    """Verify symbol_propagator stays rope-oriented."""

    def test_no_qualified_name_provider(self) -> None:
        """FlextInfraRefactorSymbolPropagator does not depend on CST providers."""
        deps = _metadata_dependency_names(FlextInfraRefactorSymbolPropagator)
        tm.that(deps, lacks="QualifiedNameProvider")

    def test_module_rename(self, tmp_path: Path) -> None:
        """Transformer renames import module path."""
        source = "from old_module import SomeClass\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"new_module"},
            module_renames={"old_module": "new_module"},
            import_symbol_renames={},
        )
        result, changes = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        tm.that(result, has="new_module")
        tm.that(result, lacks="old_module")
        tm.that(len(changes), eq=1)

    def test_symbol_rename_in_import(self, tmp_path: Path) -> None:
        """Transformer renames symbols within target module imports."""
        source = "from mylib import OldName\nOldName()\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        result, _ = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        tm.that(result, has="NewName")
        tm.that(result, lacks="OldName")

    def test_symbol_rename_propagates_to_usage(self, tmp_path: Path) -> None:
        """Transformer propagates symbol rename from import to usage sites."""
        source = "from mylib import Alpha\nx = Alpha()\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"Alpha": "Beta"},
        )
        result, _ = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        tm.that(result, has="Beta")
        tm.that(result, lacks="Alpha")

    def test_no_change_when_no_match(self, tmp_path: Path) -> None:
        """Transformer returns unchanged source when no renames apply."""
        source = "from other import SomeClass\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        result, changes = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        tm.that(result, eq=source)
        tm.that(changes, eq=[])

    def test_on_change_callback_invoked(self, tmp_path: Path) -> None:
        """on_change callback is invoked for each change made."""
        source = "from mylib import OldName\n"
        recorded: t.MutableSequenceOf[str] = []
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
            on_change=recorded.append,
        )
        _apply_transformer(tmp_path, "demo.py", source, transformer.transform)
        tm.that(len(recorded), eq=1)
        tm.that(recorded[0], has="OldName")

    def test_apply_to_source_matches_rope_transform(self, tmp_path: Path) -> None:
        """Text and rope entrypoints keep the same symbol propagation behavior."""
        source = "from mylib import OldName\nOldName()\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        rope_result, rope_changes = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        text_result, text_changes = transformer.apply_to_source(source)
        tm.that(text_result, eq=rope_result)
        tm.that(text_changes, eq=rope_changes)

    def test_rope_apply_transformer_to_source_restores_disk_state(
        self, tmp_path: Path
    ) -> None:
        """Temporary rope sync must not leak source updates to the real file."""
        file_path = tmp_path / "src" / "demo.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        original_source = "from mylib import OldName\nOldName()\n"
        staged_source = "from mylib import OldName\nvalue = OldName()\nOldName()\n"
        file_path.write_text(original_source, encoding="utf-8")
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )

        updated, changes = u.Infra.rope_apply_transformer_to_source(
            staged_source, file_path, transformer.transform
        )

        tm.that(updated, has="NewName")
        assert changes
        tm.that(file_path.read_text(encoding="utf-8"), eq=original_source)

    def test_no_parent_node_provider(self) -> None:
        """FlextInfraNestedClassPropagationTransformer has no CST parent dependency."""
        deps = _metadata_dependency_names(FlextInfraNestedClassPropagationTransformer)
        tm.that(deps, lacks="ParentNodeProvider")

    def test_class_name_not_renamed(self, tmp_path: Path) -> None:
        """Class definition names are NOT renamed (definition sites are skipped)."""
        source = "class OldName:\n    pass\n"
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames={"OldName": "Namespace.OldName"}
        )
        result, _ = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        tm.that(result, has="class OldName")

    def test_usage_site_renamed(self, tmp_path: Path) -> None:
        """Usage sites of renamed class ARE updated."""
        source = "x = OldName()\n"
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames={"OldName": "Namespace.OldName"}
        )
        result, _ = _apply_transformer(
            tmp_path, "demo.py", source, transformer.transform
        )
        tm.that(result, has="Namespace.OldName")
