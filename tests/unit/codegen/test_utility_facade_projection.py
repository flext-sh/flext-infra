"""Public evidence for declared utility-facade projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from flext_infra import c, config, infra, m, p
from tests import t, tm, u


class TestsFlextInfraUtilityFacadeProjection:
    """Exercise declared owner projection only through ``u.Infra``."""

    @pytest.mark.parametrize("length_delta", [0, 16])
    @pytest.mark.parametrize("parenthesized", [False, True])
    def test_published_import_width_preserves_mro_and_lazy_exports(
        self,
        tmp_path: Path,
        length_delta: int,
        *,
        parenthesized: bool,
    ) -> None:
        """Preserve MRO and lazy exports around the configured import budget."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        self._write(package / c.Infra.INIT_PY, "")
        width = config.Infra.tooling.tools.ruff.line_length
        owner = "Owner" + "X" * ((width + length_delta) // 2)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        prefix = f"from {package.name}.{family.directory}.owner_ import ("
        module = "owner_" + "x" * max(0, width - len(prefix))
        self._write(
            package / family.directory / f"{module}.py",
            f'class {owner}:\n    """Canonical behavior owner."""\n'
            '    marker = "owner"\n'
            "    @classmethod\n    def read(cls) -> str:\n"
            "        return cls.marker\n"
            f'__all__ = ["{owner}"]\n',
        )
        binding = f"({owner})" if parenthesized else owner
        facade = package / c.Infra.UTILITIES_PY
        self._write(
            facade,
            '"""Public utility facade.\n\n'
            "Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
            'SPDX-License-Identifier: MIT\n"""\n\n'
            f"from {package.name}.{family.directory}.{module} import {binding}\n\n\n"
            f'class Utilities({owner}):\n    """Compose the canonical owner."""\n\n\n'
            'u = Utilities\n\n__all__ = ["Utilities", "u"]\n',
        )
        script = (
            "from pathlib import Path\n"
            "from flext_infra import config, u\n"
            "from tests import tm, u as test_u\n"
            f"root = Path({str(root)!r})\n"
            f"package = Path({str(package)!r})\n"
            f"facade = Path({str(facade)!r})\n"
            "assert config.Infra.tooling.tools.ruff.line_length == "
            f"{width}\n"
            "from importlib import import_module\n"
            f"before = import_module({(package.name + '.utilities')!r}).u\n"
            "expected = tuple(item.__name__ for item in before.__mro__)\n"
            "class Receiver(before):\n    marker = 'facade'\n"
            "assert before.read() == 'owner'\n"
            "assert Receiver.read() == 'facade'\n"
            "rendered = tm.not_none(u.Infra.render_utility_facade(package))\n"
            "tm.ok(u.Cli.atomic_write_text_file(facade, rendered))\n"
            "service = test_u.Tests.create_lazy_init_service(root)\n"
            "tm.ok(test_u.Tests.materialize_lazy_init(service))\n"
            "assert u.Infra.render_utility_facade(package) == rendered\n"
            "initializer = package / '__init__.py'\n"
            "published = tm.ok(u.Cli.atomic_read_binary_file_state(\n"
            "    initializer, required=True))\n"
            "tm.ok(test_u.Tests.materialize_lazy_init(service))\n"
            "assert tm.ok(u.Cli.atomic_read_binary_file_state(\n"
            "    initializer, required=True)) == published\n"
            "assert u.Infra.render_utility_facade(package) == rendered\n"
            "print(repr(expected))\n"
        )
        environment = {
            "PYTHONPATH": str(Path(__file__).resolve().parents[3])
            + ":"
            + str(package.parent),
        }
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script),
                cwd=root,
                options=m.Cli.ProcessOptions(env=environment),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        consumer = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u\n"
                        "class Receiver(u):\n    marker = 'facade'\n"
                        "assert u.read() == 'owner'\n"
                        "assert Receiver.read() == 'facade'\n"
                        "print(repr(tuple(item.__name__ for item in u.__mro__)))\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env=environment),
            )
        )
        tm.that(
            u.Cli.process_succeeded(consumer.outcome),
            eq=True,
            msg=(
                f"consumer stderr:\n{consumer.stderr}\n"
                f"consumer stdout:\n{consumer.stdout}\n"
                f"publisher stdout:\n{result.stdout}\n"
                "published __init__.py:\n"
                f"{
                    (package / c.Infra.INIT_PY).read_text(encoding=c.DEFAULT_ENCODING)
                }\n"
                "published utilities.py:\n"
                f"{facade.read_text(encoding=c.DEFAULT_ENCODING)}"
            ),
        )
        tm.that(result.stdout.endswith(consumer.stdout), eq=True)
        checked = tm.ok(
            u.Cli.run_raw(
                (
                    c.Infra.RUFF,
                    c.Infra.CHECK,
                    "--no-fix",
                    "--config",
                    str(Path(__file__).resolve().parents[3] / c.PYPROJECT_FILENAME),
                    "--line-length",
                    str(width),
                    str(facade),
                    str(package / c.Infra.INIT_PY),
                ),
                cwd=root,
            )
        )
        tm.that(
            u.Cli.process_succeeded(checked.outcome),
            eq=True,
            msg=checked.stdout + checked.stderr,
        )

    @staticmethod
    def _write(path: Path, source: str) -> None:
        """Create one fixture source through the canonical atomic writer."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(path, source))

    @classmethod
    def _publish_facade(cls, root: Path, package: Path, facade: Path) -> str:
        """Render and publish the utility facade, then prove it is a fixed point.

        Returns:
            The rendered facade source that was published.

        """
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        cls._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        return rendered

    @staticmethod
    def _run_consumer(root: Path, package: Path, script: str) -> p.Cli.CommandOutput:
        """Run ``script`` in a real interpreter over the package and require success.

        Returns:
            The successful command output.

        """
        output = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        return output

    def test_moved_service_retires_its_utility_composition(
        self,
        tmp_path: Path,
    ) -> None:
        """A service moved out of the family uses its utility without reentry."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        upstream = package.with_name(f"{package.name}_upstream")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            upstream / "__init__.py": (
                f"from {upstream.name}.utilities import ParentUtilities\n"
                "__all__ = ['ParentUtilities']\n"
            ),
            upstream / "utilities.py": (
                "class ParentUtilities:\n"
                "    class Domain:\n"
                "        @staticmethod\n"
                "        def upstream_value():\n"
                "            return 'upstream-value'\n"
                "__all__ = ['ParentUtilities']\n"
            ),
            package / "__init__.py": (
                f"from {package.name}.utilities import Utilities, u\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
            package / directory / "__init__.py": (
                f"from {package.name}.{directory}.client import ClientOwner\n"
                "__all__ = ['ClientOwner']\n"
            ),
            package / directory / "client.py": (
                "class ClientOwner:\n"
                "    class Target:\n"
                "        def __init__(self, value):\n"
                "            self.value = value\n"
                "        def read(self):\n"
                "            return self.value\n"
                "__all__ = ['ClientOwner']\n"
            ),
            package / "services" / "__init__.py": (
                f"from {package.name}.services.runtime import ServiceRuntime\n"
                "__all__ = ['ServiceRuntime']\n"
            ),
            package / "services" / "runtime.py": (
                f"from {package.name} import u\n"
                "class ServiceRuntime:\n"
                "    @staticmethod\n"
                "    def create(value):\n"
                "        return u.Domain.Target(value).read()\n"
                "__all__ = ['ServiceRuntime']\n"
            ),
            facade: (
                f"from {upstream.name} import ParentUtilities\n"
                f"from {package.name}.{directory} import ClientOwner\n"
                f"from {package.name}.services import ServiceRuntime\n"
                "class Utilities(ParentUtilities):\n"
                "    class Domain("
                "ClientOwner, ServiceRuntime, ParentUtilities.Domain):\n"
                "        pass\n"
                "u = Utilities\n__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            self._write(path, source)
        self._publish_facade(root, package, facade)
        result = self._run_consumer(
            root,
            package,
            f"from {package.name} import u; "
            f"from {package.name}.services import ServiceRuntime; "
            "assert u.Domain.Target('client-value').read() == 'client-value'; "
            "assert u.Domain.upstream_value() == 'upstream-value'; "
            "assert not hasattr(u.Domain, 'create'); "
            "print(ServiceRuntime.create('service-value'))",
        )
        tm.that(result.stdout.strip(), eq="service-value")

    @staticmethod
    def _behavior_package(
        package: Path,
        value_type: str,
    ) -> t.MutableMappingKV[Path, str]:
        """Declare a real typed factory and its public facade in one fixture package.

        Returns:
            The resulting source mapping.

        """
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        return {
            package / "__init__.py": (
                f"from {package.name}.utilities import Utilities, u\n"
                f"from {package.name}.typings import Types, t\n"
                "__all__ = ['Types', 't', 'Utilities', 'u']\n"
            ),
            package / "typings.py": (
                "class Types:\n    pass\nt = Types\n__all__ = ['Types', 't']\n"
            ),
            package / directory / "__init__.py": "",
            package / directory / "adapter.py": (
                "from pydantic import TypeAdapter\n"
                "class AdapterOwner:\n"
                "    @staticmethod\n"
                f"    def value_adapter() -> TypeAdapter[{value_type}]:\n"
                f"        return TypeAdapter({value_type})\n"
                "__all__ = ['AdapterOwner']\n"
            ),
            package / "utilities.py": (
                f"from {package.name}.{directory}.adapter import AdapterOwner\n"
                "class Utilities(AdapterOwner):\n    pass\nu = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
        }

    @staticmethod
    def _converged_projection(
        root: Path,
        sources: t.MutableMappingKV[Path, str],
        *,
        relocated: bool,
    ) -> t.MutableMappingKV[Path, str]:
        """Plan the declaration relocation and prove the result needs no further edit.

        Returns:
            The projected sources: the planned edits applied to a copy of
            ``sources`` when ``relocated``; otherwise ``sources`` itself, after
            proving the sources already plan no edit.

        """
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
            if not relocated:
                tm.that(edits, empty=True)
                return dict(sources)
            tm.that(edits, empty=False)
            proposed = dict(sources)
            proposed.update({edit.file_path: edit.updated_source for edit in edits})
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=proposed,
                    )
                ),
                empty=True,
            )
        return proposed

    @classmethod
    def _render_and_execute_constants_consumer(
        cls,
        package: Path,
        facade: Path,
        *,
        expected_stdout: str,
    ) -> str:
        """Render the ``c`` family facade and read it back from a real consumer.

        Returns:
            The rendered facade source that was projected and executed.

        """
        service = u.Tests.create_lazy_init_service(package.parent.parent)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="c"))
        cls._write(facade, rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "from flext_sample.constants import c\nprint(c.Sample.value)\n",
                ),
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq=expected_stdout)
        return rendered

    @pytest.mark.parametrize("relation", ["isolated", "inherited", "foreign-only"])
    def test_behavior_owners_follow_the_imported_package_lineage(
        self,
        tmp_path: Path,
        relation: str,
    ) -> None:
        """Matching foreign method names neither redirect nor ambiguate a reference."""
        root, first = u.Tests.create_lazy_init_workspace(tmp_path)
        second = first.with_name(first.name + "_other")
        sources = self._behavior_package(first, "int")
        sources.update(self._behavior_package(second, "str"))
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        typings = u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY).directory
        if relation != "isolated":
            del sources[first / directory / "adapter.py"]
            sources[first / "utilities.py"] = (
                f"from {second.name} import Utilities as ParentUtilities\n"
                "class Utilities(ParentUtilities):\n    pass\nu = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
                if relation == "inherited"
                else "class Utilities:\n    pass\nu = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            )
            if relation == "inherited":
                third = first.with_name(first.name + "_leaf")
                sources.update(self._behavior_package(third, "str"))
                del sources[second / directory / "adapter.py"]
                sources[second / "__init__.py"] = (
                    f"from {third.name} import Types as ParentTypes\n"
                    f"from {second.name}.utilities import Utilities, u\n"
                    "class Types(ParentTypes):\n    pass\nt = Types\n"
                    "__all__ = ['Types', 't', 'Utilities', 'u']\n"
                )
                sources[second / "utilities.py"] = (
                    f"from {third.name} import Utilities as ParentUtilities\n"
                    "class Utilities(ParentUtilities):\n    pass\nu = Utilities\n"
                    "__all__ = ['Utilities', 'u']\n"
                )
                sources[first / typings / "eager.py"] = (
                    f"from {second.name} import Types as ImportedTypes\n"
                    "class Eager:\n    adapter = ImportedTypes.value_adapter()\n"
                    "__all__ = ['Eager']\n"
                )
                sources[first / "__init__.py"] = (
                    f"from {second.name} import Types as ParentTypes\n"
                    f"from {first.name}.utilities import Utilities, u\n"
                    "class Types(ParentTypes):\n    pass\nt = Types\n"
                    f"from {first.name}.{typings}.eager import Eager\n"
                    "__all__ = ['Types', 't', 'Utilities', 'u', 'Eager']\n"
                )
        consumer = root / "consumer.py"
        sources[consumer] = (
            "def first_call():\n"
            f"    from {first.name} import t as shared\n"
            "    return shared.value_adapter().validate_python('7')\n"
            "def second_call():\n"
            f"    from {second.name} import t as shared\n"
            "    return shared.value_adapter().validate_python('7')\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        proposed = self._converged_projection(root, sources, relocated=True)
        if relation == "foreign-only":
            tm.that(proposed[consumer], has="return shared.value_adapter()")
        else:
            tm.that(proposed[consumer], has=f"{first.name}.u.value_adapter()")
        tm.that(proposed[consumer], has=f"{second.name}.u.value_adapter()")
        for path, source in proposed.items():
            self._write(path, source)
        first_contract = (
            "try:\n    consumer.first_call()\n"
            "except AttributeError:\n    print('unavailable')\n"
            "else:\n    raise AssertionError('foreign behavior adopted')\n"
            if relation == "foreign-only"
            else f"assert consumer.first_call() == "
            f"{'7' if relation == 'isolated' else repr('7')}\n"
        )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "import consumer\n"
                    + first_contract
                    + "assert consumer.second_call() == '7'\n"
                    + (
                        f"from {first.name} import Eager\nassert "
                        f"Eager.adapter.validate_python('9') == '9'\n"
                        if relation == "inherited"
                        else ""
                    )
                    + "print('scoped')\n",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(first.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout, has="scoped")

    def test_shadowed_t_with_competing_owners_is_not_a_migration(
        self,
        tmp_path: Path,
    ) -> None:
        """Ownership decisions do not run for a lexical parameter named t."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / directory / "duplicate.py"] = (
            "class Duplicate:\n    @staticmethod\n"
            "    def value_adapter() -> int:\n        return 1\n"
            "__all__ = ['Duplicate']\n"
        )
        consumer = root / "consumer.py"
        sources[consumer] = (
            f"from {package.name} import t\n"
            "def consumer(t):\n    return t.value_adapter()\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        self._converged_projection(root, sources, relocated=False)
        tm.that(consumer.read_text(encoding="utf-8"), eq=sources[consumer])

    def test_existing_contextual_u_call_keeps_facade_dispatch(
        self,
        tmp_path: Path,
    ) -> None:
        """A valid class-context-dependent utility remains outside this migration."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / directory / "adapter.py"] = (
            "class AdapterOwner:\n    marker = 'leaf'\n"
            "    @classmethod\n    def bind_context(cls) -> str:\n"
            "        return cls.marker\n__all__ = ['AdapterOwner']\n"
        )
        sources[package / "utilities.py"] = (
            f"from {package.name}.{directory}.adapter import AdapterOwner\n"
            "class Utilities(AdapterOwner):\n    marker = 'facade'\nu = Utilities\n"
            "__all__ = ['Utilities', 'u']\n"
        )
        caller = package / "_decorators" / "consumer.py"
        sources[caller] = (
            f"from {package.name} import u\n"
            "def consume() -> str:\n    return u.bind_context()\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        self._converged_projection(root, sources, relocated=False)
        self._run_consumer(
            root,
            package,
            f"from {package.name}._decorators.consumer import consume; "
            "assert consume() == 'facade'",
        )

    @pytest.mark.parametrize("module_level", [True, False], ids=["module", "class"])
    def test_behavior_roundtrip_keeps_bootstrap_lower_dependency(
        self,
        tmp_path: Path,
        *,
        module_level: bool,
    ) -> None:
        """A real consumer imports the projected facade without a reverse cycle."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owners = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        typings = (
            package / u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY).directory
        )
        owner = owners / "adapter.py"
        runtime = owners / "runtime.py"
        facade = package / "utilities.py"
        consumer = root / "consumer.py"
        runtime_source = (
            (
                f"from {package.name} import t\n"
                "class Runtime:\n"
                "    @staticmethod\n"
                "    def parse(value):\n"
                "        first = t.value_adapter().validate_python(value)\n"
                "        return t.value_adapter().validate_python(first)\n"
                "def shadowed(t):\n    return t.value_adapter()\n"
            )
            if module_level
            else (
                "class Runtime:\n"
                "    @classmethod\n"
                "    def parse(cls, value):\n"
                "        first = cls.value_adapter().validate_python(value)\n"
                "        return cls.value_adapter().validate_python(first)\n"
                "    @staticmethod\n"
                "    def shadowed(t):\n"
                "        return t.value_adapter()\n"
            )
        )
        sources = {
            package / "__init__.py": (
                f"from {package.name}.typings import t\n"
                f"from {package.name}.utilities import u\n"
            ),
            package / "typings.py": (
                f"from {package.name}.{typings.name}.base import Types\n"
                "t = Types\n__all__ = ['Types', 't']\n"
            ),
            typings / "__init__.py": "",
            typings / "base.py": "class Types:\n    pass\n__all__ = ['Types']\n",
            owners / "__init__.py": "",
            owner: (
                "from pydantic import TypeAdapter\n"
                "class AdapterOwner:\n"
                "    @staticmethod\n"
                "    def value_adapter() -> TypeAdapter[int]:\n"
                "        return TypeAdapter(int)\n"
                "__all__ = ['AdapterOwner']\n"
            ),
            runtime: runtime_source + "__all__ = ['Runtime']\n",
            facade: (
                f"from {package.name}.{owners.name}"
                f"{'.runtime' if module_level else ''} import Runtime\n"
                "class Utilities(Runtime):\n    pass\n"
                "u = Utilities\n__all__ = ['Utilities', 'u']\n"
            ),
            consumer: (
                f"from {package.name} import t\n"
                "assert t.value_adapter().validate_python('7') == 7\n"
            ),
        }
        for path, source in sources.items():
            self._write(path, source)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        sources[facade] = rendered
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        sources = {path: tm.ok(u.Cli.files_read_text(path)) for path in sources}
        proposed = self._converged_projection(root, sources, relocated=True)
        if module_level:
            tm.that(
                proposed[runtime],
                has=f"from {package.name}.{owners.name}.adapter import AdapterOwner",
            )
            tm.that(proposed[runtime], has="return t.value_adapter()")
        for path, source in proposed.items():
            self._write(path, source)
        self._publish_facade(root, package, facade)
        result = self._run_consumer(
            root,
            package,
            f"from {package.name} import u; "
            f"import runpy; runpy.run_path({str(consumer)!r}); "
            "from pydantic import ValidationError; "
            "assert u.parse('7') == 7; "
            "assert u.value_adapter().validate_python('8') == 8"
            + (
                "\n"
                if module_level
                else "; assert u.shadowed(u).validate_python('9') == 9\n"
            )
            + "try:\n    u.parse([])\n"
            "except ValidationError:\n    print('rejected')\n"
            "else:\n    raise AssertionError('invalid payload accepted')\n",
        )
        tm.that(result.stdout, has="rejected")

    @pytest.mark.parametrize("direct", [True, False], ids=["direct", "composed"])
    def test_nested_facade_projects_lower_owner_runtime_calls(
        self,
        tmp_path: Path,
        *,
        direct: bool,
    ) -> None:
        """Lower-owner runtime calls use the nested public namespace without a cycle."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        runtime_source = (
            (
                f"from {package.name}.{directory}.adapter import AdapterOwner\n"
                "class Runtime:\n    @staticmethod\n    def parse(value):\n"
                "        return AdapterOwner.value_adapter().validate_python(value)\n"
            )
            if direct
            else (
                "class Runtime:\n    @classmethod\n    def parse(cls, value):\n"
                "        return cls.value_adapter().validate_python(value)\n"
            )
        )
        sources[package / directory / "runtime.py"] = (
            runtime_source + "__all__ = ['Runtime']\n"
        )
        facade = package / "utilities.py"
        sources[facade] = (
            f"from {package.name}.{directory}{'.runtime' if direct else ''}"
            " import Runtime\n"
            "class Utilities:\n    class Domain(Runtime):\n        pass\n"
            "u = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        self._publish_facade(root, package, facade)
        output = self._run_consumer(
            root,
            package,
            f"from {package.name} import u; "
            "assert u.Domain.parse('7') == 7; "
            "assert u.Domain.value_adapter().validate_python('8') == 8; "
            "print('nested')",
        )
        tm.that(output.stdout, has="nested")

    @pytest.mark.parametrize("alias", ["leaf", "u\u0301"])
    def test_aliased_owner_projection_preserves_unicode_and_lexical_scopes(
        self,
        tmp_path: Path,
        alias: str,
    ) -> None:
        """Native scopes retain normalized aliases, defaults and local shadows."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / directory / "adapter.py"] = (
            "from pydantic import TypeAdapter\n"
            "class AdapterOwner:\n"
            "    @staticmethod\n"
            "    def value_adapter() -> TypeAdapter[int]:\n"
            "        return TypeAdapter(int)\n"
            "    @staticmethod\n"
            "    def header_adapter() -> TypeAdapter[str]:\n"
            "        return TypeAdapter(str)\n"
            "__all__ = ['AdapterOwner']\n"
        )
        sources[package / directory / "unused.py"] = (
            "class FirstUnusedOwner:\n"
            "    @staticmethod\n"
            "    def shadow_only() -> str:\n"
            "        return 'first'\n"
            "class SecondUnusedOwner:\n"
            "    @staticmethod\n"
            "    def shadow_only() -> str:\n"
            "        return 'second'\n"
            "__all__ = ['FirstUnusedOwner', 'SecondUnusedOwner']\n"
        )
        sources[package / directory / "runtime.py"] = (
            f"from {package.name}.{directory}.adapter import AdapterOwner as {alias}\n"
            "class Local:\n"
            "    @staticmethod\n"
            "    def shadow_only() -> str:\n"
            "        return 'local'\n"
            "class Runtime:\n"
            "    @staticmethod\n"
            "    def parse(value):\n"
            f"        prefix = 'caf\u00e9'; return "
            f"{alias}.value_adapter().validate_python(value)\n"
            "    @staticmethod\n"
            f"    def default_alias({alias}={alias}.header_adapter()):\n"
            f"        return {alias}.validate_python('header')\n"
            "    @staticmethod\n"
            f"    def parameter_shadow({alias}):\n"
            f"        prefix = 'caf\u00e9'; return {alias}.shadow_only()\n"
            "    @staticmethod\n"
            "    def local_shadow():\n"
            f"        {alias} = Local()\n"
            f"        prefix = 'caf\u00e9'; return {alias}.shadow_only()\n"
            "__all__ = ['Runtime']\n"
        )
        facade = package / c.Infra.UTILITIES_PY
        sources[facade] = (
            f"from {package.name}.{directory}.runtime import Runtime\n"
            "class Utilities:\n    class Domain(Runtime):\n        pass\n"
            "u = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        self._publish_facade(root, package, facade)
        self._run_consumer(
            root,
            package,
            f"from {package.name} import u\n"
            f"from {package.name}.{directory}.runtime import Local\n"
            "assert u.Domain.parse('7') == 7\n"
            "assert u.Domain.default_alias() == 'header'\n"
            "assert u.Domain.header_adapter().validate_python('header') == 'header'\n"
            "assert u.Domain.parameter_shadow(Local()) == 'local'\n"
            "assert u.Domain.local_shadow() == 'local'\n",
        )

    @pytest.mark.parametrize("conflict", ["unpublished", "shadowing"])
    def test_behavior_cutover_rejects_unavailable_destination_without_mutation(
        self,
        tmp_path: Path,
        conflict: str,
    ) -> None:
        """An unpublished or shadowed public destination prevents every effect."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        consumer = root / "consumer.py"
        source = (
            f"from {package.name} import t\n"
            f"def consume({c.Infra.FacadeFamily.U}):\n    return t.value_adapter()\n"
            if conflict == "shadowing"
            else f"from {package.name} import t\nvalue = t.value_adapter()\n"
        )
        sources = (
            self._behavior_package(package, "int")
            if conflict == "shadowing"
            else {
                package / "__init__.py": (
                    "class Types:\n    pass\nt = Types\n__all__ = ['Types', 't']\n"
                ),
            }
        )
        sources[consumer] = source
        if conflict == "unpublished":
            for name in ("First", "Second"):
                sources[family / f"{name.lower()}.py"] = (
                    f"class {name}:\n"
                    "    @staticmethod\n"
                    "    def value_adapter() -> int:\n        return 7\n"
                    f"__all__ = ['{name}']\n"
                )
        for path, content in sources.items():
            self._write(path, content)
        with infra.rope_workspace(root) as rope:
            cause = (
                f"relocated behavior receiver is shadowed: {c.Infra.FacadeFamily.U}"
                if conflict == "shadowing"
                else "relocated behavior is not reachable through public utilities:"
            )
            with pytest.raises(ValueError, match=cause):
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
        for path, content in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=content)

    @pytest.mark.parametrize(
        ("import_statement", "consumer_name"),
        [
            ("from flext_sample import u", "batch_apply.py"),
            ("from .. import u", "batch_apply.py"),
            ("from ..utilities import u", "batch_apply.py"),
            ("from .. import u", "__init__.py"),
            ("from ..utilities import u", "__init__.py"),
        ],
    )
    def test_projects_only_uniquely_discovered_missing_owner(
        self,
        tmp_path: Path,
        import_statement: str,
        consumer_name: str,
    ) -> None:
        """Derive the required owner from the executable public consumer."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        conflicted = (
            c.Infra.AUTOGEN_HEADERS[0] + "\n<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        )
        self._write(package / "__init__.py", conflicted)
        self._write(
            package / "codemod" / consumer_name,
            "import sys\n"
            + import_statement
            + "\n\nsys.getdefaultencoding()\nu.Sample.plan_cutover()\n",
        )
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> str:\n"
            "        return 'selected'\n"
            "class _PrivateCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> str:\n"
            "        return 'private'\n"
            "__all__ = ['FlextSampleUtilitiesSemanticCutover']\n",
        )
        self._write(
            package / "_utilities" / "internal_owner.py",
            "class InternalOwner:\n"
            "    @staticmethod\n"
            "    def internal_step() -> None:\n"
            "        pass\n"
            "class OtherInternalOwner:\n"
            "    @staticmethod\n"
            "    def internal_step() -> None:\n"
            "        pass\n",
        )
        self._write(
            package / "_utilities" / "internal_consumer.py",
            "from flext_sample._utilities.internal_owner import InternalOwner\n"
            "InternalOwner.internal_step()\n",
        )
        facade = package / "utilities.py"
        self._write(
            package / "_utilities" / "existing.py",
            "class Existing:\n"
            "    @staticmethod\n"
            "    def existing_step() -> str:\n"
            "        return 'existing'\n__all__ = ['Existing']\n",
        )
        self._write(
            facade,
            "from flext_core import FlextUtilities\n"
            "from flext_sample._utilities.existing import Existing\n\n"
            "class FlextSampleUtilities(FlextUtilities):\n"
            "    class Sample(\n"
            "        Existing,\n"
            "    ):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n',
        )
        initial_facade = tm.ok(
            u.Cli.atomic_read_binary_file_state(facade, required=True),
        )
        initial_init = tm.ok(
            u.Cli.atomic_read_binary_file_state(package / "__init__.py", required=True),
        )
        updated = tm.not_none(u.Infra.render_utility_facade(package))

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)),
            eq=initial_facade,
        )
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    package / "__init__.py",
                    required=True,
                ),
            ),
            eq=initial_init,
        )
        self._write(facade, updated)
        self._write(package / "__init__.py", "from flext_sample.utilities import u\n")
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import u; "
                        "assert u.Sample.plan_cutover() == 'selected'; "
                        "assert u.Sample.existing_step() == 'existing'; "
                        "assert not hasattr(u.Sample, 'internal_step')"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("member_path", ["provider", "libraries/provider"])
    def test_declared_workspace_import_resolves_without_adopting_foreign_owner(
        self,
        tmp_path: Path,
        member_path: str,
    ) -> None:
        """Sibling facade calls resolve from declarations, not ambient installs."""
        package = tmp_path / "receiver" / "src" / "flext_sample"
        foreign = tmp_path / member_path / "src" / "foreign_facade"
        self._write(
            tmp_path / ".gitmodules",
            '[submodule "receiver"]\n\tpath = receiver\n'
            f'[submodule "provider"]\n\tpath = {member_path}\n',
        )
        for directory, distribution in (
            (package.parent.parent, "receiver"),
            (foreign.parent.parent, "provider"),
        ):
            project = u.Tests.project_spec(distribution)
            self._write(
                directory / "pyproject.toml",
                f'[project]\nname = "{distribution}"\nversion = "1.0.0"\n'
                f'authors = [{{name = "{project.author_name}", '
                f'email = "{project.author_email}"}}]\n'
                f'license = "{project.license}"\n'
                + (
                    'dependencies = ["provider"]\n'
                    if distribution == "receiver"
                    else ""
                ),
            )
        self._write(package / "__init__.py", "")
        self._write(foreign / "__init__.py", "from .utilities import u\n")
        self._write(
            foreign / "utilities.py",
            "class Foreign:\n    class Sample:\n"
            "        @staticmethod\n        def foreign_only() -> str:\n"
            "            return 'foreign'\nu = Foreign\n",
        )
        self._write(
            package / "foreign_consumer.py",
            "from foreign_facade import u\nu.Sample.foreign_only()\n",
        )
        self._write(
            package / "consumer.py",
            "from flext_sample import u\nu.Sample.required()\n",
        )
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    @staticmethod\n"
            "    def required() -> str:\n        return 'local'\n"
            "__all__ = ['Owner']\n",
        )
        self._write(
            package / "_utilities" / "foreign.py",
            "class ForeignOwner:\n    @staticmethod\n"
            "    def foreign_only() -> str:\n        return 'wrong'\n",
        )
        facade = package / "utilities.py"
        original = (
            "class Facade:\n    class Sample:\n        pass\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n"
        )
        self._write(facade, original)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.that(facade.read_text(), eq=original)
        self._write(facade, rendered)
        tm.ok(
            u.Tests.materialize_lazy_init(
                u.Tests.create_lazy_init_service(package.parent.parent),
            ),
        )
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import u; "
                        "from flext_sample._utilities import Owner; "
                        "from foreign_facade import u as foreign; "
                        "assert u.Sample.required is Owner.required; "
                        "assert u.Sample.required() == 'local'; "
                        "assert not hasattr(u.Sample, 'foreign_only'); "
                        "assert foreign.Sample.foreign_only() == 'foreign'; "
                        "print('identities-proven')"
                    ),
                ),
                cwd=package.parent.parent,
                options=m.Cli.ProcessOptions(
                    env={
                        "PYTHONPATH": os.pathsep.join(
                            (str(package.parent), str(foreign.parent)),
                        ),
                    },
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="identities-proven")

    def test_unresolved_consumer_import_remains_a_consumer_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Declared projection preserves an unrelated consumer's native failure."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "")
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    pass\n__all__ = ['Owner']\n",
        )
        self._write(
            package / "utilities.py",
            "class Facade:\n    class Sample:\n        pass\n\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n",
        )
        consumer = package / "consumer.py"
        source = "from nonexistent_facade_owner import u\nu.Sample.required()\n"
        self._write(consumer, source)
        facade = package / "utilities.py"
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)),
            eq=before,
        )
        self._write(facade, rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", "import flext_sample.consumer"),
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=False)
        tm.that(
            output.stderr,
            has="ModuleNotFoundError: No module named 'nonexistent_facade_owner'",
        )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_inherited_aggregator_keeps_one_behavior_owner(
        self, tmp_path: Path
    ) -> None:
        """A pure MRO aggregate preserves its defining owner's public behavior."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        provider = package.with_name(f"{package.name}_provider")
        self._write(package / "__init__.py", "from .utilities import u\n")
        self._write(
            package / "consumer.py", "from flext_sample import u\nu.Sample.read()\n"
        )
        self._write(
            provider / "reader.py",
            "class Reader:\n"
            "    @classmethod\n"
            "    def read(cls) -> str:\n"
            "        return cls._value()\n"
            "    @staticmethod\n"
            "    def _value() -> str:\n"
            "        return 'read'\n"
            "__all__ = ['Reader']\n",
        )
        self._write(
            provider / "__init__.py",
            f"from {provider.name}.reader import Reader\n__all__ = ['Reader']\n",
        )
        self._write(
            package / "_utilities" / "document.py",
            f"from {provider.name} import Reader\n"
            "class Document(Reader):\n    pass\n__all__ = ['Document']\n",
        )
        facade = package / "utilities.py"
        source = (
            "from ._utilities.document import Document\n"
            "class Utilities:\n"
            "    class Sample(Document):\n        pass\n"
            "u = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        self._write(facade, source)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.that(facade.read_text(), eq=source)
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "from flext_sample import u\nprint(u.Sample.read())\n",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="read")
        tm.that(facade.read_text(), eq=rendered)

    def test_rejects_competing_declared_owners(self, tmp_path: Path) -> None:
        """Fail before projection when two publishers claim one public name."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        self._write(package / "__init__.py", "")
        for module in ("first", "second"):
            self._write(
                package / family.directory / f"{module}.py",
                "class Owner:\n"
                "    @staticmethod\n"
                "    def plan_cutover() -> None:\n"
                "        pass\n"
                "__all__ = ['Owner']\n",
            )
        facade = package / c.Infra.UTILITIES_PY
        original = (
            "from flext_cli import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(u):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n'
        )
        self._write(facade, original)

        with pytest.raises(ValueError, match="Competing declared facade owner names"):
            u.Infra.render_utility_facade(package)
        tm.that(facade.read_text(), eq=original)

    def test_rejects_competing_inherited_namespaces(self, tmp_path: Path) -> None:
        """Reject an ambiguous facade without dropping either declaration body."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        facade = package / c.Infra.UTILITIES_PY
        source = (
            "from flext_cli import u\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(u):\n        declaration = 'first'\n"
            "    class Extra(u):\n        declaration = 'second'\n"
            "u = FlextSampleUtilities\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n'
        )
        self._write(facade, source)
        (package / family.directory).mkdir()

        with pytest.raises(ValueError, match="competing inherited utility namespaces"):
            u.Infra.render_utility_facade(package)
        tm.that(facade.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_rejects_owners_without_a_public_facade(self, tmp_path: Path) -> None:
        """Utility owners without a facade have no public surface at all."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    pass\n__all__ = ['Owner']\n",
        )

        with pytest.raises(ValueError, match="have no public facade"):
            u.Infra.render_utility_facade(package)

    @staticmethod
    def test_empty_owner_directory_needs_no_facade(tmp_path: Path) -> None:
        """A preflight-created empty directory is not a private implementation."""
        package = tmp_path / "src" / "flext_sample"
        (package / "_utilities").mkdir(parents=True)
        tm.that(u.Infra.render_utility_facade(package), eq=None)

    @pytest.mark.parametrize(
        "consumer_source",
        ["def invalid(:\n", "class TestInvalid(\n"],
    )
    def test_unrelated_malformed_consumer_does_not_block_declared_projection(
        self,
        tmp_path: Path,
        consumer_source: str,
    ) -> None:
        """Compose valid declarations without analyzing unrelated test bodies."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        self._write(package / c.Infra.INIT_PY, "")
        self._write(
            package / family.directory / "owner.py",
            "class Owner:\n    value = 'declared'\n__all__ = ['Owner']\n",
        )
        facade = package / c.Infra.CONSTANTS_PY
        source = (
            f"from flext_sample.{family.directory}.owner import Owner\n"
            "class Facade:\n    class Sample(Owner):\n        pass\n"
            "c = Facade\n__all__ = ['Facade', 'c']\n"
        )
        self._write(facade, source)
        consumer = package / "unit" / "test_incomplete.py"
        self._write(consumer, consumer_source)

        self._render_and_execute_constants_consumer(
            package,
            facade,
            expected_stdout="declared",
        )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=consumer_source)

    def test_stale_projected_base_order_is_regenerated_from_owner_ancestry(
        self,
        tmp_path: Path,
    ) -> None:
        """An invalid old projection cannot override its valid source owners."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        self._write(package / c.Infra.INIT_PY, "")
        self._write(
            package / family.directory / "base_owner.py",
            "class BaseOwner:\n    value = 'base'\n__all__ = ['BaseOwner']\n",
        )
        self._write(
            package / family.directory / "child_owner.py",
            f"from flext_sample.{family.directory}.base_owner import BaseOwner\n"
            "class ChildOwner(BaseOwner):\n    value = 'child'\n"
            "__all__ = ['ChildOwner']\n",
        )
        facade = package / c.Infra.CONSTANTS_PY
        self._write(
            facade,
            f"from flext_sample.{family.directory}.base_owner import BaseOwner\n"
            f"from flext_sample.{family.directory}.child_owner import ChildOwner\n"
            "class Facade:\n    class Sample(BaseOwner, ChildOwner):\n        pass\n"
            "c = Facade\n__all__ = ['Facade', 'c']\n",
        )
        rendered = self._render_and_execute_constants_consumer(
            package,
            facade,
            expected_stdout="child",
        )
        repeated = u.Infra.render_utility_facade(package, family="c")
        tm.that(
            repeated,
            eq=rendered,
            msg=f"Initial projection: {rendered!r}\nRepeated projection: {repeated!r}",
        )

    @pytest.mark.parametrize("generated", [True, False])
    def test_initializer_ownership_controls_consumer_parsing(
        self,
        tmp_path: Path,
        *,
        generated: bool,
    ) -> None:
        """Only generated propagation is excluded from authored consumer analysis."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    pass\n__all__ = ['Owner']\n",
        )
        original = (
            "from flext_sample._utilities.owner import Owner\n"
            "class Facade:\n    class Domain(Owner):\n        pass\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n"
        )
        self._write(package / "utilities.py", original)
        conflicted = (
            c.Infra.AUTOGEN_HEADERS[0] + "\n" if generated else ""
        ) + "<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        initializer = package / c.Infra.INIT_PY
        self._write(initializer, conflicted)

        if generated:
            tm.not_none(u.Infra.render_utility_facade(package))
            tm.that((package / "utilities.py").read_text(), eq=original)
        else:
            with pytest.raises(SyntaxError):
                u.Infra.render_utility_facade(package)
        tm.that(initializer.read_text(), eq=conflicted)

    def test_facade_without_local_owners_is_complete(self, tmp_path: Path) -> None:
        """A pure re-export facade with no owners directory needs no projection."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "utilities.py", "class Owner:\n    pass\n")

        tm.that(u.Infra.render_utility_facade(package), eq=None)

    def test_rejects_unsupported_facade_base_expression(self, tmp_path: Path) -> None:
        """Reject dynamic bases instead of converting them to an empty owner."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "codemod" / "batch_apply.py",
            "from flext_sample import u\n\nu.Sample.plan_cutover()\n",
        )
        # The facade and its private family exist together in a real package;
        # without the owner directory the renderer stops at the incomplete
        # artifact check and never reaches the base expression under test.
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> None:\n"
            "        pass\n",
        )
        self._write(
            package / "utilities.py",
            "from upstream import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(owner_factory()):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n',
        )

        with pytest.raises(ValueError, match="unsupported utility facade base"):
            u.Infra.render_utility_facade(package)

    @pytest.mark.parametrize("multiline", [False, True])
    def test_protocol_annotation_projects_owner_and_converges(
        self,
        tmp_path: Path,
        *,
        multiline: bool,
    ) -> None:
        """An owned annotation supplies its protocol without changing other code."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        self._write(package / "__init__.py", "")
        self._write(
            package / "services" / "payload.py",
            "from flext_sample import p\n"
            "def consume(value: p.Sample.Payload) -> None:\n    pass\n"
            "def foreign(value: p.Other.Unused) -> None:\n    pass\n",
        )
        self._write(
            package / "_protocols" / "payload.py",
            "from typing import Protocol, runtime_checkable\n"
            "class PayloadOwner:\n"
            "    preserved = 'unchanged'\n"
            "    @runtime_checkable\n"
            "    class Payload(Protocol):\n"
            "        value: str\n"
            "__all__ = ['PayloadOwner']\n",
        )
        self._write(
            package / "_protocols" / "unused.py",
            "class UnusedOwner:\n    class Unused:\n        pass\n",
        )
        self._write(
            package.parent / "foreign_package" / "__init__.py",
            "from flext_core import p\n__all__ = ['p']\n",
        )
        self._write(
            package / "foreign_consumer.py",
            "from foreign_package import p\n"
            "def foreign(value: p.Sample.Unused) -> None:\n    pass\n",
        )
        self._write(
            package / "shadowed_consumer.py",
            "from flext_sample import p\n"
            "def parameter(p):\n    return p.Sample.Unused\n"
            "def assigned():\n    p = 0\n    return p.Sample.Unused\n",
        )
        facade = package / "protocols.py"
        header = (
            "    class Sample(\n        FlextProtocols,\n    ):\n"
            if multiline
            else ("    class Sample(FlextProtocols):\n")
        )
        original = (
            "from flext_core import FlextProtocols\n\n"
            "class FlextSampleProtocols(FlextProtocols):\n"
            + header
            + "        pass\n\np = FlextSampleProtocols\n\n"
            + '__all__ = ["FlextSampleProtocols", "p"]\n'
        )
        self._write(facade, original)

        service = u.Tests.create_lazy_init_service(root)
        family = u.Infra.facade_family_declared_by(facade.name)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        updated = tm.not_none(u.Infra.render_utility_facade(package, family="p"))

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)),
            eq=before,
        )
        self._write(facade, updated)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=updated)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import p\n"
                        "class Value:\n    value = 'payload'\n"
                        "assert isinstance(Value(), p.Sample.Payload)\n"
                        "assert p.Sample.preserved == 'unchanged'\n"
                        "assert not hasattr(p.Sample, 'Unused')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("multiline", [False, True])
    def test_protocol_owner_precedes_terminal_protocol_base(
        self,
        tmp_path: Path,
        *,
        multiline: bool,
    ) -> None:
        """Both source forms import and expose the real structural protocol."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        self._write(package / "__init__.py", "")
        self._write(
            package.parent / "upstream.py",
            "from typing import Protocol\n"
            "class ParentProtocols(Protocol):\n    pass\n"
            "p = ParentProtocols\n__all__ = ['ParentProtocols', 'p']\n",
        )
        self._write(
            package / "services" / "payload.py",
            "from flext_sample import p\n"
            "def consume(value: p.Sample.Payload) -> None:\n    pass\n",
        )
        self._write(
            package / "_protocols" / "payload.py",
            "from typing import Protocol, runtime_checkable\n\n"
            "class PayloadOwner(Protocol):\n"
            "    @runtime_checkable\n"
            "    class Payload(Protocol):\n        value: str\n"
            "__all__ = ['PayloadOwner']\n",
        )
        facade = package / "protocols.py"
        header = (
            "    class Sample(\n        p,\n        Protocol,\n    ):\n"
            if multiline
            else "    class Sample(p, Protocol):\n"
        )
        self._write(
            facade,
            "from typing import Protocol\n\nfrom upstream import p\n\n"
            "class FlextSampleProtocols(p):\n"
            + header
            + "        pass\n\np = FlextSampleProtocols\n\n"
            + '__all__ = ["FlextSampleProtocols", "p"]\n',
        )

        service = u.Tests.create_lazy_init_service(root)
        family = u.Infra.facade_family_declared_by(facade.name)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        updated = tm.not_none(u.Infra.render_utility_facade(package, family="p"))
        self._write(facade, updated)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=updated)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import p\n"
                        "from flext_sample._protocols import PayloadOwner\n"
                        "class Value:\n    value = 'payload'\n"
                        "class Missing:\n    pass\n"
                        "assert p.Sample.Payload is PayloadOwner.Payload\n"
                        "assert isinstance(Value(), p.Sample.Payload)\n"
                        "assert not isinstance(Missing(), p.Sample.Payload)\n"
                        "print('protocol-proven')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="protocol-proven")

    @staticmethod
    def test_codegen_models_are_usable_through_the_composed_facade() -> None:
        """Consume both codegen families through the actual generated namespace."""
        context = m.Infra.ModuleSkeletonRenderContext(
            class_name="GeneratedPayload",
            base_class="PayloadBase",
            base_module="fixture_base",
            docstring="Generated payload fixture.",
        )
        tm.that(
            m.Infra.ModuleSkeletonRenderContext.model_validate(context.model_dump()),
            eq=context,
        )

    @staticmethod
    def test_process_options_is_usable_through_the_inherited_public_model() -> None:
        """The real process producer exposes its payload through the model MRO."""
        payload = b"  process input\n"
        environment = {"FLEXT_PROCESS_FIXTURE": "child value"}
        options = m.Cli.ProcessOptions(env=environment, input_data=payload)

        tm.that(options.input_data, eq=payload)
        tm.that(options.env, eq=environment)
        tm.that(
            m.Cli.ProcessOptions.model_validate(options.model_dump()),
            eq=options,
        )

    def test_model_projection_preserves_inherited_family_order_at_runtime(
        self,
        tmp_path: Path,
    ) -> None:
        """Declared model owners compose before any consumer requests their payload."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        self._write(package / "__init__.py", "from .models import m\n")
        for module, owner, payload in (
            ("render", "RenderOwner", "RenderPayload"),
            ("toolchain", "ToolchainOwner", "ToolchainPayload"),
            ("extra", "ExtraOwner", "ExtraPayload"),
        ):
            self._write(
                package / "_models" / f"{module}.py",
                f"class {owner}:\n    class {payload}:\n        pass\n"
                f"__all__ = ['{owner}']\n",
            )
        self._write(
            package / "_models" / "_codegen" / "base.py",
            "from ..render import RenderOwner\n"
            "from ..toolchain import ToolchainOwner\n"
            "class CodegenOwner(ToolchainOwner, RenderOwner):\n    pass\n"
            "__all__ = ['CodegenOwner']\n",
        )
        facade = package / "models.py"
        self._write(
            facade,
            "from ._models._codegen.base import CodegenOwner\n"
            "class Facade:\n    class Sample(CodegenOwner):\n        pass\n"
            "m = Facade\n__all__ = ['Facade', 'm']\n",
        )
        consumer = package / "consumer.py"
        self._write(
            consumer,
            "from flext_sample import m\n"
            "m.Sample.RenderPayload()\n"
            "m.Sample.ToolchainPayload()\n"
            "completed = True\n",
        )
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        entrypoint = root / "consume.py"
        self._write(
            entrypoint,
            "from flext_sample.consumer import completed\n"
            "from flext_sample import m\nm.Sample.ExtraPayload()\nassert completed\n",
        )
        result = tm.ok(
            u.Cli.run_raw(
                [sys.executable, str(entrypoint)],
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stderr or result.stdout,
        )
        tm.that(u.Infra.render_utility_facade(package, family="m"), eq=rendered)
