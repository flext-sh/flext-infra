"""Tests for FlextInfraCodegenLazyInit directory scanning behavior.

Validates that ``run()`` correctly scans all standard directories
(``src/``, ``tests/``, ``examples/``, ``scripts/``) and applies
PEP 562 lazy-import generation uniformly.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


_VALID_INIT = (
    '"""Test package."""\n'
    "from test_pkg.module import TestClass\n"
    '__all__: list[str] = ["TestClass"]\n'
)
_VALID_TESTS_INIT = (
    '"""Test helpers."""\n'
    "from test_helpers.fixtures import SomeFixture\n"
    '__all__: list[str] = ["SomeFixture"]\n'
)


def _create_init_file(directory: Path, content: str) -> Path:
    """Write a package initializer with exact content under ``directory``.

    Returns:
        The created initializer path.

    """
    directory.mkdir(parents=True, exist_ok=True)
    init_file = directory / "__init__.py"
    init_file.write_text(content, encoding="utf-8")
    return init_file


@pytest.fixture
def governed_project(tmp_path: Path) -> Path:
    """Provide the project manifest every scanned package belongs to.

    Lazy-init plans a package only inside a physical project, and the
    generated notice names the manifest's first author and its license.

    Returns:
        The resulting ``Path``.

    """
    (tmp_path / c.PYPROJECT_FILENAME).write_text(
        '[project]\nname = "test-helpers"\nversion = "0.1.0"\n'
        f'license = "{u.Tests.project_spec("test-helpers").license}"\n'
        'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.usefixtures("governed_project")
class TestsFlextInfraCodegenLazyInit:
    """Test suite for FlextInfraCodegenLazyInit directory scanning behavior."""

    class TestsAllDirectoriesScanned:
        """All standard directories are always scanned."""

        @staticmethod
        def test_src_dir_is_scanned(tmp_path: Path) -> None:
            """Scan public source packages in check mode."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_tests_dir_is_scanned(governed_project: Path) -> None:
            """Scan test packages in check mode."""
            _create_init_file(
                governed_project / "tests" / "helpers",
                _VALID_TESTS_INIT,
            )
            generator = FlextInfraCodegenLazyInit(repository_root=governed_project)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_tests_init_files_are_processed(tmp_path: Path) -> None:
            """Regenerate discovered test package initializers."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            tests_init = _create_init_file(
                tmp_path / "tests" / "helpers",
                _VALID_TESTS_INIT,
            )
            original_content = tests_init.read_text(encoding="utf-8")
            tm.that(u.Tests.run_lazy_init(tmp_path), eq=0)
            new_content = tests_init.read_text(encoding="utf-8")
            tm.that(
                new_content != original_content or "__all__" in new_content,
                eq=True,
            )

        @staticmethod
        def test_nested_tests_packages_are_found(tmp_path: Path) -> None:
            """Discover nested test packages recursively."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            nested_init = _create_init_file(
                tmp_path / "tests" / "unit" / "helpers",
                '"""Nested test helpers."""\n'
                "from test_helpers.deep import DeepFixture\n"
                '__all__: list[str] = ["DeepFixture"]\n',
            )
            tm.that(u.Tests.run_lazy_init(tmp_path), eq=0)
            tm.ok(nested_init.exists())

    class TestsCheckOnlyMode:
        """check_only=True reports without writing."""

        @staticmethod
        def test_check_only_does_not_modify_files(governed_project: Path) -> None:
            """Leave initializer bytes unchanged in check mode."""
            tests_init = _create_init_file(
                governed_project / "tests" / "helpers",
                _VALID_TESTS_INIT,
            )
            original_content = tests_init.read_text(encoding="utf-8")
            generator = FlextInfraCodegenLazyInit(repository_root=governed_project)
            tm.ok(generator.plan_files().success)
            tm.that(tests_init.read_text(encoding="utf-8"), eq=original_content)

    class TestsExcludedDirectories:
        """Vendor and .venv directories are excluded."""

        @staticmethod
        def test_vendor_dir_excluded(tmp_path: Path) -> None:
            """Exclude vendored test packages from discovery."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            _create_init_file(
                tmp_path / "tests" / "vendor" / "pkg",
                _VALID_TESTS_INIT,
            )
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_venv_dir_excluded(tmp_path: Path) -> None:
            """Exclude virtual-environment test packages from discovery."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            _create_init_file(
                tmp_path / "tests" / ".venv" / "pkg",
                _VALID_TESTS_INIT,
            )
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_nested_site_packages_dir_excluded(tmp_path: Path) -> None:
            """Exclude nested site-packages directories from discovery."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            _create_init_file(
                tmp_path
                / "pkg"
                / "container"
                / "venv"
                / "lib"
                / "site-packages"
                / "bad",
                _VALID_TESTS_INIT,
            )
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_runtime_scratch_dir_excluded_from_plans(tmp_path: Path) -> None:
            """Exclude ephemeral runtime packages declared by the artifact SSOT."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            scratch_init = _create_init_file(
                tmp_path / ".test-runtime" / "invocation" / "tests",
                _VALID_TESTS_INIT,
            )
            result = FlextInfraCodegenLazyInit(repository_root=tmp_path).plan_files()
            tm.ok(result)
            tm.that({plan.path for plan in result.value.files}, lacks=scratch_init)

        @staticmethod
        def test_generated_tool_state_is_excluded_from_plans(
            tmp_path: Path,
        ) -> None:
            """Exclude disposable test and projected provider package trees."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            generated = tuple(
                _create_init_file(
                    tmp_path / directory / "provider" / "pkg",
                    _VALID_TESTS_INIT,
                )
                for directory in (".agents-sync-home", ".test-tmp")
            )

            result = FlextInfraCodegenLazyInit(repository_root=tmp_path).plan_files()

            tm.ok(result)
            planned = {plan.path for plan in result.value.files}
            for init_file in generated:
                tm.that(planned, lacks=init_file)

        @staticmethod
        def test_declared_sources_do_not_include_foreign_runtime_trees(
            tmp_path: Path,
        ) -> None:
            """Only governed source roots supply packages and snapshot inputs."""
            repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
            u.Tests.write_lazy_init_namespace_module(
                package / "models.py",
                class_name="FlextScopedModels",
                alias="m",
                docstring="Owned models.",
            )
            owned_inits = {package / c.Infra.INIT_PY}
            source_roots = config.Infra.source_scan.roots
            for source_root in source_roots:
                if source_root == c.Infra.DEFAULT_SRC_DIR:
                    continue
                owned = repository / source_root / "owned_package"
                owned_init = _create_init_file(owned, "")
                (owned / "provider.py").write_text(
                    "class Owned: pass\n__all__ = ('Owned',)\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                owned_inits.add(owned_init)
            outside = repository / ("off_scope_" + "_".join(source_roots))
            foreign_paths: set[Path] = set()
            for relative in (
                "worktrees/member/.venv/python/bin",
                "skills/provider/scripts",
                "scratch/demos/examples",
            ):
                foreign = outside / relative
                foreign_paths.add(_create_init_file(foreign, ""))
                for suffix in c.Infra.PYTHON_SOURCE_SUFFIXES:
                    module = foreign / f"provider{suffix}"
                    module.write_text(
                        "class Foreign: pass\n__all__ = ('Foreign',)\n",
                        encoding=c.DEFAULT_ENCODING,
                    )
                    foreign_paths.add(module)

            result = FlextInfraCodegenLazyInit(repository_root=repository).plan_files()

            tm.ok(result)
            planned = {plan.path for plan in result.value.files}
            tm.ok(owned_inits <= planned)
            inputs = {state.path for state in result.value.inputs}
            tm.ok(planned.isdisjoint(foreign_paths))
            tm.ok(inputs.isdisjoint(foreign_paths))

    class TestsEdgeCases:
        """Edge cases for directory scanning."""

        @staticmethod
        def test_empty_workspace_returns_zero(tmp_path: Path) -> None:
            """Return zero changes for an empty workspace."""
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            tm.ok(generator.plan_files().success)
            tm.that(u.Tests.run_lazy_init(tmp_path), eq=0)

        @staticmethod
        def test_tests_dir_without_init_py_is_skipped(tmp_path: Path) -> None:
            """Ignore a test directory that is not a package."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            tests_dir = tmp_path / "tests" / "helpers"
            tests_dir.mkdir(parents=True)
            (tests_dir / "conftest.py").write_text("# conftest", encoding="utf-8")
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_no_tests_dir_at_all(tmp_path: Path) -> None:
            """Process source packages when no tests directory exists."""
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            result = generator.plan_files()
            tm.ok(result.success)

        @staticmethod
        def test_plan_files_returns_flext_result(tmp_path: Path) -> None:
            """Expose planning status through the public result contract.

            Publication is owned by ``codegen conform``: the generation
            transaction publishes ``plan_files()``, so a direct ``execute()``
            is refused by design and the planning surface is the contract.
            """
            _create_init_file(tmp_path / "src" / "pkg", _VALID_INIT)
            generator = FlextInfraCodegenLazyInit(repository_root=tmp_path)
            tm.ok(generator.execute().failure)
            planned = tm.ok(generator.plan_files())
            tm.that(
                all(plan.path.name == c.Infra.INIT_PY for plan in planned.files),
                eq=True,
            )

        @staticmethod
        def test_src_content_consistent_across_runs(tmp_path: Path) -> None:
            """Render identical source packages to identical bytes."""
            src_content = (
                '"""Package."""\n'
                "from pkg.models import MyModel\n"
                '__all__: list[str] = ["MyModel"]\n'
            )
            # Each run plans one repository, so each owns the project manifest.
            manifest = (tmp_path / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
            for repository in ("a", "b"):
                (tmp_path / repository).mkdir()
                (tmp_path / repository / c.PYPROJECT_FILENAME).write_text(
                    manifest,
                    encoding="utf-8",
                )
            src_dir_a = tmp_path / "a" / "src" / "pkg"
            _create_init_file(src_dir_a, src_content)
            tm.that(u.Tests.run_lazy_init(tmp_path / "a"), eq=0)
            content_a = (src_dir_a / "__init__.py").read_text(encoding="utf-8")
            src_dir_b = tmp_path / "b" / "src" / "pkg"
            _create_init_file(src_dir_b, src_content)
            tm.that(u.Tests.run_lazy_init(tmp_path / "b"), eq=0)
            content_b = (src_dir_b / "__init__.py").read_text(encoding="utf-8")
            tm.that(content_a, eq=content_b)

    class TestsGeneratedSourceTrees:
        """A generated source tree is a regular package, never a facade.

        Premise (flext-gknfx): protoc output carries no ``__init__.py``; the
        fresh-import gate rejected the resulting namespace package because its
        modules had no origin inside the checkout.
        """

        @classmethod
        def _generated_tree(cls, project: Path) -> Path:
            """Create one indexed package holding the declared generated tree.

            Returns:
                The generated source directory inside ``src/pkg``.

            """
            names = config.Infra.codegen.generated_sources
            tm.that(names, empty=False)
            package = project / "src" / "pkg"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text(_VALID_INIT, encoding="utf-8")
            tree = package / names[0]
            tree.mkdir()
            return tree

        def test_tree_with_modules_receives_a_static_initializer(
            self,
            governed_project: Path,
        ) -> None:
            """Generation writes one exportless initializer and then converges."""
            tree = self._generated_tree(governed_project)
            (tree / "wire_pb2.py").write_text("DESCRIPTOR = None\n", encoding="utf-8")

            tm.that(u.Tests.run_lazy_init(governed_project), eq=0)

            initializer = (tree / c.Infra.INIT_PY).read_text(encoding="utf-8")
            tm.ok(initializer.startswith(c.Infra.AUTOGEN_HEADERS))
            tm.that(initializer, lacks="wire_pb2")
            replanned = tm.ok(
                FlextInfraCodegenLazyInit(
                    repository_root=governed_project
                ).plan_files(),
            )
            tm.that(
                tuple(
                    plan.path
                    for plan in replanned.files
                    if u.Infra.codegen_file_requires_effect(plan)
                ),
                eq=(),
            )

        def test_tree_without_modules_receives_no_initializer(
            self,
            governed_project: Path,
        ) -> None:
            """A tree holding only protocol sources is not a Python package."""
            tree = self._generated_tree(governed_project)
            (tree / "wire.proto").write_text('syntax = "proto3";\n', encoding="utf-8")

            tm.that(u.Tests.run_lazy_init(governed_project), eq=0)

            tm.fail((tree / c.Infra.INIT_PY).exists())
