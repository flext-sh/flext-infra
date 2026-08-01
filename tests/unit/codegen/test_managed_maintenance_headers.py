"""Contracts for continuously managed artifact maintenance headers."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config
from flext_tests import tm


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

    def test_live_managed_owners_publish_regeneration_contract(self) -> None:
        """Publish the real owner and canonical regeneration command."""
        templates = Path(__file__).parents[3] / "src" / "flext_infra" / "templates"
        makefile_fields = self._fields(
            (templates / "project" / "base" / "Makefile.j2").read_text(encoding="utf-8")
        )
        tm.that(makefile_fields.get("@flext-managed"), eq="continuous")
        make = config.Infra.codegen.make
        tm.that(
            makefile_fields.get("@flext-regenerate"),
            eq=f"make gen {make.apply_variable}={make.apply_value}",
        )
        tm.that(makefile_fields.get("@flext-ssot", ""), has="flext-infra/")
        tm.that(makefile_fields.get("@flext-maintenance", ""), has="do not edit")

        pyproject_banner = c.Infra.BANNER_TEMPLATE.format(
            selector=make.selector,
            apply_variable=make.apply_variable,
            apply_value=make.apply_value,
        )
        pyproject_fields = self._fields(pyproject_banner)
        tm.that(pyproject_fields.get("@flext-managed"), eq="continuous")
        tm.that(
            pyproject_fields.get("@flext-regenerate"),
            eq=(
                f"make deps {make.selector}=upgrade "
                f"{make.apply_variable}={make.apply_value}"
            ),
        )
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
        text = template.read_text(encoding="utf-8")
        tm.that(text, lacks="[MANAGED]")
