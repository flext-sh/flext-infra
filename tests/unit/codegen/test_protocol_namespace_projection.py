"""Execute generated protocol namespaces without changing real interfaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from textwrap import indent
from typing import Literal

import pytest

from flext_infra.gates import FlextInfraMypyGate, FlextInfraPyreflyGate
from tests import c, m, p, tm, u


class TestsFlextInfraProtocolNamespaceProjection:
    """Check namespace MRO and nested contracts through a fresh public import."""

    @staticmethod
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize("aliased", [False, True])
    def test_namespace_parts_preserve_real_protocols_and_converge(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        *,
        nested: bool,
        aliased: bool,
    ) -> None:
        """Remove namespace-only markers, not interfaces or their runtime checks."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.PROTOCOLS_PY)
        facade = package / c.Infra.PROTOCOLS_PY
        marker = "Interface" if aliased else "Protocol"
        checked = "checked" if aliased else "runtime_checkable"
        imports = (
            "from typing import Protocol as Interface, runtime_checkable as checked\n"
            if aliased
            else "from typing import Protocol, runtime_checkable\n"
        )
        declaration = (
            f"@{checked}\n"
            f"class {'Namespace' if nested else 'Facade'}"
            f"(FirstPart, SecondPart, {marker}):\n"
            f"    @{checked}\n"
            f"    class Local({marker}):\n"
            "        local: str\n"
            f"    @{checked}\n"
            f"    class Other({marker}):\n"
            "        other: int\n"
        )
        if nested:
            declaration = "class Facade:\n" + indent(declaration, "    ")
        files = {
            package / c.Infra.INIT_PY: "",
            package / family.directory / "first.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class FirstPart:\n"
                "    @runtime_checkable\n"
                "    class Payload(Protocol):\n"
                "        value: str\n"
                "__all__ = ['FirstPart']\n"
            ),
            package / family.directory / "second.py": (
                "class SecondPart:\n"
                "    marker = 'second-part'\n"
                "__all__ = ['SecondPart']\n"
            ),
            facade: (
                imports
                + f"from {package.name}.{family.directory}.first import FirstPart\n"
                + f"from {package.name}.{family.directory}.second import SecondPart\n"
                + declaration
                + "p = Facade\n"
                + "__all__ = ['Facade', 'p']\n"
            ),
        }
        for path, source in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "import pytest\n"
            "with pytest.raises(TypeError, match="
            "'Protocols can only inherit from other protocols'):\n"
            f"    from {package.name}.protocols import p\n",
            cwd=root,
        )
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="p"))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        namespace = "p.Namespace" if nested else "p"
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from typing import Protocol, get_type_hints, is_protocol\n"
            f"from {package.name} import p\n"
            f"namespace = {namespace}\n"
            "assert not is_protocol(namespace)\n"
            "assert Protocol not in namespace.__mro__\n"
            "assert namespace.marker == 'second-part'\n"
            "assert tuple(base.__name__ for base in namespace.__bases__) == "
            "('FirstPart', 'SecondPart')\n"
            "assert is_protocol(namespace.Payload)\n"
            "assert is_protocol(namespace.Local)\n"
            "assert is_protocol(namespace.Other)\n"
            "class Value:\n"
            "    value = 'payload'\n"
            "    local = 'local'\n"
            "    other = 1\n"
            "assert isinstance(Value(), namespace.Payload)\n"
            "assert isinstance(Value(), namespace.Local)\n"
            "assert isinstance(Value(), namespace.Other)\n"
            "assert not isinstance(None, namespace.Payload)\n"
            "def consume(value: namespace.Payload) -> namespace.Local:\n"
            "    return value\n"
            "assert get_type_hints(consume) == "
            "{'value': namespace.Payload, 'return': namespace.Local}\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("family", ["p", "m"])
    @pytest.mark.parametrize("annotated", [False, True])
    def test_class_aliases_project_native_owners_for_typed_consumers(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        family: Literal["p", "m"],
        *,
        annotated: bool,
    ) -> None:
        """Plain and annotated aliases become inherited types, not new identities."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = c.Infra.PROTOCOLS_PY if family == "p" else c.Infra.MODELS_PY
        directory = u.Infra.facade_family_declared_by(module).directory
        facade = package / module
        imports = "from typing import Protocol\n" if family == "p" else ""
        base = "(Protocol)" if family == "p" else ""
        aliases = "".join(
            f"        {payload}"
            + (f": type[{owner}.{payload}]" if annotated else "")
            + f" = {owner}.{payload}\n"
            for owner, payload in (("FirstPart", "Payload"), ("SecondPart", "Reply"))
        )
        sources = {
            package / c.Infra.INIT_PY: "",
            package / directory / "first.py": (
                imports + f"class FirstPart:\n    class Payload{base}:\n"
                "        value: str = 'payload'\n"
                "__all__ = ['FirstPart']\n"
            ),
            package / directory / "second.py": (
                imports + f"class SecondPart:\n    class Reply{base}:\n"
                "        value: str = 'reply'\n"
                "__all__ = ['SecondPart']\n"
            ),
            package / "external.py": (
                "class External:\n    class Payload:\n        pass\n"
                "__all__ = ['External']\n"
            ),
            facade: (
                imports
                + f"from {package.name}.{directory}.first import FirstPart\n"
                + f"from {package.name}.{directory}.second import SecondPart\n"
                + f"from {package.name}.external import External\n"
                + "class Facade:\n    class Namespace"
                + ("(Protocol):\n" if family == "p" else "(FirstPart, SecondPart):\n")
                + aliases
                + "        Unrelated: type[External.Payload] = External.Payload\n"
                + f"{family} = Facade\n__all__ = ['Facade', '{family}']\n"
            ),
            package / "consumer.py": (
                f"from {package.name}.{facade.stem} import Facade\n"
                f"from {package.name}.{directory}.first import FirstPart\n"
                "def consume(value: Facade.Namespace.Payload) -> FirstPart.Payload:\n"
                "    return value\n"
                "def produce(value: FirstPart.Payload) -> Facade.Namespace.Payload:\n"
                "    return value\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family=family))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.that(u.Infra.render_utility_facade(package, family=family), eq=rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from typing import get_type_hints, is_protocol\n"
            f"from {package.name} import {family} as public\n"
            f"from {package.name}.{directory} import FirstPart, SecondPart\n"
            f"from {package.name}.external import External\n"
            f"from {package.name}.consumer import consume, produce\n"
            "namespace = public.Namespace\n"
            "assert namespace.Payload is FirstPart.Payload\n"
            "assert namespace.Reply is SecondPart.Reply\n"
            "assert FirstPart in namespace.__mro__\n"
            "assert SecondPart in namespace.__mro__\n"
            "assert 'Payload' not in vars(namespace)\n"
            "assert 'Reply' not in vars(namespace)\n"
            "assert namespace.Unrelated is External.Payload\n"
            "assert get_type_hints(namespace)['Unrelated'] == type[External.Payload]\n"
            "assert get_type_hints(consume) == "
            "{'value': FirstPart.Payload, 'return': FirstPart.Payload}\n"
            "assert get_type_hints(produce) == get_type_hints(consume)\n"
            "assert not is_protocol(namespace)\n"
            f"assert is_protocol(namespace.Payload) is {family == 'p'}\n",
            cwd=root,
        )
        pyproject = root / c.PYPROJECT_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                pyproject,
                tm.ok(u.Cli.files_read_text(pyproject))
                + '\n[tool.mypy]\n[tool.pyrefly]\nproject-includes = ["src"]\n',
            )
        )
        context = m.Infra.GateContext(
            repository_root=root, reports_dir=root / ".reports"
        )
        context.reports_dir.mkdir(parents=True, exist_ok=True)
        for gate in (FlextInfraMypyGate(root), FlextInfraPyreflyGate(root)):
            checked = gate.check(root, context)
            tm.that(checked.result.passed, eq=True, msg=checked.raw_output)

    @staticmethod
    @pytest.mark.parametrize("family", ["p", "m"])
    @pytest.mark.parametrize("conflict", ["renamed", "losing", "annotation"])
    @pytest.mark.parametrize("annotated", [False, True])
    def test_class_aliases_reject_unproven_owner_identity(
        tmp_path: Path,
        family: Literal["p", "m"],
        conflict: str,
        *,
        annotated: bool,
    ) -> None:
        """Do not erase renamed bindings, losing owners or contradictory annotations."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = c.Infra.PROTOCOLS_PY if family == "p" else c.Infra.MODELS_PY
        directory = u.Infra.facade_family_declared_by(module).directory
        facade = package / module
        imports = "from typing import Protocol\n" if family == "p" else ""
        base = "(Protocol)" if family == "p" else ""
        target = "Renamed" if conflict == "renamed" else "Payload"
        value = "SecondPart.Payload" if conflict == "losing" else "FirstPart.Payload"
        annotation = "SecondPart.Payload" if conflict == "annotation" else value
        sources = {
            package / c.Infra.INIT_PY: "",
            **{
                package / directory / f"{name}.py": (
                    imports + f"class {owner}:\n    class Payload{base}:\n"
                    "        value: str\n"
                    f"__all__ = ['{owner}']\n"
                )
                for name, owner in (("first", "FirstPart"), ("second", "SecondPart"))
            },
            facade: (
                f"from {package.name}.{directory}.first import FirstPart\n"
                f"from {package.name}.{directory}.second import SecondPart\n"
                "class Facade:\n    class Namespace(FirstPart, SecondPart):\n"
                f"        {target}"
                + (
                    f": type[{annotation}]"
                    if annotated or conflict == "annotation"
                    else ""
                )
                + f" = {value}\n"
                + f"{family} = Facade\n__all__ = ['Facade', '{family}']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        with pytest.raises(ValueError, match=r"ambiguous .* class attribute"):
            u.Infra.render_utility_facade(package, family=family)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)), eq=before
        )

    @staticmethod
    @pytest.mark.parametrize("marker_base", [False, True])
    def test_alias_only_namespace_is_not_an_interface(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        *,
        marker_base: bool,
    ) -> None:
        """Keep original protocol types inside a plain namespace of aliases."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.PROTOCOLS_PY)
        facade = package / c.Infra.PROTOCOLS_PY
        files = {
            package / c.Infra.INIT_PY: "",
            package / family.directory / "base.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class Marker(Protocol): pass\n"
                "class Contracts:\n"
                "    @runtime_checkable\n"
                "    class Payload(Protocol):\n"
                "        value: str\n"
                "__all__ = ['Contracts', 'Marker']\n"
            ),
            facade: (
                "from typing import Protocol, runtime_checkable\n"
                f"from {package.name}.{family.directory} import Contracts, Marker\n"
                "class Facade:\n"
                "    @runtime_checkable\n"
                f"    class Namespace({'Marker, ' if marker_base else ''}Protocol):\n"
                "        Payload = Contracts.Payload\n"
                "p = Facade\n"
                "__all__ = ['Facade', 'p']\n"
            ),
        }
        for path, source in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="p"))
        tm.that(
            sum(
                alias.name == "Contracts"
                for node in ast.walk(ast.parse(rendered))
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            ),
            eq=1,
        )
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from typing import is_protocol\n"
            f"from {package.name} import p\n"
            f"from {package.name}.{family.directory}.base import Contracts, Marker\n"
            "assert not is_protocol(p.Namespace)\n"
            f"assert (Marker in p.Namespace.__mro__) is {marker_base!r}\n"
            "assert p.Namespace.Payload is Contracts.Payload\n"
            "assert is_protocol(p.Namespace.Payload)\n"
            "class Value:\n"
            "    value = 'payload'\n"
            "assert isinstance(Value(), p.Namespace.Payload)\n",
            cwd=root,
        )
