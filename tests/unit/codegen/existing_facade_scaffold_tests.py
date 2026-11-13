"""Conform creates absent family facades in an existing FLEXT repository.

A repository newly declared ``internal_flext`` must not need hand-written
facades before its first generation: the scaffold templates render each
absent facade once, and never touch one that already exists.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodegenExistingFacadeScaffold:
    """Existing internal FLEXT repositories gain only their absent facades."""

    @staticmethod
    def _plan(tmp_path: Path, *, authored_models: str | None) -> tuple[Path, str]:
        """Plan one existing governed repository without pre-written facades.

        Returns:
            The repository root and its package name.

        """
        distribution = "sample-library"
        root = tmp_path / distribution
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=distribution,
                database=distribution.replace("-", "_"),
                issue_prefix=distribution,
            ),
        )
        project = u.Tests.project_spec(distribution)
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {
                                "project": project.model_dump(mode="json"),
                            },
                        },
                    },
                },
            ),
        )
        package_dir = root / c.Infra.DEFAULT_SRC_DIR / project.package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        if authored_models is not None:
            (package_dir / "models.py").write_text(authored_models, encoding="utf-8")
        return root, project.package_name

    @staticmethod
    def _planned(root: Path) -> p.Infra.CodegenPlan:
        """Run the public conform planner read-only.

        Returns:
            The validated plan.

        """
        request = u.Tests.conform_request(root)
        result = u.Tests.conform_plan_result(root, request)
        return m.Infra.CodegenPlan.model_validate(tm.ok(result))

    @c.Tests.MARK.slow
    def test_absent_facades_are_planned(self, tmp_path: Path) -> None:
        """Every absent public facade appears in the plan with its canonical class."""
        root, package = self._plan(tmp_path, authored_models=None)
        plan = self._planned(root)
        project = u.Tests.project_spec("sample-library")
        for module, suffix in (("models", "Models"), ("protocols", "Protocols")):
            text = u.Tests.planned_text(plan, f"src/{package}/{module}.py")
            tm.that(text, none=False)
            tm.that(text, has=f"class {project.class_stem}{suffix}")

    @c.Tests.MARK.slow
    def test_an_existing_facade_is_never_rewritten(self, tmp_path: Path) -> None:
        """An authored facade keeps its bytes; only absent ones are planned."""
        authored = (
            '"""Authored."""\n\n'
            "from __future__ import annotations\n\n"
            "from flext_core import FlextModels\n\n\n"
            "class SampleLibraryModels(FlextModels):\n"
            '    """Authored models facade."""\n\n\n'
            "m = SampleLibraryModels\n\n"
            '__all__: list[str] = ["SampleLibraryModels", "m"]\n'
        )
        root, package = self._plan(tmp_path, authored_models=authored)
        plan = self._planned(root)
        tm.that(u.Tests.planned_text(plan, f"src/{package}/models.py"), none=True)
        tm.that(
            (root / c.Infra.DEFAULT_SRC_DIR / package / "models.py").read_text(
                encoding="utf-8"
            ),
            eq=authored,
        )
