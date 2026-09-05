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


__all__: list[str] = ["TestsFlextInfraPrivateImportCutover"]
