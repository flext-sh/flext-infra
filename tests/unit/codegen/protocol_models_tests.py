"""Runtime behavior of the generated structural protocol assembly.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys

import pytest

from tests import c, t, u

MEMBER = "demo_member"
ALIAS_CASES: t.VariadicTuple[t.Quad[str, str, str, str]] = (
    ("tags", "t.VariadicTuple[str]", "()", "tuple[str, ...]"),
    ("permuted", "Permuted[int, str]", '("tag", 1)', "tuple[str, int]"),
    ("repeated", "Repeated[int]", "(1, 2)", "tuple[int, int]"),
    ("unused", "Unused[str, int]", "()", "tuple[str, ...]"),
    ("identity", "Identity[str]", '"identity"', "str"),
    ("nested", "Nested[int]", "([1], 1)", "tuple[list[int], int]"),
    ("factory", "type[str]", "str", "type[str]"),
)

MODELS = (
    '''\
"""Demo member models."""


from flext_core import m, t


type Permuted[First, Second] = tuple[Second, First]
type Repeated[Value] = tuple[Value, Value]
type Unused[Value, Ignored] = tuple[Value, ...]
type Identity[Value] = Value
type Nested[Value] = Permuted[Value, list[Value]]


class Order(m.FrozenModel):
    """A validated order."""

    sku: str = m.Field(description="Stock keeping unit of the ordered item.")
    quantity: int = m.Field(default=1, description="Number of units ordered.")
'''
    + "".join(
        f"    {name}: {annotation} = m.Field(default={default}, description={name!r})\n"
        for name, annotation, default, _expected in ALIAS_CASES
    )
    + '''


class Shipment(m.FrozenModel):
    """A validated shipment referencing its order."""

    order: Order | None = m.Field(default=None, description="Shipped order.")


type Payload = Order | Shipment


class DemoMemberModels(m):
    """Member models container."""

    class DemoMember:
        """The member's public model namespace."""

        Order = Order
        Shipment = Shipment
        Payload = Payload


m = DemoMemberModels
__all__ = ["DemoMemberModels", "m"]
'''
)


PROTOCOLS = '''\
"""Demo member protocols container."""

from demo_member._protocols.manual_ports import ManualPort
from flext_core import p

__all__ = ["DemoMemberProtocols", "p"]


class DemoMemberProtocols(p):
    """Member protocols container."""

    class DemoMember:
        """The member's public protocol namespace."""

        ManualPort = ManualPort


p = DemoMemberProtocols
'''

MANUAL_PORTS = '''\
"""Hand-declared ports; the generator never regenerates these."""

from typing import Protocol


class ManualPort(Protocol):
    """A hand-owned structural port."""

    def bind(self) -> bool:
        """Bind the port."""
        ...
'''

CONSUMER = '''\
"""Consumer referencing the member protocols facade."""

from demo_member import p


def ship(order: p.DemoMember.Order) -> p.DemoMember.Payload:
    """Consume the structural contracts."""
    raise NotImplementedError
'''

TYPINGS = '''\
"""Demo member typings container."""


from flext_core import t


class DemoMemberTypes(t):
    """Member typings container."""

    VariadicTuple = t.VariadicTuple


