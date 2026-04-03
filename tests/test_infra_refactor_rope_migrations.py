"""Tests for rope-migrated transformers: symbol_propagator, nested_class_propagation."""

from __future__ import annotations

import pathlib
from pathlib import Path

from libcst import metadata as meta

from flext_infra import (
    FlextInfraNestedClassPropagationTransformer,
    FlextInfraRefactorSymbolPropagator,
    t,
    u,
)


def _apply_transformer(
    tmp_path: Path,
    file_name: str,
    source: str,
    transform: t.Infra.RopeTransformFn,
) -> tuple[str, list[str]]:
    file_path = tmp_path / "src" / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(source, encoding="utf-8")
    updated, changes = u.Infra.apply_transformer_to_source(
        source,
        file_path,
        transform,
    )
    return updated, list(changes)


class TestSymbolPropagatorRopeMigration:
    """Verify symbol_propagator uses rope APIs and no longer needs QualifiedNameProvider."""

    def test_no_qualified_name_provider(self) -> None:
        """FlextInfraRefactorSymbolPropagator does not declare QualifiedNameProvider dependency."""
        deps = getattr(FlextInfraRefactorSymbolPropagator, "METADATA_DEPENDENCIES", ())
        assert meta.QualifiedNameProvider not in deps

    def test_module_rename(self, tmp_path: Path) -> None:
        """Transformer renames import module path."""
        source = "from old_module import SomeClass\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"new_module"},
            module_renames={"old_module": "new_module"},
            import_symbol_renames={},
        )
        result, changes = _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
        assert "new_module" in result
        assert "old_module" not in result
        assert len(changes) == 1

    def test_symbol_rename_in_import(self, tmp_path: Path) -> None:
        """Transformer renames symbols within target module imports."""
        source = "from mylib import OldName\nOldName()\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        result, _ = _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
        assert "NewName" in result
        assert "OldName" not in result

    def test_symbol_rename_propagates_to_usage(self, tmp_path: Path) -> None:
        """Transformer propagates symbol rename from import to usage sites."""
        source = "from mylib import Alpha\nx = Alpha()\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"Alpha": "Beta"},
        )
        result, _ = _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
        assert "Beta" in result
        assert "Alpha" not in result

    def test_no_change_when_no_match(self, tmp_path: Path) -> None:
        """Transformer returns unchanged source when no renames apply."""
        source = "from other import SomeClass\n"
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
        )
        result, changes = _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
        assert result == source
        assert changes == []

    def test_on_change_callback_invoked(self, tmp_path: Path) -> None:
        """on_change callback is invoked for each change made."""
        source = "from mylib import OldName\n"
        recorded: list[str] = []
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules={"mylib"},
            module_renames={},
            import_symbol_renames={"OldName": "NewName"},
            on_change=recorded.append,
        )
        _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
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

    def test_class_name_not_renamed(self, tmp_path: Path) -> None:
        """Class definition names are NOT renamed (definition sites are skipped)."""
        source = "class OldName:\n    pass\n"
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames={"OldName": "Namespace.OldName"},
        )
        result, _ = _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
        assert "class OldName" in result

    def test_usage_site_renamed(self, tmp_path: Path) -> None:
        """Usage sites of renamed class ARE updated."""
        source = "x = OldName()\n"
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames={"OldName": "Namespace.OldName"},
        )
        result, _ = _apply_transformer(
            tmp_path,
            "demo.py",
            source,
            transformer.transform,
        )
        assert "Namespace.OldName" in result

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
