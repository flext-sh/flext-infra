"""Public evidence for own components composing in the package namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tests import c, p, tm, u
from tests.unit.codegen._utility_facade_projection.publication import (
    UtilityFacadePublication,
)


class UtilityFacadeNamespace(UtilityFacadePublication):
    """ADR-028 Decision 10: own parts compose in one nested namespace class."""

    _STEM = "FlextTestProject"

    @classmethod
    def _owner(cls) -> str:
        """Name the fixture's public utility facade owner.

        Returns:
            The package stem followed by the utility family suffix.

        """
        return f"{cls._STEM}{u.Infra.facade_families()['u'].suffix}"

    @classmethod
    def _namespace_package(
        cls,
        package: Path,
        parts: Mapping[str, str],
        header: tuple[str, str],
    ) -> Path:
        """Write an upstream facade, the own parts and the public utility facade.

        Returns:
            The public utility facade path.

        """
        directory = u.Infra.facade_families()["u"].directory
        upstream = package.with_name(f"{package.name}_upstream")
        owner = cls._owner()
        bases, body = header
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            upstream / c.Infra.INIT_PY: (
                f"from {upstream.name}.utilities import ParentUtilities\n"
                "__all__ = ['ParentUtilities']\n"
            ),
            upstream / c.Infra.UTILITIES_PY: (
                "class ParentUtilities:\n"
                "    @staticmethod\n"
                "    def upstream_value():\n"
                "        return 'upstream-value'\n"
                "__all__ = ['ParentUtilities']\n"
            ),
            package / c.Infra.INIT_PY: (
                f"from {package.name}.utilities import {owner}, u\n"
                f"__all__ = ['{owner}', 'u']\n"
            ),
            package / directory / c.Infra.INIT_PY: "".join(
                f"from {package.name}.{directory}.{name.lower()} import {name}\n"
                for name in parts
            )
            + f"__all__ = {sorted(parts)!r}\n",
            facade: (
                f"from {upstream.name} import ParentUtilities\n"
                f"from {package.name}.{directory} import {', '.join(parts)}\n"
                f"class {owner}({bases}):\n{body}"
                f"u = {owner}\n__all__ = ['{owner}', 'u']\n"
            ),
        }
        sources.update({
            package / directory / f"{name.lower()}.py": (
                f"{source}__all__ = ['{name}']\n"
            )
            for name, source in parts.items()
        })
        for path, source in sources.items():
            cls._write(path, source)
        return facade

    @classmethod
    def _converged_render(cls, root: Path, package: Path, facade: Path) -> str:
        """Render the facade, publish it and prove a second render is identical.

        Returns:
            The published facade source.

        """
        rendered = tm.ok(tm.not_none(u.Infra.render_utility_facade(package)))
        cls._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.ok(tm.not_none(u.Infra.render_utility_facade(package)), eq=rendered)
        return rendered

    @staticmethod
    def _own_part() -> str:
        """Declare one own utility part.

        Returns:
            The part module source without its export list.

        """
        return (
            "class OwnPart:\n"
            "    @staticmethod\n"
            "    def own_value():\n"
            "        return 'own-value'\n"
        )

    def test_flat_root_composes_own_parts_in_created_namespace(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Own root parts move into the package namespace; the upstream stays."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        namespace = u.Infra.facade_namespace(self._STEM)
        facade = self._namespace_package(
            package,
            {"OwnPart": self._own_part()},
            ("ParentUtilities, OwnPart", "    pass\n"),
        )
        rendered = self._converged_render(root, package, facade)
        tm.that(rendered, has=f"class {self._owner()}(ParentUtilities):")
        tm.that(rendered, has=f"class {namespace}(OwnPart):")
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            f"from {package.name}._utilities import OwnPart\n"
            f"assert u.{namespace}.own_value() == 'own-value'\n"
            "assert u.upstream_value() == 'upstream-value'\n"
            "assert OwnPart not in u.__mro__\n"
            f"assert OwnPart in u.{namespace}.__mro__\n",
            cwd=root,
        )

    def test_root_duplicate_of_a_namespace_part_is_dropped(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """A part both the root and the namespace compose leaves the root."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        namespace = u.Infra.facade_namespace(self._STEM)
        facade = self._namespace_package(
            package,
            {"OwnPart": self._own_part()},
            (
                "ParentUtilities, OwnPart",
                f"    class {namespace}(OwnPart):\n        pass\n",
            ),
        )
        rendered = self._converged_render(root, package, facade)
        tm.that(rendered, has=f"class {self._owner()}(ParentUtilities):")
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            f"from {package.name}._utilities import OwnPart\n"
            "assert OwnPart not in u.__mro__\n"
            f"assert u.{namespace}.own_value() == 'own-value'\n",
            cwd=root,
        )

    def test_part_declaring_a_real_namespace_named_class_composes_whole(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """A part's real class named like the namespace reads through it."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        namespace = u.Infra.facade_namespace(self._STEM)
        facade = self._namespace_package(
            package,
            {
                "RealPart": (
                    "class RealPart:\n"
                    f"    class {namespace}(dict):\n"
                    "        pass\n"
                    "    @staticmethod\n"
                    "    def real_value():\n"
                    "        return 'real-value'\n"
                ),
            },
            ("ParentUtilities, RealPart", "    pass\n"),
        )
        rendered = self._converged_render(root, package, facade)
        tm.that(rendered, has=f"class {namespace}(RealPart):")
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            f"from {package.name}._utilities import RealPart\n"
            f"assert u.{namespace}.{namespace} is RealPart.{namespace}\n"
            f"assert u.{namespace}.real_value() == 'real-value'\n"
            "assert RealPart not in u.__mro__\n",
            cwd=root,
        )

    def test_namespace_holder_part_composes_through_its_namespace_class(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """A part holding only ``class <Namespace>:`` composes as its member."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        namespace = u.Infra.facade_namespace(self._STEM)
        facade = self._namespace_package(
            package,
            {
                "HolderPart": (
                    "class HolderPart:\n"
                    f"    class {namespace}:\n"
                    "        @staticmethod\n"
                    "        def held_value():\n"
                    "            return 'held-value'\n"
                ),
                "OwnPart": self._own_part(),
            },
            ("ParentUtilities, HolderPart, OwnPart", "    pass\n"),
        )
        rendered = self._converged_render(root, package, facade)
        tm.that(rendered, has=f"HolderPart.{namespace}")
        tm.that(rendered, has=f"class {self._owner()}(ParentUtilities):")
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            f"from {package.name}._utilities import HolderPart\n"
            f"assert u.{namespace}.held_value() == 'held-value'\n"
            f"assert u.{namespace}.own_value() == 'own-value'\n"
            "assert HolderPart not in u.__mro__\n"
            f"assert not hasattr(u.{namespace}, '{namespace}')\n",
            cwd=root,
        )

    def test_namespace_name_bound_to_a_non_class_fails_loud(
        self,
        tmp_path: Path,
    ) -> None:
        """The owner binding the namespace name otherwise stops the render."""
        _root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        namespace = u.Infra.facade_namespace(self._STEM)
        facade = self._namespace_package(
            package,
            {"OwnPart": self._own_part()},
            ("ParentUtilities, OwnPart", f"    {namespace} = 'bound'\n"),
        )
        before = facade.read_bytes()
        message = tm.fail(tm.not_none(u.Infra.render_utility_facade(package)))
        tm.that(message, has=f"binds its namespace name {namespace!r}")
        tm.that(facade.read_bytes(), eq=before)

    def test_test_surface_flat_facade_is_untouched(
        self,
        tmp_path: Path,
    ) -> None:
        """A tests-tier facade keeps its flat composition."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        namespace = u.Infra.facade_namespace(self._STEM)
        self._namespace_package(
            package,
            {"OwnPart": self._own_part()},
            ("ParentUtilities, OwnPart", "    pass\n"),
        )
        surface = root / "tests"
        directory = u.Infra.facade_families()["u"].directory
        owner = f"Tests{self._owner().removeprefix('Flext')}"
        sources = {
            surface / c.Infra.INIT_PY: "",
            surface / directory / c.Infra.INIT_PY: (
                f"from tests.{directory}.part import TestsPart\n"
                "__all__ = ['TestsPart']\n"
            ),
            surface / directory / "part.py": (
                "class TestsPart:\n"
                "    @staticmethod\n"
                "    def tests_value():\n"
                "        return 'tests-value'\n"
                "__all__ = ['TestsPart']\n"
            ),
            surface / c.Infra.UTILITIES_PY: (
                f"from {package.name}_upstream import ParentUtilities\n"
                f"from tests.{directory} import TestsPart\n"
                f"class {owner}(ParentUtilities, TestsPart):\n    pass\n"
                f"u = {owner}\n__all__ = ['{owner}', 'u']\n"
            ),
        }
        for path, source in sources.items():
            self._write(path, source)
        rendered = tm.ok(tm.not_none(u.Infra.render_utility_facade(surface)))
        tm.that(rendered, has="TestsPart")
        tm.that(rendered, lacks=f"class {namespace}(")
