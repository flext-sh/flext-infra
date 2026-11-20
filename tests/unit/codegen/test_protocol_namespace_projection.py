"""Execute generated protocol namespaces without changing real interfaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from textwrap import indent
from typing import Literal

from flext_infra.gates import FlextInfraGatesPyrefly
from tests import c, m, p, tm, u


class TestsFlextInfraProtocolNamespaceProjection:
    """Check namespace MRO and nested contracts through a fresh public import."""

    @staticmethod
    @c.Tests.MARK.parametrize("nested", [False, True])
    @c.Tests.MARK.parametrize("aliased", [False, True])
    def test_protocol_marker_beside_concrete_parts_is_refused(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        *,
        nested: bool,
        aliased: bool,
    ) -> None:
        """Refuse a Protocol-marked namespace composed from concrete parts."""
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
            tm.ok(
                u.Cli.atomic_write_text_file(
                    path, source, durability=c.Cli.WriteDurability.SCRATCH
                )
            )
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "import pytest\n"
            "with pytest.raises(TypeError, match="
            "'Protocols can only inherit from other protocols'):\n"
            f"    from {package.name}.protocols import p\n",
            cwd=root,
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        # The source is corrected, never compensated (ADR-018 rules 5 and 6).
        error = tm.fail(
            tm.not_none(u.Infra.render_utility_facade(package, family="p")),
            has="declares Protocol beside non-protocol parts",
        )
        tm.that(error, has="FirstPart")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)), eq=before
        )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize("family", ["p", "m"])
    @c.Tests.MARK.parametrize("annotated", [False, True])
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
                # The generator never strips an authored Protocol marker
                # (ADR-018 rule 6): both families compose the parts directly.
                + "class Facade:\n    class Namespace(FirstPart, SecondPart):\n"
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
            tm.ok(
                u.Cli.atomic_write_text_file(
                    path, source, durability=c.Cli.WriteDurability.SCRATCH
                )
            )
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family=family))
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade, rendered, durability=c.Cli.WriteDurability.SCRATCH
            )
        )
        tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family=family)),
            eq=rendered,
        )
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
                + '\n[tool.pyrefly]\nproject-includes = ["src"]\n',
                durability=c.Cli.WriteDurability.SCRATCH,
            )
        )
        # The gate resolves pyrefly from the checkout's own environment.
        u.Tests.provision_checkout(root)
        context = m.Infra.GateContext(
            repository_root=root, reports_dir=root / ".reports"
        )
        context.reports_dir.mkdir(parents=True, exist_ok=True)
        checked = FlextInfraGatesPyrefly(root).check(root, context)
        tm.that(checked.result.passed, eq=True, msg=checked.raw_output)

    @staticmethod
    @c.Tests.MARK.parametrize("family", ["p", "m"])
    @c.Tests.MARK.parametrize("conflict", ["renamed", "losing", "annotation"])
    @c.Tests.MARK.parametrize("annotated", [False, True])
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
            tm.ok(
                u.Cli.atomic_write_text_file(
                    path, source, durability=c.Cli.WriteDurability.SCRATCH
                )
            )
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        projected = tm.not_none(u.Infra.render_utility_facade(package, family=family))
        if conflict == "renamed":
            # Unrelated parts both declaring an unbound member collide (7099d8c516).
            tm.fail(projected, has="declares 'Payload' in unrelated parts")
        else:
            # A member the namespace binds itself shadows the parts and survives.
            declared = (
                f": type[{annotation}]" if annotated or conflict == "annotation" else ""
            )
            tm.that(tm.ok(projected), has=f"{target}{declared} = {value}")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)), eq=before
        )

    @staticmethod
    @c.Tests.MARK.parametrize("marker_base", [False, True])
    def test_alias_only_namespace_is_not_an_interface(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        *,
        marker_base: bool,
    ) -> None:
        """Keep protocol aliases verbatim; refuse a Protocol class as a part."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.PROTOCOLS_PY)
        facade = package / c.Infra.PROTOCOLS_PY
        files = {
            package / c.Infra.INIT_PY: "",
            # A Protocol class is never a facade part (ADR-018 rule 5, cba6c33ce6).
            package / "markers.py": (
                "from typing import Protocol\n"
                "class Marker(Protocol): pass\n"
                "__all__ = ['Marker']\n"
            ),
            package / family.directory / "base.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class Contracts:\n"
                "    @runtime_checkable\n"
                "    class Payload(Protocol):\n"
                "        value: str\n"
                "__all__ = ['Contracts']\n"
            ),
            facade: (
                "from typing import Protocol, runtime_checkable\n"
                f"from {package.name}.{family.directory} import Contracts\n"
                f"from {package.name}.markers import Marker\n"
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
            tm.ok(
                u.Cli.atomic_write_text_file(
                    path, source, durability=c.Cli.WriteDurability.SCRATCH
                )
            )
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        if marker_base:
            # A Protocol class is never a facade part (ADR-018 rule 5): the
            # lazy initializer refuses the composed facade.
            tm.ok(
                u.Cli.atomic_write_text_file(
                    facade,
                    tm.ok(
                        tm.not_none(u.Infra.render_utility_facade(package, family="p"))
                    ),
                    durability=c.Cli.WriteDurability.SCRATCH,
                )
            )
            tm.fail(
                u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)),
                has="cannot be a stand-in",
            )
            return
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="p"))
        )
        tm.that(
            sum(
                alias.name == "Contracts"
                for node in ast.walk(ast.parse(rendered))
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            ),
            eq=1,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade, rendered, durability=c.Cli.WriteDurability.SCRATCH
            )
        )
        tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="p")), eq=rendered
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        # The authored Protocol marker is propagated, never compensated
        # (ADR-018 rule 6); the alias keeps the original protocol identity.
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from typing import is_protocol\n"
            f"from {package.name} import p\n"
            f"from {package.name}.{family.directory}.base import Contracts\n"
            "assert is_protocol(p.Namespace)\n"
            "assert p.Namespace.Payload is Contracts.Payload\n"
            "assert is_protocol(p.Namespace.Payload)\n"
            "class Value:\n"
            "    value = 'payload'\n"
            "assert isinstance(Value(), p.Namespace.Payload)\n",
            cwd=root,
        )

    @staticmethod
    def test_override_alias_follows_native_c3_order(tmp_path: Path) -> None:
        """An alias that overrides the C3 owner stays; ``Generic`` is no part."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
        facade = package / c.Infra.MODELS_PY
        sources = {
            package / c.Infra.INIT_PY: "",
            package / directory / "root.py": (
                "class RootPart:\n    class Member:\n        pass\n"
                "__all__ = ['RootPart']\n"
            ),
            package / directory / "left.py": (
                f"from {package.name}.{directory}.root import RootPart\n"
                "class LeftPart(RootPart):\n    pass\n__all__ = ['LeftPart']\n"
            ),
            package / directory / "right.py": (
                f"from {package.name}.{directory}.root import RootPart\n"
                "class RightPart(RootPart):\n    class Member:\n        pass\n"
                "__all__ = ['RightPart']\n"
            ),
            facade: (
                f"from {package.name}.{directory}.left import LeftPart\n"
                f"from {package.name}.{directory}.right import RightPart\n"
                f"from {package.name}.{directory}.root import RootPart\n"
                "class Facade:\n    class Namespace(LeftPart, RightPart):\n"
                "        Member = RootPart.Member\n"
                "m = Facade\n__all__ = ['Facade', 'm']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(
                u.Cli.atomic_write_text_file(
                    path, source, durability=c.Cli.WriteDurability.SCRATCH
                )
            )
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))
        service = u.Tests.create_lazy_init_service(root)
        service.module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        # C3 resolves Member to RightPart.Member, so the authored alias is an
        # override, never a redundant binding.
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        )
        tm.that(rendered, has="Member = RootPart.Member")
