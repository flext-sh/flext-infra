r"""Runtime-model aliases must stay importable at runtime.

The canonical-alias injector deferred ``t`` under ``if TYPE_CHECKING:``
whenever every use sat inside an annotation. A pydantic model resolves its
class-body annotations while the class is built, so that deferral left
``t.VariadicTuple`` unresolvable and ``_SmellData.model_validate_json`` raised
``PydanticUserError`` during package import (flext-dk13k). Class-body
annotations on a runtime model therefore keep a module-level import, while a
purely type-checking use keeps the deferred import that avoids an
initialisation cycle.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c, u

_MODULE_IMPORT = f"from {c.Infra.PKG_CORE_UNDERSCORE} import t\n"

_MODEL_USES_ALIAS = """\
from __future__ import annotations

from pydantic import BaseModel, Field


class _Row(BaseModel):
    skills: t.VariadicTuple[str]
    rows: t.VariadicTuple[str] = Field(alias="rows")
"""

_TYPE_CHECKING_USES_ALIAS = """\
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def render(value: t.SequenceOf[str]) -> t.Pair[str, str]: ...
"""

_PLAIN_CLASS_USES_ALIAS = """\
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Helper:
    values: t.SequenceOf[str]
"""

_NO_TYPE_CHECKING_BLOCK = """\
from __future__ import annotations

from email.utils import parseaddr


class Version:
    info: t.Triple[int, int, int]

    @staticmethod
    def resolve() -> t.Pair[str, str]: ...
"""


class TestsFlextInfraRuntimeModelAlias:
    """Keep a runtime model's alias import at runtime, not under TYPE_CHECKING."""

    def test_model_class_body_alias_gets_a_module_level_import(self) -> None:
        """A pydantic model resolves its field annotations at import time."""
        updated = u.Infra.ensure_alias_import(
            _MODEL_USES_ALIAS, c.Infra.PKG_CORE_UNDERSCORE, "t"
        )
        tm.that(_MODULE_IMPORT in updated, eq=True)
        tm.that(f"    {_MODULE_IMPORT}" in updated, eq=False)

    def test_type_checking_only_alias_keeps_the_deferred_import(self) -> None:
        """A signature-only use stays inside the type-checking block."""
        updated = u.Infra.ensure_alias_import(
            _TYPE_CHECKING_USES_ALIAS, c.Infra.PKG_CORE_UNDERSCORE, "t"
        )
        tm.that(f"    {_MODULE_IMPORT}" in updated, eq=True)
        tm.that(f"\n{_MODULE_IMPORT}" in updated, eq=False)

    def test_plain_class_body_alias_keeps_the_deferred_import(self) -> None:
        """A non-model class body does not force a runtime import."""
        updated = u.Infra.ensure_alias_import(
            _PLAIN_CLASS_USES_ALIAS, c.Infra.PKG_CORE_UNDERSCORE, "t"
        )
        tm.that(f"    {_MODULE_IMPORT}" in updated, eq=True)

    def test_missing_block_is_created_instead_of_a_runtime_import(self) -> None:
        """An initialisation-cycle module must not import its own package at runtime."""
        updated = u.Infra.ensure_alias_import(
            _NO_TYPE_CHECKING_BLOCK, c.Infra.PKG_CORE_UNDERSCORE, "t"
        )
        tm.that("if TYPE_CHECKING:" in updated, eq=True)
        tm.that(f"    {_MODULE_IMPORT}" in updated, eq=True)
        tm.that(f"\n{_MODULE_IMPORT}" in updated, eq=False)
        tm.that("from typing import TYPE_CHECKING" in updated, eq=True)


__all__: list[str] = ["TestsFlextInfraRuntimeModelAlias"]
