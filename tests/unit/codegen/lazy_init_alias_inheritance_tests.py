"""Facade-parent alias inheritance sources only from the indexed workspace."""

from __future__ import annotations

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
