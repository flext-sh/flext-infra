"""Contracts for continuously managed artifact maintenance headers."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c
from flext_tests import tm


class TestsFlextInfraManagedMaintenanceHeaders:
    """Validate machine-readable maintenance metadata at canonical owners."""

    def test_live_managed_owners_publish_regeneration_contract(self) -> None:
        """Publish the real owner and canonical regeneration command."""
        templates = Path(__file__).parents[3] / "src" / "flext_infra" / "templates"
        makefile_template = (templates / "project" / "base" / "Makefile.j2").read_text(
            encoding="utf-8"
        )

        tm.that(
            makefile_template,
            has=[
                "Managed by flext-infra codegen conform",
                "{{ makefile_custom_include }}",
            ],
        )
        tm.that(
            c.Infra.BANNER,
            has=[
                "[MANAGED] FLEXT pyproject standardization",
                "flext_infra.deps.modernizer",
                "make deps WHAT=upgrade APPLY=Y",
                "[CUSTOM]",
            ],
        )

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
