"""Contracts for continuously managed artifact maintenance headers."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c


class TestsFlextInfraManagedMaintenanceHeaders:
    """Validate machine-readable maintenance metadata at canonical owners."""

    @staticmethod
    def _fields(text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for line in text.splitlines():
            marker = line.lstrip("# ")
            if not marker.startswith("@flext-") or ":" not in marker:
                continue
            key, value = marker.split(":", 1)
            fields[key] = value.strip()
        return fields

    def test_representative_managed_owners_publish_complete_contract(self) -> None:
        """Publish status, regeneration, SSOT, and maintenance fields."""
        templates = Path(__file__).parents[3] / "src" / "flext_infra" / "templates"
        owners = (
            templates / "project" / "base" / "Makefile.j2",
            templates / "workspace_makefile.mk.j2",
        )
        for owner in owners:
            fields = self._fields(owner.read_text(encoding="utf-8"))
            tm.that(fields.get("@flext-managed"), eq="continuous")
            tm.that(fields.get("@flext-regenerate", ""), has="make build WHAT=")
            tm.that(fields.get("@flext-ssot", ""), has="flext-infra/")
            tm.that(fields.get("@flext-maintenance", ""), has="do not edit")

        pyproject_fields = self._fields(c.Infra.BANNER)
        tm.that(pyproject_fields.get("@flext-managed"), eq="continuous")
        tm.that(pyproject_fields.get("@flext-regenerate"), eq="make build WHAT=mod")
        tm.that(pyproject_fields.get("@flext-ssot", ""), has="_constants/deps.py")
        tm.that(pyproject_fields.get("@flext-maintenance", ""), has="do not edit")

    def test_scaffold_once_owner_has_no_continuous_contract(self) -> None:
        """Keep user-owned scaffold output outside continuous maintenance."""
        template = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / "custom.mk.j2"
        )
        fields = self._fields(template.read_text(encoding="utf-8"))
        tm.that(fields.get("@flext-managed") == "continuous", eq=False)
