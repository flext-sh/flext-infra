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
        tm.that(makefile_fields.get("@flext-generated"), eq="continuous")
        tm.that(makefile_fields.get("@flext-regenerate"), eq="make gen APPLY=Y")
        tm.that(makefile_fields.get("@flext-owner", ""), has="config/codegen.yaml")
        tm.that(makefile_fields.get("@flext-adjust", ""), has="never this projection")

        pyproject_fields = self._fields(c.Infra.BANNER)
        tm.that(pyproject_fields.get("@flext-generated"), eq="continuous")
        tm.that(pyproject_fields.get("@flext-regenerate"), eq="make gen APPLY=Y")
        tm.that(pyproject_fields.get("@flext-owner", ""), has="config/codegen.yaml")
        tm.that(pyproject_fields.get("@flext-adjust", ""), has="preserve_project_keys")
        tm.that(pyproject_fields.get("@flext-adjust", ""), has="conflict_sections")
        template_fields = self._fields(
            (templates / "project" / "base" / "pyproject.toml.j2").read_text(
                encoding="utf-8"
            )
        )
        tm.that(template_fields.get("@flext-regenerate"), eq="make gen APPLY=Y")
        tm.that(template_fields.get("@flext-adjust", ""), has="preserve_project_keys")

    def test_pyproject_template_marks_ssot_project_keys(self) -> None:
        """[project] comments list preserve_project_keys; they are not all CUSTOM."""
        spec = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.path.as_posix() == "pyproject.toml"
        )
        template = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / "pyproject.toml.j2"
        ).read_text(encoding="utf-8")
        custom_line = next(
            line for line in template.splitlines() if line.startswith("# [CUSTOM]")
        )
        for key in spec.preserve_project_keys:
            tm.that(custom_line, has=key)
        tm.that(template, has="# [MANAGED] " + ", ".join(c.Infra.PROJECT_MANAGED_KEYS))
        tm.that(
            set(c.Infra.PROJECT_MANAGED_KEYS).isdisjoint(spec.preserve_project_keys),
            eq=True,
        )
        tm.that(custom_line, lacks="project metadata")

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
