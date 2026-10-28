"""Public utility evidence for semantic private-import cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from collections.abc import MutableMapping
from pathlib import Path

import pytest

from flext_infra import u
from tests import tm
from tests.unit.codemod.private_import_cutover_support import (
    TestsFlextInfraFacadeNaming,
    TestsFlextInfraPrivateImportCutoverSupport,
)


class TestsFlextInfraPrivateImportCutover(
    TestsFlextInfraPrivateImportCutoverSupport,
):
    """Exercise installed and declared re-export cutovers only through ``u.Infra``."""

    @staticmethod
    @pytest.mark.parametrize(
        ("example_path", "consumer"),
        [
            (
                "flext-grpc/examples/advanced_usage.py",
                (
                    "from flext_grpc import FlextGrpcModels, c, p, t\n"
                    "from examples import ExamplesFlextGrpcTypes\n"
                    "from examples import (c as example_c, p as example_p, "
                    "t as example_t)\n"
                    "example = namespace['ExamplesFlextGrpcAdvancedUsage']()\n"
                    "assert example.c is example_c is namespace['c']\n"
                    "assert example.p is example_p is namespace['p']\n"
                    "assert example.t is example_t is namespace['t']\n"
                    "assert issubclass(example_c, c)\n"
                    "assert issubclass(example_p, p)\n"
                    "assert issubclass(example_t, t)\n"
                    "assert example_c is c\n"
                    "assert example_p is p\n"
                    "assert example_t is ExamplesFlextGrpcTypes\n"
                    "assert t.Grpc.CompleteSetup.__value__ "
                    "is FlextGrpcModels.Grpc.CompleteSetup\n"
                ),
            ),
            (
                "flext-oracle-wms/examples/example_02_configuration.py",
                (
                    "from flext_oracle_wms import c\n"
                    "configurations = namespace['get_environment_configs']()\n"
                    "assert configurations\n"
                    "assert all(configuration.timeout == c.OracleWms.DEFAULT_TIMEOUT\n"
                    "           for configuration in configurations.values())\n"
                    "settings = namespace['create_demo_config']()\n"
                    "assert settings.OracleWms.timeout == c.OracleWms.DEFAULT_TIMEOUT\n"
                ),
            ),
        ],
    )
    def test_workspace_examples_preserve_public_facade_runtime(
        example_path: str,
        consumer: str,
    ) -> None:
        """Exercise actual facade accessors and offline configuration consumers."""
        root = Path(__file__).resolve().parents[4]
        executed = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-c",
                    "import sys\nfrom runpy import run_path\n"
                    "namespace = run_path(sys.argv[1])\n" + consumer,
                    str(root / example_path),
                ],
                cwd=(root / example_path).parents[1],
            ),
        )
        tm.that(u.Cli.process_succeeded(executed.outcome), eq=True, msg=executed.stderr)
        tm.that(executed.stderr, eq="")

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

    @pytest.mark.parametrize("bad_source_reachable", [False, True])
    def test_installed_import_validation_follows_public_reachability(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        *,
        bad_source_reachable: bool,
    ) -> None:
        """An invalid import blocks only a cutover that reaches its module."""
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
        (package / "__init__.py").write_text("", encoding="utf-8")
        invalid_import = "from ..outside import Invalid\n"
        facade_source = next(iter(facade_sources.values()))
        (package / "constants.py").write_text(
            facade_source + (invalid_import if bad_source_reachable else ""),
            encoding="utf-8",
        )
        private = package / "_constants/profile.py"
        private.parent.mkdir()
        private.write_text(
            "class FlextSampleConstantsProfile:\n    Value = str\n",
            encoding="utf-8",
        )
        unrelated = package / "unrelated.py"
        unrelated.write_text(invalid_import, encoding="utf-8")
        sources = {
            consumer: f"{statement}\nprofile = FlextSampleConstantsProfile.Value\n",
        }

        if bad_source_reachable:
            # flext-core's result factory catches broad runtime errors only
            # ("no IO, no import"): an invalid reachable import escapes raw.
            with pytest.raises(
                ImportError,
                match="attempted relative import beyond top-level",
            ):
                self._plan(tmp_path, sources, consumer, statement)
            return
        edits = self._edits(tmp_path, sources, consumer, statement)

        tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
        tm.that(edits[0].updated_source, has="from flext_sample import c")
        tm.that(edits[0].updated_source, has="profile = c.Profile.Value")
        tm.that(unrelated.read_text(encoding="utf-8"), eq=invalid_import)

    def _seed_sample_dependency(
        self,
        package: Path,
        facade_sources: Mapping[Path, str],
        *,
        case: str,
        depth: int,
    ) -> MutableMapping[Path, str]:
        """Materialize the installed sample dependency package for one case.

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
        if case == "ambiguous":
            dependency_sources[package / "other.py"] = self._facade_source(
                naming=TestsFlextInfraFacadeNaming(
                    private_module="flext_sample._constants.profile",
                    private_class="FlextSampleConstantsProfile",
                    root_class="OtherConstants",
                    nested_class="Other",
                    alias="c",
                ),
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

    @pytest.mark.parametrize("case", ["unique", "ambiguous", "shadowed"])
    @pytest.mark.parametrize("depth", [0, 2])
    def test_installed_facades_are_read_only_discovery_inputs(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        case: str,
        depth: int,
    ) -> None:
        """Test installed facades are read only discovery inputs."""
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
            case=case,
            depth=depth,
        )
        sources = {
            consumer: f"{statement}\nprofile = FlextSampleConstantsProfile.Value\n",
        }
        if case == "shadowed":
            sources[consumer] += "c = 1\n"
        if case == "unique":
            edits = self._edits(tmp_path, sources, consumer, statement)
            tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
            tm.that(edits[0].updated_source, has="from flext_sample import c")
            tm.that(edits[0].updated_source, has="profile = c.Profile.Value")
        elif case == "shadowed":
            with pytest.raises(ValueError, match="public facade alias c is shadowed"):
                self._plan(tmp_path, sources, consumer, statement)
        else:
            with pytest.raises(ValueError, match=case):
                self._plan(tmp_path, sources, consumer, statement)
        for path, source in dependency_sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(tuple(sources), eq=(consumer,))

    @pytest.mark.parametrize("root_export", [False, True])
    def test_installed_declared_reexports_preserve_binding(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        *,
        root_export: bool,
    ) -> None:
        """Test installed declared reexports preserve binding."""
        consumer, statement, sources = self._declared_export_case(
            tmp_path,
            package_import=True,
            root_export=root_export,
            renamed=True,
        )
        consumer_sources = {consumer: sources.pop(consumer)}
        dependency_sources = {
            installed_dependency_path
            / path.relative_to(tmp_path / "sample/src"): source
            for path, source in sources.items()
        }
        package_init = installed_dependency_path / "sample/__init__.py"
        dependency_sources[package_init] = dependency_sources.get(package_init, "") + (
            "raise RuntimeError('discovery must not execute dependency code')\n"
        )
        for path, source in dependency_sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

        edits = self._edits(tmp_path, consumer_sources, consumer, statement)

        module = "sample" if root_export else "sample.api"
        tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
        tm.that(
            edits[0].updated_source,
            has=f"from {module} import PublicClient as BoundClient",
        )
        tm.that(edits[0].updated_source, has="instance = BoundClient()")
        for path, source in dependency_sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.parametrize(
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
    def test_installed_facade_bases_follow_declaration_scope(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        declaration: str,
        expected: str,
    ) -> None:
        """Test installed facade bases follow declaration scope."""
        package = installed_dependency_path / "lexical_sample"
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
        for path, source in dependency_sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        consumer = tmp_path / "consumer/src/consumer/service.py"
        statement = "from lexical_sample._private import Target"
        sources = {consumer: f"{statement}\nvalue = Target.Value\n"}

        if expected.startswith("c."):
            edits = self._edits(tmp_path, sources, consumer, statement)
            tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
            tm.that(edits[0].updated_source, has="from lexical_sample import c")
            tm.that(edits[0].updated_source, has=f"value = {expected}.Value")
            tm.that(edits[0].updated_source, lacks=statement)
        else:
            with pytest.raises(
                ValueError,
                match=expected or "no public facade exposes",
            ):
                self._plan(tmp_path, sources, consumer, statement)
        for path, source in dependency_sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

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

    @pytest.mark.parametrize("package_import", [False, True])
    @pytest.mark.parametrize("root_export", [False, True])
    @pytest.mark.parametrize("renamed", [False, True])
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

    @pytest.mark.parametrize("case", ["unexposed", "homonym", "ambiguous", "shadowed"])
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

        with pytest.raises(ValueError, match=expected):
            self._plan(tmp_path, sources, consumer, statement)
