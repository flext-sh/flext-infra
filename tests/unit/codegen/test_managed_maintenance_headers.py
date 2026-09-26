"""Contracts for continuously managed artifact maintenance headers."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config
from tests import t, u

pytestmark = pytest.mark.slow


class TestsFlextInfraManagedMaintenanceHeaders:
    """Validate machine-readable maintenance metadata on rendered artifacts."""

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

    def test_live_managed_owners_publish_regeneration_contract(
        self, tmp_path: Path
    ) -> None:
        """Publish the real owner and canonical regeneration command."""
        makefile_fields = self._fields(
            u.Tests.scaffold_text(
                tmp_path / "fixture-project", c.Infra.MAKEFILE_FILENAME
            )
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

    def test_scaffold_once_owner_has_no_continuous_contract(
        self, tmp_path: Path
    ) -> None:
        """Keep user-owned scaffold output outside continuous maintenance."""
        custom = u.Tests.scaffold_text(
            tmp_path / "fixture-project", c.Infra.CUSTOM_MAKE_FILENAME
        )
        tm.that(custom, lacks="[MANAGED]")
        tm.that(self._fields(custom), eq={})

    def test_makefile_fmt_renders_ssot_ruff_preview_and_unsafe_fixes(
        self, tmp_path: Path
    ) -> None:
        """Fmt is format-only: ruff --preview format plus the fmt_gates writers.

        Single-pass verb law: no lint fix may render inside fmt (the lint
        gate's apply mode inside ``make fix`` is the only lint repair).
        """
        make = config.Infra.codegen.make
        tm.that("--preview" in make.ruff.format_apply, eq=True)
        tm.that("--unsafe-fixes" in make.ruff.lint_fix, eq=True)
        tm.that("--fix" in make.ruff.lint_fix, eq=True)
        tm.that(make.fmt_gates, eq=("markdown-format",))
        rendered = u.Tests.scaffold_text(
            tmp_path / "fixture-project", c.Infra.MAKEFILE_FILENAME
        )
        fmt_recipe = rendered.split("\n_builtin_fmt_all:", 1)[1].split("\n\n", 1)[0]
        tm.that(
            fmt_recipe,
            has=f"ruff format {' '.join(make.ruff.format_apply)} $(RUFF_PATHS)",
        )
        tm.that(
            fmt_recipe, has=f'--gates "{",".join(make.fmt_gates)}" --projects . --apply'
        )
        tm.that(fmt_recipe, lacks="ruff check")
        tm.that(
            rendered,
            has=(
                f'--gates "{",".join(make.check_gates_fixable)}" '
                "--projects . --apply --report-findings"
            ),
        )
        tm.that("--preview" in make.ruff.format_check, eq=True)
        tm.that("--preview" in make.ruff.lint_check, eq=True)
