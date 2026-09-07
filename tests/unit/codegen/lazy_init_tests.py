"""Directory-scanning contract of the public lazy-init codegen service.

Every workspace here is provisioned by the canonical ``u.Tests`` builders, so a
change to what a FLEXT project must declare reaches these tests through that
owner instead of a private copy of the layout.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_infra import c
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_tests import tm
from tests import t, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodegenLazyInit:
    """All standard directories are scanned and excluded trees never planned."""

    SOURCE_INIT: ClassVar[str] = (
        '"""Test package."""\n'
        "from test_pkg.module import TestClass\n"
        '__all__: list[str] = ["TestClass"]\n'
    )
    TESTS_INIT: ClassVar[str] = (
        '"""Test helpers."""\n'
        "from test_helpers.fixtures import SomeFixture\n"
        '__all__: list[str] = ["SomeFixture"]\n'
    )

    def test_source_package_is_scanned(self, tmp_path: Path) -> None:
        """Scan public source packages in check mode."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_package_init(
            root / c.Infra.DEFAULT_SRC_DIR / "pkg", self.SOURCE_INIT
        )
        tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())

    def test_tests_package_is_scanned(self, tmp_path: Path) -> None:
        """Scan test packages in check mode."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_package_init(root / "tests" / "helpers", self.TESTS_INIT)
        tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())

    def test_tests_initializer_is_materialized(self, tmp_path: Path) -> None:
        """Regenerate discovered test package initializers."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        tests_init = u.Tests.write_package_init(
            root / "tests" / "helpers", self.TESTS_INIT
        )
        original = tests_init.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        rendered = tests_init.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        tm.that(rendered != original or "__all__" in rendered, eq=True)

    def test_nested_tests_packages_are_found(self, tmp_path: Path) -> None:
        """Discover nested test packages recursively."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        nested_init = u.Tests.write_package_init(
            root / "tests" / "unit" / "helpers",
            '"""Nested test helpers."""\n'
            "from test_helpers.deep import DeepFixture\n"
            '__all__: list[str] = ["DeepFixture"]\n',
        )
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        tm.that(nested_init.exists(), eq=True)

    def test_check_only_leaves_bytes_untouched(self, tmp_path: Path) -> None:
        """Planning alone never writes an initializer."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        tests_init = u.Tests.write_package_init(
            root / "tests" / "helpers", self.TESTS_INIT
        )
        original = tests_init.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())
        tm.that(tests_init.read_text(encoding=c.Infra.ENCODING_DEFAULT), eq=original)

    def test_vendor_and_environment_trees_are_excluded(self, tmp_path: Path) -> None:
        """Vendored, virtual-environment and site-packages trees never plan."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_package_init(
            root / c.Infra.DEFAULT_SRC_DIR / "pkg", self.SOURCE_INIT
        )
        excluded = tuple(
            u.Tests.write_package_init(root / relative, self.TESTS_INIT)
            for relative in (
                "tests/vendor/pkg",
                "tests/.venv/pkg",
                "pkg/container/venv/lib/site-packages/bad",
            )
        )
        planned = tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())
        planned_paths = {plan.path for plan in planned.files}
        for init_file in excluded:
            tm.that(planned_paths, lacks=init_file)

    def test_runtime_scratch_tree_is_excluded(self, tmp_path: Path) -> None:
        """Exclude ephemeral runtime packages declared by the artifact SSOT."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_package_init(
            root / c.Infra.DEFAULT_SRC_DIR / "pkg", self.SOURCE_INIT
        )
        scratch_init = u.Tests.write_package_init(
            root / ".test-runtime" / "invocation" / "tests", self.TESTS_INIT
        )
        planned = tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())
        tm.that({plan.path for plan in planned.files}, lacks=scratch_init)

    def test_workspace_without_extra_packages_plans_no_change(
        self, tmp_path: Path
    ) -> None:
        """A workspace carrying only its declared package needs no rewrite."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())
        tm.that(u.Tests.run_lazy_init(root), eq=0)

    def test_directory_without_initializer_is_skipped(self, tmp_path: Path) -> None:
        """Ignore a test directory that is not a package."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_package_init(
            root / c.Infra.DEFAULT_SRC_DIR / "pkg", self.SOURCE_INIT
        )
        loose_directory = root / "tests" / "helpers"
        loose_directory.mkdir(parents=True)
        (loose_directory / "conftest.py").write_text(
            "# conftest", encoding=c.Infra.ENCODING_DEFAULT
        )
        planned = tm.ok(FlextInfraCodegenLazyInit(repository_root=root).plan_files())
        tm.that(
            {plan.path for plan in planned.files},
            lacks=loose_directory / c.Infra.INIT_PY,
        )

    def test_execute_reports_through_the_result_contract(self, tmp_path: Path) -> None:
        """Expose execution status through the public result contract."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_package_init(
            root / c.Infra.DEFAULT_SRC_DIR / "pkg", self.SOURCE_INIT
        )
        executed = tm.ok(FlextInfraCodegenLazyInit(repository_root=root).execute())
        tm.that(executed, is_=bool)

    def test_identical_sources_render_identical_bytes(self, tmp_path: Path) -> None:
        """Render identical source packages to identical bytes across runs."""
        source = (
            '"""Package."""\n'
            "from pkg.models import MyModel\n"
            '__all__: list[str] = ["MyModel"]\n'
        )
        rendered: list[str] = []
        for lane in ("a", "b"):
            root, _ = u.Tests.create_lazy_init_workspace(tmp_path / lane)
            package_init = u.Tests.write_package_init(
                root / c.Infra.DEFAULT_SRC_DIR / "pkg", source
            )
            tm.that(u.Tests.run_lazy_init(root), eq=0)
            rendered.append(package_init.read_text(encoding=c.Infra.ENCODING_DEFAULT))
        tm.that(rendered[0], eq=rendered[1])


__all__: t.StrSequence = []
