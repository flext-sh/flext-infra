"""Exercise declared utility ownership through the public semantic phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSelfFacadeCutover:
    """Preserve eager execution, lexical bindings and standalone consumers."""

    @staticmethod
    def test_external_declaration_import_survives_a_local_model_mask(
        tmp_path: Path,
    ) -> None:
        """A distinct model binding cannot replace a permitted external helper."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        declarations = package / "_models"
        declarations.mkdir()
        (declarations / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        consumer = declarations / "consumer.py"
        sources = {
            package / c.Infra.INIT_PY: "from .models import Models as m\n",
            package / c.Infra.MODELS_PY: (
                "from flext_core import m as core_m\n"
                "class Models(core_m):\n"
                "    empty = None\n"
                "__all__ = ('Models',)\n"
            ),
            consumer: (
                f"from {package.name} import m\n"
                "from flext_core import t, u\n"
                "from typing_extensions import TypeForm\n"
                "class Consumer(m.ContractModel):\n"
                "    values: t.MutableSequenceOf[str] = m.Field("
                "default_factory=u.empty(TypeForm(t.MutableSequenceOf[str])), "
                "description='Consumer values')\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        tm.that(edits, empty=True)
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}._models.consumer import Consumer; "
                        "assert Consumer().values == []; "
                        "print('external declaration accepted')"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            root / c.Infra.DEFAULT_SRC_DIR
                        )
                    }
                ),
            )
        )
        tm.that(result.stdout.strip(), eq="external declaration accepted")

    @staticmethod
    @pytest.mark.parametrize("tier", ["private", "public", "examples"])
    @pytest.mark.parametrize("mutable", [False, True])
    def test_declaring_model_receiver_preserves_default_factory(
        tmp_path: Path,
        tier: str,
        *,
        mutable: bool,
    ) -> None:
        """Execute the rewritten model declaration through a real package import."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        if tier == "private":
            declarations = package / "_models"
            declarations.mkdir()
            (declarations / c.Infra.INIT_PY).write_text("", encoding="utf-8")
            consumer = declarations / "consumer.py"
            module = f"{package.name}._models.consumer"
        elif tier == "public":
            consumer = package / c.Infra.MODELS_PY
            module = f"{package.name}.models"
        else:
            declarations = root / tier
            declarations.mkdir()
            (declarations / c.Infra.INIT_PY).write_text("", encoding="utf-8")
            consumer = declarations / c.Infra.MODELS_PY
            module = f"{tier}.models"
        source = (
            "from __future__ import annotations\n"
            "from flext_core import m, t\n"
            f"type Bag[T] = t.{'MutableSequenceOf' if mutable else 'SequenceOf'}[T]\n"
            "class Consumer(m.ContractModel):\n"
            '    """Consumer-owned collection declaration."""\n'
            "    values: Bag[str] = m.Field(default_factory=list, "
            'description="Consumer values")\n'
        )
        consumer.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={consumer: source},
                )
            )
            tm.that(edits, empty=mutable)
            for edit in edits:
                tm.ok(u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source))
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={consumer: consumer.read_text(encoding="utf-8")},
                )
            )
        tm.that(remaining, empty=True)
        output = tm.ok(
            u.Cli.run(
                [
                    sys.executable,
                    "-c",
                    (
                        f"from {module} import Consumer; "
                        "first, second = Consumer(), Consumer(); "
                        "first.values.append('consumer'); "
                        "assert second.values == []; "
                        "assert Consumer.model_validate_json("
                        "first.model_dump_json()).values == first.values; "
                        "print('declaration contract accepted')"
                    ),
                ],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: os.pathsep.join((
                            str(root / c.Infra.DEFAULT_SRC_DIR),
                            str(root),
                        ))
                    }
                ),
            )
        )
        tm.that(output.stdout.strip(), eq="declaration contract accepted")

    @staticmethod
    @pytest.mark.parametrize("tier", ["_models", "models", "examples"])
    @pytest.mark.parametrize("reference", ["u", "tools", "namespace.u", "u.Domain"])
    @pytest.mark.parametrize("stateful", [False, True])
    def test_model_utility_calls_bind_only_lazy_static_owners(
        tmp_path: Path, tier: str, reference: str, *, stateful: bool
    ) -> None:
        """Cold models use source-proven owners, never their own utility facade."""
        root, production = u.Tests.create_lazy_init_workspace(tmp_path)
        package = root / "examples" if tier == "examples" else production
        package.mkdir(exist_ok=True)
        helpers = package / "_utilities"
        helpers.mkdir()
        models = package / "_models" if tier != "models" else package
        models.mkdir(exist_ok=True)
        (models / c.Infra.INIT_PY).touch()
        consumer = models / "consumer.py" if tier != "models" else package / "models.py"
        imported = (
            f"import {package.name} as namespace\n"
            if reference == "namespace.u"
            else (
                f"from {package.name} import u as "
                f"{reference.split('.', maxsplit=1)[0]}\n"
            )
        )
        sources = {
            package / c.Infra.INIT_PY: (
                "from flext_core import install_lazy_exports\n"
                "__getattr__ = install_lazy_exports(__name__, globals(), "
                "{'u': ('.utilities', 'Utilities')})[0]\n"
            ),
            helpers / c.Infra.INIT_PY: (
                "from flext_core import install_lazy_exports\n"
                "__getattr__ = install_lazy_exports(__name__, globals(), "
                "{'Owner': '.owner'})[0]\n"
            ),
            helpers / "owner.py": (
                "class Owner:\n"
                + ("    @classmethod\n" if stateful else "    @staticmethod\n")
                + (
                    "    def normalize(cls, value: str) -> str:\n"
                    "        return cls.prefix + value\n"
                    if stateful
                    else "    def normalize(value: str) -> str:\n"
                    "        return value.upper()\n"
                )
                + "__all__ = ['Owner']\n"
            ),
            package / "utilities.py": (
                "from ._utilities import Owner\n"
                "class Utilities(Owner):\n"
                "    prefix = 'facade'\n"
                "    class Domain(Owner):\n        pass\n"
                "__all__ = ['Utilities']\n"
            ),
            consumer: (
                "from flext_core import m\n"
                "from pydantic import field_validator\n"
                + imported
                + "class Consumer(m.ContractModel):\n"
                + f"    literal: str = {reference}.normalize('literal')\n"
                + "    value: str = m.Field(default_factory=lambda: "
                + f"{reference}.normalize('model'), validate_default=True)\n"
                + "    values: list[str] = m.Field(default_factory=list[str])\n"
                + "    @field_validator('value')\n"
                + "    @classmethod\n"
                + "    def normalized(cls, value: str) -> str:\n"
                + f"        return {reference}.normalize(value)\n"
                + "def shadow(u):\n    return u.normalize('local')\n"
                + "TEXT = 'u.normalize stays a string'\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            if stateful:
                with pytest.raises(ValueError, match="requires facade dispatch"):
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=sources,
                    )
                return
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
            tm.that(edits, empty=False)
            for edit in edits:
                sources[edit.file_path] = edit.updated_source
                edit.file_path.write_text(edit.updated_source, encoding="utf-8")
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=sources,
                    )
                ),
                empty=True,
            )
        module = ".".join(
            consumer
            .relative_to(root if tier == "examples" else root / "src")
            .with_suffix("")
            .parts
        )
        output = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {module} import Consumer, TEXT, shadow\n"
                        "first, second = Consumer(), Consumer()\n"
                        "first.values.append('independent')\n"
                        "assert second.values == []\n"
                        "assert first.value == 'MODEL'\n"
                        "assert first.literal == 'LITERAL'\n"
                        "assert Consumer.model_validate_json("
                        "first.model_dump_json()) == first\n"
                        "assert TEXT == 'u.normalize stays a string'\n"
                        "class Local:\n"
                        "    def normalize(self, value): return value\n"
                        "assert shadow(Local()) == 'local'\n"
                        "print('model-owner-proven')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: os.pathsep.join((
                            str(root / "src"),
                            str(root),
                        ))
                    }
                ),
            )
        )
        tm.that(output.stdout.strip(), eq="model-owner-proven")

    @staticmethod
    def test_native_factory_defers_nested_contract_and_validates_fresh_values(
        tmp_path: Path,
    ) -> None:
        """A native typed factory resolves Outer.Child after class creation."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer = package / "models.py"
        source = (
            "from __future__ import annotations\n"
            "from flext_core import m, t\n"
            "class Outer:\n"
            "    class Child(m.ContractModel):\n"
            "        value: str\n"
            "    class Consumer(m.ContractModel):\n"
            "        children: t.SequenceOf[Outer.Child] = m.Field("
            "default_factory=list, description='Owned child values')\n"
        )
        consumer.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={consumer: source},
                )
            )
            tm.that(edits, empty=False)
            for edit in edits:
                edit.file_path.write_text(edit.updated_source, encoding="utf-8")
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                        rope_workspace=rope,
                        sources={consumer: consumer.read_text(encoding="utf-8")},
                    )
                ),
                empty=True,
            )
        output = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.models import Outer\n"
                        "from pydantic import ValidationError\n"
                        "first, second = Outer.Consumer(), Outer.Consumer()\n"
                        "assert isinstance(first.children, list)\n"
                        "first.children.append(Outer.Child(value='child'))\n"
                        "assert second.children == []\n"
                        "restored = Outer.Consumer.model_validate_json("
                        "first.model_dump_json())\n"
                        "assert restored == first\n"
                        "assert isinstance(restored.children[0], Outer.Child)\n"
                        "try: Outer.Consumer(children=[{'value': []}])\n"
                        "except ValidationError: pass\n"
                        "else: raise AssertionError("
                        "'native child validation missing')\n"
                        "print('native-factory-proven')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(root / "src")}
                ),
            )
        )
        tm.that(output.stdout.strip(), eq="native-factory-proven")

    @staticmethod
    def test_native_factory_retains_declaring_model_policy(tmp_path: Path) -> None:
        """Native schema policy rejects strict ports and accepts arbitrary presets."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer = package / "models.py"
        source = (
            "from __future__ import annotations\n"
            "from typing import Protocol, runtime_checkable\n"
            "from pydantic import (BaseModel, ConfigDict, Field, "
            "PydanticSchemaGenerationError)\n"
            "from flext_core import m, t\n"
            "@runtime_checkable\n"
            "class Capability(Protocol):\n    value: str\n"
            "STRICT_REJECTED = False\n"
            "try:\n"
            "    class Strict(BaseModel):\n"
            "        model_config = ConfigDict(arbitrary_types_allowed=False)\n"
            "        items: t.SequenceOf[Capability] = Field(default_factory=list)\n"
            "except PydanticSchemaGenerationError:\n"
            "    STRICT_REJECTED = True\n"
            "class Arbitrary(m.ArbitraryTypesModel):\n"
            "    items: t.SequenceOf[Capability] = m.Field(default_factory=list)\n"
        )
        consumer.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={consumer: source},
                )
            )
            tm.that(edits, empty=False)
            for edit in edits:
                edit.file_path.write_text(edit.updated_source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.models import "
                        "Arbitrary, STRICT_REJECTED\n"
                        "assert STRICT_REJECTED\n"
                        "class Collaborator:\n    value = 'real capability'\n"
                        "port = Collaborator()\n"
                        "assert Arbitrary(items=[port]).items[0] is port\n"
                        "first, second = Arbitrary(), Arbitrary()\n"
                        "assert isinstance(first.items, list)\n"
                        "first.items.append(port)\n"
                        "assert second.items == []\n"
                        "print('declaring-policy-proven')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(root / "src")}
                ),
            )
        )
        tm.that(result.stdout.strip(), eq="declaring-policy-proven")

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "from {package} import u\n",
            "from {package} import u as first, u as second\n",
        ],
    )
    def test_declared_leaf_breaks_self_composition_cycle(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Import a peripheral project in a fresh process after public planning."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / "_utilities" / "owner.py"
        owner.parent.mkdir()
        (owner.parent / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        consumer = owner.parent / "consumer.py"
        first, second = ("first", "second") if "first" in declaration else ("u", "u")
        sources = {
            package / c.Infra.INIT_PY: (
                "from .utilities import Utilities as u\n__all__ = ('u',)\n"
            ),
            package / c.Infra.UTILITIES_PY: (
                "from ._utilities.owner import Owner\n"
                "from ._utilities.consumer import Consumer\n"
                "class Utilities(Owner):\n"
                "    pass\n"
                "__all__ = ('Utilities', 'Consumer')\n"
            ),
            owner: (
                "class Owner:\n"
                "    @staticmethod\n"
                "    def render(value: str) -> str:\n"
                "        return value.upper()\n"
                "__all__ = ('Owner',)\n"
            ),
            consumer: declaration.format(package=package.name)
            + (
                f"VALUE = {first}.render('module')\n"
                "class Consumer:\n"
                f"    value = {second}.render('class')\n"
                "    @staticmethod\n"
                f"    def render(value={first}.render('default')):\n"
                "        '''Documented public operation.'''\n"
                f"        return {second}.render(value)\n"
                "def shadow(u):\n"
                "    return u.render('local')\n"
                "TEXT = 'u.render stays a string'\n"
                "__all__ = ('Consumer', 'VALUE', 'TEXT', 'shadow')\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
            tm.that(edits, empty=False)
            for edit in edits:
                tm.ok(
                    u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source),
                )
                sources[edit.file_path] = edit.updated_source
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
        tm.that(remaining, empty=True)
        output = tm.ok(
            u.Cli.run(
                [
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        f"from {package.name}._utilities.consumer import "
                        "Consumer, VALUE, TEXT, shadow; "
                        "assert VALUE == 'MODULE'; "
                        "assert Consumer.value == 'CLASS'; "
                        "assert Consumer.render() == 'DEFAULT'; "
                        "assert Consumer.render.__doc__ == "
                        "'Documented public operation.'; "
                        "assert shadow(u) == 'LOCAL'; "
                        "assert TEXT == 'u.render stays a string'; "
                        "print('consumer contract accepted')"
                    ),
                ],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            root / c.Infra.DEFAULT_SRC_DIR,
                        ),
                    },
                ),
            ),
        )
        tm.that(output.stdout.strip(), eq="consumer contract accepted")

    @staticmethod
    @pytest.mark.parametrize(
        ("method", "body", "expected"),
        [
            (
                (
                    "    @classmethod\n"
                    "    def render(cls, value):\n"
                    "        return cls.prefix + value\n"
                ),
                "VALUE = u.render('input')\n",
                "requires facade dispatch",
            ),
            (
                ("    @staticmethod\n    def render(value):\n        return value\n"),
                "VALUE = u.unknown('input')\n",
                "callable owner is unresolved",
            ),
            (
                ("    @staticmethod\n    def render(value):\n        return value\n"),
                ("class Owner:\n    pass\nVALUE = u.render('input')\n"),
                "receiver is shadowed",
            ),
        ],
    )
    def test_owner_failure_preserves_input(
        tmp_path: Path,
        method: str,
        body: str,
        expected: str,
    ) -> None:
        """Keep unresolved and contextual bindings causal and unpublished."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / "_utilities" / "owner.py"
        owner.parent.mkdir()
        consumer = owner.parent / "consumer.py"
        source = f"from {package.name} import u\n{body}"
        sources = {
            package / c.Infra.INIT_PY: (
                "from .utilities import Utilities as u\n__all__ = ('u',)\n"
            ),
            package / c.Infra.UTILITIES_PY: (
                "from ._utilities.owner import Owner\n"
                "class Utilities(Owner):\n"
                "    pass\n"
                "__all__ = ('Utilities',)\n"
            ),
            owner: f"class Owner:\n{method}__all__ = ('Owner',)\n",
            consumer: source,
        }
        for path, content in sources.items():
            path.write_text(content, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(result, has=expected)
        tm.that(isinstance(result.exception, ValueError), eq=True)
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)
