"""Public evidence for utility-facade behavior relocation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import MutableMapping
from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, tm, u
from tests.unit.codegen._utility_facade_projection.publication import (
    UtilityFacadePublication,
)


class UtilityFacadeBehavior(UtilityFacadePublication):
    """Exercise behavior relocation and public facade dispatch."""

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
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        f"from {package.name}.services import ServiceRuntime; "
                        "assert u.Domain.Target('client-value').read() "
                        "== 'client-value'; "
                        "assert u.Domain.upstream_value() == 'upstream-value'; "
                        "assert not hasattr(u.Domain, 'create'); "
                        "print(ServiceRuntime.create('service-value'))"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="service-value")

    @staticmethod
    def _behavior_package(
        package: Path,
        value_type: str,
    ) -> MutableMapping[Path, str]:
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
        sources: MutableMapping[Path, str],
        *,
        relocated: bool,
    ) -> MutableMapping[Path, str]:
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
            tm.ok(len(edits) > 0)
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
            "else:\n    tm.reject('foreign behavior adopted')\n"
            if relation == "foreign-only"
            else f"assert consumer.first_call() == "
            f"{'7' if relation == 'isolated' else repr('7')}\n"
        )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "import consumer\nfrom flext_tests import tm\n"
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
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}._decorators.consumer import consume; "
                        f"assert "
                        f"consume() == 'facade'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)

    @pytest.mark.parametrize(
        ("runtime_source", "facade_source", "closing_checks", "relocation_fragments"),
        [
            pytest.param(
                (
                    "from {package} import t\n"
                    "class Runtime:\n"
                    "    @staticmethod\n"
                    "    def parse(value):\n"
                    "        first = t.value_adapter().validate_python(value)\n"
                    "        return t.value_adapter().validate_python(first)\n"
                    "def shadowed(t):\n    return t.value_adapter()\n"
                    "__all__ = ['Runtime']\n"
                ),
                (
                    "from {package}.{family}.runtime import Runtime\n"
                    "class Utilities(Runtime):\n    pass\n"
                    "u = Utilities\n__all__ = ['Utilities', 'u']\n"
                ),
                (
                    "assert u.parse('7') == 7; "
                    "assert u.value_adapter().validate_python('8') == 8\n"
                ),
                (
                    "from {package}.{family}.adapter import AdapterOwner",
                    "return t.value_adapter()",
                ),
                id="relocated-staticmethod-runtime",
            ),
            pytest.param(
                (
                    "class Runtime:\n"
                    "    @classmethod\n"
                    "    def parse(cls, value):\n"
                    "        first = cls.value_adapter().validate_python(value)\n"
                    "        return cls.value_adapter().validate_python(first)\n"
                    "    @staticmethod\n"
                    "    def shadowed(t):\n"
                    "        return t.value_adapter()\n"
                    "__all__ = ['Runtime']\n"
                ),
                (
                    "from {package}.{family} import Runtime\n"
                    "class Utilities(Runtime):\n    pass\n"
                    "u = Utilities\n__all__ = ['Utilities', 'u']\n"
                ),
                (
                    "assert u.parse('7') == 7; "
                    "assert u.value_adapter().validate_python('8') == 8; "
                    "assert u.shadowed(u).validate_python('9') == 9\n"
                ),
                (),
                id="declared-classmethod-runtime",
            ),
        ],
    )
    def test_behavior_roundtrip_keeps_bootstrap_lower_dependency(
        self,
        tmp_path: Path,
        runtime_source: str,
        facade_source: str,
        closing_checks: str,
        relocation_fragments: tuple[str, ...],
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
            runtime: runtime_source.format(package=package.name, family=owners.name),
            facade: facade_source.format(package=package.name, family=owners.name),
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
        for fragment in relocation_fragments:
            tm.that(
                proposed[runtime],
                has=fragment.format(package=package.name, family=owners.name),
            )
        for path, source in proposed.items():
            self._write(path, source)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        f"import runpy; runpy.run_path({str(consumer)!r}); "
                        "from pydantic import ValidationError; "
                        "from flext_tests import tm; "
                        + closing_checks
                        + "try:\n    u.parse([])\n"
                        "except ValidationError:\n    print('rejected')\n"
                        "else:\n    tm.reject('invalid payload accepted')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout, has="rejected")

    @pytest.mark.parametrize(
        ("runtime_source", "facade_source"),
        [
            pytest.param(
                (
                    "from {package}.{directory}.adapter import AdapterOwner\n"
                    "class Runtime:\n    @staticmethod\n    def parse(value):\n"
                    "        return AdapterOwner.value_adapter()"
                    ".validate_python(value)\n"
                    "__all__ = ['Runtime']\n"
                ),
                (
                    "from {package}.{directory}.runtime import Runtime\n"
                    "class Utilities:\n    class Domain(Runtime):\n        pass\n"
                    "u = Utilities\n__all__ = ['Utilities', 'u']\n"
                ),
                id="direct-adapter-runtime",
            ),
            pytest.param(
                (
                    "class Runtime:\n    @classmethod\n    def parse(cls, value):\n"
                    "        return cls.value_adapter().validate_python(value)\n"
                    "__all__ = ['Runtime']\n"
                ),
                (
                    "from {package}.{directory} import Runtime\n"
                    "class Utilities:\n    class Domain(Runtime):\n        pass\n"
                    "u = Utilities\n__all__ = ['Utilities', 'u']\n"
                ),
                id="composed-declared-runtime",
            ),
        ],
    )
    def test_nested_facade_projects_lower_owner_runtime_calls(
        self,
        tmp_path: Path,
        runtime_source: str,
        facade_source: str,
    ) -> None:
        """Nested facades project direct and composed runtime rows without a cycle."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / directory / "runtime.py"] = runtime_source.format(
            package=package.name,
            directory=directory,
        )
        facade = package / "utilities.py"
        sources[facade] = facade_source.format(
            package=package.name,
            directory=directory,
        )
        for path, source in sources.items():
            self._write(path, source)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        "assert u.Domain.parse('7') == 7; "
                        "assert u.Domain.value_adapter().validate_python('8') == 8; "
                        "print('nested')"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
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
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u\n"
                        f"from {package.name}.{directory}.runtime import Local\n"
                        "assert u.Domain.parse('7') == 7\n"
                        "assert u.Domain.default_alias() == 'header'\n"
                        "assert u.Domain.header_adapter().validate_python('header') == "
                        "'header'\n"
                        "assert u.Domain.parameter_shadow(Local()) == 'local'\n"
                        "assert u.Domain.local_shadow() == 'local'\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)

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
