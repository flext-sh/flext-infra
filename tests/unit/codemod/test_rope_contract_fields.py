"""Real Pydantic field-factory evidence for native Rope contract migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, p, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeFieldContracts:
    """Preserve Pydantic field factories, validation effects and runtime values."""

    @staticmethod
    @pytest.mark.parametrize(
        ("declaration", "changes"),
        [
            ("values: list[str] = Field(default_factory=list)", False),
            ("values: dict[str, list[int]] = Field(default_factory=dict)", False),
            ("values: Meta[list[str], Field(default_factory=list)]", True),
            ("values: Meta[int, Field(default=3)]", True),
            ("values: set[str] = Field(default_factory=set)", False),
            ("values: tuple[str, ...] = Field(default_factory=tuple)", False),
            ("values: frozenset[str] = Field(default_factory=frozenset)", False),
            ("values: list[str] = Field(default_factory=list, description='d')", False),
            (
                (
                    "values: dict[str, list[int]] = "
                    "Field(default_factory=dict, description='d')"
                ),
                False,
            ),
            (
                (
                    "values: Meta[list[str], Field(description='d')] = "
                    "Field(default_factory=list)"
                ),
                False,
            ),
            (
                (
                    "values: Meta[dict[str, list[int]], Field(min_length=0)] = "
                    "Field(default_factory=dict)"
                ),
                False,
            ),
        ],
    )
    def test_real_defaults_preserve_runtime_and_converge(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        declaration: str,
        *,
        changes: bool,
    ) -> None:
        """Native Rope retains independent instances and public JSON roundtrips."""
        source = (
            "from typing import Annotated as Meta\n"
            "from pydantic import BaseModel, Field\n"
            "class Payload(BaseModel):\n"
            f"    {declaration}\n"
            "first, second = Payload(), Payload()\n"
            "if isinstance(first.values, list):\n"
            "    first.values.append('consumer')\n"
            "elif isinstance(first.values, dict):\n"
            "    first.values['consumer'] = [1]\n"
            "restored = Payload.model_validate_json(first.model_dump_json())\n"
            "evidence = (first.model_dump_json(), second.model_dump_json(), "
            "restored.model_dump_json(), "
            "Payload.model_fields['values'].default_factory)\n"
        )
        workspace, path = rope_contract_consumer
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(bool(edits), eq=changes)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        updated = edits[0].updated_source if edits else source
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        after = runpy.run_path(str(path))["evidence"]
        tm.that(after[:3], eq=before[:3])
        if not changes:
            tm.ok(after[3] is before[3])
        tm.that(
            tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=workspace,
                    sources={path: updated},
                )
            ),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "values: list[Domain.Item] = Field(default_factory=list)",
            "values: t.MutableSequenceOf[Domain.Item] = Field(default_factory=list)",
            "values: dict[str, Domain.Item] = Field(default_factory=dict)",
            (
                "values: Annotated[list[Domain.Item], 'metadata'] = "
                "Field(default_factory=list)"
            ),
            (
                "values: Annotated[dict[str, Domain.Item], 'metadata'] = "
                "Field(default_factory=dict)"
            ),
            "values: list[Domain.Item] = Field(default_factory=list, description='d')",
            (
                "values: dict[str, Domain.Item] = "
                "Field(default_factory=dict, description='d')"
            ),
        ],
    )
    def test_own_outer_contract_stays_deferred_during_class_construction(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        declaration: str,
    ) -> None:
        """Native mutable factories never evaluate an unfinished outer owner."""
        source = (
            "from __future__ import annotations\n"
            "from typing import Annotated\n"
            "from flext_core import t\n"
            "from pydantic import BaseModel, Field\n"
            "from flext_tests import tm\n"
            "class Domain:\n"
            "    class Item(BaseModel):\n"
            "        label: str\n"
            "    class Payload(BaseModel):\n"
            f"        {declaration}\n"
            "class Independent(BaseModel):\n"
            "    values: list[str] = Field(default_factory=list)\n"
            "deferred = not Domain.Payload.__pydantic_complete__\n"
            "if not deferred:\n"
            "    tm.reject('outer contract resolved during construction')\n"
            "first, second = Domain.Payload(), Domain.Payload()\n"
            "if isinstance(first.values, dict):\n"
            "    first.values['entry'] = Domain.Item(label='consumer')\n"
            "else:\n"
            "    first.values.append(Domain.Item(label='consumer'))\n"
            "restored = Domain.Payload.model_validate_json(first.model_dump_json())\n"
            "evidence = (deferred, first.values is not second.values, "
            "first.model_dump_json(), second.model_dump_json(), "
            "restored.model_dump_json(), Independent().model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )
        _workspace, path = rope_contract_consumer
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), contains=declaration)

    @staticmethod
    def test_own_class_contract_keeps_its_native_factory(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Pydantic self resolution does not bind the class name for field values."""
        source = (
            "from __future__ import annotations\n"
            "from pydantic import BaseModel, Field\n"
            "class Payload(BaseModel):\n"
            "    values: list[Payload] = Field(default_factory=list)\n"
            "class Independent(BaseModel):\n"
            "    values: list[str] = Field(default_factory=list)\n"
            "first, second = Payload(), Payload()\n"
            "first.values.append(Payload())\n"
            "restored = Payload.model_validate_json(first.model_dump_json())\n"
            "evidence = (first.values is not second.values, first.model_dump_json(), "
            "second.model_dump_json(), restored.model_dump_json(), "
            "Independent().model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )
        _workspace, path = rope_contract_consumer
        tm.that(
            path.read_text(encoding=c.DEFAULT_ENCODING),
            contains="values: list[Payload] = Field(default_factory=list)",
        )

    @staticmethod
    def test_already_bound_mutable_outer_contract_stays_native(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Binding an outer owner does not change a mutable factory's identity."""
        source = (
            "from __future__ import annotations\n"
            "from pydantic import BaseModel, Field\n"
            "class Domain:\n"
            "    class Item(BaseModel):\n"
            "        label: str\n"
            "class Payload(BaseModel):\n"
            "    values: list[Domain.Item] = Field(default_factory=list)\n"
            "first, second = Payload(), Payload()\n"
            "first.values.append(Domain.Item(label='consumer'))\n"
            "restored = Payload.model_validate_json(first.model_dump_json())\n"
            "evidence = (Payload.model_fields['values'].default_factory is list, "
            "first.values is not second.values, first.model_dump_json(), "
            "second.model_dump_json(), restored.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )

    @staticmethod
    @pytest.mark.parametrize("minimum", [0, 1])
    @pytest.mark.parametrize("alias", [False, True])
    def test_readonly_factory_preserves_full_field_validation_and_freshness(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        minimum: int,
        *,
        alias: bool,
    ) -> None:
        """The owning field validates all metadata, not just a collection origin."""
        declaration = (
            f"type Contract = Annotated[Sequence[str], Field(min_length={minimum})]\n"
            if alias
            else ""
        )
        annotation = (
            "Contract"
            if alias
            else f"Annotated[Sequence[str], Field(min_length={minimum})]"
        )
        source = (
            "from collections.abc import Sequence\n"
            "from typing import Annotated\n"
            "from pydantic import BaseModel, ConfigDict, Field, ValidationError\n"
            "from flext_tests import tm\n"
            f"{declaration}"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            "    seed: int = 7\n"
            f"    values: {annotation} = "
            "Field(default_factory=list)\n"
            "try:\n"
            "    first, second = Payload(), Payload()\n"
            "except ValidationError as error:\n"
            "    default = tuple(item['type'] "
            "for item in error.errors())\n"
            f"    if {minimum} == 0 or default != ('too_short',):\n"
            "        tm.reject('default constraint changed')\n"
            "else:\n"
            f"    if {minimum} > 0 or first.values is second.values:\n"
            "        tm.reject('default constraint or freshness lost')\n"
            "    first.values.append('consumer')\n"
            "    default = (first.values is not second.values, "
            "first.model_dump_json(), second.model_dump_json())\n"
            "try:\n"
            "    Payload(values=[3])\n"
            "except ValidationError as error:\n"
            "    rejected = tuple((item['type'], item['loc']) "
            "for item in error.errors())\n"
            "else:\n"
            "    tm.reject('element contract was discarded')\n"
            "evidence = (default, rejected, "
            "Payload.model_fields['values'].default_factory_takes_validated_data)\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)
        _workspace, path = rope_contract_consumer
        path.write_text(
            path.read_text(encoding=c.DEFAULT_ENCODING) + "try:\n"
            "    raw = Payload.model_fields['values'].get_default("
            "call_default_factory=True)\n"
            "except ValidationError as error:\n"
            "    rejected_default = tuple(item['type'] for item in error.errors())\n"
            f"    if {minimum} == 0 or rejected_default != ('too_short',):\n"
            "        tm.reject('factory constraint changed')\n"
            "else:\n"
            f"    if {minimum} > 0 or raw is "
            "Payload.model_fields['values'].get_default(call_default_factory=True):\n"
            "        tm.reject('factory constraint or freshness lost')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runpy.run_path(str(path))

    @staticmethod
    @pytest.mark.parametrize(
        ("contract", "factory", "native"),
        [
            ("tuple[str, ...]", c.Action.LIST, "tuple"),
            ("frozenset[str]", "set", "frozenset"),
            ("Mapping[str, int]", c.Action.LIST, "dict"),
        ],
    )
    def test_canonical_empty_repairs_return_contract_with_default_validation_disabled(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        contract: str,
        factory: str,
        native: str,
    ) -> None:
        """The factory itself returns the full contract, not an unvalidated seed."""
        workspace, path = rope_contract_consumer
        source = (
            "from collections.abc import Mapping\n"
            "from pydantic import (BaseModel, ConfigDict, Field, "
            "TypeAdapter, ValidationError)\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True, validate_default=False)\n"
            f"    values: {contract} = Field(default_factory={factory})\n"
            "value = Payload.model_fields['values'].default_factory()\n"
            "try:\n"
            f"    TypeAdapter({contract}).validate_python(value, strict=True)\n"
            "except ValidationError:\n"
            "    accepted = False\n"
            "else:\n"
            "    accepted = True\n"
            f"evidence = (type(value) is {native}, accepted, "
            "Payload.model_config['validate_default'], "
            "Payload.model_fields['values'].validate_default)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        tm.that(before[:2], eq=(False, False))
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(len(edits), eq=1)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        updated = edits[0].updated_source
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        after = runpy.run_path(str(path))["evidence"]
        tm.that(after[:2], eq=(True, True))
        tm.that(after[2:], eq=before[2:])
        tm.that(
            tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=workspace,
                    sources={path: updated},
                )
            ),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize("factory", ["tuple", "frozenset"])
    def test_strict_native_immutable_factory_is_not_a_raw_mutable_violation(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        factory: str,
    ) -> None:
        """A correct native immutable factory must retain its exact identity."""
        arguments = "str, ..." if factory == "tuple" else "str"
        source = (
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True, validate_default=True)\n"
            f"    values: {factory}[{arguments}] = Field(default_factory={factory})\n"
            f"evidence = (Payload.model_fields['values'].default_factory is {factory}, "
            f"type(Payload().values) is {factory}, Payload().model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("origin", "factory", "changes"),
        [
            ("Sequence", c.Action.LIST, True),
            ("MutableSequence", c.Action.LIST, False),
            ("Mapping", "dict", True),
            ("MutableMapping", "dict", False),
            ("Set", "set", True),
            ("MutableSet", "set", False),
        ],
    )
    def test_alias_factory_admission_follows_native_origin_not_alias_spelling(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        origin: str,
        factory: str,
        *,
        changes: bool,
    ) -> None:
        """An arbitrary alias name cannot grant or deny collection mutability."""
        arguments = "str, int" if factory == "dict" else "str"
        source = (
            f"from collections.abc import {origin}\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "type Unrelated = list[str]\n"
            "def sibling_scope():\n"
            "    type Contract = dict[str, str]\n"
            "    return Contract\n"
            f"type Contract = {origin}[{arguments}]\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            f"    values: Contract = Field(default_factory={factory})\n"
            "first, second = Payload(), Payload()\n"
            "evidence = (first.values is not second.values, "
            "first.model_dump_json(), second.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=changes
        )

    @staticmethod
    @pytest.mark.parametrize("declaration", ["Contract =", "type Contract ="])
    def test_rebound_type_alias_cannot_prove_a_deferred_factory_contract(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        declaration: str,
    ) -> None:
        """A later alias value must not replace the field's original resolved type."""
        source = (
            "from collections.abc import Sequence\n"
            "from typing import Annotated\n"
            "from annotated_types import MinLen\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "type Contract = Sequence[str]\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            "    values: Contract = Field(default_factory=list)\n"
            f"{declaration} Annotated[Sequence[str], MinLen(1)]\n"
            "first, second = Payload(), Payload()\n"
            "evidence = (first.values is not second.values, "
            "first.model_dump_json(), second.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )

    @staticmethod
    @pytest.mark.parametrize("factory", ["list[str]", "lambda: ['consumer']"])
    def test_typed_constructor_and_authored_callback_keep_distinct_behavior(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        factory: str,
    ) -> None:
        """Only the catalogue's builtin factories are empty-factory candidates."""
        source = (
            "from collections.abc import Sequence\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            f"factory = {factory}\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            f"    values: Sequence[str] = Field(default_factory={factory})\n"
            "first, second = Payload(), Payload()\n"
            "evidence = (Payload.model_fields['values'].default_factory is factory, "
            "first.values is not second.values, first.model_dump_json(), "
            "second.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )

    @staticmethod
    def test_readonly_deferred_outer_owner_keeps_native_field_resolution(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """The SDK callback never evaluates an unfinished enclosing annotation."""
        source = (
            "from __future__ import annotations\n"
            "from collections.abc import Sequence\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "class Domain:\n"
            "    class Item(BaseModel):\n"
            "        label: str\n"
            "    class Payload(BaseModel):\n"
            "        model_config = ConfigDict(validate_default=True)\n"
            "        values: Sequence[Domain.Item] = Field(default_factory=list)\n"
            "first, second = Domain.Payload(), Domain.Payload()\n"
            "evidence = (first.values is not second.values, "
            "first.model_dump_json(), second.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)
        _workspace, path = rope_contract_consumer
        updated = path.read_text(encoding=c.DEFAULT_ENCODING)
        tm.ok("TypeAdapter" not in updated)
        tm.ok("contract_factory=lambda: TypeForm(" in updated)

    @staticmethod
    @pytest.mark.parametrize(
        "marker",
        [
            "AfterValidator",
            "BeforeValidator",
            "WrapValidator",
            "PlainValidator",
            "GetPydanticSchema",
        ],
    )
    @pytest.mark.parametrize("alias", [False, True])
    def test_effectful_metadata_alias_rejects_additional_native_validation(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        marker: str,
        *,
        alias: bool,
    ) -> None:
        """Stable metadata aliases do not prove validation callbacks idempotent."""
        workspace, path = rope_contract_consumer
        callback = (
            "def append_marker(value, handler, info):\n"
            "    events.append((info.mode, info.context))\n"
            "    return [*handler(value), 'marker']\n"
            if marker == "WrapValidator"
            else "def append_marker(value, info):\n"
            "    events.append((info.mode, info.context))\n"
            "    return [*value, 'marker']\n"
        )
        schema = (
            "def schema(source_type, handler):\n"
            "    return core_schema.with_info_after_validator_function("
            "append_marker, handler(source_type))\n"
            if marker == "GetPydanticSchema"
            else ""
        )
        argument = "schema" if marker == "GetPydanticSchema" else "append_marker"
        declaration = (
            "type Contract = Annotated[Sequence[str], validator_alias]\n"
            if alias
            else ""
        )
        annotation = (
            "Contract" if alias else "Annotated[Sequence[str], validator_alias]"
        )
        source = (
            "from collections.abc import Sequence\n"
            "from typing import Annotated\n"
            "from typing_extensions import TypeForm\n"
            "from annotated_types import MinLen\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            f"from pydantic import {marker} as MetadataFactory\n"
            "from pydantic_core import core_schema\n"
            "from flext_core import u\n"
            "events = []\n"
            f"{callback}{schema}"
            f"constraint = MinLen(0); validator = MetadataFactory({argument})\n"
            "validator_alias = validator\n"
            f"{declaration}"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            f"    values: {annotation} = Field(default_factory=list)\n"
            "first = Payload.model_validate({}, context={'consumer': 'field'})\n"
            "first_events = tuple(events)\n"
            "events.clear()\n"
            "class RepeatedValidation(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            f"    values: {annotation} = Field(default_factory=u.empty(\n"
            f"        contract_factory=lambda: TypeForm({annotation})))\n"
            "second = RepeatedValidation.model_validate("
            "{}, context={'consumer': 'field'})\n"
            "evidence = (tuple(first.values), first_events, "
            "tuple(second.values), tuple(events))\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        tm.that(before[0], eq=("marker",))
        tm.that(before[1], eq=(("python", {"consumer": "field"}),))
        tm.that(before[2], eq=("marker", "marker"))
        tm.that(before[3], eq=(("json", None), ("python", {"consumer": "field"})))
        with pytest.raises(
            ValueError, match="additional validation effects are not proven idempotent"
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    @pytest.mark.parametrize(
        ("definition", "metadata"),
        [
            ("", "Field(min_length=0, description='constraint')"),
            ("", "MinLen(0)"),
            (
                "constraint = MinLen(0)\nconstraint_alias = constraint\n",
                "constraint_alias",
            ),
            ("", "MaxLen(8)"),
        ],
    )
    @pytest.mark.parametrize("alias", [False, True])
    def test_native_declarative_metadata_preserves_constraints_and_literal_payloads(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        definition: str,
        metadata: str,
        *,
        alias: bool,
    ) -> None:
        """Native registered constraints are not opaque validation callbacks."""
        declaration = (
            f"type Contract = Annotated[Sequence[Literal['entry']], {metadata}]\n"
            if alias
            else ""
        )
        annotation = (
            "Contract"
            if alias
            else f"Annotated[Sequence[Literal['entry']], {metadata}]"
        )
        source = (
            "from collections.abc import Sequence\n"
            "from typing import Annotated, Literal\n"
            "from annotated_types import MinLen, MaxLen\n"
            "from pydantic import BaseModel, ConfigDict, Field, ValidationError\n"
            "from flext_tests import tm\n"
            f"{definition}{declaration}"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(validate_default=True)\n"
            f"    values: {annotation} = Field(default_factory=list)\n"
            "first, second = Payload(), Payload()\n"
            "try:\n"
            "    Payload(values=['other'])\n"
            "except ValidationError as error:\n"
            "    rejected = tuple(item['type'] for item in error.errors())\n"
            "else:\n"
            "    tm.reject('literal element contract was discarded')\n"
            "evidence = (first.values is not second.values, first.model_dump_json(), "
            "second.model_dump_json(), rejected)\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    def test_strict_json_boundary_and_validator_modes_survive_factory_migration(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """A safe factory migration must preserve distinct validation contracts."""
        source = (
            "from datetime import date\n"
            "from json import loads\n"
            "from pydantic import BaseModel, ConfigDict, Field, "
            "ValidationError, field_validator\n"
            "events = []\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True)\n"
            "    when: date\n"
            "    where: tuple[int, int]\n"
            "    values: list[str] = Field(default_factory=list)\n"
            "    @field_validator('where', mode='after')\n"
            "    @classmethod\n"
            "    def observe(cls, value, info):\n"
            "        events.append((info.mode, info.context))\n"
            "        return value\n"
            'raw = \'{"when": "2000-01-02", "where": [1, 2]}\'\n'
            "try:\n"
            "    Payload.model_validate(loads(raw), context={'consumer': 'python'})\n"
            "except ValidationError as error:\n"
            "    rejected = tuple((item['type'], item['loc']) "
            "for item in error.errors())\n"
            "accepted = Payload.model_validate_json(raw, "
            "context={'consumer': 'json'})\n"
            "evidence = (rejected, accepted.model_dump_json(), tuple(events))\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )

    @staticmethod
    def test_dependent_factory_preserves_call_order_and_instance_isolation(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Moving sole Field metadata preserves data-dependent factory effects."""
        source = (
            "from typing import Annotated\n"
            "from pydantic import BaseModel, Field\n"
            "calls = []\n"
            "def factory(data):\n"
            "    calls.append(data['seed'])\n"
            "    return [data['seed']]\n"
            "class Payload(BaseModel):\n"
            "    seed: str\n"
            "    values: Annotated[list[str], Field(default_factory=factory)]\n"
            "first = Payload(seed='first')\n"
            "second = Payload(seed='second')\n"
            "first.values.append('changed')\n"
            "explicit = Payload(seed='explicit', values=['supplied'])\n"
            "evidence = (tuple(calls), first.model_dump_json(), "
            "second.model_dump_json(), explicit.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    # Outer facades from this project's own declared FLEXT dependencies; a
    # library test never imports a downstream consumer it does not install.
    @pytest.mark.parametrize("namespace", ["flext_core", "flext_cli"])
    def test_outer_facades_preserve_nested_contracts(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        namespace: str,
    ) -> None:
        """Real outer model presets and utilities retain their inherited contracts."""
        source = (
            f"from {namespace} import m, t, u\n"
            "class Payload(m.BaseModel):\n"
            "    values: list[dict[str, int | None]] = m.Field(default_factory=list)\n"
            "first, second = Payload(), Payload()\n"
            "first.values.append({'present': 1, 'absent': None})\n"
            "restored = Payload.model_validate_json(first.model_dump_json())\n"
            "evidence = (first.model_dump_json(), second.model_dump_json(), "
            "restored.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )

    @staticmethod
    def test_factory_migration_cannot_repeat_annotation_effects(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """A repeated type expression must not run an authored callback twice."""
        source = (
            "from collections.abc import Sequence\n"
            "from pydantic import BaseModel, Field\n"
            "events = []\n"
            "def element_type():\n"
            "    events.append('annotation')\n"
            "    return str\n"
            "class Payload(BaseModel):\n"
            "    values: Sequence[element_type()] = Field(default_factory=list)\n"
            "evidence = (tuple(events), Payload().model_dump_json())\n"
        )
        workspace, path = rope_contract_consumer
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with pytest.raises(ValueError, match="authored evaluation cannot repeat"):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    @pytest.mark.parametrize(
        "field_argument",
        ["default=default_value()", "default_factory=factory_value()"],
    )
    def test_metadata_migration_cannot_reorder_authored_effects(
        tmp_path: Path,
        field_argument: str,
    ) -> None:
        """Assignment syntax must not reverse callbacks in an Annotated field."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from typing import Annotated\n"
            "from pydantic import BaseModel, Field\n"
            "events = []\n"
            "def contract():\n"
            "    events.append('annotation')\n"
            "    return int\n"
            "def default_value():\n"
            "    events.append('default')\n"
            "    return 7\n"
            "def factory_value():\n"
            "    events.append('factory')\n"
            "    return lambda: 7\n"
            "class Payload(BaseModel):\n"
            f"    value: Annotated[contract(), Field({field_argument})]\n"
            "evidence = (tuple(events), Payload().model_dump_json())\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=r"annotation.*reorder"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    def test_unrelated_field_factory_is_not_a_pydantic_field(tmp_path: Path) -> None:
        """Same-spelled functions do not establish a Pydantic identity."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "def Field(*, default_factory):\n"
            "    return default_factory()\n"
            "values: list[str] = Field(default_factory=list)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: source},
                )
            )
        tm.that(edits, empty=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_existing_cli_facade_and_unrelated_field_info_are_preserved(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Valid model fields migrate independently without capturing richer u."""
        source = (
            "from flext_cli import u\n"
            "from pydantic import BaseModel, Field\n"
            "info: list[str] = Field(default_factory=list)\n"
            "class Payload(BaseModel):\n"
            "    values: list[str] = Field(default_factory=list)\n"
            "evidence = (Payload().model_dump_json(), "
            "info.default_factory is list, "
            "u.Cli.env_read('consumer_key', {'consumer_key': 'value'}).unwrap())\n"
        )
        u.Tests.prove_contract_migration(
            rope_contract_consumer, source, expect_change=False
        )
