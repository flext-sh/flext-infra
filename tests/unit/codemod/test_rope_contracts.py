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
    def _plan(
        rope: p.Infra.RopeWorkspaceDsl,
        path: Path,
        source: str,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan the contract-normalization cutover over one source.

        Returns:
            The planning verdict, never published.

        """
        return u.Infra.plan_semantic_cutover(
            c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
            rope_workspace=rope,
            sources={path: source},
        )

    @staticmethod
    def _seed(tmp_path: Path, source: str) -> tuple[Path, Path]:
        """Write one consumer module into a fresh workspace.

        Returns:
            The repository root and the consumer module path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        return root, path

    @staticmethod
    def _edits(
        root: Path,
        path: Path,
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Plan the cutover over the module as written on disk.

        Returns:
            The planned edits.

        """
        with infra.rope_workspace(root) as rope:
            return tm.ok(
                TestsFlextInfraRopeContracts._plan(
                    rope,
                    path,
                    path.read_text(encoding=c.DEFAULT_ENCODING),
                ),
            )

    @staticmethod
    def _rejects(root: Path, path: Path, match: str) -> None:
        """Prove planning the module on disk escapes loud and changes nothing."""
        source = path.read_text(encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=match),
        ):
            TestsFlextInfraRopeContracts._plan(rope, path, source)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)

    @staticmethod
    def test_catalog_phases_roundtrip_and_reject_unknown_values(
        tmp_path: Path,
    ) -> None:
        """Configured rules retain enum identities, never an unvalidated phase."""
        for rule in u.Infra.declared_contract_rules(tmp_path):
            payload = rule.model_dump(round_trip=True)
            restored = m.Infra.RopeContractRule.model_validate_json(
                rule.model_dump_json(round_trip=True)
            )
            tm.that(restored.phase, eq=c.Infra.SemanticCutoverPhase(rule.phase))
            payload["phase"] = "".join(c.Infra.SemanticCutoverPhase)
            with pytest.raises(ValueError, match="phase"):
                m.Infra.RopeContractRule.model_validate(payload)

    @staticmethod
    def test_repository_overlay_composes_after_packaged_rules(
        tmp_path: Path,
    ) -> None:
        """A repository's own rules extend the universal catalogue, in order."""
        packaged = tuple(rule.id for rule in u.Infra.declared_contract_rules(tmp_path))
        overlay = tmp_path / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        overlay.parent.mkdir(parents=True)
        overlay.write_text(
            "rules:\n"
            "  - id: consumer-own-helper\n"
            "    pattern: '${helper}(${value})'\n"
            "    goal: 'str(${value})'\n"
            "    arguments:\n"
            "      helper: name=consumer.helpers.Helpers.render\n",
            encoding=c.DEFAULT_ENCODING,
        )
        composed = tuple(rule.id for rule in u.Infra.declared_contract_rules(tmp_path))
        tm.that(composed, eq=(*packaged, "consumer-own-helper"))

    @staticmethod
    def test_repository_overlay_cannot_redeclare_a_packaged_rule(
        tmp_path: Path,
    ) -> None:
        """A rule identity has one owner; an overlay redeclaration fails loud."""
        packaged = u.Infra.declared_contract_rules(tmp_path)[0]
        overlay = tmp_path / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        overlay.parent.mkdir(parents=True)
        overlay.write_text(
            "rules:\n"
            f"  - id: {packaged.id}\n"
            f"    pattern: {packaged.pattern!r}\n"
            f"    goal: {packaged.goal!r}\n"
            "    arguments: {}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with pytest.raises(ValueError, match="duplicate Rope contract rule"):
            u.Infra.declared_contract_rules(tmp_path)

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
            (
                "values: dict[str, list[int]] = "
                "Field(default_factory=dict, description='d')"
            ),
            (
                "values: Meta[list[str], Field(description='d')] = "
                "Field(default_factory=list)"
            ),
            (
                "values: Meta[dict[str, list[int]], Field(min_length=0)] = "
                "Field(default_factory=dict)"
            ),
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
        u.Tests.prove_contract_migration(rope_contract_consumer, source)

    @staticmethod
    def test_factory_migration_cannot_repeat_annotation_effects(
        tmp_path: Path,
    ) -> None:
        """A repeated type expression must not run an authored callback twice."""
        root, path = TestsFlextInfraRopeContracts._seed(
            tmp_path,
            "from pydantic import BaseModel, Field\n"
            "events = []\n"
            "def element_type():\n"
            "    events.append('annotation')\n"
            "    return str\n"
            "class Payload(BaseModel):\n"
            "    values: list[element_type()] = Field(default_factory=list)\n"
            "evidence = (tuple(events), Payload().model_dump_json())\n",
        )
        TestsFlextInfraRopeContracts._rejects(root, path, r"annotation.*repeat")

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
        root, path = TestsFlextInfraRopeContracts._seed(
            tmp_path,
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
            "evidence = (tuple(events), Payload().model_dump_json())\n",
        )
        TestsFlextInfraRopeContracts._rejects(root, path, r"annotation.*reorder")

    @staticmethod
    def test_unrelated_field_factory_is_not_a_pydantic_field(tmp_path: Path) -> None:
        """Same-spelled functions do not establish a Pydantic identity."""
        source = (
            "def Field(*, default_factory):\n"
            "    return default_factory()\n"
            "values: list[str] = Field(default_factory=list)\n"
        )
        root, path = TestsFlextInfraRopeContracts._seed(tmp_path, source)
        tm.that(TestsFlextInfraRopeContracts._edits(root, path), empty=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_shadowed_dictionary_constructor_retains_its_own_contract(
        tmp_path: Path,
    ) -> None:
        """Inherited BaseModel.dict is not lexical, but a real local dict is."""
        root, path = TestsFlextInfraRopeContracts._seed(
            tmp_path,
            "from builtins import dict as BuiltinDictionary\n"
            "from pydantic import BaseModel, Field, ConfigDict\n"
            "class dict(BuiltinDictionary):\n"
            "    pass\n"
            "class Payload(BaseModel):\n"
            "    model_config = ConfigDict(arbitrary_types_allowed=True)\n"
            "    values: dict[str, list[int]] = Field(default_factory=dict)\n"
            "evidence = type(Payload().values) is dict\n",
        )
        tm.that(runpy.run_path(str(path))["evidence"], eq=True)
        tm.that(TestsFlextInfraRopeContracts._edits(root, path), empty=True)
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
            TestsFlextInfraRopeContracts._plan(rope, path, source)
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
