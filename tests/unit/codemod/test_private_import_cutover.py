"""Public utility evidence for semantic private-import cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path

from tests import c, tm, u
from tests.unit.codemod.private_import_cutover_support import (
    TestsFlextInfraFacadeNaming,
    TestsFlextInfraPrivateImportCutoverSupport,
)


@c.Tests.MARK.usefixtures("semantic_cutover_runtime")
class TestsFlextInfraPrivateImportCutover(
    TestsFlextInfraPrivateImportCutoverSupport,
):
    """Exercise installed and declared re-export cutovers only through ``u.Infra``."""

    def test_earlier_semantic_move_retires_stale_preflight_import(
        self,
        tmp_path: Path,
    ) -> None:
        """Test earlier semantic move retires stale preflight import."""
        consumer, statement, _ = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "constants",
                "profile",
                "Profile",
                "c",
            ),
        )
        sources = {consumer: "from flext_sample import c\nvalue = c.Profile.Value\n"}
        tm.that(self._edits(tmp_path, sources, consumer, statement), empty=True)

    @staticmethod
    def _seed_sample_dependency(
        package: Path,
        facade_sources: Mapping[Path, str],
        *,
        depth: int,
    ) -> MutableMapping[Path, str]:
        """Materialize the installed sample dependency package.

        Deep cases bridge the private facade through real subclasses and
        rewire every facade reference to the outermost bridge class.

        Returns:
            Every seeded dependency path and its written source.

        """
        dependency_sources = {
            package / path.name: source for path, source in facade_sources.items()
        }
        dependency_sources[package / "__init__.py"] = (
            "raise RuntimeError('discovery must not execute dependency code')\n"
        )
        dependency_sources[package / "_constants/profile.py"] = (
            "class FlextSampleConstantsProfile:\n    Value = str\n"
        )
        previous_module = "flext_sample._constants.profile"
        previous_class = "FlextSampleConstantsProfile"
        for level in range(depth):
            module_name = f"bridge_{level}"
            class_name = f"FlextSampleConstantsBridge{level}"
            previous_leaf = previous_module.rsplit(".", maxsplit=1)[-1]
            dependency_sources[package / f"_constants/{module_name}.py"] = (
                f"from .{previous_leaf} import {previous_class}\n"
                f"class {class_name}({previous_class}):\n    pass\n"
            )
            previous_module = f"flext_sample._constants.{module_name}"
            previous_class = class_name
        if depth:
            for path in tuple(dependency_sources):
                if path.parent == package and path.name != "__init__.py":
                    dependency_sources[path] = (
                        dependency_sources[path]
                        .replace("flext_sample._constants.profile", previous_module)
                        .replace("FlextSampleConstantsProfile", previous_class)
                    )
        for path, source in dependency_sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        return dependency_sources

    @c.Tests.MARK.parametrize("depth", [0, 2])
    def test_installed_facades_are_never_discovery_inputs(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        depth: int,
    ) -> None:
        """Installed facades are never discovery inputs (per-repository law).

        Whatever facade shape an installed distribution declares, the cutover
        resolves only the repository's own sources and leaves the installed
        files untouched.
        """
        consumer, statement, facade_sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "constants",
                "profile",
                "Profile",
                "c",
            ),
        )
        package = installed_dependency_path / "flext_sample"
        package.mkdir()
        dependency_sources = self._seed_sample_dependency(
            package,
            facade_sources,
            depth=depth,
        )
        sources = {
            consumer: f"{statement}\nprofile = FlextSampleConstantsProfile.Value\n",
        }
        with u.Tests.raises(ValueError, match="no public facade exposes"):
            self._plan(tmp_path, sources, consumer, statement)
        for path, source in dependency_sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(tuple(sources), eq=(consumer,))

    @c.Tests.MARK.parametrize(
        ("declaration", "expected"),
        [
            (
                (
                    "class Facade:\n"
                    "    class Base:\n        pass\n"
                    "    class Leaf(Base):\n        pass\n"
                ),
                "",
            ),
            (
                (
                    "class Facade:\n"
                    "    class Base:\n        pass\n"
                    "    class Branch(Base):\n"
                    "        class Leaf(Base):\n            pass\n"
                ),
                "c.Branch.Leaf",
            ),
            (
                (
                    "class Facade:\n"
                    "    class Branch:\n"
                    "        class Base:\n            pass\n"
                    "        class Leaf(Base):\n            pass\n"
                ),
                "",
            ),
            (
                "class Facade:\n    class Leaf(private.Target):\n        pass\n",
                "c.Leaf",
            ),
            (
                (
                    "class Facade:\n"
                    "    class private:\n"
                    "        class Target:\n            pass\n"
                    "    class Leaf(private.Target):\n        pass\n"
                ),
                "",
            ),
            (
                (
                    "class Facade:\n"
                    "    class Left(Base):\n        pass\n"
                    "    class Right(Base):\n        pass\n"
                ),
                "ambiguous",
            ),
        ],
        ids=[
            "sibling-shadow",
            "grandchild-module-binding",
            "grandchild-local-shadow",
            "qualified-module-base",
            "qualified-local-shadow",
            "ambiguous-siblings",
        ],
    )
    def test_facade_bases_follow_declaration_scope(
        self,
        tmp_path: Path,
        declaration: str,
        expected: str,
    ) -> None:
        """Facade bases resolve a private target through lexical declaration scope."""
        package = tmp_path / "lexical-sample/src/lexical_sample"
        dependency_sources = {
            package / "__init__.py": (
                "raise RuntimeError('discovery must not execute dependency code')\n"
            ),
            package / "_private.py": "class Target:\n    Value = str\n",
            package / "constants.py": (
                "from lexical_sample._private import Target as Base\n"
                "import lexical_sample._private as private\n"
                f"{declaration}\nc = Facade\n"
            ),
        }
        consumer = tmp_path / "consumer/src/consumer/service.py"
        statement = "from lexical_sample._private import Target"
        sources = {
            **dependency_sources,
            consumer: f"{statement}\nvalue = Target.Value\n",
        }

        if expected.startswith("c."):
            edits = self._edits(tmp_path, sources, consumer, statement)
            tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
            tm.that(edits[0].updated_source, has="from lexical_sample import c")
            tm.that(edits[0].updated_source, has=f"value = {expected}.Value")
            tm.that(edits[0].updated_source, lacks=statement)
        else:
            with u.Tests.raises(
                ValueError,
                match=expected or "no public facade exposes",
            ):
                self._plan(tmp_path, sources, consumer, statement)

    @staticmethod
    def _declared_export_case(
        root: Path,
        *,
        package_import: bool = False,
        root_export: bool = False,
        renamed: bool = False,
    ) -> tuple[Path, str, MutableMapping[Path, str]]:
        package = root / "sample/src/sample"
        public_name = "PublicClient" if renamed else "Client"
        sources = {
            package / "_private/client.py": "class Client:\n    pass\n",
            package / "_private/__init__.py": (
                "from typing import TYPE_CHECKING\n"
                "from flext_core.lazy import "
                "build_lazy_import_map, install_lazy_exports\n"
                "if TYPE_CHECKING:\n    from .client import Client\n"
                "__all__ = ('Client',)\n"
                "_LAZY_IMPORTS = build_lazy_import_map({'.client': ('Client',)})\n"
                "install_lazy_exports("
                "__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)\n"
            ),
            package / "api.py": (
                f"from ._private.client import Client as {public_name}\n"
                f"__all__ = ('{public_name}',)\n"
            ),
        }
        if root_export:
            sources[package / "__init__.py"] = (
                f"from .api import {public_name}\n__all__ = ('{public_name}',)\n"
            )
        module = "sample._private" if package_import else "sample._private.client"
        statement = f"from {module} import Client as BoundClient"
        consumer = root / "consumer/src/consumer/service.py"
        sources[consumer] = (
            f"{statement}\ninstance = BoundClient()\n"
            "def local(BoundClient: str) -> str:\n    return BoundClient\n"
        )
        return consumer, statement, sources

    @c.Tests.MARK.parametrize("package_import", [False, True])
    @c.Tests.MARK.parametrize("root_export", [False, True])
    @c.Tests.MARK.parametrize("renamed", [False, True])
    def test_declared_reexports_preserve_identity_binding_and_shadowing(
        self,
        tmp_path: Path,
        *,
        package_import: bool,
        root_export: bool,
        renamed: bool,
    ) -> None:
        """Test declared reexports preserve identity binding and shadowing."""
        consumer, statement, sources = self._declared_export_case(
            tmp_path,
            package_import=package_import,
            root_export=root_export,
            renamed=renamed,
        )

        updated = self._updated_source(tmp_path, sources, consumer, statement)

        module = "sample" if root_export else "sample.api"
        public_name = "PublicClient" if renamed else "Client"
        tm.that(updated, has=f"from {module} import {public_name} as BoundClient")
        tm.that(updated, has="instance = BoundClient()")
        tm.that(
            updated,
            has="def local(BoundClient: str) -> str:\n    return BoundClient",
        )
        tm.that(updated, lacks=statement)

    def test_declared_reexport_rename_keeps_an_unaliased_consumer_binding(
        self,
        tmp_path: Path,
    ) -> None:
        """Test declared reexport rename keeps an unaliased consumer binding."""
        consumer, statement, sources = self._declared_export_case(
            tmp_path,
            renamed=True,
        )
        unaliased = statement.replace(" as BoundClient", "")
        sources[consumer] = f"{unaliased}\ninstance = Client()\n"

        updated = self._updated_source(tmp_path, sources, consumer, unaliased)

        tm.that(updated, has="from sample.api import PublicClient as Client")
        tm.that(updated, has="instance = Client()")

    def test_declared_reexport_retains_type_checking_boundary(
        self,
        tmp_path: Path,
    ) -> None:
        """Test declared reexport retains type checking boundary."""
        consumer, statement, sources = self._declared_export_case(tmp_path)
        sources[consumer] = (
            "from __future__ import annotations\nfrom typing import TYPE_CHECKING\n"
            f"if TYPE_CHECKING:\n    {statement}\nvalue: BoundClient\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer, statement)

        tm.that(
            updated,
            has="if TYPE_CHECKING:\n    from sample.api import Client as BoundClient",
        )
        tm.that(updated, has="value: BoundClient")

    def test_unrelated_export_cycle_does_not_block_a_proven_public_import(
        self,
        tmp_path: Path,
    ) -> None:
        """Test unrelated export cycle does not block a proven public import."""
        consumer, statement, sources = self._declared_export_case(tmp_path)
        package = tmp_path / "sample/src/sample"
        sources[package / "left.py"] = "from .right import Loop\n__all__ = ('Loop',)\n"
        sources[package / "right.py"] = "from .left import Loop\n__all__ = ('Loop',)\n"

        updated = self._updated_source(tmp_path, sources, consumer, statement)

        tm.that(updated, has="from sample.api import Client as BoundClient")

    @c.Tests.MARK.parametrize("case", ["unexposed", "homonym", "ambiguous", "shadowed"])
    def test_declared_export_resolution_rejects_unproven_or_ambiguous_targets(
        self,
        tmp_path: Path,
        case: str,
    ) -> None:
        """Test declared export resolution rejects unproven or ambiguous targets."""
        consumer, statement, sources = self._declared_export_case(tmp_path)
        package = tmp_path / "sample/src/sample"
        if case == "unexposed":
            sources[package / "api.py"] = "from ._private.client import Client\n"
        elif case == "homonym":
            sources[package / "api.py"] = (
                "class Client:\n    pass\n__all__ = ('Client',)\n"
            )
        elif case == "ambiguous":
            sources[package / "other.py"] = sources[package / "api.py"]
        else:
            sources[package / "api.py"] += "Client = object\n"
        # A shadowed re-export is rebound at runtime (``Client = object``), so
        # the facade does not expose the private class at all.
        expected = (
            "no public facade exposes"
            if case in {"unexposed", "homonym", "shadowed"}
            else "ambiguous"
        )

        with u.Tests.raises(ValueError, match=expected):
            self._plan(tmp_path, sources, consumer, statement)
