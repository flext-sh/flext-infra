"""Generated initializer bytes observed through the public planner.

Every scenario writes real fixture sources, plans them through
``FlextInfraCodegenLazyInit.plan_files`` and observes the planned bytes, the
Ruff fixed point, and the lazy runtime behavior of the published package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.gates import FlextInfraRuffLintGate
from tests import c, m, tm, u


class TestsFlextInfraLazyInitGeneration:
    """Validate rendered initializers produced from fixture packages."""

    @staticmethod
    def _apply(repository: Path) -> None:
        """Publish the repository's planned initializers."""
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.run_lazy_init(repository, check_only=True), eq=0)

    @staticmethod
    def _ruff(*arguments: str) -> None:
        """Run one Ruff command with the project configuration and expect success."""
        result = tm.ok(
            u.Cli.run_raw([
                c.Infra.RUFF,
                *arguments,
                "--config",
                str(Path(__file__).resolve().parents[3] / c.PYPROJECT_FILENAME),
            ])
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=f"{result.stdout}\n{result.stderr}",
        )

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "class Original: pass\ns = Original\n",
            "class Original[T]: pass\ns = Original\n",
            "class Original: pass\ns = Original()\n",
            "def Original(): pass\ns = Original\n",
        ],
    )
    def test_initializer_imports_aliases_and_never_assigns(
        tmp_path: Path, declaration: str
    ) -> None:
        """An initializer imports a declared alias from its module, never binds it.

        Premise (operator ruling 2026-10-24): an initializer propagates and
        never declares; the alias exists only where its owning module declares
        it and lists it in ``__all__``.
        """
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        (package / "provider.py").write_text(
            f"{declaration}__all__ = ('Original', 's')\n", encoding=c.DEFAULT_ENCODING
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        generated = u.Tests.generated_init(package)

        tm.that(generated, has=f"from {package.name}.provider import Original, s")
        tm.that(generated, lacks="s = Original")
        tm.that(generated, has='"s": ".provider"')
        compile(generated, "__init__.py", "exec")

    @staticmethod
    def test_owner_import_beyond_the_line_length_stays_static(tmp_path: Path) -> None:
        """An owner import longer than the line length is wrapped, never bound.

        Premise: line length is the formatter's concern; the initializer keeps
        the plain parenthesized import and never binds a name.
        """
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        width: int = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        domain = package / ("_" + "d" * (width - len(package.name) - 22))
        domain.mkdir()
        (domain / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (domain / "provider.py").write_text(
            "class PublishedContract:\n    pass\n\n__all__ = ['PublishedContract']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        generated = u.Tests.generated_init(domain)
        namespace = f"{package.name}.{domain.name}"

        tm.that(generated, has=f"    from {namespace}.provider import (\n")
        tm.that(generated, lacks="_owner_")
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {namespace} as public\n"
                f"from {namespace}.provider import PublishedContract\n"
                "print(public.PublishedContract is PublishedContract)\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["True"],
        )

    @staticmethod
    def test_class_owned_test_root_installs_lazy_exports(tmp_path: Path) -> None:
        """A class-owned ``__all__`` publishes lazily and passes the Ruff gate."""
        repository, _ = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-rendered", package_name="flext_rendered"
        )
        testing = repository / c.Infra.DIR_TESTS
        testing.mkdir()
        testing.joinpath("constants.py").write_text(
            "class TestsFlextRenderedConstants:\n"
            "    __all__ = ('TestsFlextRenderedConstants',)\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        init_path = testing / c.Infra.INIT_PY
        source = init_path.read_text(encoding=c.DEFAULT_ENCODING)

        tm.that(source, has='"TestsFlextRenderedConstants": ".constants"')
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\nimport tests as package\n"
                "print('tests.constants' not in sys.modules)\n"
                "from tests.constants import TestsFlextRenderedConstants\n"
                "print(package.TestsFlextRenderedConstants is "
                "TestsFlextRenderedConstants)\n",
                python_paths=(str(repository),),
                cwd=repository,
            ),
            eq=["True", "True"],
        )
        checked = FlextInfraRuffLintGate(repository).check_files(
            (init_path,),
            repository,
            m.Infra.GateContext(
                repository_root=repository,
                reports_dir=repository,
                selected_files=(init_path,),
            ),
        )
        tm.that(checked.result.passed, eq=True, msg=checked.raw_output)
        tm.that(init_path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_root_initializer_carries_static_and_lazy_contracts(
        tmp_path: Path,
    ) -> None:
        """The root publishes modules, children and eager version metadata."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        (package / "api.py").write_text(
            "class Demo: pass\n__all__ = ['Demo']\n", encoding=c.DEFAULT_ENCODING
        )
        (package / "__version__.py").write_text(
            "__version__ = '1.0.0'\n__all__ = ['__version__']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        services = package / "services"
        services.mkdir()
        (services / "runner.py").write_text(
            "class DemoRunner: pass\n__all__ = ['DemoRunner']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        content = u.Tests.generated_init(package)

        compile(content, "__init__.py", "exec")
        tm.that(
            content,
            has=[
                f"    from {package.name} import services as services\n",
                f"    from {package.name}.__version__ import __version__\n",
                f"    from {package.name}.api import Demo\n",
                '__all__: tuple[str, ...] = ("Demo", "__version__", "services")',
                '"Demo": ".api"',
                '"services": ".services"',
                "install_lazy_exports(",
            ],
        )
        runtime_prefix = content.split("if TYPE_CHECKING:", maxsplit=1)[0]
        tm.that(runtime_prefix, lacks=f"from {package.name}.api import Demo")
        tm.that(runtime_prefix, lacks=f"from {package.name}.__version__ import")
        tm.that(
            content.split("install_lazy_exports(", maxsplit=2)[-1],
            has=(
                "if not TYPE_CHECKING:\n"
                f"    from {package.name}.__version__ import __version__\n"
            ),
        )
        tm.that(content, lacks="DemoRunner")
        tm.that(u.Tests.generated_init(services), has='"DemoRunner": ".runner"')

    @staticmethod
    @pytest.mark.parametrize("width_offset", [-1, 0, 1])
    def test_wrapped_contracts_are_formatter_fixed_points(
        tmp_path: Path, width_offset: int
    ) -> None:
        """``__all__``, the mapping and imports agree with Ruff at every width."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        width: int = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        first = "FlextDemoFirst"
        second = "FlextDemoSecond" + "x" * max(
            1, width + width_offset - len(f'__all__: tuple[str, ...] = ("{first}", "")')
        )
        (package / "owner.py").write_text(
            f"class {first}: pass\nclass {second}: pass\n"
            f"__all__ = [{first!r}, {second!r}]\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "__version__.py").write_text(
            "__version__ = '1.0.0'\n__all__ = ['__version__']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        init_path = package / c.Infra.INIT_PY

        TestsFlextInfraLazyInitGeneration._ruff("format", "--check", str(init_path))
        TestsFlextInfraLazyInitGeneration._ruff(
            "check", "--no-fix", "--select", "I,COM812", str(init_path)
        )

    @staticmethod
    def test_overlong_mapping_entry_keeps_its_trailing_comma(tmp_path: Path) -> None:
        """An exploded mapping entry carries the comma COM812 requires."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        width: int = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        # The owner import still fits once wrapped; the mapping entry does not.
        module = "owner_" + "x" * (width - len("owner_") - 38)
        name = "DemoFacade" + "Y" * (width - len(module) - len("DemoFacade") - 15)
        (package / f"{module}.py").write_text(
            f"class {name}: pass\n__all__ = [{name!r}]\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        content = u.Tests.generated_init(package)

        tm.that(
            content,
            has=f'        "{name}": (\n            ".{module}"\n        ),\n    }}),',
        )
        TestsFlextInfraLazyInitGeneration._ruff(
            "format", "--check", str(package / c.Infra.INIT_PY)
        )

    @staticmethod
    def test_root_never_publishes_private_entries(tmp_path: Path) -> None:
        """No private child declaration reaches the facade root's contract."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        (package / "api.py").write_text(
            "class Demo: pass\n__all__ = ['Demo']\n", encoding=c.DEFAULT_ENCODING
        )
        private = package / "_utilities"
        private.mkdir()
        (private / "conversion.py").write_text(
            "class DemoConversion: pass\n__all__ = ['DemoConversion']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        content = u.Tests.generated_init(package)

        tm.that(content, has='__all__: tuple[str, ...] = ("Demo",)')
        tm.that(content, lacks=["DemoConversion", "_utilities"])
        tm.that(u.Tests.generated_init(private), has='"DemoConversion"')

    @staticmethod
    def test_root_letters_import_their_classes_and_instances(tmp_path: Path) -> None:
        """Class and instance letters both import by name from their module."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        (package / "base.py").write_text(
            "class FlextDemoServiceBase: pass\n\ns = FlextDemoServiceBase\n\n"
            "__all__ = ['FlextDemoServiceBase', 's']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "_settings.py").write_text(
            "class FlextDemoSettings: pass\n\nsettings = FlextDemoSettings()\n\n"
            "__all__ = ['FlextDemoSettings', 'settings']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        lines = u.Tests.generated_init(package).splitlines()

        tm.that(
            lines,
            has=[
                f"    from {package.name}._settings import FlextDemoSettings, settings",
                f"    from {package.name}.base import FlextDemoServiceBase, s",
            ],
        )
        tm.that("\n".join(lines), lacks="s = FlextDemoServiceBase")

    @staticmethod
    def test_nested_package_resolves_its_exports_lazily(tmp_path: Path) -> None:
        """A nested package publishes its modules and children without importing."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        services = package / "services"
        nested = services / "nested"
        nested.mkdir(parents=True)
        (services / "demo.py").write_text(
            "class Demo: pass\n__all__ = ['Demo']\n", encoding=c.DEFAULT_ENCODING
        )
        (nested / "item.py").write_text(
            "class Nested: pass\n__all__ = ['Nested']\n", encoding=c.DEFAULT_ENCODING
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        namespace = f"{package.name}.services"

        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import sys\nimport {namespace} as package\n"
                f"print('{namespace}.demo' not in sys.modules and "
                f"'{namespace}.nested.item' not in sys.modules)\n"
                f"from {namespace}.demo import Demo\n"
                f"from {namespace}.nested.item import Nested\n"
                "print(package.Demo is Demo and package.Nested is Nested)\n"
                "print(sorted(package.__all__))\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["True", "True", "['Demo', 'Nested', 'nested']"],
        )

    @staticmethod
    def test_tests_root_renders_only_its_facade_contract(tmp_path: Path) -> None:
        """Test facades publish runtime aliases, never collected test classes."""
        repository, _ = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-rendered", package_name="flext_rendered"
        )
        testing = repository / c.Infra.DIR_TESTS
        unit = testing / "unit"
        unit.mkdir(parents=True)
        u.Tests.write_lazy_init_namespace_module(
            testing / "constants.py", class_name="TestsDemoConstants", alias="c"
        )
        (unit / "test_demo.py").write_text(
            "class TestsDemoCase: pass\n__all__ = ['TestsDemoCase']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        TestsFlextInfraLazyInitGeneration._apply(repository)
        content = (testing / c.Infra.INIT_PY).read_text(encoding=c.DEFAULT_ENCODING)

        tm.that(
            content,
            has=(
                "if TYPE_CHECKING:\n    from flext_tests import "
                "d, e, h, m, p, r, s, t, td, tf, tk, tm, u, x\n\n"
                "    from tests.constants import TestsDemoConstants, c\n"
            ),
        )
        tm.that(content, lacks="c = TestsDemoConstants")
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\nimport tests as package\nfrom flext_tests import tm\n"
                "print(package.tm is tm)\n"
                "print('TestsDemoCase' not in dir(package))\n"
                "print('tests.unit.test_demo' not in sys.modules)\n",
                python_paths=(str(repository),),
                cwd=repository,
            ),
            eq=["True", "True", "True"],
        )
