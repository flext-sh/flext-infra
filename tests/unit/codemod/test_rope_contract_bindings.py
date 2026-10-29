"""Native Rope binding proofs preserve the real consumer before publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeContractBindings:
    """Prove lexical identity and execution order without publishing unsafe edits."""

    @staticmethod
    @pytest.mark.parametrize(
        ("imports", "metadata", "variant"),
        [
            (
                "import pydantic as m",
                "m.Field(discriminator='kind')",
                "Payload | OtherPayload",
            ),
            (
                "import pydantic",
                "pydantic.Field(discriminator='kind')",
                "Payload | OtherPayload",
            ),
            (
                "import pydantic as m",
                "m.Discriminator('kind')",
                "Payload | OtherPayload",
            ),
            (
                "from pydantic import Field as Tag",
                "Tag(discriminator='kind')",
                "Payload | OtherPayload",
            ),
            (
                "import pydantic as m",
                "m.Field(discriminator='kind')",
                "'Payload | OtherPayload'",
            ),
            (
                "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from pydantic import Field as Tag\nelse:\n    from pydantic import Field as Tag",
                "Tag(discriminator='kind')",
                "Payload | OtherPayload",
            ),
        ],
    )
    def test_qualified_and_forward_discriminator_consumers_retain_literal_contract(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        imports: str,
        metadata: str,
        variant: str,
    ) -> None:
        """Real Pydantic consumes qualified, aliased and quoted discriminators."""
        workspace, path = rope_contract_consumer
        source = (
            "from enum import StrEnum, unique\n"
            "from typing import Annotated, Literal\n"
            "from pydantic import BaseModel\n"
            f"{imports}\n"
            "@unique\nclass State(StrEnum):\n    READY = 'ready'\n    FAILED = 'failed'\n"
            "class Payload(BaseModel):\n    kind: Literal[State.READY, State.FAILED]\n"
            "class OtherPayload(BaseModel):\n    kind: Literal['other']\n"
            f"class Envelope(BaseModel):\n    payload: Annotated[{variant}, {metadata}]\n"
            "evidence = Envelope.model_validate({'payload': {'kind': 'ready'}}).model_dump_json()\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules))
        tm.that(edits, empty=True)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    def test_imported_type_and_metadata_aliases_protect_discriminator(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        infra_subprocess: p.Cli.CommandRunner,
    ) -> None:
        """Native import provenance connects foreign union and metadata aliases."""
        workspace, path = rope_contract_consumer
        models = path.parent / "variant_models.py"
        metadata = path.parent / "discriminator_metadata.py"
        package = path.parent.name
        sources = {
            models: (
                "from enum import StrEnum, unique\nfrom typing import Literal\nfrom pydantic import BaseModel\n"
                "@unique\nclass State(StrEnum):\n    READY = 'ready'\n    FAILED = 'failed'\n"
                "class Payload(BaseModel):\n    kind: Literal[State.READY, State.FAILED]\n"
                "class OtherPayload(BaseModel):\n    kind: Literal['other']\n"
                "type Variants = Payload | OtherPayload\n"
            ),
            metadata: "import pydantic as pd\nDiscriminatorMetadata = pd.Field(discriminator='kind')\n",
            path: (
                "from typing import Annotated\nfrom pydantic import BaseModel\n"
                f"from {package}.variant_models import Variants\n"
                f"from {package}.discriminator_metadata import DiscriminatorMetadata\n"
                "class Envelope(BaseModel):\n    payload: Annotated[Variants, DiscriminatorMetadata]\n"
            ),
        }
        for target, source in sources.items():
            target.write_text(source, encoding=c.DEFAULT_ENCODING)
        command = (
            sys.executable,
            "-c",
            f"from {package}.consumer import Envelope\nprint(Envelope.model_validate({{'payload': {{'kind': 'ready'}}}}).model_dump_json())\n",
        )
        options = m.Cli.ProcessOptions(env={"PYTHONPATH": str(path.parent.parent)})
        before = tm.ok(
            infra_subprocess.capture(
                command, cwd=workspace.repository_root, options=options
            )
        )
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, sources, rules)), empty=True
        )
        after = tm.ok(
            infra_subprocess.capture(
                command, cwd=workspace.repository_root, options=options
            )
        )
        tm.that(after.stdout, eq=before.stdout)

    @staticmethod
    @pytest.mark.parametrize(
        "default",
        [
            "'ready'",
            "Field(default='ready', description='Retained')",
            "Field('ready', validate_default=True)",
        ],
    )
    def test_exhaustive_enum_string_defaults_keep_strict_pydantic_contract(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        default: str,
    ) -> None:
        """A valid Literal string default becomes its native enum member producer."""
        workspace, path = rope_contract_consumer
        source = (
            "from enum import StrEnum, unique\nfrom typing import Literal\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "@unique\nclass State(StrEnum):\n    READY = 'ready'\n    FAILED = 'failed'\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True, use_enum_values=True, validate_default=True)\n"
            f"    kind: Literal[State.READY, State.FAILED] = {default}\n"
            "evidence = (Payload().model_dump_json(), Payload.model_fields['kind'].description, Payload.model_json_schema()['properties']['kind']['default'])\n"
            "primitive = type(Payload().kind) is str\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules))
        tm.that(len(edits), eq=1)
        path.write_text(edits[0].updated_source, encoding=c.DEFAULT_ENCODING)
        after = runpy.run_path(str(path))
        tm.that(after["evidence"], eq=before)
        tm.that(after["primitive"], eq=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("default", "error"),
        [
            ("Field(default_factory=produce)", "default factory"),
            ("produce()", "default producer"),
            ("DEFAULT", "default alias"),
        ],
    )
    def test_exhaustive_enum_unproven_default_producers_fail_before_effects(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        default: str,
        error: str,
    ) -> None:
        """Valid old defaults remain authored when their enum producer is unproven."""
        workspace, path = rope_contract_consumer
        source = (
            "from enum import StrEnum, unique\nfrom typing import Literal\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "@unique\nclass State(StrEnum):\n    READY = 'ready'\n    FAILED = 'failed'\n"
            "DEFAULT = 'ready'\ndef produce():\n    return 'ready'\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True, use_enum_values=True, validate_default=True)\n"
            f"    kind: Literal[State.READY, State.FAILED] = {default}\n"
            "evidence = Payload().model_dump_json()\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        with pytest.raises(ValueError, match=error):
            u.Infra.plan_contract_rules(workspace, {path: source}, rules)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    @pytest.mark.parametrize(
        "annotation",
        [
            "Choice[StateAlias.READY, StateAlias.FAILED]",
            "Annotated[Choice[StateAlias.READY, StateAlias.FAILED], Field(description='Retained')]",
            "list[Choice[StateAlias.READY, StateAlias.FAILED]]",
            "Choice[StateAlias.READY, StateAlias.FAILED] | None",
            "Choice[ready, failed]",
        ],
    )
    def test_exhaustive_enum_contract_preserves_real_pydantic_wire_values(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        annotation: str,
    ) -> None:
        """The native action retains metadata/defaults and enum wire domains."""
        workspace, path = rope_contract_consumer
        value = "[State.READY]" if annotation.startswith("list[") else "State.READY"
        source = (
            "from enum import StrEnum, unique\n"
            "from typing import Annotated, Literal as Choice\n"
            "from pydantic import BaseModel, ConfigDict, Field\n"
            "@unique\n"
            "class State(StrEnum):\n"
            "    READY = 'ready'\n"
            "    FAILED = 'failed'\n"
            "StateAlias = State\n"
            "ready = State.READY\n"
            "failed = State.FAILED\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True, use_enum_values=True, validate_default=True)\n"
            f"    value: {annotation} = {value}\n"
            f"parsed = Payload.model_validate({{'value': {value}}})\n"
            "evidence = (parsed.model_dump_json(), Payload().model_dump_json(), "
            "Payload.model_fields['value'].description)\n"
            "stored_primitive = (all(type(item) is str for item in parsed.value) "
            "if isinstance(parsed.value, list) else type(parsed.value) is str)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        tm.that(len(rules), eq=1)
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules))
        tm.that(len(edits), eq=1)
        path.write_text(edits[0].updated_source, encoding=c.DEFAULT_ENCODING)
        after = runpy.run_path(str(path))
        tm.that(after["evidence"], eq=before)
        tm.that(after["stored_primitive"], eq=True)
        tm.that(
            tm.ok(
                u.Infra.plan_contract_rules(
                    workspace, {path: edits[0].updated_source}, rules
                )
            ),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("annotation", "consumer"),
        [
            ("Literal[State.READY]", ""),
            ("Literal[State.READY, State.READY]", ""),
            ("Literal[State.READY, Other.FAILED]", ""),
            ("Annotated[str, Literal[State.READY, State.FAILED]]", ""),
            (
                "Literal[State.READY, State.FAILED]",
                (
                    "class OtherPayload(BaseModel):\n"
                    "    kind: Literal['other']\n"
                    "Variants = Payload | OtherPayload\n"
                    "DiscriminatorMetadata = Field(description='Retained', discriminator='kind')\n"
                    "class Envelope(BaseModel):\n"
                    "    payload: Annotated[Variants, DiscriminatorMetadata]\n"
                ),
            ),
        ],
    )
    def test_exhaustive_enum_contract_retains_narrowed_and_discriminator_contracts(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        annotation: str,
        consumer: str,
    ) -> None:
        """Subset, duplicate, mixed, metadata and alias discriminators stay intact."""
        workspace, path = rope_contract_consumer
        source = (
            "from enum import StrEnum, unique\n"
            "from typing import Annotated, Literal\n"
            "from pydantic import BaseModel, Field\n"
            "@unique\n"
            "class State(StrEnum):\n"
            "    READY = 'ready'\n"
            "    FAILED = 'failed'\n"
            "@unique\n"
            "class Other(StrEnum):\n"
            "    READY = 'other-ready'\n"
            "    FAILED = 'other-failed'\n"
            "class Payload(BaseModel):\n"
            f"    kind: {annotation}\n" + consumer
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, rules)),
            empty=True,
        )

    @staticmethod
    def test_exhaustive_enum_contract_refuses_opaque_discriminator_before_effects(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """A callable discriminator requires explicit proof before any preview."""
        workspace, path = rope_contract_consumer
        source = (
            "from enum import StrEnum, unique\n"
            "from typing import Annotated, Literal\n"
            "from pydantic import BaseModel, Field\n"
            "@unique\n"
            "class State(StrEnum):\n"
            "    READY = 'ready'\n"
            "    FAILED = 'failed'\n"
            "class Payload(BaseModel):\n"
            "    kind: Literal[State.READY, State.FAILED]\n"
            "def classify(value):\n"
            "    return value['kind']\n"
            "class Envelope(BaseModel):\n"
            "    payload: Annotated[Payload, Field(discriminator=classify)]\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        with pytest.raises(ValueError, match="native string field identity"):
            u.Infra.plan_contract_rules(workspace, {path: source}, rules)

    @staticmethod
    def test_exhaustive_enum_contract_imports_owner_for_foreign_member_aliases(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        infra_subprocess: p.Cli.CommandRunner,
    ) -> None:
        """Bare imported member aliases acquire their proven native enum import."""
        workspace, path = rope_contract_consumer
        owner = path.parent / "enum_owner.py"
        provider = (
            "from enum import StrEnum, unique\n"
            "@unique\n"
            "class State(StrEnum):\n"
            "    READY = 'ready'\n"
            "    WAITING = 'waiting'\n"
            "Ready = State.READY\n"
            "Waiting = State.WAITING\n"
        )
        source = (
            "from typing import Literal\n"
            "from pydantic import BaseModel, ConfigDict\n"
            f"from {path.parent.name}.enum_owner import Ready, Waiting\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(strict=True, use_enum_values=True, validate_default=True)\n"
            "    kind: Literal[Ready, Waiting] = Ready\n"
        )
        owner.write_text(provider, encoding=c.DEFAULT_ENCODING)
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        command = (
            sys.executable,
            "-c",
            (
                f"from {path.parent.name}.consumer import Payload\n"
                f"from {path.parent.name}.enum_owner import Ready\n"
                "print(Payload.model_validate({'kind': Ready}).model_dump_json())\n"
                "print(Payload().model_dump_json())\n"
            ),
        )
        options = m.Cli.ProcessOptions(env={"PYTHONPATH": str(path.parent.parent)})
        before = tm.ok(
            infra_subprocess.capture(
                command, cwd=workspace.repository_root, options=options
            )
        )
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.id == "pydantic-exhaustive-strenum-annotation"
        )
        edits = tm.ok(
            u.Infra.plan_contract_rules(
                workspace, {owner: provider, path: source}, rules
            )
        )
        tm.that(len(edits), eq=1)
        for edit in edits:
            edit.file_path.write_text(edit.updated_source, encoding=c.DEFAULT_ENCODING)
        after = tm.ok(
            infra_subprocess.capture(
                command, cwd=workspace.repository_root, options=options
            )
        )
        tm.that(after.stdout, eq=before.stdout)

    @staticmethod
    def _assertion_rules() -> Sequence[p.Infra.RopeContractRule]:
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
        tm.ok(runpy.run_path(str(path))["evidence"])
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: source},
                )
            )
        tm.that(edits, empty=True)
        tm.ok(runpy.run_path(str(path))["evidence"])

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
                    "evidence = (u, type(Payload().values), "
                    "Payload.model_json_schema())\n"
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
                    "evidence = (type(Payload().values), Payload.model_json_schema())\n"
                ),
                "no preceding unconditional import",
            ),
        ],
        ids=["module-shadow", "parameter-shadow", "late-import"],
    )
    def test_destination_binding_refuses_invalid_publication(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
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
