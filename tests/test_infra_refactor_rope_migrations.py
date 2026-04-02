"""Tests for rope-migrated transformers: symbol_propagator, nested_class_propagation."""

from __future__ import annotations

import pathlib

from flext_infra import (
    FlextInfraNestedClassPropagationTransformer,
    FlextInfraRefactorSymbolPropagator,
)


class TestSymbolPropagatorRopeMigration:
    """Verify symbol_propagator uses rope APIs and no longer needs QualifiedNameProvider."""

    def test_no_qualified_name_provider(self) -> None:
        """FlextInfraRefactorSymbolPropagator does not declare QualifiedNameProvider dependency."""
        deps = getattr(FlextInfraRefactorSymbolPropagator, "METADATA_DEPENDENCIES", ())
        assert meta.QualifiedNameProvider not in deps

    def test_module_rename(self) -> None:
        """Transformer renames import module path."""
        source = "from old_module import SomeClass\n"
        tree = cst.parse_module(source)
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"new_module"},
            module_renames={"old_module": "new_module"},
            import_symbol_renames={},
        )
        result = tree.visit(transformer)
        assert "new_module" in result.code
        assert "old_module" not in result.code
        assert len(transformer.changes) == 1

    def test_symbol_rename_in_import(self) -> None:
        """Transformer renames symbols within target module imports."""
        source = "from mylib import OldName\nOldName()\n"
        tree = cst.parse_module(source)
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        result = tree.visit(transformer)
        assert "NewName" in result.code
        assert "OldName" not in result.code

    def test_symbol_rename_propagates_to_usage(self) -> None:
        """Transformer propagates symbol rename from import to usage sites."""
        source = "from mylib import Alpha\nx = Alpha()\n"
        tree = cst.parse_module(source)
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"Alpha": "Beta"},
        )
        result = tree.visit(transformer)
        assert "Beta" in result.code
        assert "Alpha" not in result.code

    def test_no_change_when_no_match(self) -> None:
        """Transformer returns unchanged tree when no renames apply."""
        source = "from other import SomeClass\n"
        tree = cst.parse_module(source)
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        result = tree.visit(transformer)
        assert result.code == source
        assert len(transformer.changes) == 0

    def test_on_change_callback_invoked(self) -> None:
        """on_change callback is invoked for each change made."""
        source = "from mylib import OldName\n"
        tree = cst.parse_module(source)
        recorded: list[str] = []
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
            on_change=recorded.append,
        )
        tree.visit(transformer)
        assert len(recorded) == 1
        assert "OldName" in recorded[0]

    def test_file_shorter_than_baseline(self) -> None:
        """symbol_propagator.py is shorter than the 117-line baseline."""
        path = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "flext_infra"
            / "transformers"
            / "symbol_propagator.py"
        )
        lines = path.read_text().splitlines()
        assert len(lines) < 117, f"Expected < 117 lines, got {len(lines)}"


class TestNestedClassPropagationRopeMigration:
    """Verify nested_class_propagation uses rope and removes ParentNodeProvider."""

    def test_no_parent_node_provider(self) -> None:
        """FlextInfraNestedClassPropagationTransformer has no ParentNodeProvider dependency."""
        deps = getattr(
            FlextInfraNestedClassPropagationTransformer, "METADATA_DEPENDENCIES", ()
        )
        assert meta.ParentNodeProvider not in deps

    def test_class_name_not_renamed(self) -> None:
        """Class definition names are NOT renamed (definition sites are skipped)."""
        source = "class OldName:\n    pass\n"
        tree = cst.parse_module(source)
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames={"OldName": "Namespace.OldName"},
        )
        result = tree.visit(transformer)
        assert "class OldName" in result.code

    def test_usage_site_renamed(self) -> None:
        """Usage sites of renamed class ARE updated."""
        source = "x = OldName()\n"
        tree = cst.parse_module(source)
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames={"OldName": "Namespace.OldName"},
        )
        result = tree.visit(transformer)
        assert "Namespace.OldName" in result.code

    def test_combined_loc_under_baseline(self) -> None:
        """Combined LOC of all 3 transformer files is < 385 (the baseline)."""
        transformers_dir = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "flext_infra"
            / "transformers"
        )
        files = [
            "symbol_propagator.py",
            "nested_class_propagation.py",
        ]
        total = sum(len((transformers_dir / f).read_text().splitlines()) for f in files)
        assert total < 310, f"Expected combined LOC < 310, got {total}"
