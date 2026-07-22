"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import yaml
from flext_tests import tm

from flext_infra import c
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew


class TestCodegenCiMatrix:
    """Prove codegen emits the CI matrix workflow and distro Dockerfiles."""

    @staticmethod
    def _render_project(root: Path) -> Path:
        """Render a fresh EXTERNAL project into root and return the root."""
        service = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        )
        result = service.execute()
        tm.ok(result)
        return root

    def test_ci_matrix_workflow_emitted(self, tmp_path: Path) -> None:
        """Generated project carries .github/workflows/ci-matrix.yml."""
        root = self._render_project(tmp_path / "external")
        tm.that((root / ".github" / "workflows" / "ci-matrix.yml").is_file(), eq=True)

    def test_distro_dockerfiles_emitted(self, tmp_path: Path) -> None:
        """Generated project carries one Dockerfile per supported distro."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            tm.that(
                (root / "ci" / "docker" / f"{distro}.Dockerfile").is_file(), eq=True
            )

    def test_ci_matrix_has_all_legs(self, tmp_path: Path) -> None:
        """ci-matrix.yml declares every environment leg as a job."""
        root = self._render_project(tmp_path / "external")
        workflow = root / ".github" / "workflows" / "ci-matrix.yml"
        tm.that(workflow.is_file(), eq=True)
        content = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        jobs = content["jobs"]
        for leg in ("distro-matrix", "macos", "windows", "wsl", "kind"):
            tm.that(leg in jobs, eq=True)


__all__: list[str] = []
