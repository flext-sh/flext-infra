"""Behaviour tests for the generated test namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraLazyInitTestNamespace:
    """The tests facade publishes sibling public APIs, never test modules."""

    @staticmethod
    def test_tests_root_publishes_src_scripts_and_examples_publics(
        tmp_path: Path,
    ) -> None:
        """The tests facade exposes sibling public APIs and omits test modules."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoPublic",
            alias="demo_public",
        )
        scripts_root = repository_root / c.Infra.DIR_SCRIPTS
        scripts_root.mkdir()
        scripts_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.DEFAULT_ENCODING
        )
        u.Tests.write_lazy_init_namespace_module(
            scripts_root / "constants.py",
            class_name="ScriptsPublic",
            alias="scripts_public",
        )
        examples_root = repository_root / c.Infra.DIR_EXAMPLES
        examples_root.mkdir()
        examples_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.DEFAULT_ENCODING
        )
        u.Tests.write_lazy_init_namespace_module(
            examples_root / "constants.py",
            class_name="ExamplesPublic",
            alias="examples_public",
        )
        tests_root = repository_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        tests_root.joinpath("test_namespace_leak.py").write_text(
            "from __future__ import annotations\n\n"
            "class TestsNamespaceLeak:\n"
            "    pass\n\n"
            '__all__: list[str] = ["TestsNamespaceLeak"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        init_content = u.Tests.generated_init(tests_root)

        tm.that(init_content, has='"FlextDemoPublic"')
        tm.that(init_content, has='"ScriptsPublic"')
        tm.that(init_content, has='"ExamplesPublic"')
        tm.that(init_content, lacks='"TestsNamespaceLeak"')
        compile(init_content, "tests/__init__.py", "exec")

    @staticmethod
    def test_tests_root_reads_the_planned_root_exports_in_one_run(
        tmp_path: Path,
    ) -> None:
        """A stale root initializer never reaches the tests facade.

        Premise: a class moved out of the package, so the previous generated
        root initializer still publishes it. One run must plan the tests
        facade from the root exports planned in the same run, and a second
        run must be a no-op.
        """
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoPublic",
            alias="demo_public",
        )
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '"""Previous root projection."""\n\n'
            "from __future__ import annotations\n\n"
            "from flext_core.lazy import install_lazy_exports\n\n"
            '__all__: tuple[str, ...] = ("FlextDemoMoved", "FlextDemoPublic")\n\n'
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            '    {"FlextDemoMoved": ".moved", "FlextDemoPublic": ".models"},\n'
            "    public_exports=__all__,\n"
            ")\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tests_root = repository_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        first = u.Tests.generated_init(tests_root)
        tm.that(first, has='"FlextDemoPublic"')
        tm.that(first, lacks='"FlextDemoMoved"')
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(u.Tests.generated_init(tests_root), eq=first)


__all__: list[str] = ["TestsFlextInfraLazyInitTestNamespace"]