t = DemoMemberTypes
__all__ = ["DemoMemberTypes", "t"]
'''


@pytest.fixture
def member_root(tmp_path: t.DirectoryPath) -> t.DirectoryPath:
    """Populate the shared real-project fixture with this model contract.

    Returns:
        The resulting ``t.DirectoryPath``.

    """
    root, package = u.Tests.create_lazy_init_workspace(
        tmp_path,
        project_name="demo-member",
        package_name=MEMBER,
    )
    (package / "_protocols").mkdir()
    for filename, content in (
        ("models.py", MODELS),
        ("protocols.py", PROTOCOLS),
        ("typings.py", TYPINGS),
        ("consumer.py", CONSUMER),
        ("_protocols/manual_ports.py", MANUAL_PORTS),
    ):
        (package / filename).write_text(content, encoding=c.DEFAULT_ENCODING)
    u.Tests.run_lazy_init(root)
    return root


def _probe(
    root: t.DirectoryPath,
    script: str = "tm.ok(service.execute())\n",
    *,
    consumer: str = (
        "from demo_member import m, p\n"
        'assert isinstance(m.DemoMember.Order(sku="a"), p.DemoMember.Order)\n'
    ),
) -> None:
    """Generate, then exercise the public facade in a separate real interpreter."""
    u.Tests.run_lazy_init_probe(
        "from pathlib import Path\n"
        "from flext_tests import tm\n"
        "from flext_infra.codegen import FlextInfraCodegenProtocolModels\n"
        f"root = Path({str(root)!r})\n"
        "service = FlextInfraCodegenProtocolModels(\n"
        "    repository_root=root, apply_changes=True)\n" + script,
        python_paths=(str(root / c.Infra.DEFAULT_SRC_DIR), *sys.path),
        cwd=root,
    )
    if consumer:
        u.Tests.run_lazy_init_probe(
            "from typing import get_type_hints\n" + consumer,
            python_paths=(str(root / c.Infra.DEFAULT_SRC_DIR), *sys.path),
            cwd=root,
        )


def test_apply_generates_runtime_checkable_contracts(
    member_root: t.DirectoryPath,
) -> None:
    """A generated protocol accepts the public facade's validated model directly."""
    _probe(member_root)


@pytest.mark.parametrize(
    ("field_name", "expected"),
    [(name, expected) for name, _annotation, _default, expected in ALIAS_CASES],
)
def test_generated_annotations_resolve_specialized_aliases(
    member_root: t.DirectoryPath,
    field_name: str,
    expected: str,
) -> None:
    """Public runtime hints retain specialized parameters without free aliases."""
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "protocol = p.DemoMember.Order\n"
        f"accessor = getattr(protocol, {field_name!r})\n"
        f'assert get_type_hints(accessor.fget)["return"] == {expected}\n'
        'assert isinstance(m.DemoMember.Order(sku="alias consumer"), protocol)\n',
    )


def test_apply_is_idempotent(member_root: t.DirectoryPath) -> None:
    """Repeated apply retains every generated byte and check-only succeeds."""
    _probe(
        member_root,
        "tm.ok(service.execute())\n"
        f'generated = root / "src" / {MEMBER!r} / "_protocols"\n'
        "before = "
        '{path: path.read_bytes() for path in generated.glob("generated*.py")}\n'
        "tm.ok(service.execute())\n"
        "assert {path: path.read_bytes() "
        'for path in generated.glob("generated*.py")} == before\n'
        "tm.ok(FlextInfraCodegenProtocolModels(\n"
        "    repository_root=root, apply_changes=False).execute())\n",
    )


def test_check_only_reports_drift(member_root: t.DirectoryPath) -> None:
    """A fresh process detects drift after the canonical model changes."""
    _probe(member_root, "tm.ok(service.execute())\n")
    models_path = member_root / "src" / MEMBER / "models.py"
    models_path.write_text(
        MODELS.replace(
            '    sku: str = m.Field(description="Stock keeping unit of the ordered '
            'item.")',
            '    sku: str = m.Field(description="Stock keeping unit of the ordered '
            'item.")'
            '\n    weight: float = m.Field(default=1.0, description="Drift probe '
            'weight.")',
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        "result = FlextInfraCodegenProtocolModels(\n"
        "    repository_root=root, apply_changes=False).execute()\n"
        'assert result.failure and "drifted" in result.error\n',
        consumer="",
    )


def test_unresolved_reference_fails_typed(member_root: t.DirectoryPath) -> None:
    """A protocol without a corresponding model fails with its exact name."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        CONSUMER + "\n\ndef ghost(port: p.DemoMember.Ghost) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        "result = service.execute()\n"
        'assert result.failure and "Ghost" in result.error\n',
        consumer="",
    )


@pytest.mark.parametrize(
    "source_root", ["tests", "scripts", "examples", "workflow_tools"]
)
@pytest.mark.parametrize(
    "annotation", ["ports.DemoMember.Order", '"ports.DemoMember.Order"']
)
def test_discovery_uses_real_references_in_every_root(
    member_root: t.DirectoryPath,
    source_root: str,
    annotation: str,
) -> None:
    """Aliases work; documentation and shadowed names select no contracts."""
    (member_root / "src" / MEMBER / "consumer.py").unlink()
    source = member_root / source_root
    source.mkdir()
    (source / "consumer.py").write_text(
        '"""ports.DemoMember.Ghost is documentation."""\n'
        "from demo_member import p as ports\n"
        f"def ship(order: {annotation}) -> None: ...\n"
        "def shadow(ports: str) -> str: return ports.strip()\n"
        "# ports.DemoMember.Ghost is documentation.\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(member_root)
