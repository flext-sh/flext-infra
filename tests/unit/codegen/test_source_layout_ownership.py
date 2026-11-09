# Copyright (c) 2026 FLEXT Team. All rights reserved.
"""Prove declared ownership for complete staged project views."""

from __future__ import annotations

import stat
from pathlib import Path

from flext_infra.codegen import FlextInfraStagedPackage
from tests import c, m, tm, u


class TestsFlextInfraSourceLayoutOwnership:
    """Metadata and helper locations do not invent project boundaries."""

    @staticmethod
    def test_materializes_independent_directories_with_declared_bytes_and_modes(
        tmp_path: Path,
    ) -> None:
        """A bounded write wave preserves every staged file's exact identity."""
        root = u.Tests.git_repository(tmp_path / "workspace")
        package = u.Tests.src_package(
            root,
            "ownership_sample",
            pyproject="[project]\nname='ownership-sample'\nversion='1.0.0'\n",
        )
        first = package / "one" / "first.py"
        second = root / "automation" / "two" / "second.py"
        for path, content, mode in (
            (first, "FIRST = 1\n", 0o640),
            (second, "SECOND = 1\n", 0o751),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=c.DEFAULT_ENCODING)
            path.chmod(mode)

        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {first: "FIRST = 2\n", second: "SECOND = 2\n"},
            )
        )
        candidate = tmp_path / "candidate"

        tm.ok(FlextInfraStagedPackage.materialize_sources(plan, candidate))

        for path, content, mode in (
            (first, b"FIRST = 2\n", 0o640),
            (second, b"SECOND = 2\n", 0o751),
        ):
            staged = candidate / path.relative_to(root)
            tm.that(staged.read_bytes(), eq=content)
            tm.that(stat.S_IMODE(staged.stat().st_mode), eq=mode)
        tm.that(first.read_bytes(), eq=b"FIRST = 1\n")
        tm.that(second.read_bytes(), eq=b"SECOND = 1\n")

    @staticmethod
    def test_materialize_failure_leaves_live_source_untouched(tmp_path: Path) -> None:
        """A scratch symlink collision fails without following into live sources."""
        root = u.Tests.git_repository(tmp_path / "workspace")
        u.Tests.src_package(
            root,
            "ownership_sample",
            pyproject="[project]\nname='ownership-sample'\nversion='1.0.0'\n",
        )
        manifest = root / c.PYPROJECT_FILENAME
        original = manifest.read_bytes()
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {manifest: original.decode(c.DEFAULT_ENCODING) + "\n# candidate\n"},
            )
        )
        candidate = tmp_path / "candidate"
        candidate.mkdir()
        collision = candidate / c.PYPROJECT_FILENAME
        collision.symlink_to(manifest)

        rejected = FlextInfraStagedPackage.materialize_sources(plan, candidate)

        tm.fail(rejected)
        tm.that(manifest.read_bytes(), eq=original)
        tm.that(collision.is_symlink(), eq=True)

    @staticmethod
    @c.Tests.MARK.parametrize("directory", ["project", ".project"])
    @c.Tests.MARK.parametrize(
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
        sibling = helper.with_name("other.py")
        sibling.write_text("OTHER = 1\n", encoding=c.DEFAULT_ENCODING)

        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {helper: "VALUE = 2\n"},
                options=m.Infra.StageSourceOptions(
                    inputs=tuple(
                        tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                        for path in (helper, sibling)
                    ),
                ),
            )
        )
        candidate = tmp_path / "candidate"
        tm.ok(FlextInfraStagedPackage.materialize_sources(plan, candidate))

        tm.ok(any(layout.project_root == member for layout in plan.layouts))
        tm.fail(any(layout.project_root == root for layout in plan.layouts))
        tm.that(
            (candidate / helper.relative_to(root)).read_text(
                encoding=c.DEFAULT_ENCODING
            ),
            eq="VALUE = 2\n",
        )
        tm.that(helper.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE = 1\n")
        tm.that(sibling.read_text(encoding=c.DEFAULT_ENCODING), eq="OTHER = 1\n")
