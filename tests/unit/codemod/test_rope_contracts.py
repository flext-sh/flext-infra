"""Real Pydantic consumer evidence for native Rope contract migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import runpy
from contextlib import redirect_stderr
from io import StringIO
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, p, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeContractCatalog:
    """Validate rule ownership, catalogue composition and public export retirement."""

    @staticmethod
    @pytest.mark.parametrize(
        "source",
        [
            "__all__ = ['u']; side_effect()\n",
            "side_effect(); __all__ = ['u']\n",
            "PUBLIC = __all__ = ['u']\n",
            "__all__ = ['u']\n__all__ += ['kept']\n",
        ],
    )
    def test_export_retirement_refuses_shared_lines_and_chained_targets(
        source: str,
    ) -> None:
        """The owned writer cannot discard effects or another public binding."""
        with pytest.raises(ValueError, match=r"__all__|exports"):
            u.Infra.remove_runtime_alias_export(source, alias="u")

    @staticmethod
    def test_export_retirement_keeps_an_explicit_empty_literal() -> None:
        """Empty literal exports stay explicit, so unrelated statements stay intact."""
        updated = u.Infra.remove_runtime_alias_export("__all__ = ['u']\n", alias="u")
        declarations = u.Infra.runtime_alias_bindings(updated, alias="__all__")
        tm.that(len(declarations), eq=1)
        value = declarations[0].value
        if not isinstance(value, ast.List):
            pytest.fail("export retirement must emit a literal list")
        tm.that(value.elts, empty=True)

    @staticmethod
    def test_catalog_phases_roundtrip_and_reject_unknown_values(
        tmp_path: Path,
    ) -> None:
        """Configured rules retain enum identities, never an unvalidated phase."""
        for declared in u.Infra.declared_contract_rules(tmp_path):
            rule = m.Infra.RopeContractRule.model_validate(
                declared, from_attributes=True
            )
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
    def test_workspace_loads_only_declared_member_overlays(tmp_path: Path) -> None:
        """One workspace catalogue discovers member policy without directory sweeps."""
        packaged = tuple(rule.id for rule in u.Infra.declared_contract_rules(tmp_path))
        member, _ = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="governed",
            package_name="governed",
        )
        (tmp_path / ".gitmodules").write_text(
            '[submodule "governed"]\n\tpath = governed\n\turl = https://example.invalid/governed.git\n',
            encoding=c.DEFAULT_ENCODING,
        )
        overlay = member / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text(
            "rules:\n  - id: governed-member-contract\n"
            "    pattern: '${helper}(${value})'\n"
            "    goal: 'str(${value})'\n"
            "    arguments:\n      helper: name=consumer.helpers.Helpers.render\n",
            encoding=c.DEFAULT_ENCODING,
        )
        outsider = tmp_path / "not-declared" / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        outsider.parent.mkdir(parents=True)
        outsider.write_text("not valid policy", encoding=c.DEFAULT_ENCODING)
        rules = u.Infra.declared_contract_rules(tmp_path)
        tm.that(
            tuple(rule.id for rule in rules), eq=(*packaged, "governed-member-contract")
        )
        tm.that(rules[-1].source_states[0].path, eq=overlay)

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
    @pytest.mark.parametrize("asynchronous", [False, True])
    @pytest.mark.parametrize(
        "rejected", ["", "callback", "prototype", "snapshot", "default", "decorator"]
    )
    def test_native_delegation_contract(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        *,
        asynchronous: bool,
        rejected: str,
    ) -> None:
        """Preserve calling conventions and dynamic ports, or reject before effects."""
        workspace, path = rope_contract_consumer
        prefix = "async " if asynchronous else ""
        source = (
            "from __future__ import annotations\n"
            "from functools import update_wrapper\n"
            "from collections.abc import Callable\n"
            "from typing import Concatenate, get_type_hints, overload\n"
            "from pydantic import ConfigDict\n"
            "import asyncio\n"
            "import inspect\n"
            "class Binding[Receiver, Service, **Params, Result]:\n"
            "    def __init__(self, operation: Callable[[Receiver], "
            "Callable[Params, Result]], prototype: "
            "Callable[Concatenate[Service, Params], Result]) -> None:\n"
            "        self.operation = operation\n"
            "        def invoke(self: Receiver, *args: Params.args, "
            "**kwargs: Params.kwargs) -> Result:\n"
            "            return operation(self)(*args, **kwargs)\n"
            "        update_wrapper(invoke, prototype)\n"
            "        invoke.__annotations__ = get_type_hints(prototype)\n"
            "        self.unbound = invoke\n"
            "    @overload\n"
            "    def __get__(self, instance: None, owner: type[Receiver] | None "
            "= None) -> Callable[Concatenate[Receiver, Params], Result]: ...\n"
            "    @overload\n"
            "    def __get__(self, instance: Receiver, owner: type[Receiver] | None "
            "= None) -> Callable[Params, Result]: ...\n"
            "    def __get__(self, instance: Receiver | None, "
            "owner: type[Receiver] | None = None):\n"
            "        if instance is None:\n"
            "            return self.unbound\n"
            "        return self.operation(instance)\n"
            "class Port:\n"
            "    def __init__(self, bias):\n"
            "        self.bias = bias\n"
            f"    {prefix}def perform[Item: int](self, item: Item, /, "
            "extra: int | None = None, *values: int, "
            "flag: bool = True, **labels: str) -> tuple:\n"
            "        '''Perform the selected port operation.'''\n"
            "        if item < 0:\n"
            "            raise ValueError('native failure')\n"
            "        return (self.bias, item, extra, values, flag, labels)\n"
            "class Other:\n"
            "    def perform(self, item):\n"
            "        return item\n"
            "class Application:\n"
            "    port: Port\n"
            "    model_config = ConfigDict(extra='forbid', "
            "ignored_types=(Binding, str), frozen=True)\n"
            "    @staticmethod\n"
            "    def bind[Service, **Params, Result](operation: "
            "Callable[[Application], Callable[Params, Result]], "
            "prototype: Callable[Concatenate[Service, Params], Result]) "
            "-> Binding[Application, Service, Params, Result]:\n"
            "        return Binding(operation, prototype)\n"
            "    execute = bind(lambda self: self.port.perform, Port.perform)\n"
            "    def __init__(self):\n"
            "        self.port = Port(1)\n"
            "application = Application()\n"
            "def complete(value):\n"
            "    return asyncio.run(value) if inspect.isawaitable(value) else value\n"
            "first = complete(application.execute(3, 4, 5, flag=False, label='a'))\n"
            "application.port = Port(2)\n"
            "second = complete(Application.execute(application, 3, label='b'))\n"
            "try:\n"
            "    complete(application.execute(-1))\n"
            "except ValueError as error:\n"
            "    failure = str(error)\n"
            "evidence = (first, second, failure, "
            "str(inspect.signature(Application.execute)), "
            "Application.execute.__doc__)\n"
            "default_identity = inspect.signature(Application.execute)."
            "parameters['extra'].default is inspect.signature(Port.perform)."
            "parameters['extra'].default\n"
        )
        if rejected == "callback":
            source = source.replace(
                "lambda self: self.port.perform", "lambda self: self.port.perform()"
            )
        elif rejected == "prototype":
            source = source.replace(
                "self.port.perform, Port.perform)", "self.port.perform, Other.perform)"
            )
        elif rejected == "snapshot":
            source = source.replace(
                "return self.operation(instance)", "return self.unbound"
            )
        elif rejected == "default":
            source = source.replace("extra: int | None = None", "extra: int = int()")
        elif rejected == "decorator":
            source = source.replace(
                "class Port:",
                "decorator_events = []\ndef decorate(function):\n"
                "    decorator_events.append('decorate')\n"
                "    return function\nclass Port:",
            )
            source = source.replace(
                f"    {prefix}def perform[Item: int](self, item: Item",
                f"    @decorate\n    {prefix}def perform[Item: int](self, item: Item",
            )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rules = tuple(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if m.Infra.RopeContractRule.model_validate(
                rule, from_attributes=True
            ).operation
            == "materialize-delegations"
        )
        tm.that(len(rules), eq=1)
        if asynchronous and not rejected:
            with pytest.raises(ValueError, match="async prototype"):
                u.Infra.plan_contract_rules(workspace, {path: source}, rules)
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
            return
        if rejected:
            decorated = runpy.run_path(str(path)) if rejected == "decorator" else None
            if decorated is not None:
                tm.that(decorated["decorator_events"], eq=["decorate"])
            with pytest.raises(
                ValueError,
                match=r"delegation|descriptor|prototype|port|default|callback|async",
            ):
                u.Infra.plan_contract_rules(workspace, {path: source}, rules)
            if decorated is not None:
                tm.that(decorated["decorator_events"], eq=["decorate"])
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
            return
        before = runpy.run_path(str(path))["evidence"]
        sources = {
            workspace.repository_root / resource.path: resource.read()
            for resource in workspace.rope_project.get_python_files()
        }
        sources[path] = source
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, sources, rules))
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(
            updated, contains=f"{prefix}def execute[Item: int](self, item: Item, /,"
        )
        tm.that(updated, contains="ignored_types=(str,)")
        tm.that(updated, contains="extra='forbid'")
        tm.that(updated, contains="frozen=True")
        tm.that("def bind[" in updated, eq=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        after = runpy.run_path(str(path))
        tm.that(after["evidence"], eq=before)
        tm.that(after["default_identity"], eq=True)
        tm.that(
            u.Cli.atomic_verify_binary_file_states(
                tuple(
                    m.Cli.AtomicFileState.model_validate(state, from_attributes=True)
                    for state in edits[0].source_states
                )
            ).failure,
            eq=True,
        )
        sources[path] = updated
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, sources, rules)),
            empty=True,
        )


class TestsFlextInfraRopeConstructorContracts:
    """Preserve constructor targets, injected ports and native adapter behavior."""

    @staticmethod
    @pytest.mark.parametrize("readonly", [False, True])
    @pytest.mark.parametrize("chained", [False, True])
    def test_constructor_target_preserves_arguments_and_noncall_references(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        *,
        readonly: bool,
        chained: bool,
    ) -> None:
        """Replace native callees without a signature catalogue or argument rewrite."""
        workspace, path = rope_contract_consumer
        source = (
            "events = []\n"
            "class Service:\n"
            "    def __init__(self, value, *, label, registry=None):\n"
            "        self.value, self.label = value, label\n"
            "class Api(Service):\n"
            "    pass\n"
            "class FinalApi(Api):\n"
            "    pass\n"
            "class Child(Service):\n"
            "    pass\n"
            "selected: type[Service] = Service\n"
            "def load():\n"
            "    events.append('positional')\n"
            "    return 3\n"
            "def tag():\n"
            "    events.append('keyword')\n"
            "    return 'label'\n"
            "result = Service(load(), label=tag())\n"
            "explicit = Service(load(), label=tag(), registry=object())\n"
            "evidence = (result.value, result.label, tuple(events))\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        module = f"{path.parent.name}.{path.stem}"
        rule = m.Infra.RopeContractRule(
            id="service-constructor-composition",
            pattern="${service}",
            goal="Api",
            arguments={"service": f"name={module}.Service"},
            bindings={"Api": f"{module}.Api"},
            call_target="service",
            missing_keywords=("registry",),
        )
        rules = [rule]
        target = "Api"
        if chained:
            rules.append(
                m.Infra.RopeContractRule(
                    id="service-constructor-final-composition",
                    pattern="${service}",
                    goal="FinalApi",
                    arguments={"service": f"name={module}.Api"},
                    bindings={"FinalApi": f"{module}.FinalApi"},
                    call_target="service",
                    missing_keywords=("registry",),
                )
            )
            target = "FinalApi"
        sources = {path: source}
        edits = tm.ok(
            u.Infra.plan_contract_rules(
                workspace,
                MappingProxyType(sources) if readonly else sources,
                rules,
            )
        )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(updated, contains=f"result = {target}(load(), label=tag())")
        tm.that(updated, contains="class Child(Service):")
        tm.that(updated, contains="selected: type[Service] = Service")
        tm.that(
            updated,
            contains="explicit = Service(load(), label=tag(), registry=object())",
        )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        tm.that(runpy.run_path(str(path))["evidence"], eq=before)
        tm.that(
            tm.ok(u.Infra.plan_contract_rules(workspace, {path: updated}, rules)),
            empty=True,
        )

    @staticmethod
    def test_constructor_missing_port_proof_rejects_expanded_keywords(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Unproven expanded keywords never authorize a second composition graph."""
        workspace, path = rope_contract_consumer
        source = (
            "class Service:\n    pass\n"
            "class Api(Service):\n    pass\n"
            "kwargs = {}\nresult = Service(**kwargs)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        module = f"{path.parent.name}.{path.stem}"
        rule = m.Infra.RopeContractRule(
            id="service-constructor-injected-port",
            pattern="${service}",
            goal="Api",
            arguments={"service": f"name={module}.Service"},
            bindings={"Api": f"{module}.Api"},
            call_target="service",
            missing_keywords=("registry",),
        )
        with pytest.raises(ValueError, match="expanded keywords"):
            u.Infra.plan_contract_rules(workspace, {path: source}, (rule,))
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_aliased_adapter_preserves_validation_and_failure_modes(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """The public constructor preserves native coercion and rejection."""
        source = (
            "from pydantic import TypeAdapter as Parse, ValidationError\n"
            "from flext_tests import tm\n"
            "def consume():\n"
            "    adapter = Parse(list[int])\n"
            "    accepted = adapter.validate_json('[1, \"2\"]')\n"
            "    try:\n"
            "        adapter.validate_python(['invalid'])\n"
            "    except ValidationError as error:\n"
            "        return accepted, tuple(item['type'] for item in error.errors())\n"
            "    tm.reject('invalid input was accepted')\n"
            "evidence = consume()\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)


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
            ("tuple[str, ...]", "list", "tuple"),
            ("frozenset[str]", "set", "frozenset"),
            ("Mapping[str, int]", "list", "dict"),
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
            ("Sequence", "list", True),
            ("MutableSequence", "list", False),
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


class TestsFlextInfraRopeTypePositionContracts:
    """Distinguish quoted type references from Literal and Annotated payload data."""

    @staticmethod
    @pytest.mark.parametrize("alias", [False, True])
    def test_quoted_type_positions_require_explicit_declaring_source_repair(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        *,
        alias: bool,
    ) -> None:
        """A quoted owner is not converted into a runtime type by string surgery."""
        workspace, path = rope_contract_consumer
        declaration = "type Contract = Sequence['Domain.Item']\n" if alias else ""
        annotation = "Contract" if alias else "Sequence['Domain.Item']"
        source = (
            "from collections.abc import Sequence\n"
            "from pydantic import BaseModel, Field\n"
            "class Domain:\n"
            "    class Item(BaseModel):\n"
            "        label: str\n"
            f"{declaration}"
            "class Payload(BaseModel):\n"
            f"    values: {annotation} = Field(default_factory=list)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="fix the declaring source"):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_literal_and_annotated_payload_strings_remain_data(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """The existing native payload classifier never unquotes literal metadata."""
        source = (
            "from collections.abc import Sequence\n"
            "from typing import Annotated, Literal\n"
            "from pydantic import BaseModel, Field\n"
            "class Payload(BaseModel):\n"
            "    values: Annotated[Sequence[Literal['entry']], 'metadata'] = "
            "Field(default_factory=list)\n"
            "first, second = Payload(), Payload()\n"
            "evidence = (first.values is not second.values, first.model_dump_json(), "
            "second.model_dump_json())\n"
        )
        u.Tests.prove_contract_migration(rope_contract_consumer, source)
        _workspace, path = rope_contract_consumer
        updated = path.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(updated, contains="Literal['entry']")
        tm.that(updated, contains="'metadata'")


class TestsFlextInfraRopeLoggingContracts:
    """Preserve logger identity, emission contracts and CLI diagnostic effects."""

    @staticmethod
    @pytest.mark.parametrize(
        ("declaration", "factory"),
        [
            ("from logging import getLogger as acquire", "acquire"),
            ("import logging as diagnostics", "diagnostics.getLogger"),
            ("from structlog import get_logger as acquire", "acquire"),
            ("import structlog as diagnostics", "diagnostics.get_logger"),
        ],
    )
    def test_logging_factory_identity_imports_and_real_printf(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        declaration: str,
        factory: str,
    ) -> None:
        """Native aliases migrate once, complete imports and emit through Core."""
        workspace, path = rope_contract_consumer
        source = (
            f"{declaration}\n"
            "names = []\n"
            "def module_name():\n"
            "    names.append('evaluated')\n"
            "    return 'contract.consumer'\n"
            f"logger = {factory}(module_name())\n"
            "logger.info('worker %s', 'ready')\n"
            "logger.debug('filtered %s %s', 'one argument')\n"
            "evidence = tuple(names)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        stream = StringIO()
        original_settings, original_options = u.logging_settings(), u.logging_options()
        handler = u.create_logging_handler(stream=stream)
        try:
            selected = u.resolve_logging_settings(
                runtime_settings=original_settings,
                log_level="INFO",
                debug=False,
                trace=False,
            )
            u.configure_structlog(
                settings=m.StructlogOptions(handlers=(handler,), async_logging=False),
                runtime_settings=selected,
            )
            namespace = runpy.run_path(str(path))
            tm.that(namespace["evidence"], eq=("evaluated",))
            tm.that(stream.getvalue(), contains="worker ready")
            tm.fail("filtered" in stream.getvalue())
        finally:
            u.configure_structlog(
                settings=original_options, runtime_settings=original_settings
            )
            handler.close()
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
        # The retired native factory import had a real use before this cut.
        # No wholesale unused-import sweep is part of the contract planner.
        tm.fail(declaration in updated)

    @staticmethod
    @pytest.mark.parametrize(
        "source",
        [
            (
                "import logging\n"
                "def configure():\n"
                "    logger = logging.getLogger('thirdparty')\n"
                "    logger.addHandler(logging.NullHandler())\n"
                "    return logger\n"
            ),
            (
                "from logging import getLogger\n"
                "__all__ = ['logger']\n"
                "logger = getLogger(__name__)\n"
                "logger.info('exported interface')\n"
            ),
            (
                "from logging import getLogger\n"
                "logger = getLogger(__name__)\n"
                "def inject(logger):\n"
                "    return logger\n"
                "injected = inject(logger)\n"
            ),
            (
                "from logging import getLogger\n"
                "logger = getLogger(__name__)\n"
                "alias = logger\n"
                "alias.info('escaped alias')\n"
            ),
            (
                "import logging\n"
                "logger = logging.getLogger()\n"
                "logger.info('native root logger')\n"
            ),
            (
                "import logging\n"
                "logger = logging.getLogger(None)\n"
                "logger.info('explicit native root logger')\n"
            ),
            (
                "import logging\n"
                "class Service:\n"
                "    logger = logging.getLogger(__name__)\n"
                "    def run(self):\n"
                "        self.logger.info('service interface')\n"
            ),
            (
                "import logging\n"
                "def run(logging):\n"
                "    logger = logging.getLogger(__name__)\n"
                "    logger.info('parameter is not the module')\n"
            ),
            (
                "import structlog\n"
                "def run(structlog):\n"
                "    return structlog.get_logger()\n"
                "HELP = 'structlog.get_logger() and logging.getLogger(__name__)'\n"
            ),
            (
                "from structlog import get_logger as acquire\n"
                "def run(__name__):\n"
                "    return acquire()\n"
            ),
        ],
        ids=[
            "handler-setup",
            "export",
            "di-escape",
            "assigned-alias",
            "root-logger",
            "none-root-logger",
            "service-interface",
            "stdlib-shadow",
            "structlog-shadow-and-prose",
            "implicit-module-name-shadow",
        ],
    )
    def test_logging_factory_preserves_unproven_native_interfaces(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        source: str,
    ) -> None:
        """Unrelated symbols and richer native interfaces are never guessed."""
        workspace, path = rope_contract_consumer
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(edits, empty=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.parametrize(
        "emission",
        [
            "logger.log(logging.WARNING, 'numeric contract')",
            "logger.warn('deprecated native alias')",
            "logger.exception('implicit exception state is not proven')",
            "logger.info('event', extra={'native': 'context'})",
            "logger.info('event', stack_info=True)",
            "logger.info('event', stacklevel=2)",
            "logger.info(msg='keyword native message')",
            "logger.info(42)",
        ],
    )
    def test_logging_factory_blocks_unproven_emission_signatures_before_effects(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        emission: str,
    ) -> None:
        """A method name alone never proves printf, context or level equivalence."""
        workspace, path = rope_contract_consumer
        source = (
            "import logging\n"
            "logger = logging.getLogger('contract.arguments')\n"
            f"{emission}\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(
            ValueError, match=r"unproven native logging|proven string message"
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.parametrize("factory_arguments", ["'contract.bound'", ""])
    def test_structlog_bound_context_and_stdout_are_not_collapsed(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        factory_arguments: str,
    ) -> None:
        """Only the native factory changes; bound context and output stay authored."""
        workspace, path = rope_contract_consumer
        source = (
            "from structlog import get_logger as acquire\n"
            "from io import StringIO\n"
            "from contextlib import redirect_stdout\n"
            f"logger = acquire({factory_arguments}).bind(component='receiver')\n"
            "output = StringIO()\n"
            "with redirect_stdout(output):\n"
            "    print('result')\n"
            "logger.info('bound %s', 'event')\n"
            "HELP = 'acquire(\"contract.bound\") is prose'\n"
            "evidence = (output.getvalue(), HELP)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(updated, contains=".bind(component='receiver')")
        tm.that(updated, contains="logger.info('bound %s', 'event')")
        tm.that(updated, contains="print('result')")
        tm.that(updated, contains="HELP = 'acquire(\"contract.bound\") is prose'")
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        stream = StringIO()
        original_settings, original_options = u.logging_settings(), u.logging_options()
        handler = u.create_logging_handler(stream=stream)
        try:
            u.configure_structlog(
                settings=m.StructlogOptions(handlers=(handler,), async_logging=False),
                runtime_settings=u.resolve_logging_settings(
                    runtime_settings=original_settings, log_level="INFO", debug=False
                ),
            )
            namespace = runpy.run_path(str(path))
            tm.that(
                namespace["evidence"],
                eq=("result\n", 'acquire("contract.bound") is prose'),
            )
            tm.that(stream.getvalue(), contains="bound event")
            tm.that(stream.getvalue(), contains="receiver")
        finally:
            u.configure_structlog(
                settings=original_options, runtime_settings=original_settings
            )
            handler.close()

    @staticmethod
    @pytest.mark.parametrize("implementation", ["_native_logging", "moved_logging"])
    def test_factory_contract_keeps_only_the_native_backend_unrewritten(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        implementation: str,
    ) -> None:
        """A constructor's native factory survives; an importing consumer does not."""
        workspace, path = rope_contract_consumer
        package = path.parent
        namespace = package.name
        backend_path = package / "_logging_backend.py"
        backend = (
            "import structlog\n"
            "class NativeBackend:\n"
            "    def create(self, name):\n"
            "        return structlog.get_logger('native.backend')\n"
        )
        (package / f"{implementation}.py").write_text(
            "from ._logging_backend import NativeBackend\n"
            "class Logging:\n"
            "    @staticmethod\n"
            "    def fetch(name):\n"
            "        return NativeBackend().create(name)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "logging_api.py").write_text(
            f"from .{implementation} import Logging as Utilities\n",
            encoding=c.DEFAULT_ENCODING,
        )
        backend_path.write_text(backend, encoding=c.DEFAULT_ENCODING)
        consumer = (
            "from structlog import get_logger as acquire\n"
            "from .logging_api import Utilities\n"
            "logger = acquire('consumer.backend')\n"
            "logger.info('consumer event')\n"
        )
        path.write_text(consumer, encoding=c.DEFAULT_ENCODING)
        rules = tuple(
            m.Infra.RopeContractRule.model_validate(
                rule, from_attributes=True
            ).model_copy(
                update={
                    "implementation_owner": (
                        f"{namespace}.logging_api",
                        "Utilities.fetch",
                    )
                }
            )
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.implementation_owner is not None
        )
        edits = tm.ok(
            u.Infra.plan_contract_rules(
                workspace, {backend_path: backend, path: consumer}, rules
            )
        )
        tm.that(tuple(edit.file_path for edit in edits), eq=(path,))
        tm.that(backend_path.read_text(encoding=c.DEFAULT_ENCODING), eq=backend)
        tm.that(edits[0].updated_source, contains="u.fetch_logger('consumer.backend')")

    @staticmethod
    def test_logging_factory_keeps_live_imports_and_a_richer_utilities_facade(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
    ) -> None:
        """Retire only the disappeared factory use, not a live alias or CLI facade."""
        workspace, path = rope_contract_consumer
        source = (
            "from flext_cli import u\n"
            "import logging as diagnostics\n"
            "from logging import getLogger as acquire\n"
            "level = diagnostics.WARNING\n"
            "logger = acquire('contract.imports')\n"
            "logger.info('retained %s', level)\n"
            "evidence = u.Cli.env_read("
            "'consumer_key', {'consumer_key': 'value'}).unwrap()\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(updated, contains="from flext_cli import u")
        tm.that(updated, contains="import logging as diagnostics")
        tm.fail("from logging import getLogger" in updated)
        tm.fail("from flext_core import u" in updated)

    @staticmethod
    def test_logging_factory_refuses_a_shadowed_destination(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
    ) -> None:
        """A correct source identity cannot overwrite an authored u binding."""
        workspace, path = rope_contract_consumer
        source = (
            "from logging import getLogger\n"
            "u = 'authored consumer binding'\n"
            "logger = getLogger('contract.shadow')\n"
            "logger.info('authored %s', u)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match=r"destination u.fetch_logger is shadowed"):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.parametrize("literal", [True, False])
    def test_cli_result_error_retires_only_literal_verbose_flags(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        *,
        literal: bool,
    ) -> None:
        """Keep native receiver and argument evaluation when removing a flag."""
        workspace, path = rope_contract_consumer
        source = (
            "from flext_cli import u as cli\n"
            "from flext_core import r\n"
            "calls = []\n"
            "def result():\n"
            "    calls.append('result')\n"
            "    return r.fail('command error')\n"
            "def unrelated(emit):\n"
            f"    emit(result(), verbose={literal})\n"
            "def report():\n"
            f"    cli.Cli.commands_emit_result_error(result(), verbose={literal})\n"
            "report()\n"
            "evidence = tuple(calls)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        edits = tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(updated, contains="cli.Cli.commands_emit_result_error(result())")
        tm.that(updated, contains=f"emit(result(), verbose={literal})")
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        stream = StringIO()
        original_settings, original_options = u.logging_settings(), u.logging_options()
        handler = u.create_logging_handler(stream=stream)
        try:
            u.configure_structlog(
                settings=m.StructlogOptions(handlers=(handler,), async_logging=False),
                runtime_settings=original_settings,
            )
            with redirect_stderr(stream):
                namespace = runpy.run_path(str(path))
            tm.that(namespace["evidence"], eq=("result",))
            tm.that(stream.getvalue(), contains="command error")
        finally:
            u.configure_structlog(
                settings=original_options, runtime_settings=original_settings
            )
            handler.close()
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
    @pytest.mark.parametrize("expression", ["detail()", "settings.verbose", "verbose"])
    def test_cli_result_error_never_discards_authored_argument_evaluation(
        rope_contract_consumer: t.Pair[
            p.Infra.RopeWorkspaceDsl, t.Infra.RopeSourcePath
        ],
        expression: str,
    ) -> None:
        """Keep call, property and name lookup effects or fail before publication."""
        workspace, path = rope_contract_consumer
        source = (
            "from flext_cli import u as cli\n"
            "def report(result, settings, verbose, detail):\n"
            f"    cli.Cli.commands_emit_result_error(result, verbose={expression})\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(
            ValueError, match="cannot discard authored evaluation of verbose"
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
