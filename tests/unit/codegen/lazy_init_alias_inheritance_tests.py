"""Facade-parent alias inheritance sources only from the indexed workspace."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flext_tests import tm

from tests import c, u


class TestsFlextInfraLazyInitAliasInheritance:
    """A parent's exported letters come only from the indexed workspace scan.

    Regression coverage for flext-b3xmn: root/member lazy-init renders used to
    union in ``u.Infra.installed_package_exports`` (ambient ``importlib``
    introspection of whatever happens to be installed) whenever a declared
    facade parent was not indexed by the current Rope workspace scan. That
    made generated ``__init__.py`` content diverge between a local editable
    venv and a pinned CI checkout. The fix removes the ambient union/fallback
    and fails loud instead.
    """

    def test_generated_parent_retains_operational_result_alias_in_child(
        self, tmp_path: Path
    ) -> None:
        """A generated parent cannot erase a declared result needed at bootstrap."""
        repository, child = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-bootstrap-result",
            package_name="flext_bootstrap_child",
        )
        parent = repository / c.Infra.DEFAULT_SRC_DIR / "flext_bootstrap_parent"
        parent.mkdir()
        (parent / c.Infra.INIT_PY).write_text(
            c.Infra.AUTOGEN_HEADERS[0] + "\n__all__ = []\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        u.Tests.write_lazy_init_namespace_module(
            parent / "constants.py", class_name="BootstrapParentConstants", alias="c"
        )
        parent_constants = parent / c.Infra.CONSTANTS_PY
        parent_constants.write_text(
            parent_constants.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            + "\nimport re\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (parent / "result.py").write_text(
            "from flext_core import FlextResult\nr = FlextResult\n"
            "__all__ = ['FlextResult', 'r']\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child / "constants.py").write_text(
            "from flext_bootstrap_parent import c as parent_c\n"
            "class BootstrapChildConstants(parent_c):\n    pass\n"
            "c = BootstrapChildConstants\n__all__ = ['BootstrapChildConstants', 'c']\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child / "consumer.py").write_text(
            "from flext_bootstrap_child import r\n"
            "def execute():\n    return r.ok('bootstrap-ready')\n"
            "__all__ = ['execute']\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        first = (child / c.Infra.INIT_PY).read_bytes()
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that((child / c.Infra.INIT_PY).read_bytes(), eq=first)
        probe_env = dict(os.environ)
        probe_env["PYTHONPATH"] = os.pathsep.join([
            str(repository / c.Infra.DEFAULT_SRC_DIR),
            *sys.path,
        ])
        probe = (
            "from flext_bootstrap_child.consumer import execute\n"
            "import flext_bootstrap_child as generated\n"
            "from flext_core import r\n"
            "print(generated.r is r)\n"
            "print('r' in generated.__all__)\n"
            "print('compile' in generated.__all__)\n"
            "print(execute().value)\n"
        )
        result = tm.ok(
            u.Cli.run([sys.executable, "-c", probe], env=probe_env, cwd=repository)
        )
        tm.that(
            result.stdout.splitlines(), eq=["True", "True", "False", "bootstrap-ready"]
        )

    def test_child_inherits_exactly_the_indexed_parent_letters(
        self, tmp_path: Path
    ) -> None:
        """An indexed parent's exact alias set is what the child inherits."""
        repository_root, child_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-inherit",
            package_name="flext_test_inherit_child",
        )
        parent_root = (
            repository_root / c.Infra.DEFAULT_SRC_DIR / "flext_test_inherit_parent"
        )
        parent_root.mkdir(parents=True)
        parent_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Infra.ENCODING_DEFAULT
        )
        u.Tests.write_lazy_init_namespace_module(
            parent_root / "constants_ns.py",
            class_name="FlextTestInheritParentConstantsNs",
            alias="c",
        )
        u.Tests.write_lazy_init_namespace_module(
            parent_root / "models_ns.py",
            class_name="FlextTestInheritParentModelsNs",
            alias="m",
        )
        u.Tests.write_lazy_init_namespace_module(
            parent_root / "protocols_ns.py",
            class_name="FlextTestInheritParentProtocolsNs",
            alias="p",
        )
        child_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_test_inherit_parent import c\n\n"
            "class FlextTestInheritChildConstants(c):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextTestInheritChildConstants"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = child_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        tm.that(
            generated.splitlines(),
            has="    from flext_test_inherit_parent import c, m, p",
        )
        tm.that(generated, lacks="from flext_test_inherit_parent import c, m, p, ")

    def test_declared_parent_resolving_nowhere_fails_loud(self, tmp_path: Path) -> None:
        """A declared parent that resolves nowhere in the environment is a typed failure."""
        repository_root, child_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-ghost",
            package_name="flext_test_ghost_child",
        )
        child_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_ghost_parent_zzz import c\n\n"
            "class FlextTestGhostChildConstants(c):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextTestGhostChildConstants"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        planned = u.Tests.plan_lazy_init(repository_root)

        tm.that(planned.failure, eq=True)
        tm.that(
            planned.error,
            contains=(
                "lazy-init: declared facade parent 'flext_ghost_parent_zzz'"
                " resolves nowhere in the active environment"
            ),
        )


__all__: list[str] = ["TestsFlextInfraLazyInitAliasInheritance"]
