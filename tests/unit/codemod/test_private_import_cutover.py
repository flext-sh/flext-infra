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
            "from flext_sample._utilities.managers import "
            "FlextSampleUtilitiesManagers"
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

    def test_prefers_nested_facade_over_its_root_ancestor(
        self, tmp_path: Path
    ) -> None:
        """Select the deepest public namespace when the root shares its base."""
        facade_path = tmp_path / "flext-sample/src/flext_sample/utilities.py"
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        private_import = (
            "from flext_sample._utilities.managers import "
            "FlextSampleUtilitiesManagers"
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
            "from flext_sample._utilities.managers import "
            "FlextSampleUtilitiesManagers"
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
                    self._finding(
                        consumer_path.relative_to(tmp_path), private_import
                    ),
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


__all__: list[str] = ["TestsFlextInfraPrivateImportCutover"]
