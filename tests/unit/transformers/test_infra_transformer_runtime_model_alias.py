r"""Runtime-model aliases must stay importable at runtime.

The canonical-alias injector deferred ``t`` under ``if TYPE_CHECKING:``
whenever every use sat inside an annotation. A pydantic model resolves its
class-body annotations while the class is built, so that deferral left
``t.VariadicTuple`` unresolvable and ``_SmellData.model_validate_json`` raised
``PydanticUserError`` during package import. Class-body
annotations on a runtime model therefore keep a module-level import, while a
purely type-checking use keeps the deferred import that avoids an
initialisation cycle.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra import u
from tests import c, tm

if TYPE_CHECKING:
    from pathlib import Path

_MODULE_IMPORT = f"from {c.Infra.PKG_CORE_UNDERSCORE} import t\n"

_MODEL_USES_ALIAS = f"""\
from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from {c.Infra.PKG_CORE_UNDERSCORE} import m

class _Row(m.BaseModel):
    skills: tuple[str, ...]
    rows: tuple[str, ...], = m.Field(alias="rows")
"""

_TYPE_CHECKING_USES_ALIAS = """\
from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def render(value: Sequence[str]) -> tuple[str, str]: ...
"""

_PLAIN_CLASS_USES_ALIAS = """\
from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Helper:
    values: Sequence[str]
"""

_NO_TYPE_CHECKING_BLOCK = """\
from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from email.utils import parseaddr


class Version:
    info: tuple[int, int, int]

    @staticmethod
    def resolve() -> tuple[str, str]: ...
"""


class TestsFlextInfraRuntimeModelAlias:
    """Keep a runtime model's alias import at runtime, not under TYPE_CHECKING."""

    @staticmethod
    def test_model_class_body_alias_gets_a_module_level_import(
        tmp_path: Path,
    ) -> None:
        """A pydantic model resolves its field annotations at import time."""
        updated = u.Infra.ensure_alias_import(
            _MODEL_USES_ALIAS,
            c.Infra.PKG_CORE_UNDERSCORE,
            "t",
        )
        tm.ok(_MODULE_IMPORT in updated)
        tm.fail(f"    {_MODULE_IMPORT}" in updated)
        (tmp_path / "runtime_model.py").write_text(updated, encoding="utf-8")
        probe = (
            "from runtime_model import _Row\n"
            "row = _Row.model_validate_json("
            '\'{"skills": ["skill"], "rows": ["row"]}\')\n'
            "print(row.skills[0], row.rows[0])\n"
        )
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(outcome.stdout.strip(), eq="skill row")

    @staticmethod
    def test_type_checking_only_alias_keeps_the_deferred_import() -> None:
        """A signature-only use stays inside the type-checking block."""
        updated = u.Infra.ensure_alias_import(
            _TYPE_CHECKING_USES_ALIAS,
            c.Infra.PKG_CORE_UNDERSCORE,
            "t",
        )
        tm.ok(f"    {_MODULE_IMPORT}" in updated)
        tm.fail(f"\n{_MODULE_IMPORT}" in updated)

    @staticmethod
    def test_plain_class_body_alias_keeps_the_deferred_import() -> None:
        """A non-model class body does not force a runtime import."""
        updated = u.Infra.ensure_alias_import(
            _PLAIN_CLASS_USES_ALIAS,
            c.Infra.PKG_CORE_UNDERSCORE,
            "t",
        )
        tm.ok(f"    {_MODULE_IMPORT}" in updated)

    @staticmethod
    def test_missing_block_is_created_instead_of_a_runtime_import() -> None:
        """An initialisation-cycle module must not import its own package at runtime."""
        updated = u.Infra.ensure_alias_import(
            _NO_TYPE_CHECKING_BLOCK,
            c.Infra.PKG_CORE_UNDERSCORE,
            "t",
        )
        tm.ok("if TYPE_CHECKING:" in updated)
        tm.ok(f"    {_MODULE_IMPORT}" in updated)
        tm.fail(f"\n{_MODULE_IMPORT}" in updated)
        tm.ok("from typing import TYPE_CHECKING" in updated)
