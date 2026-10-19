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


type Envelope[Value] = tuple[Order, Value]


class Shipment(m.FrozenModel):
    """A validated shipment referencing its order."""

    order: Order | None = m.Field(default=None, description="Shipped order.")
    envelope: Envelope[str] | None = m.Field(default=None, description="Typed envelope.")


class Inventory(m.BaseModel):
    """A mutable inventory count."""

    quantity: int = m.Field(default=1, description="Available units.")
    sku: str = m.Field(default="item", frozen=True, description="Fixed item.")


type ShipmentPayload = Shipment
type Payload = Order | ShipmentPayload


class DemoMemberModels(m):
    """Member models container."""

    class DemoMember:
        """The member's public model namespace."""

        Order = Order
        Shipment = Shipment
        Inventory = Inventory
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
    manifest = root / c.PYPROJECT_FILENAME
    manifest.write_text(
        manifest.read_text(encoding=c.DEFAULT_ENCODING).replace(
            "[project]\n", '[project]\ndependencies = ["flext-core"]\n'
        )
        + f'\n[dependency-groups]\ncodegen = ["{u.Tests.flext_source()}"]\n',
        encoding=c.DEFAULT_ENCODING,
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
    u.Tests.copy_tracked_mise_seeds(root)
    u.Tests.run_lazy_init(root)
    return root


def _probe(
    root: t.DirectoryPath,
    script: str = "tm.ok(service.execute())\n",
    *,
    consumer: str = (
        "from demo_member import m, p\n"
        'assert isinstance(m.DemoMember.Order(sku="a"), p.DemoMember.Order)\n'
        "assert callable(p.DemoMember.ManualPort.bind)\n"
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


def test_transitive_model_dependency_is_a_structural_contract(
    member_root: t.DirectoryPath,
) -> None:
    """An indirectly referenced field resolves through the generated public port."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        "from demo_member import p\n"
        "def ship(value: p.DemoMember.Shipment) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        'assert get_type_hints(p.DemoMember.Shipment.order.fget)["return"] '
        "== p.DemoMember.Order | None\n"
        'assert isinstance(m.DemoMember.Order(sku="nested"), p.DemoMember.Order)\n',
    )


def test_mutable_fields_and_frozen_fields_retain_public_contract(
    member_root: t.DirectoryPath,
) -> None:
    """Writable attributes and frozen accessors match the model's native fields."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        "from demo_member import p\n"
        "def count(value: p.DemoMember.Inventory) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "contract = p.DemoMember.Inventory\n"
        'assert get_type_hints(contract)["quantity"] is int\n'
        'assert get_type_hints(contract.sku.fget)["return"] is str\n'
        "value = m.DemoMember.Inventory()\n"
        "value.quantity = 5\n"
        "assert value.quantity == 5 and isinstance(value, contract)\n"
        'assert value.model_dump()["quantity"] == 5\n',
    )


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


def test_authored_model_projection_transfers_without_removing_operational_ports(
    member_root: t.DirectoryPath,
) -> None:
    """The native transfer replaces incomplete data while retaining real ports."""
    package = member_root / "src" / MEMBER
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS + "\n\nclass Order(Protocol):\n"
        '    """An incomplete authored model-shaped projection."""\n'
        "    sku: str\n",
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("import ManualPort", "import ManualPort, Order").replace(
            "ManualPort = ManualPort", "ManualPort = ManualPort\n        Order = Order"
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "from demo_member._protocols.manual_ports import ManualPort\n"
        "assert p.DemoMember.ManualPort is ManualPort\n"
        "assert callable(ManualPort.bind)\n"
        'assert get_type_hints(p.DemoMember.Order.quantity.fget)["return"] is int\n'
        'assert isinstance(m.DemoMember.Order(sku="transferred"), p.DemoMember.Order)\n',
    )


def test_generation_uses_current_source_not_cached_model_classes(
    member_root: t.DirectoryPath,
) -> None:
    """A previously imported class cannot override the authenticated source view."""
    _probe(
        member_root,
        "from demo_member import m\n"
        "cached = m.DemoMember.Order\n"
        'assert cached.model_fields["sku"].annotation is str\n'
        'domain = root / "src/demo_member/_models/domain.py"\n'
        'domain.write_text(domain.read_text().replace("sku: str", "sku: bytes"))\n'
        "tm.ok(service.execute())\n"
        'assert cached.model_fields["sku"].annotation is str\n',
        consumer="from demo_member import p\n"
        'assert get_type_hints(p.DemoMember.Order.sku.fget)["return"] is bytes\n',
    )


def test_concrete_model_alias_is_rewired_without_retiring_the_schema(
    member_root: t.DirectoryPath,
) -> None:
    """Replacing a leaked m alias must preserve the original Pydantic model."""
    package = member_root / "src" / MEMBER
    (package / "protocols.py").write_text(
        PROTOCOLS.replace(
            "from flext_core import p",
            "from flext_core import p\nfrom demo_member import m",
        ).replace(
            "ManualPort = ManualPort",
            "ManualPort = ManualPort\n        Order = m.DemoMember.Order",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "assert p.DemoMember.Order is not m.DemoMember.Order\n"
        'value = m.DemoMember.Order(sku="retained-schema")\n'
        "assert isinstance(value, p.DemoMember.Order)\n"
        'assert value.model_dump()["sku"] == "retained-schema"\n',
    )


def test_transferred_consumer_binds_the_canonical_public_protocol_facade(
    member_root: t.DirectoryPath,
) -> None:
    """The final consumer imports public p and accepts the real model at runtime."""
    package = member_root / "src" / MEMBER
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS + "\n\nclass Order(Protocol):\n"
        '    """An incomplete legacy data projection."""\n'
        "    sku: str\n",
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("import ManualPort", "import ManualPort, Order").replace(
            "ManualPort = ManualPort", "ManualPort = ManualPort\n        Order = Order"
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        "def ship(order: p.DemoMember.Order) -> str:\n"
        "    return order.sku\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import consumer, m, p\n"
        "assert consumer.p is p\n"
        'assert get_type_hints(consumer.ship)["order"] is p.DemoMember.Order\n'
        'value = m.DemoMember.Order(sku="public-boundary")\n'
        "assert isinstance(value, p.DemoMember.Order)\n"
        'assert consumer.ship(value) == "public-boundary"\n',
    )


def test_operational_port_model_annotations_use_the_projected_contract(
    member_root: t.DirectoryPath,
) -> None:
    """Native annotation rewiring retains the authored operational interface."""
    package = member_root / "src" / MEMBER
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS.replace(
            "from typing import Protocol",
            "from typing import Protocol\nfrom demo_member import m",
        ).replace(
            "def bind(self) -> bool:",
            "def bind(self, value: m.DemoMember.Order) -> m.DemoMember.Order:",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        "def bind(port: p.DemoMember.ManualPort) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "from demo_member._protocols.manual_ports import ManualPort\n"
        "assert p.DemoMember.ManualPort is ManualPort\n"
        "hints = get_type_hints(ManualPort.bind)\n"
        'assert hints["value"] is p.DemoMember.Order\n'
        'assert hints["return"] is p.DemoMember.Order\n'
        'assert isinstance(m.DemoMember.Order(sku="port"), hints["value"])\n',
    )


def test_distinct_same_named_models_cannot_silently_collapse_a_union(
    member_root: t.DirectoryPath,
) -> None:
    """Distinct native Item identities fail explicitly instead of losing a leaf."""
    domain = member_root / "src" / MEMBER / "_models/domain.py"
    source = domain.read_text(encoding=c.DEFAULT_ENCODING)
    source = source.replace(
        "type Payload = Order | ShipmentPayload",
        'class Left:\n    class Item(m.FrozenModel):\n        left: str = m.Field(description="Left value.")\n'
        'class Right:\n    class Item(m.FrozenModel):\n        right: int = m.Field(description="Right value.")\n'
        "type Payload = Left.Item | Right.Item",
    ).replace(
        "Payload = Payload",
        "Payload = Payload\n        Left = Left\n        Right = Right",
    )
    domain.write_text(source, encoding=c.DEFAULT_ENCODING)
    _probe(
        member_root,
        "result = service.execute()\n"
        'assert result.failure and "competing generated protocol member identities" in result.error\n',
        consumer="",
    )


def test_specialized_alias_closes_over_its_model_payload(
    member_root: t.DirectoryPath,
) -> None:
    """An Envelope[str] field retains its source Order dependency and argument."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        "from demo_member import p\n"
        "def ship(value: p.DemoMember.Shipment) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import p\n"
        'assert get_type_hints(p.DemoMember.Shipment.envelope.fget)["return"] '
        "== tuple[p.DemoMember.Order, str] | None\n",
    )


@pytest.mark.parametrize(
    ("imports", "alias", "signature", "message"),
    [
        (
            "from typing import Any\n",
            "type Weak = Any\n",
            "value: Weak",
            "forbidden generated protocol annotation",
        ),
        ("", "", "value", "untyped signature"),
    ],
)
def test_weak_or_untyped_method_contracts_fail_before_publication(
    member_root: t.DirectoryPath,
    imports: str,
    alias: str,
    signature: str,
    message: str,
) -> None:
    """Weak aliases and untyped parameters are not emitted as structural ports."""
    domain = member_root / "src" / MEMBER / "_models/domain.py"
    source = domain.read_text(encoding=c.DEFAULT_ENCODING)
    source = source.replace(
        "from flext_core import m, t", f"{imports}from flext_core import m, t\n{alias}"
    )
    source = source.replace(
        '    quantity: int = m.Field(default=1, description="Number of units ordered.")',
        '    quantity: int = m.Field(default=1, description="Number of units ordered.")\n'
        f"    def inspect(self, {signature}) -> str: ...",
    )
    domain.write_text(source, encoding=c.DEFAULT_ENCODING)
    _probe(
        member_root,
        "from pytest import raises\n"
        f"with raises(TypeError, match={message!r}):\n"
        "    service.execute()\n",
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
