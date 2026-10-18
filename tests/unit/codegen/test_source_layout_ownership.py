# Copyright (c) 2026 FLEXT Team. All rights reserved.
"""Prove declared ownership for complete staged project views."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codegen import FlextInfraStagedPackage
from tests import c, tm, u


class TestsFlextInfraSourceLayoutOwnership:
    """Metadata and helper locations do not invent project boundaries."""

    @staticmethod
    @pytest.mark.parametrize("directory", ["project", ".project"])
    @pytest.mark.parametrize(
        "relative",
        [".github/scripts/check.py", "automation/scripts/check.py"],
    )
    def test_declared_project_owns_helpers_and_its_manifest(
        tmp_path: Path,
        directory: str,
        relative: str,
    ) -> None:
        """Materialize a joint candidate without touching its original sources."""
        root = u.Tests.git_repository(tmp_path / directory)
        package = u.Tests.src_package(
            root,
            "ownership_sample",
            pyproject="[project]\nname='ownership-sample'\nversion='1.0.0'\n",
        )
        (package / c.Infra.INIT_PY).write_text(
            "VALUE = 1\n", encoding=c.DEFAULT_ENCODING
        )
        helper = root / relative
        helper.parent.mkdir(parents=True)
        helper.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        manifest = root / c.PYPROJECT_FILENAME
        original = manifest.read_text(encoding=c.DEFAULT_ENCODING)
        desired = original + "\n# Candidate metadata\n"

        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {helper: "VALUE = 2\n", manifest: desired},
            )
        )
        candidate = tmp_path / "candidate"
        tm.ok(FlextInfraStagedPackage.materialize_sources(plan, candidate))

        tm.that(
            (candidate / relative).read_text(encoding=c.DEFAULT_ENCODING),
            eq="VALUE = 2\n",
        )
        tm.that(
            (candidate / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
            eq=desired,
        )
        tm.that(helper.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE = 1\n")
        tm.that(manifest.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

    @staticmethod
    def test_nested_member_keeps_its_most_specific_declared_owner(
        tmp_path: Path,
    ) -> None:
        """A containing workspace cannot replace the member's import identity."""
        root = u.Tests.git_repository(tmp_path / "workspace")
        u.Tests.src_package(
            root,
            "outer_sample",
            pyproject="[project]\nname='outer-sample'\nversion='1.0.0'\n",
        )
        member = root / "member"
        package = u.Tests.src_package(
            member,
            "inner_sample",
            pyproject="[project]\nname='inner-sample'\nversion='1.0.0'\n",
        )
        (package / c.Infra.INIT_PY).write_text(
            "VALUE = 1\n", encoding=c.DEFAULT_ENCODING
        )
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "member"]\n\tpath = member\n',
            encoding=c.DEFAULT_ENCODING,
        )
        helper = member / "automation" / "scripts" / "check.py"
        helper.parent.mkdir(parents=True)
        helper.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)

        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(root, {helper: "VALUE = 2\n"})
        )
        candidate = tmp_path / "candidate"
        tm.ok(FlextInfraStagedPackage.materialize_sources(plan, candidate))

        tm.that(any(layout.project_root == member for layout in plan.layouts), eq=True)
        tm.that(any(layout.project_root == root for layout in plan.layouts), eq=False)
        tm.that(
            (candidate / helper.relative_to(root)).read_text(
                encoding=c.DEFAULT_ENCODING
            ),
            eq="VALUE = 2\n",
        )
        tm.that(helper.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE = 1\n")
