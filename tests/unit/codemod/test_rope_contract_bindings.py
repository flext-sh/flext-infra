"""Native Rope binding proofs preserve the real consumer before publication.

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


class TestsFlextInfraRopeContractBindings:
    """Prove lexical identity and execution order without publishing unsafe edits."""

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "value: str = Field(description='Required input')",
            "value: str = Field(..., min_length=2)",
            "value: str = Field(default=..., alias='wire', description='Wire input')",
            "value: 'str' = Field(min_length=2)",
        ],
    )
    def test_required_metadata_preserves_native_validation_and_schema(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        declaration: str,
    ) -> None:
        """Required fields retain metadata, aliases, failures and JSON behavior."""
        source = (
            "from pydantic import BaseModel, Field, ValidationError\n"
            "class Payload(BaseModel):\n"
            f"    {declaration}\n"
            "    optional: str | None = Field(default=None)\n"
            "    generated: str = Field(default_factory=str)\n"
            "first = Payload.model_validate({'value': 'valid', 'wire': 'valid'})\n"
            "raw = first.model_dump_json(by_alias=True)\n"
            "restored = Payload.model_validate_json(raw)\n"
            "try:\n"
            "    Payload.model_validate({})\n"
            "except ValidationError as error:\n"
            "    rejected = tuple((item['type'], item['loc']) for item in error.errors())\n"
            "evidence = (Payload.model_json_schema(), raw, "
            "restored.model_dump_json(by_alias=True), rejected)\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    @pytest.mark.parametrize(
        "metadata", ["description='Value'", "default_factory=None"]
    )
    def test_required_metadata_preserves_annotation_factory_precedence(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        metadata: str,
    ) -> None:
        """Moving assignment metadata does not invent or revive a factory."""
        source = (
            "from typing import Annotated\n"
            "from pydantic import BaseModel, Field, ValidationError\n"
            "class Payload(BaseModel):\n"
            "    value: Annotated[str, Field(default_factory=str)] = "
            f"Field({metadata})\n"
            "try:\n"
            "    omitted = Payload().model_dump_json()\n"
            "except ValidationError as error:\n"
            "    omitted = tuple(item['type'] for item in error.errors())\n"
            "evidence = (omitted, Payload(value='supplied').model_dump_json(), "
            "Payload.model_json_schema())\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    def test_unset_private_annotation_preserves_native_descriptor_behavior(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Native private handling keeps missing state and per-instance values."""
        source = (
            "from pydantic import BaseModel, PrivateAttr\n"
            "class Payload[T](BaseModel):\n"
            "    _history: list[T] = PrivateAttr()\n"
            "first, second = Payload[str](), Payload[str]()\n"
            "missing = not hasattr(first, '_history')\n"
            "first._history = ['event']\n"
            "descriptor = Payload.__private_attributes__['_history']\n"
            "evidence = (missing, not hasattr(second, '_history'), "
            "first._history, descriptor.get_default() is descriptor.default)\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    def test_native_metadata_admission_preserves_nonfields_and_homonyms(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Class variables, nonmodels and unrelated factories are not fields."""
        rope, path = rope_contract_consumer
        source = (
            "from typing import ClassVar as CV\n"
            "from pydantic import BaseModel, Field, PrivateAttr\n"
            "info: str = Field(description='Not a model declaration')\n"
            "class Plain:\n"
            "    value: str = Field(description='Not a model field')\n"
            "    _state: int = PrivateAttr()\n"
            "def unrelated(**kwargs):\n"
            "    return 'unchanged'\n"
            "class Payload(BaseModel):\n"
            "    static: CV[str] = Field(description='Class variable')\n"
            "    value: str = unrelated(description='Not an SDK factory')\n"
            "evidence = (info.description, Plain.value.description, "
            "Payload.static.description, Payload().model_dump_json())\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=rope,
                sources={path: source},
            )
        )
        tm.that(edits, empty=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    def test_metadata_destination_cannot_capture_a_generic_parameter(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """An imported Annotated cannot replace an existing generic binding."""
        rope, path = rope_contract_consumer
        source = (
            "from pydantic import BaseModel, Field\n"
            "class Payload[Annotated](BaseModel):\n"
            "    value: Annotated = Field(description='Generic payload')\n"
            "evidence = Payload[str](value='valid').model_dump_json()\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with pytest.raises(ValueError, match="shadow"):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

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
