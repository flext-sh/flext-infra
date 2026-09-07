"""Public conformance contract for declared Python distribution roots."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Literal

import pytest

from flext_infra import c, config, main as infra_main
from flext_tests import tm
from tests import t, u

if TYPE_CHECKING:
    from pathlib import Path


def _declared_roots() -> tuple[t.NonEmptyStr, t.NonEmptyStr]:
    """Derive arbitrary valid roots from the typed project fixture owner."""
    package_name = u.Tests.project_spec(config.Infra.name).package_name
    return f"{package_name}_entry", f"{package_name}_client"


def _prepare_project(
    root: Path, *, materialize_module: bool, materialize_package: bool
) -> tuple[t.NonEmptyStr, t.NonEmptyStr]:
    """Materialize one provider-governed project through shared typed fixtures."""
    _ = u.Tests.standalone_workspace(root, config.Infra.name)
    root_module, root_package = _declared_roots()
    source_root = root / c.Infra.DEFAULT_SRC_DIR
    if materialize_module:
        tm.ok(
            u.Cli.atomic_write_text_file(
                source_root / f"{root_module}.py", "VALUE = 1\n"
            )
        )
    if materialize_package:
        tm.ok(
            u.Cli.atomic_write_text_file(
                source_root / root_package / c.Infra.INIT_PY, "VALUE = 1\n"
            )
        )
    _ = u.Tests.write_standalone_workspace_manifest(root, config.Infra.name)
    u.Tests.copy_tracked_mise_seeds(root)
    return root_module, root_package


@pytest.mark.slow
def _conform_self(infra_git_repo: Path) -> int:
    """Run codegen conform self-apply through the public CLI entrypoint."""
    return infra_main([
        c.Infra.CLI_GROUP_CODEGEN,
        "conform",
        "--root",
        str(infra_git_repo),
        "--scope",
        c.Infra.CodegenConformScope.SELF.value,
        "--mode",
        c.Infra.CodegenConformMode.APPLY.value,
    ])


def test_conform_packages_every_declared_python_root(infra_git_repo: Path) -> None:
    """The public generator emits matching bounded wheel and sdist targets."""
    root_module, root_package = _prepare_project(
        infra_git_repo, materialize_module=True, materialize_package=True
    )

    applied = _conform_self(infra_git_repo)

    tm.that(applied, eq=0)
    payload = tomllib.loads(
        (infra_git_repo / c.Infra.PYPROJECT_FILENAME).read_text(encoding="utf-8")
    )
    targets = payload[c.Infra.TOOL]["hatch"]["build"]["targets"]
    primary_package = u.Tests.project_spec(config.Infra.name).package_name
    package_paths = {
        f"{c.Infra.DEFAULT_SRC_DIR}/{primary_package}",
        f"{c.Infra.DEFAULT_SRC_DIR}/{root_package}",
    }
    module_path = f"{c.Infra.DEFAULT_SRC_DIR}/{root_module}.py"
    tm.that(set(targets["wheel"]["packages"]), eq=package_paths)
    tm.that(targets["wheel"]["force-include"][module_path], eq=f"{root_module}.py")
    tm.that(package_paths <= set(targets["sdist"]["only-include"]), eq=True)
    tm.that(module_path in targets["sdist"]["only-include"], eq=True)

    fixed_point = infra_main([
        c.Infra.CLI_GROUP_CODEGEN,
        "conform",
        "--root",
        str(infra_git_repo),
        "--scope",
        c.Infra.CodegenConformScope.SELF.value,
        "--mode",
        c.Infra.CodegenConformMode.CHECK.value,
    ])
    tm.that(fixed_point, eq=0)


@pytest.mark.slow
@pytest.mark.parametrize("missing_kind", ["module", "package"])
def test_conform_rejects_missing_declared_python_root(
    infra_git_repo: Path,
    missing_kind: Literal["module", "package"],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A declaration never produces a phantom wheel or sdist path."""
    _ = _prepare_project(
        infra_git_repo,
        materialize_module=missing_kind != "module",
        materialize_package=missing_kind != "package",
    )
    before = (infra_git_repo / c.Infra.PYPROJECT_FILENAME).read_bytes()

    exit_code = _conform_self(infra_git_repo)

    output = capsys.readouterr()
    tm.that(exit_code, ne=0)
    tm.that(output.out + output.err, has=f"root {missing_kind}")
    tm.that((infra_git_repo / c.Infra.PYPROJECT_FILENAME).read_bytes(), eq=before)


__all__: t.StrSequence = []
