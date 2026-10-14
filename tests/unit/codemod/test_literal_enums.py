"""Public singleton Literal enum reuse retains Pydantic wire contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests import c, m, p, t, tm


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
        constants_workspace: t.Pair[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
        infra_subprocess: p.Cli.CommandRunner,
        imports: str,
        qualifier: str,
    ) -> None:
        """Aliases retain their Literal shape and real models serialize strings."""
        root, package = constants_workspace
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
        constant_candidate(sources, (consumer,))
        tm.ok(
            infra_subprocess.capture(
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

    @staticmethod
    def test_literal_homonym_does_not_acquire_enum_semantics(
        constants_workspace: t.Pair[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
    ) -> None:
        """A user-owned Literal class retains its actual subscription behavior."""
        _root, package = constants_workspace
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
        constant_candidate(sources, ())

    @staticmethod
    @pytest.mark.parametrize("case", ["shadowed", "ambiguous"])
    def test_competing_enum_bindings_fail_before_publication(
        constants_workspace: t.Pair[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
        case: str,
    ) -> None:
        """A singleton annotation never selects an arbitrary member or facade."""
        _root, package = constants_workspace
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
        message = (
            "literal constant facade c is shadowed"
            if case == "shadowed"
            else "literal annotation has ambiguous enum owners"
        )
        with pytest.raises(ValueError, match=message):
            constant_candidate(sources, ())
