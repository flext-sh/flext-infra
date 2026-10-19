"""Native Rope binding proofs preserve the real consumer before publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, p, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeContractBindings:
    """Prove lexical identity and execution order without publishing unsafe edits."""

    @staticmethod
    def _assertion_rules() -> t.SequenceOf[p.Infra.RopeContractRule]:
        """Declare the Python statement contract consumed by the native writer.

        Returns:
            A sequence of RopeContractRule instances.

        """
        return tuple(
            m.Infra.RopeContractRule(
                id=f"native-assert-{name}",
                pattern=pattern,
                goal=goal,
                arguments={},
                unshadowed_builtins=("AssertionError",),
            )
            for name, pattern, goal in (
                (
                    "predicate",
                    "assert ${predicate}",
                    "if not (${predicate}):\n    raise AssertionError",
                ),
                (
                    "message",
                    "assert ${predicate}, ${message}",
                    "if not (${predicate}):\n    raise AssertionError((${message}))",
                ),
            )
        )

    @staticmethod
    @pytest.mark.parametrize(
        "statement",
        [
            "assert (retained := predicate(value)) is not None",
            "assert (retained := predicate(value)) is not None, diagnostic()",
            "assert (retained := predicate(value)) is not None, ('one', 'two')",
            "assert isinstance((retained := predicate(value)), str), diagnostic()",
            "assert 0 < len((retained := predicate(value)) or '') < 100",
            (
                "assert (retained := predicate(\n"
                "        value,  # predicate capture comment\n"
                "    )) is not None, diagnostic()"
            ),
            (
                "assert (retained := predicate(value)) is not None, diagnostic(\n"
                "        # message capture comment\n"
                "    )"
            ),
        ],
    )
    def test_assert_lowering_preserves_lazy_values_and_optimized_checks(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        infra_subprocess: p.Cli.CommandRunner,
        statement: str,
    ) -> None:
        """Real Rope retains evaluation, exception payloads, trivia and narrowing."""
        workspace, path = rope_contract_consumer
        source = (
            "events = []\n"
            "class Message:\n"
            "    def __str__(self):\n"
            "        raise RuntimeError('message must not be formatted')\n"
            "message = Message()\n"
            "def predicate(value: str | None) -> str | None:\n"
            "    events.append(('predicate', value))\n"
            "    return value\n"
            "def diagnostic():\n"
            "    events.append(('message',))\n"
            "    return message\n"
            "def check(value: str | None) -> int:\n"
            f"    {statement}\n"
            "    events.append(('after', value))\n"
            "    return len(retained)\n"
            "results = []\n"
            "for value in ('ready', None):\n"
            "    try:\n"
            "        results.append(check(value))\n"
            "    except AssertionError as error:\n"
            "        results.append((len(error.args), "
            "not error.args or error.args[0] is message))\n"
            "evidence = (results, events)\n"
            "print(repr(evidence))\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = TestsFlextInfraRopeContractBindings._assertion_rules()
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules))
        tm.that(len(edits), eq=1)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        updated = edits[0].updated_source
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)
        tm.that(
            tm.ok(
                infra_subprocess.capture(
                    (sys.executable, "-O", str(path)), cwd=path.parent
                )
            ),
            eq=repr(before),
        )
        tm.that(
            tuple(
                updated[start:end]
                for start, end, _metadata in u.Infra.ignored_regions(updated)
                if updated[start:end].startswith("#")
            ),
            eq=tuple(
                source[start:end]
                for start, end, _metadata in u.Infra.ignored_regions(source)
                if source[start:end].startswith("#")
            ),
        )
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, {path: updated}, rules)),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "source",
        [
            "assert True; effect()\n",
            "effect(); assert True\n",
            "if True: assert True\n",
            "if True: assert True; effect()\n",
            "if True: \\\n    assert True\n",
            "def check(): assert True\n",
            "assert True  # retained trailing comment\n",
            "assert (  # outside predicate capture\n    True\n)\n",
            "assert True, (  # outside message capture\n    'message'\n)\n",
            "def check():\n    assert True, '''first\nsecond'''\n",
            "def check():\n    assert '''first\nsecond'''\n",
            "def check():\n    assert 'first\vsecond'\n",
        ],
    )
    def test_assert_lowering_refuses_incomplete_effects_and_lost_trivia(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        source: str,
    ) -> None:
        """Unsupported native slices fail before an edit or a source write exists."""
        workspace, path = rope_contract_consumer
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="complete standalone statement"):
            u.Infra.plan_contract_rules(
                workspace,
                {path: source},
                TestsFlextInfraRopeContractBindings._assertion_rules(),
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.parametrize(
        "source",
        [
            "AssertionError = ValueError\nassert True\n",
            "assert True\nAssertionError = ValueError\n",
            "from builtins import AssertionError\nassert True\n",
            "from builtins import ValueError as AssertionError\nassert True\n",
            "def check(AssertionError):\n    assert True\n",
            "def check():\n    AssertionError = ValueError\n    assert True\n",
            (
                "def outer(AssertionError):\n"
                "    def check():\n"
                "        assert True\n"
                "    return check\n"
            ),
        ],
    )
    def test_assert_lowering_requires_the_interpreter_exception_binding(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        source: str,
    ) -> None:
        """LOAD_ASSERTION_ERROR must not become a shadowed lexical constructor."""
        workspace, path = rope_contract_consumer
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="requires unshadowed builtins"):
            u.Infra.plan_contract_rules(
                workspace,
                {path: source},
                TestsFlextInfraRopeContractBindings._assertion_rules(),
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

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
            "    rejected = tuple((item['type'], item['loc']) "
            "for item in error.errors())\n"
            "evidence = (Payload.model_json_schema(), raw, "
            "restored.model_dump_json(by_alias=True), rejected)\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    @pytest.mark.parametrize(
        ("argument", "expression"),
        [
            ("()", "()"),
            ("default=()", "()"),
            ("default=None", "None"),
            ("default=Choice.READY", "Choice.READY"),
            ("default=make_default()", "make_default()"),
            ("default='ready'", "'ready'"),
        ],
    )
    def test_defaulted_metadata_single_rule_preserves_concrete_default(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        argument: str,
        expression: str,
    ) -> None:
        """Preview exactly one native rule before proving runtime and fixed point."""
        workspace, path = rope_contract_consumer
        source = (
            "from enum import StrEnum\n"
            "from pydantic import BaseModel, Field\n"
            "events = []\n"
            "class Choice(StrEnum):\n"
            "    READY = 'ready'\n"
            "def make_default():\n"
            "    events.append('default')\n"
            "    return ()\n"
            "class Payload(BaseModel):\n"
            "    value: tuple[str, ...] | str | None = "
            f"Field({argument}, description='Retained', validate_default=True)\n"
            "evidence = (Payload().model_dump_json(), "
            "Payload.model_json_schema(), events)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-defaulted-field-metadata"
        )
        tm.that(len(rules), eq=1)
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules))
        tm.that(len(edits), eq=1)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        updated = edits[0].updated_source
        tm.that(
            f"Field(description='Retained', validate_default=True)] = {expression}"
            in updated,
            eq=True,
        )
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, {path: updated}, rules)),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "arguments",
        [
            "description='Required'",
            "...",
            "default=...",
            "default_factory=tuple",
            "default=(), default_factory=tuple",
            "(), default=()",
            "(), default_factory=None",
            "(), description=describe()",
            "*defaults",
            "**metadata",
        ],
    )
    def test_defaulted_metadata_preserves_required_factories_and_invalid_calls(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        arguments: str,
    ) -> None:
        """Unsupported/default-conflicting calls retain their native behavior."""
        workspace, path = rope_contract_consumer
        source = (
            "from pydantic import BaseModel, Field\n"
            "defaults = ((),)\n"
            "metadata = {'default': ()}\n"
            "def describe():\n"
            "    return 'Retained authored call'\n"
            "class Payload(BaseModel):\n"
            f"    value: tuple[str, ...] = Field({arguments})\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-defaulted-field-metadata"
        )
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules)),
            empty=True,
        )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        if arguments in {"(), default=()", "default=(), default_factory=tuple"}:
            with pytest.raises(TypeError):
                runpy.run_path(str(path))

    @staticmethod
    def test_defaulted_metadata_composes_distinct_shapes_in_one_native_epoch(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Native sequential shapes never overwrite another field's proposed edit."""
        source = (
            "from pydantic import BaseModel, Field\n"
            "class Payload(BaseModel):\n"
            "    first: tuple[str, ...] = Field((), description='First')\n"
            "    second: str | None = Field(description='Second', "
            "default=None, validate_default=True)\n"
            "evidence = (Payload().model_dump_json(), Payload.model_json_schema())\n"
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
    @pytest.mark.parametrize(
        "annotation",
        [
            "Type()",
            "Annotated[str, metadata(default_factory=str)]",
            "Annotated[str, SDKField(default_factory=make_factory())]",
            "Annotated[str, SDKField(description=metadata())]",
            "Annotated[str, SDKField(default_factory=custom_factory)]",
            "ForeignAnnotated[str, SDKField(default_factory=str)]",
        ],
    )
    def test_required_metadata_rejects_unproved_annotation_calls(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        annotation: str,
    ) -> None:
        """Only native inert SDK metadata can cross the evaluation-order boundary."""
        workspace, path = rope_contract_consumer
        source = (
            "from typing import Annotated\n"
            "from pydantic import BaseModel, Field as SDKField\n"
            "events = []\n"
            "def Type():\n"
            "    events.append('type')\n"
            "    return str\n"
            "def metadata(**kwargs):\n"
            "    events.append('metadata')\n"
            "    return 'tag'\n"
            "def custom_factory():\n"
            "    return ''\n"
            "def make_factory():\n"
            "    events.append('factory')\n"
            "    return str\n"
            "class ForeignAnnotated:\n"
            "    def __class_getitem__(cls, args):\n"
            "        events.append('subscription')\n"
            "        return str\n"
            "class Payload(BaseModel):\n"
            f"    value: {annotation} = SDKField(description='Required')\n"
            "evidence = (Payload.model_json_schema(), tuple(events))\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-required-field-metadata"
        )
        with pytest.raises(ValueError, match="cannot reorder authored calls"):
            u.Infra.plan_contract_rules(workspace, {path: source}, rules)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

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
                    "    values: tuple[str, ...] = Field(default_factory=list)\n"
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
                    "    values: tuple[str, ...] = Field(default_factory=list)\n"
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
