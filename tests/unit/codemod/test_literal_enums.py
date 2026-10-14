"""Public singleton Literal enum reuse retains Pydantic wire contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, tm, u


class TestsFlextInfraLiteralEnums:
    """Prove enum identities and wire behavior through the public phase."""

    @staticmethod
    @pytest.mark.parametrize(
        ("imports", "qualifier"),
        [
            ("from typing import Literal", "Literal"),
            ("from typing import Literal as Choice", "Choice"),
            ("import typing as types", "types.Literal"),
        ],
    )
    def test_singleton_enum_fields_preserve_discriminator_json(
        tmp_path: Path, imports: str, qualifier: str
    ) -> None:
        """Aliases retain their Literal shape and real models serialize strings."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / c.Infra.CONSTANTS_PY
        initializer = package / c.Infra.INIT_PY
        consumer = package / "consumer.py"
        sources = {
            owner: (
                "from enum import StrEnum\n"
                "class Values:\n"
                "    class Kind(StrEnum):\n"
                "        ALPHA = 'alpha'\n"
                "        BETA = 'beta'\n"
                "c = Values\n"
                "__all__ = ['c']\n"
            ),
            initializer: "from .constants import c\n__all__ = ['c']\n",
            consumer: (
                f"{imports}\n"
                "from typing import Annotated\n"
                "from pydantic import BaseModel, Field\n"
                "class Alpha(BaseModel):\n"
                f"    kind: {qualifier}['alpha']\n"
                "class Beta(BaseModel):\n"
                f"    kind: {qualifier}['beta'] = 'beta'\n"
                "class Envelope(BaseModel):\n"
                "    payload: Annotated[Alpha | Beta, Field(discriminator='kind')]\n"
                "class Defaults:\n"
                f"    value: {qualifier}['alpha'] = {qualifier}['alpha']\n"
                "    metadata: Annotated[str, 'alpha'] = 'alpha'\n"
                "def value() -> str:\n"
                "    return 'alpha'\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources=sources,
                )
            )
            tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
            proposed = {
                **sources,
                **{edit.file_path: edit.updated_source for edit in edits},
            }
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources=proposed,
                )
            )
            tm.that(repeated, empty=True)
        for path, source in proposed.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-W",
                    "error",
                    "-c",
                    (
                        "import json\n"
                        "from typing import get_args\n"
                        "from pydantic import ValidationError\n"
                        f"from {package.name} import c\n"
                        f"from {package.name}.consumer import "
                        "Alpha, Beta, Envelope, Defaults, value\n"
                        "for model, member in "
                        "((Alpha, c.Kind.ALPHA), (Beta, c.Kind.BETA)):\n"
                        "    parsed = model.model_validate({'kind': member.value})\n"
                        "    assert parsed.kind is member\n"
                        "    assert json.loads(parsed.model_dump_json()) == "
                        "{'kind': member.value}\n"
                        "    envelope = Envelope.model_validate("
                        "{'payload': {'kind': member.value}})\n"
                        "    assert envelope.payload.kind is member\n"
                        "    assert json.loads(envelope.model_dump_json()) == "
                        "{'payload': {'kind': member.value}}\n"
                        "assert get_args(Defaults.__annotations__['value'])[0] "
                        "is c.Kind.ALPHA\n"
                        "assert type(get_args(Defaults.value)[0]) is str\n"
                        "assert Defaults.metadata == c.Kind.ALPHA.value\n"
                        "assert type(value()) is str\n"
                        "try:\n"
                        "    Alpha.model_validate({'kind': 'invalid-kind'})\n"
                        "except ValidationError:\n"
                        "    pass\n"
                        "else:\n"
                        "    raise AssertionError('invalid discriminator accepted')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    def test_literal_homonym_does_not_acquire_enum_semantics(tmp_path: Path) -> None:
        """A user-owned Literal class retains its actual subscription behavior."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / c.Infra.CONSTANTS_PY
        consumer = package / "consumer.py"
        sources = {
            owner: (
                "from enum import StrEnum\n"
                "class Values:\n"
                "    class Kind(StrEnum):\n"
                "        ALPHA = 'alpha'\n"
                "c = Values\n"
            ),
            consumer: (
                "class Literal:\n"
                "    @classmethod\n"
                "    def __class_getitem__(cls, value):\n"
                "        return str\n"
                "class Consumer:\n"
                "    kind: Literal['alpha']\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources=sources,
                )
            )
        tm.that(edits, empty=True)

    @staticmethod
    @pytest.mark.parametrize("case", ["shadowed", "ambiguous"])
    def test_competing_enum_bindings_fail_before_publication(
        tmp_path: Path, case: str
    ) -> None:
        """A singleton annotation never selects an arbitrary member or facade."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / c.Infra.CONSTANTS_PY
        consumer = package / "consumer.py"
        extra = (
            "    class Other(StrEnum):\n        ALPHA = 'alpha'\n"
            if case == "ambiguous"
            else ""
        )
        shadow = "    c = str\n" if case == "shadowed" else ""
        sources = {
            owner: (
                "from enum import StrEnum\n"
                "class Values:\n"
                "    class Kind(StrEnum):\n"
                "        ALPHA = 'alpha'\n"
                f"{extra}"
                "c = Values\n"
            ),
            consumer: (
                "from typing import Literal\n"
                "class Consumer:\n"
                f"{shadow}"
                "    kind: Literal['alpha']\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        message = (
            "literal constant facade c is shadowed"
            if case == "shadowed"
            else "literal annotation has ambiguous enum owners"
        )
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match=message),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=workspace,
                sources=sources,
            )
