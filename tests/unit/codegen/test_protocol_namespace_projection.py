"""Execute generated protocol namespaces without changing real interfaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from textwrap import indent

import pytest

from tests import c, p, tm, u


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
