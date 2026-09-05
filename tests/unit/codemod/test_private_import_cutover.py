"""Public utility evidence for semantic private-import cutovers."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m, u
from flext_tests import tm


class TestsFlextInfraPrivateImportCutover:
    """Exercise private-import automation only through ``u.Infra``."""

    @staticmethod
    def _finding(file_path: Path, text: str) -> m.Infra.ModScanFinding:
        """Build one authenticated-shape semantic finding."""
        return m.Infra.ModScanFinding(
            rule_file="semantic-private-import.yml",
            rule_id="semantic-private-import",
            repository="flext-sample",
            file=file_path,
            range={},
            text=text,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
            payload={},
        )

    def test_rewires_unique_public_facade_binding(self, tmp_path: Path) -> None:
        """Derive the nested facade path and remove the private import atomically."""
        facade_path = tmp_path / "flext-sample/src/flext_sample/utilities.py"
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        private_import = (
            "from flext_sample._utilities.managers import FlextSampleUtilitiesManagers"
        )
        sources = {
            facade_path: (
                f"{private_import}\n\n"
                "class FlextSampleUtilities:\n"
                "    class Sample(FlextSampleUtilitiesManagers):\n"
                "        pass\n\n"
                "u = FlextSampleUtilities\n"
            ),
            consumer_path: (
                "from flext_sample import p\n"
                f"{private_import}\n\n"
                "manager: FlextSampleUtilitiesManagers.ServiceManagers\n"
            ),
        }

        edits = u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=(
                self._finding(consumer_path.relative_to(tmp_path), private_import),
            ),
        )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source

        tm.that(
            "from flext_sample import p, u" in updated
            or "from flext_sample import u" in updated,
            eq=True,
        )
        tm.that(updated, has="manager: u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)
        tm.that(updated, lacks="FlextSampleUtilitiesManagers.ServiceManagers")

    def test_prefers_nested_facade_over_its_root_ancestor(self, tmp_path: Path) -> None:
        """Select the deepest public namespace when the root shares its base."""
        facade_path = tmp_path / "flext-sample/src/flext_sample/utilities.py"
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        private_import = (
            "from flext_sample._utilities.managers import FlextSampleUtilitiesManagers"
        )
        sources = {
            facade_path: (
                f"{private_import}\n\n"
                "class FlextSampleUtilities(FlextSampleUtilitiesManagers):\n"
                "    class Sample(FlextSampleUtilitiesManagers):\n"
                "        pass\n\n"
                "u = FlextSampleUtilities\n"
            ),
            consumer_path: (
                f"{private_import}\n\n"
                "manager = FlextSampleUtilitiesManagers.ServiceManagers\n"
            ),
        }

        edits = u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=(
                self._finding(consumer_path.relative_to(tmp_path), private_import),
            ),
        )
        updated = edits[0].updated_source

        tm.that(updated, has="manager = u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)

    def test_rejects_shadowed_public_facade_alias(self, tmp_path: Path) -> None:
        """Fail before effects when a local binding would capture the facade alias."""
        facade_path = tmp_path / "flext-sample/src/flext_sample/utilities.py"
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        private_import = (
            "from flext_sample._utilities.managers import FlextSampleUtilitiesManagers"
        )
        sources = {
            facade_path: (
                f"{private_import}\n\n"
                "class FlextSampleUtilities:\n"
                "    class Sample(FlextSampleUtilitiesManagers):\n"
                "        pass\n\n"
                "u = FlextSampleUtilities\n"
            ),
            consumer_path: (
                f"{private_import}\n\n"
                "def select(u: str) -> str:\n"
                "    return FlextSampleUtilitiesManagers.ServiceManagers or u\n"
            ),
        }

        with pytest.raises(ValueError, match="public facade alias u is shadowed"):
            u.Infra.plan_private_import_cutover(
                root=tmp_path,
                sources=sources,
                findings=(
                    self._finding(consumer_path.relative_to(tmp_path), private_import),
                ),
            )

    def test_accepts_alias_owned_by_removed_private_import(
        self, tmp_path: Path
    ) -> None:
        """Replace the old import binding with its public facade atomically."""
        facade_path = tmp_path / "flext-sample/src/flext_sample/models.py"
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        private_import = (
            "from flext_sample._models.base import FlextSampleModelsBase as m"
        )
        sources = {
            facade_path: (
                "from flext_sample._models.base import FlextSampleModelsBase\n\n"
                "class FlextSampleModels:\n"
                "    class Metadata(FlextSampleModelsBase):\n"
                "        pass\n\n"
                "m = FlextSampleModels\n"
            ),
            consumer_path: f"{private_import}\n\nmetadata = m.Metadata()\n",
        }

        edits = u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=(
                self._finding(consumer_path.relative_to(tmp_path), private_import),
            ),
        )
        updated = edits[0].updated_source

        tm.that(updated, has="from flext_sample import m")
        tm.that(updated, has="metadata = m.Metadata()")
        tm.that(updated, lacks=private_import)

    def test_preserves_type_checking_boundary_for_public_facade(
        self, tmp_path: Path
    ) -> None:
        """Keep a type-only facade import in the original type-only boundary."""
        facade_path = tmp_path / "flext-sample/src/flext_sample/models.py"
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        private_import = (
            "from flext_sample._models.base import FlextSampleModelsBase as m"
        )
        sources = {
            facade_path: (
                "from flext_sample._models.base import FlextSampleModelsBase\n\n"
                "class FlextSampleModels:\n"
                "    class Metadata(FlextSampleModelsBase):\n"
                "        pass\n\n"
                "m = FlextSampleModels\n"
            ),
            consumer_path: (
                "from __future__ import annotations\n\n"
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                f"    {private_import}\n\n"
                "metadata: m.Metadata\n"
            ),
        }

        edits = u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=(
                self._finding(consumer_path.relative_to(tmp_path), private_import),
            ),
        )
        updated = edits[0].updated_source

        tm.that(updated, has="if TYPE_CHECKING:\n    from flext_sample import m")
        tm.that(updated, lacks="\nfrom flext_sample import m\n")
        tm.that(updated, lacks=private_import)

    def test_preserves_multiple_type_only_facades_from_one_package(
        self, tmp_path: Path
    ) -> None:
        """Rewire every type facade without promoting imports to runtime."""
        package_path = tmp_path / "flext-sample/src/flext_sample"
        consumer_path = package_path / "service.py"
        layers = (
            ("models", "m", "FlextSampleModelsBase", "Model"),
            ("protocols", "p", "FlextSampleProtocolsBase", "Protocol"),
            ("typings", "t", "FlextSampleTypesBase", "Type"),
        )
        sources: dict[Path, str] = {}
        private_imports: list[str] = []
        annotations: list[str] = []
        for layer, alias, private_class, nested_class in layers:
            private_module = f"flext_sample._{layer}.base"
            private_import = f"from {private_module} import {private_class} as {alias}b"
            private_imports.append(private_import)
            root_class = f"FlextSample{layer.title()}"
            sources[package_path / f"{layer}.py"] = (
                f"from {private_module} import {private_class}\n\n"
                f"class {root_class}:\n"
                f"    class {nested_class}({private_class}):\n"
                "        pass\n\n"
                f"{alias} = {root_class}\n"
            )
            annotations.append(f"value_{alias}: {alias}b.Member")
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n    "
            + "\n    ".join(private_imports)
            + "\n\n"
            + "\n".join(annotations)
            + "\n"
        )

        edits = u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=tuple(
                self._finding(consumer_path.relative_to(tmp_path), private_import)
                for private_import in private_imports
            ),
        )
        updated = edits[0].updated_source

        tm.that(updated, has="    from flext_sample import m, p, t")
        tm.that(updated.count("from flext_sample import"), eq=1)
        for _layer, alias, _private_class, nested_class in layers:
            tm.that(updated, has=f"value_{alias}: {alias}.{nested_class}.Member")
            tm.that(updated, lacks=f"\nfrom flext_sample import {alias}\n")
        for private_import in private_imports:
            tm.that(updated, lacks=private_import)

    def test_replaces_public_long_alias_during_private_cutover(
        self, tmp_path: Path
    ) -> None:
        """Delete the long public alias while wiring the canonical facade."""
        package_path = tmp_path / "flext-sample/src/flext_sample"
        facade_path = package_path / "models.py"
        consumer_path = package_path / "service.py"
        private_import = (
            "from flext_sample._models.pydantic import FlextSampleModelsPydantic as mp"
        )
        sources = {
            facade_path: (
                "from flext_sample._models.pydantic import FlextSampleModelsPydantic\n\n"
                "class FlextSampleModels:\n"
                "    class Pydantic(FlextSampleModelsPydantic):\n"
                "        pass\n\n"
                "m = FlextSampleModels\n"
            ),
            consumer_path: (
                "from __future__ import annotations\n\n"
                f"{private_import}\n\n"
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                "    from flext_sample import FlextSampleModels as m\n\n"
                "value: m.Metadata\n"
                "model: mp.BaseModel\n"
            ),
        }

        edits = u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=(
                self._finding(consumer_path.relative_to(tmp_path), private_import),
            ),
        )
        updated = edits[0].updated_source

        tm.that(updated.count("from flext_sample import m"), eq=1)
        tm.that(updated, lacks="FlextSampleModels as m")
        tm.that(updated, lacks=private_import)
        tm.that(updated, has="model: m.Pydantic.BaseModel")


__all__: list[str] = ["TestsFlextInfraPrivateImportCutover"]
