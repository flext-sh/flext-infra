"""Contracts for continuously managed artifact maintenance headers."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, u
from tests import t


class TestsFlextInfraManagedMaintenanceHeaders:
    """Validate machine-readable maintenance metadata at canonical owners."""

    @staticmethod
    def _fields(text: str) -> t.MutableMappingKV[str, str]:
        fields: t.MutableMappingKV[str, str] = {}
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
        tm.that(makefile_fields.get("@flext-regenerate"), eq="make gen")
        tm.that(makefile_fields.get("@flext-owner", ""), has="config/codegen.yaml")
        tm.that(makefile_fields.get("@flext-adjust", ""), has="never this projection")

        pyproject_fields = self._fields(c.Infra.BANNER)
        tm.that(pyproject_fields.get("@flext-generated"), eq="continuous")
        tm.that(pyproject_fields.get("@flext-regenerate"), eq="make gen")
        tm.that(pyproject_fields.get("@flext-owner", ""), has="config/codegen.yaml")
        tm.that(pyproject_fields.get("@flext-adjust", ""), has="overwrite_project_keys")
        tm.that(pyproject_fields.get("@flext-adjust", ""), has="conflict_sections")
        template_fields = self._fields(
            (templates / "project" / "base" / "pyproject.toml.j2").read_text(
                encoding="utf-8"
            )
        )
        tm.that(template_fields.get("@flext-regenerate"), eq="make gen")
        tm.that(template_fields.get("@flext-adjust", ""), has="overwrite_project_keys")

    def test_pyproject_template_marks_ssot_project_keys(self) -> None:
        """[project] comments list SSOT keys; the table is not wholly CUSTOM."""
        spec = tm.ok(u.Infra.pyproject_managed_file())
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
        tm.that(template, has="# [MANAGED] " + ", ".join(spec.overwrite_project_keys))
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

    def test_makefile_fmt_renders_ssot_ruff_preview_and_unsafe_fixes(self) -> None:
        """Fmt is format-only: ruff --preview format plus the fmt_gates writers.

        Single-pass verb law: no lint fix may render inside fmt (the lint
        gate's apply mode inside ``make fix`` is the only lint repair), so the
        template must not reference the removed ``lint_apply`` contract at all.
        """
        make = config.Infra.codegen.make
        tm.that("--preview" in make.ruff.format_apply, eq=True)
        tm.that("--unsafe-fixes" in make.ruff.lint_fix, eq=True)
        tm.that("--fix" in make.ruff.lint_fix, eq=True)
        tm.that(make.fmt_gates, eq=("markdown-format",))
        template = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        ).read_text(encoding="utf-8")
        tm.that(template, has="make.ruff.format_apply")
        tm.that(template, has="make.fmt_gates")
        tm.that(template, has="make.check_gates_fixable")
        tm.that(template, lacks="lint_apply")
        tm.that("--preview" in ruff.format_check, eq=True)
        tm.that("--preview" in ruff.lint_check, eq=True)


__all__: list[str] = ["TestsFlextInfraManagedMaintenanceHeaders"]
