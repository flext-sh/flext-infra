"""Canonical lazy-init generation behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from flext_infra import c, u
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit

_TEST_FACADE_EXPORTS = ("c", "d", "e", "h", "m", "p", "r", "s", "t", "u", "x")
_PROJECT_CONFIG = Path(__file__).parents[3] / "pyproject.toml"


def _generator(
    workspace_root: Path, *, module: str = "tests"
) -> FlextInfraCodegenLazyInit:
    return FlextInfraCodegenLazyInit.model_validate({
        "workspace": workspace_root,
        "module": module,
    })


def _generated_exports(generated: str, tests_init: Path) -> tuple[str, ...]:
    module = ast.parse(generated, filename=str(tests_init))
    assignment = next(
        statement
        for statement in module.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == "__all__"
    )
    if assignment.value is None:
        pytest.fail("generated tests facade has no __all__ value")
    exports = ast.literal_eval(assignment.value)
    if not isinstance(exports, tuple) or not all(
        isinstance(export_name, str) for export_name in exports
    ):
        pytest.fail(f"generated tests facade has invalid __all__: {exports}")
    return exports


def _workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "flext-sample"
    package_root = workspace_root / "src" / "flext_sample"
    deps_tests = workspace_root / "tests" / "unit" / "deps"
    package_root.mkdir(parents=True)
    deps_tests.mkdir(parents=True)
    (workspace_root / "pyproject.toml").write_text(
        '[project]\nname = "flext-sample"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (package_root / "__init__.py").write_text("__all__ = ()\n", encoding="utf-8")
    (workspace_root / "tests" / "__init__.py").write_text(
        '"""Tests package."""\n', encoding="utf-8"
    )
    (deps_tests / "test_example.py").write_text(
        "def test_example() -> None:\n    assert True\n", encoding="utf-8"
    )
    (workspace_root / "tests" / "unit" / "test_unit.py").write_text(
        "def test_unit() -> None:\n    assert True\n", encoding="utf-8"
    )
    return workspace_root


def _examples_workspace(tmp_path: Path) -> Path:
    workspace_root = _workspace(tmp_path)
    examples_root = workspace_root / "examples"
    examples_root.mkdir()
    (examples_root / "__init__.py").write_text(
        f'{c.Infra.AUTOGEN_HEADER}\n"""Examples package."""\n', encoding="utf-8"
    )
    (examples_root / "protocols.py").write_text(
        "class ExamplesProtocols:\n    VALUE = 42\n\np = ExamplesProtocols\n"
        '\n__all__ = ("ExamplesProtocols", "p")\n',
        encoding="utf-8",
    )
    (examples_root / "typings.py").write_text(
        "class ExamplesTypes:\n    VALUE = 1\n\nt = ExamplesTypes\n"
        '\n__all__ = ("ExamplesTypes", "t")\n',
        encoding="utf-8",
    )
    (examples_root / "constants.py").write_text(
        "class ExamplesConstants:\n    VALUE = 42\n\n"
        "c = ExamplesConstants\n\n"
        '__all__ = ("ExamplesConstants", "c")\n',
        encoding="utf-8",
    )
    (examples_root / "models.py").write_text(
        "from examples import c, p, t\n\n"
        "class ExamplesModels:\n    VALUE = c.VALUE + p.VALUE + t.VALUE\n\n"
        "m = ExamplesModels\n\n"
        '__all__ = ("ExamplesModels", "m")\n',
        encoding="utf-8",
    )
    (examples_root / "utilities.py").write_text(
        "from examples import c, m\n\n"
        "class ExamplesUtilities:\n    VALUE = c.VALUE + m.VALUE\n\n"
        "u = ExamplesUtilities\n\n"
        '__all__ = ("ExamplesUtilities", "u")\n',
        encoding="utf-8",
    )
    (examples_root / "executable.py").write_text(
        "from examples import c, m\n\n"
        "class ExecutableExample:\n    VALUE = c.VALUE + m.VALUE\n\n"
        'def main() -> None:\n    print(f"PASS: {ExecutableExample.VALUE}")\n\n'
        'if __name__ == "__main__":\n    main()\n\n'
        '__all__ = ("ExecutableExample",)\n',
        encoding="utf-8",
    )
    return workspace_root


class TestsFlextInfraCodegenLazyInit:
    """Verify generated test wrappers through the public service."""

    def test_tests_surface_is_ruff_clean_and_preserves_facades(
        self, tmp_path: Path
    ) -> None:
        """Generate one Ruff-clean wrapper with the canonical test facades."""
        workspace_root = _workspace(tmp_path)
        generator = _generator(workspace_root)

        errors = generator.generate_inits()

        if errors:
            pytest.fail(f"lazy-init generation returned {errors} errors")
        tests_init = workspace_root / "tests" / "__init__.py"
        generated = tests_init.read_text(encoding="utf-8")
        exports = _generated_exports(generated, tests_init)
        if exports != _TEST_FACADE_EXPORTS:
            pytest.fail(f"unexpected tests facade exports: {exports}")
        ruff = u.Cli.run_raw(
            (
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--no-fix",
                "--config",
                str(_PROJECT_CONFIG),
                str(tests_init),
            ),
            cwd=workspace_root,
        ).unwrap()
        if ruff.exit_code != 0:
            pytest.fail(ruff.stderr or ruff.stdout)

    def test_tests_children_are_empty_static_packages(self, tmp_path: Path) -> None:
        """Generate empty static initializers for every tests child package."""
        workspace_root = _workspace(tmp_path)
        generator = _generator(workspace_root)

        errors = generator.generate_inits()

        if errors:
            pytest.fail(f"lazy-init generation returned {errors} errors")
        for relative_path in ("tests/unit/__init__.py", "tests/unit/deps/__init__.py"):
            generated = (workspace_root / relative_path).read_text(encoding="utf-8")
            if "__all__: tuple[str, ...] = ()" not in generated:
                pytest.fail(f"non-empty static package generated at {relative_path}")
            if "_install_lazy_exports" in generated:
                pytest.fail(f"lazy exports generated at {relative_path}")

    def test_wrapper_binds_inherited_facade_before_local_consumer(
        self, tmp_path: Path
    ) -> None:
        """A generated wrapper imports when a local module consumes its root facade."""
        workspace_root = _examples_workspace(tmp_path)
        generator = _generator(workspace_root, module="examples")

        errors = generator.generate_inits()

        if errors:
            pytest.fail(f"lazy-init generation returned {errors} errors")
        imported = u.Cli.run_raw(
            (
                c.Infra.PYTHON,
                "-c",
                "import examples; print(examples.u.VALUE)",
            ),
            cwd=workspace_root,
        ).unwrap()
        if imported.exit_code != 0:
            pytest.fail(imported.stderr or imported.stdout)
        if imported.stdout.strip() != "127":
            pytest.fail(f"unexpected generated wrapper value: {imported.stdout!r}")

        executed = u.Cli.run_raw(
            (c.Infra.PYTHON, "-W", "error", "-m", "examples.executable"),
            cwd=workspace_root,
        ).unwrap()
        if executed.exit_code != 0:
            pytest.fail(executed.stderr or executed.stdout)
        if executed.stdout.strip() != "PASS: 127":
            pytest.fail(f"unexpected executable output: {executed.stdout!r}")
