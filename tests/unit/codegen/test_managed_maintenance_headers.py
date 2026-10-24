"""Contracts for continuously managed artifact maintenance headers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codegen import FlextInfraCodegenConformExecute
from tests import c, m, t, tm, u

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
        self,
        tmp_path: Path,
    ) -> None:
        """Publish the real owner and canonical regeneration command."""
        makefile_fields = self._fields(
            u.Tests.scaffold_text(
                tmp_path / "fixture-project",
                c.Infra.MAKEFILE_FILENAME,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
            ),
        )
        tm.that(makefile_fields.get("@flext-generated"), eq="continuous")
        tm.that(makefile_fields.get("@flext-regenerate"), eq="make gen")
        tm.that(makefile_fields.get("@flext-owner", ""), has="config/codegen.yaml")
        tm.that(makefile_fields.get("@flext-adjust", ""), has="never this projection")

        pyproject = u.Tests.scaffold_text(
            tmp_path / "fixture-project",
            c.PYPROJECT_FILENAME,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
        )
        tm.that(pyproject, starts=c.Infra.BANNER)
        pyproject_fields = self._fields(pyproject)
        tm.that(pyproject_fields.get("@flext-generated"), eq="continuous")
        tm.that(pyproject_fields.get("@flext-regenerate"), eq="make gen")
        tm.that(pyproject_fields.get("@flext-owner", ""), has="config/codegen.yaml")
        tm.that(pyproject_fields.get("@flext-adjust", ""), has="overwrite_project_keys")
        tm.that(pyproject_fields.get("@flext-adjust", ""), has="conflict_sections")

    @staticmethod
    def test_pyproject_header_is_a_fixed_point(tmp_path: Path) -> None:
        """Recomposing a published pyproject keeps exactly one header."""
        root = tmp_path / "fixture-project"
        first = u.Tests.scaffold_text(
            root, c.PYPROJECT_FILENAME, what=c.Infra.CodegenConformSurface.PYPROJECT
        )
        root.mkdir(parents=True, exist_ok=True)
        (root / c.PYPROJECT_FILENAME).write_text(first, encoding="utf-8")
        second = tm.ok(
            FlextInfraCodegenConformExecute.compose_project_artifact(
                root,
                c.PYPROJECT_FILENAME,
                first,
            ),
        ).rendered
        tm.that(second, eq=first)
        tm.that(second.count(c.Infra.BANNER), eq=1)

    def test_scaffold_once_owner_has_no_continuous_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Keep user-owned scaffold output outside continuous maintenance."""
        custom = u.Tests.scaffold_text(
            tmp_path / "fixture-project",
            c.Infra.CUSTOM_MAKE_FILENAME,
        )
        tm.that(custom, lacks="[MANAGED]")
        tm.that(self._fields(custom), eq={})

    @staticmethod
    @pytest.mark.parametrize(
        "surface",
        [
            c.Infra.CodegenConformSurface.MAKEFILE,
            c.Infra.CodegenConformSurface.PYPROJECT,
        ],
    )
    def test_nested_scaffold_does_not_inherit_outer_git_identity(
        tmp_path: Path,
        surface: c.Infra.CodegenConformSurface,
    ) -> None:
        """A new destination retains unversioned evidence inside a real checkout."""
        outer = u.Tests.git_repository(tmp_path)
        root = outer / "fixture-project"
        plan = u.Tests.scaffold_plan(root, what=surface)
        tm.that(plan.issues, eq=(), msg=str(plan.issues))
        evidence = m.Infra.CodegenPlanningReport.model_validate_json(
            (
                tm.ok(u.Infra.refactor_report_evidence_root(Path.cwd()))
                / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH
            ).read_bytes()
        )
        tm.that(evidence.outcomes, len=1)
        tm.that(evidence.outcomes[0].candidate_kind, eq="unversioned")
        tm.that(evidence.outcomes[0].candidate_sha, eq=None)
        tm.that(evidence.outcomes[0].candidate_dirty, eq=None)
        tm.fail((root / c.GIT_DIR_NAME).exists())
        if surface is c.Infra.CodegenConformSurface.PYPROJECT:
            destinations = {
                file.path.relative_to(root)
                for file in plan.files
                if file.desired_content is not None
            }
            tm.that(destinations, has=Path(c.PYPROJECT_FILENAME))

    @staticmethod
    def test_scaffold_preserves_original_git_identity(tmp_path: Path) -> None:
        """An existing destination records its own original Git identity."""
        root = u.Tests.git_repository(tmp_path, name="fixture-project")
        plan = u.Tests.scaffold_plan(root, what=c.Infra.CodegenConformSurface.MAKEFILE)
        tm.that(plan.issues, eq=(), msg=str(plan.issues))
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        evidence = m.Infra.CodegenPlanningReport.model_validate_json(
            (
                tm.ok(u.Infra.refactor_report_evidence_root(Path.cwd()))
                / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH
            ).read_bytes()
        )
        tm.that(evidence.outcomes, len=1)
        tm.that(evidence.outcomes[0].candidate_kind, eq="git")
        tm.that(evidence.outcomes[0].candidate_sha, eq=identity.head_oid)
        tm.that(evidence.outcomes[0].candidate_dirty, eq=identity.dirty)

    @staticmethod
    def test_scaffold_preserves_original_git_failure(tmp_path: Path) -> None:
        """Malformed destination Git metadata remains an identity failure."""
        root = tmp_path / "fixture-project"
        (root / c.GIT_DIR_NAME).mkdir(parents=True)
        with pytest.raises(OSError, match="cannot open git repository"):
            u.Tests.scaffold_plan(root, what=c.Infra.CodegenConformSurface.MAKEFILE)
