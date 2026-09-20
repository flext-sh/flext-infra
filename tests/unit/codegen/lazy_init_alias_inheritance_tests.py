"""Generated initializers expose only symbols declared in their directory."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c, u


class TestsFlextInfraLazyInitAliasInheritance:
    """Parent imports never become child initializer exports."""

    def test_child_does_not_reexport_parent_letters(self, tmp_path: Path) -> None:
        """The child initializer exposes declarations from its own directory only."""
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

        tm.that(generated, lacks="from flext_test_inherit_parent import")
        tm.that(generated, lacks='"c",')
        tm.that(generated, has='"FlextTestInheritChildConstants",')

    def test_unknown_parent_is_not_an_initializer_export(self, tmp_path: Path) -> None:
        """A child does not make an unknown parent's aliases public."""
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

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = child_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        tm.that(generated, lacks="flext_ghost_parent_zzz")
        tm.that(generated, lacks='"c",')


__all__: list[str] = ["TestsFlextInfraLazyInitAliasInheritance"]
