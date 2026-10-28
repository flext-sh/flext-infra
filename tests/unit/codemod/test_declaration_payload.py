"""Native Rope declaration recognition through the public utilities facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra import infra
from tests import tm, u


class TestsFlextInfraDeclarationPayload:
    """Exercise semantic identity and inherited declarations without source parsing."""

    @staticmethod
    def test_same_named_declarations_use_captured_occurrence(
        declaration_workspace: tuple[Path, Path],
    ) -> None:
        """Resolve each nested declaration in its own native class scope."""
        root, package = declaration_workspace
        source = (
            '"""Unicode source prefix: caf\u00e9."""\n'
            "from pydantic import BaseModel\n"
            "class First:\n"
            "    class Payload(BaseModel):\n"
            "        value: str\n"
            "class Second:\n"
            "    class Payload:\n"
            "        value: str\n"
        )
        path = package / "payload.py"
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as workspace:
            for enclosing, header, accepted in (
                ("First", "class Payload(BaseModel)", True),
                ("Second", "class Payload:", False),
            ):
                declarations = u.Infra.declaration_names(
                    workspace.rope_project,
                    path,
                    "Payload",
                    offset=source.index(header) + len("class "),
                )
                tm.that(declarations, eq=(f"{enclosing}.Payload",))
                binding = u.Infra.payload_declaration(
                    workspace.rope_project,
                    path,
                    declarations[0],
                )
                tm.that(binding is not None, eq=accepted)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize(
        ("definition", "accepted"),
        [
            (
                ("class Holder:\n    class Payload(ForeignBase): value: str\n"),
                True,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase): print('class body effect')\n"
                ),
                False,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase): value: str; print('effect')\n"
                ),
                False,
            ),
            (
                (
                    "class Parent(ForeignBase):\n"
                    "    value: str = 'payload'\n"
                    "class Holder:\n"
                    "    class Payload(Parent):\n"
                    "        pass\n"
                ),
                True,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        @field_serializer('value')\n"
                    "        def serialize(self, value: str) -> str:\n"
                    "            return value.upper()\n"
                ),
                True,
            ),
            (
                (
                    "import builtins\n"
                    "from pydantic import field_validator\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @field_validator('value')\n"
                    "        @builtins.classmethod\n"
                    "        def normalize(cls, value: str) -> str:\n"
                    "            return value.strip()\n"
                ),
                True,
            ),
            (
                (
                    "from pydantic import field_validator as validate_value\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @validate_value('value')\n"
                    "        @classmethod\n"
                    "        def normalize(cls, value: str) -> str:\n"
                    "            return value.strip()\n"
                ),
                True,
            ),
            (
                (
                    "from pydantic import model_validator as validate_payload\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @validate_payload(mode='after')\n"
                    "        def normalize(self):\n"
                    "            return self\n"
                ),
                True,
            ),
            (
                (
                    "from pydantic import model_serializer as serialize_payload\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @serialize_payload(mode='plain')\n"
                    "        def serialize(self):\n"
                    "            return self.value\n"
                ),
                True,
            ),
            (
                (
                    "class Parent[T](ForeignBase):\n"
                    "    value: T\n"
                    "class Holder:\n"
                    "    class Payload(Parent[str]):\n"
                    "        pass\n"
                ),
                True,
            ),
            (
                (
                    "class Parent[T](ForeignBase):\n"
                    "    value: T\n"
                    "class Holder:\n"
                    "    class Payload((Parent[list[str]])):\n"
                    "        pass\n"
                ),
                True,
            ),
            (
                (
                    "class Parent[T](ForeignBase):\n"
                    "    value: T\n"
                    "class Holder:\n"
                    "    class Payload(\n"
                    "        Parent[list[str]],  # Specialized native base.\n"
                    "    ):\n"
                    "        pass\n"
                ),
                True,
            ),
            (
                (
                    "class Ordinary:\n"
                    "    pass\n"
                    "def choose_base(label: str):\n"
                    "    return Ordinary\n"
                    "class Holder:\n"
                    "    class Payload(choose_base('[')):\n"
                    "        value: str\n"
                ),
                False,
            ),
            (
                (
                    "class Parent(ForeignBase):\n"
                    "    @classmethod\n"
                    "    def __class_getitem__(cls, item):\n"
                    "        return str\n"
                    "class Holder:\n"
                    "    class Payload(Parent[str]):\n"
                    "        pass\n"
                ),
                False,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        @computed_field\n"
                    "        @property\n"
                    "        def size(self) -> int:\n"
                    "            return len(self.value)\n"
                ),
                True,
            ),
            (
                (
                    "from builtins import property as native_property\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @computed_field\n"
                    "        @native_property\n"
                    "        def size(self) -> int:\n"
                    "            return len(self.value)\n"
                ),
                True,
            ),
            (
                (
                    "def property(function):\n"
                    "    return function\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @computed_field\n"
                    "        @property\n"
                    "        def size(self) -> int:\n"
                    "            return len(self.value)\n"
                ),
                False,
            ),
            (
                (
                    "class ForeignBase:\n"
                    "    pass\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                ),
                False,
            ),
            (
                (
                    "def opaque(function):\n"
                    "    return function\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        @opaque\n"
                    "        @field_serializer('value')\n"
                    "        def serialize(self, value: str) -> str:\n"
                    "            return value.upper()\n"
                ),
                False,
            ),
            (
                (
                    "def opaque(declaration):\n"
                    "    return declaration\n"
                    "class Holder:\n"
                    "    @opaque\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                ),
                False,
            ),
            (
                (
                    "def field_serializer(function):\n"
                    "    return function\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str\n"
                    "        @field_serializer\n"
                    "        def serialize(self, value: str) -> str:\n"
                    "            return value\n"
                ),
                False,
            ),
            (
                (
                    "def opaque(function):\n"
                    "    return function\n"
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        @opaque(field_serializer('value'))\n"
                    "        def serialize(self, value: str) -> str:\n"
                    "            return value.upper()\n"
                ),
                False,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(BaseSettings):\n"
                    "        value: str = 'payload'\n"
                ),
                False,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        @property\n"
                    "        def execute(self) -> str:\n"
                    "            return self.value.upper()\n"
                ),
                False,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        def execute(self) -> str:\n"
                    "            return self.value.upper()\n"
                ),
                False,
            ),
            (
                (
                    "class Holder:\n"
                    "    class Payload(ForeignBase):\n"
                    "        value: str = 'payload'\n"
                    "        print('class body effect')\n"
                ),
                False,
            ),
        ],
    )
    def test_native_model_identity(
        declaration_workspace: tuple[Path, Path],
        definition: str,
        *,
        accepted: bool,
    ) -> None:
        """Model admission preserves ancestry, declaration behavior and settings."""
        root, package = declaration_workspace
        source = (
            "from pydantic import BaseModel as ForeignBase, "
            "field_serializer, computed_field\n"
            "from pydantic_settings import BaseSettings\n" + definition
        )
        path = package / "payload.py"
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as workspace:
            binding = u.Infra.payload_declaration(
                workspace.rope_project,
                path,
                "Holder.Payload",
            )
            tm.that(binding is not None, eq=accepted)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize(
        ("definition", "accepted"),
        [
            ("class Payload(Contract):\n    value: str\n", True),
            (
                (
                    "from typing_extensions import Protocol as ExtendedContract\n"
                    "class Payload(ExtendedContract):\n"
                    "    value: str\n"
                ),
                True,
            ),
            (
                (
                    "from typing_extensions import Protocol as ExtendedContract\n"
                    "class Payload[T](ExtendedContract[T]):\n"
                    "    value: T\n"
                ),
                True,
            ),
            (
                (
                    "from typing import runtime_checkable\n"
                    "@runtime_checkable\n"
                    "class Payload(Contract):\n"
                    "    value: str\n"
                ),
                True,
            ),
            (
                "class Payload[T](Contract[T]):\n    value: T\n",
                True,
            ),
            (
                (
                    "from typing import runtime_checkable\n"
                    "@runtime_checkable\n"
                    "class Payload[T](\n"
                    "    Contract[T],  # Multiline generic protocol.\n"
                    "):\n"
                    "    value: T\n"
                ),
                True,
            ),
            (
                (
                    "class Parent(Contract):\n"
                    "    value: str\n"
                    "class Payload(Parent, Contract):\n"
                    "    pass\n"
                ),
                True,
            ),
            (
                (
                    "class Parent(Contract):\n"
                    "    value: str\n"
                    "class Payload(Parent):\n"
                    "    pass\n"
                ),
                False,
            ),
            (
                "class Contract:\n    pass\nclass Payload(Contract):\n    value: str\n",
                False,
            ),
        ],
    )
    def test_native_protocol_identity(
        declaration_workspace: tuple[Path, Path],
        definition: str,
        *,
        accepted: bool,
    ) -> None:
        """Aliased protocols and their concrete implementations remain distinct."""
        root, package = declaration_workspace
        source = "from typing import Protocol as Contract\n" + definition
        path = package / "contracts.py"
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as workspace:
            binding = u.Infra.protocol_declaration(
                workspace.rope_project,
                path,
                "Payload",
            )
            tm.that(binding is not None, eq=accepted)
        tm.that(path.read_text(encoding="utf-8"), eq=source)
