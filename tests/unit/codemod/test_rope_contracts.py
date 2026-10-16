"""Real Pydantic consumer evidence for native Rope contract migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, p, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeContracts:
    """Prove runtime values, failure contracts and the shared fixed point."""

    @staticmethod
    def test_catalog_phases_roundtrip_and_reject_unknown_values() -> None:
        """Configured rules retain enum identities, never an unvalidated phase."""
        for rule in u.Infra.declared_contract_rules():
            payload = rule.model_dump(round_trip=True)
            restored = m.Infra.RopeContractRule.model_validate_json(
                rule.model_dump_json(round_trip=True)
            )
            tm.that(restored.phase, eq=c.Infra.SemanticCutoverPhase(rule.phase))
            payload["phase"] = "".join(c.Infra.SemanticCutoverPhase)
            with pytest.raises(ValueError, match="phase"):
                m.Infra.RopeContractRule.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "values: list[str] = Field(default_factory=list)",
            "values: dict[str, list[int]] = Field(default_factory=dict)",
            "values: Meta[list[str], Field(default_factory=list)]",
            "values: Meta[int, Field(default=3)]",
            "values: set[str] = Field(default_factory=set)",
            "values: tuple[str, ...] = Field(default_factory=tuple)",
            "values: list[str] = Field(default_factory=list, description='d')",
            "values: dict[str, int] = Field(default_factory=dict, description='d')",
            "values: Meta[list[str], Field(description='d')] = "
            "Field(default_factory=list)",
            "values: Meta[dict[str, int], Field(min_length=0)] = "
            "Field(default_factory=dict)",
        ],
    )
    def test_real_defaults_preserve_runtime_and_converge(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        declaration: str,
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
            "restored.model_dump_json())\n"
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
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

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
    @pytest.mark.parametrize(
        "namespace",
        ["flext_tap_ldif", "flext_target_ldif", "flext_dbt_ldif"],
    )
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
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    def test_factory_migration_cannot_repeat_annotation_effects(
        tmp_path: Path,
    ) -> None:
        """A repeated type expression must not run an authored callback twice."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from pydantic import BaseModel, Field\n"
            "events = []\n"
            "def element_type():\n"
            "    events.append('annotation')\n"
            "    return str\n"
            "class Payload(BaseModel):\n"
            "    values: list[element_type()] = Field(default_factory=list)\n"
            "evidence = (tuple(events), Payload().model_dump_json())\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=r"annotation.*repeat"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=rope,
                sources={path: source},
            )
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
    def test_shadowed_dictionary_constructor_retains_its_own_contract(
        tmp_path: Path,
    ) -> None:
        """Inherited BaseModel.dict is not lexical, but a real local dict is."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from builtins import dict as BuiltinDictionary\n"
            "from pydantic import BaseModel, Field, ConfigDict\n"
            "class dict(BuiltinDictionary):\n"
            "    pass\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(arbitrary_types_allowed=True)\n"
            "    values: dict[str, list[int]] = Field(default_factory=dict)\n"
            "evidence = type(Payload().values) is dict\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        tm.that(runpy.run_path(str(path))["evidence"], eq=True)
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: source},
                )
            )
        tm.that(edits, empty=True)
        tm.that(runpy.run_path(str(path))["evidence"], eq=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("source", "diagnostic"),
        [
            (
                (
                    "from pydantic import BaseModel, Field\n"
                    "u = 'existing consumer binding'\n"
                    "class Payload(BaseModel):\n"
                    "    values: list[str] = Field(default_factory=list)\n"
                    "evidence = (u, Payload().model_dump_json())\n"
                ),
                r"destination u.empty is shadowed",
            ),
            (
                (
                    "from pydantic import TypeAdapter\n"
                    "def consume(u):\n"
                    "    return TypeAdapter(list[int]).validate_python([1])\n"
                    "evidence = consume('existing parameter')\n"
                ),
                r"destination u.type_adapter is shadowed",
            ),
            (
                (
                    "from pydantic import BaseModel, Field\n"
                    "class Payload(BaseModel):\n"
                    "    values: list[str] = Field(default_factory=list)\n"
                    "from flext_core import u\n"
                    "evidence = Payload().model_dump_json()\n"
                ),
                "no preceding unconditional import",
            ),
        ],
        ids=["module-shadow", "parameter-shadow", "late-import"],
    )
    def test_destination_binding_refuses_invalid_publication(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        source: str,
        diagnostic: str,
    ) -> None:
        """Module, parameter and execution-order bindings preserve public behavior."""
        rope, path = rope_contract_consumer
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with pytest.raises(ValueError, match=diagnostic):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

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
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    def test_aliased_adapter_preserves_validation_and_failure_modes(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """The public constructor preserves native coercion and rejection."""
        source = (
            "from pydantic import TypeAdapter as Parse, ValidationError\n"
            "def consume():\n"
            "    adapter = Parse(list[int])\n"
            "    accepted = adapter.validate_json('[1, \"2\"]')\n"
            "    try:\n"
            "        adapter.validate_python(['invalid'])\n"
            "    except ValidationError as error:\n"
            "        return accepted, tuple(item['type'] for item in error.errors())\n"
            "    raise AssertionError('invalid input was accepted')\n"
            "evidence = consume()\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)
