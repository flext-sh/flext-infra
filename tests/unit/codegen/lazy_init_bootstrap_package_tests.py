"""Declared initializer exports exercised through real package consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraLazyInitBootstrapPackage:
    """Every initializer publishes its owning modules' declared contract."""

    @staticmethod
    @pytest.mark.parametrize("subpackage_first", [False, True])
    def test_shipped_bootstrap_packages_publish_their_declared_classes(
        *, subpackage_first: bool
    ) -> None:
        """Cold-import native roots and preserve installer/declaration identities."""
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "import importlib, pkgutil, sys\n"
                        "from typing import TypeAliasType\n"
                        "assert sys.argv[1] not in sys.modules\n"
                        f"if {subpackage_first!r}:\n"
                        "    importlib.import_module(sys.argv[3])\n"
                        "core = importlib.import_module(sys.argv[1])\n"
                        "helpers = sys.argv[4:]\n"
                        "for name in helpers:\n"
                        "    assert name in vars(core), name\n"
                        "    assert name in core.__all__, name\n"
                        "    assert name in dir(core), name\n"
                        "    assert name not in core._LAZY_IMPORTS, name\n"
                        "loader = importlib.import_module(sys.argv[2])\n"
                        "for name in helpers:\n"
                        "    assert vars(core)[name] is getattr(loader, name), name\n"
                        f"from {c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE} import "
                        "install_lazy_exports\n"
                        "assert install_lazy_exports is loader.install_lazy_exports\n"
                        "for name in loader.__all__:\n"
                        "    value = getattr(loader, name)\n"
                        "    if isinstance(value, type):\n"
                        "        assert getattr(core, name) is value, name\n"
                        "packages = (sys.argv[3],)\n"
                        "for package_name in packages:\n"
                        "    package = importlib.import_module(package_name)\n"
                        "    assert vars(package)['install_lazy_exports'] is"
                        " install_lazy_exports, package_name\n"
                        "    expected = set()\n"
                        "    for info in pkgutil.iter_modules(package.__path__,"
                        " package_name + '.'):\n"
                        "        if info.ispkg:\n"
                        "            continue\n"
                        "        leaf = importlib.import_module(info.name)\n"
                        "        for name in getattr(leaf, '__all__', ()):\n"
                        "            if not isinstance(getattr(leaf, name), type):\n"
                        "                continue\n"
                        "            assert name not in expected, name\n"
                        "            expected.add(name)\n"
                        "            declared = getattr(leaf, name)\n"
                        "            assert declared.__module__ =="
                        " leaf.__name__, name\n"
                        "            assert getattr(package, name) is"
                        " declared, (package_name, info.name, name)\n"
                        "            assert declared in core.t.__mro__, name\n"
                        "            for alias in vars(declared).values():\n"
                        "                if isinstance(alias, TypeAliasType):\n"
                        "                    alias.__value__\n"
                        "    assert expected, package_name\n"
                        "    published = {name for name in package.__all__"
                        " if isinstance(getattr(package, name), type)}\n"
                        "    assert published == expected, package_name\n"
                        "    print('declared typing classes:', len(expected))\n"
                        "print('declared bootstrap exports resolved')\n"
                    ),
                    c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE,
                    c.Infra.LAZY_BOOTSTRAP_MODULE,
                    (
                        f"{c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE}."
                        f"{u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY).directory}"
                    ),
                    *c.Infra.LAZY_BOOTSTRAP_HELPERS,
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout, has="declared bootstrap exports resolved")

    @staticmethod
    @pytest.mark.parametrize("class_name", ["PublishedOwner", "DifferentDeclaredType"])
    @pytest.mark.parametrize(
        "module_name",
        [
            "owner",
            "_private_owner",
            "test_owner",
            "__main__",
            "conftest",
            "__version__",
        ],
    )
    def test_declared_module_exports_survive_filename_classification(
        tmp_path: Path,
        module_name: str,
        class_name: str,
    ) -> None:
        """Import declared classes lazily regardless of their source filename."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        (package_root / f"{module_name}{c.Infra.EXT_PYTHON}").write_text(
            '"""Explicit module contract."""\n\n'
            "from __future__ import annotations\n\n"
            f"class {class_name}:\n"
            '    """Declared class."""\n\n'
            "class UndeclaredOwner:\n"
            '    """Class outside the declared contract."""\n\n'
            "__hidden_metadata__ = 'unpublished'\n\n"
            f"__all__ = ({class_name!r},)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        projection = package_root / c.Infra.INIT_PY
        fixed_point = projection.read_bytes()
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(projection.read_bytes(), eq=fixed_point)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "import importlib, sys\n"
                        "package = importlib.import_module(sys.argv[1])\n"
                        "module_name = package.__name__ + '.' + sys.argv[2]\n"
                        "assert module_name not in sys.modules\n"
                        "published = getattr(package, sys.argv[3])\n"
                        "leaf = importlib.import_module(module_name)\n"
                        "assert published is getattr(leaf, sys.argv[3])\n"
                        "assert set(package.__all__) == set(leaf.__all__)\n"
                        "assert not hasattr(package, 'UndeclaredOwner')\n"
                        "assert not hasattr(package, '__hidden_metadata__')\n"
                        "print('declared lazy consumer resolved')\n"
                    ),
                    package_root.name,
                    module_name,
                    class_name,
                ),
                cwd=repository_root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package_root.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout, has="declared lazy consumer resolved")
