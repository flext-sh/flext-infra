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

from tests import c, tm, u

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
from {c.Infra.PKG_CORE_UNDERSCORE} import m, p

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

_AUTHORED_PROTOCOL_USES_ALIASES = f"""\
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from {c.Infra.PKG_CORE_UNDERSCORE} import p, t


class AuthoredPorts:
    class Reader(Protocol):
        record: p.Infra.Record

        def read(self, value: t.JsonValue) -> p.Infra.Record: ...
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
    def test_runtime_import_after_type_checking_block_is_detected() -> None:
        """An early typing guard does not hide a later runtime binding."""
        source = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from flext_core import t\n"
            "from collections.abc import Iterable\n"
            "from flext_core import t\n"
            "class Port:\n"
            "    value: t.JsonValue\n"
        )
        tm.ok(u.Infra.has_runtime_alias_import(source, "t"))

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

    @staticmethod
    def test_authored_protocol_aliases_remain_type_checking_only() -> None:
        """Protocol bases and signatures do not promote facade imports to runtime."""
        updated = u.Infra.ensure_alias_import(
            _AUTHORED_PROTOCOL_USES_ALIASES,
            c.Infra.PKG_CORE_UNDERSCORE,
            "t",
        )
        updated = u.Infra.ensure_alias_import(
            updated,
            c.Infra.PKG_CORE_UNDERSCORE,
            "p",
        )

        tm.that(updated, eq=_AUTHORED_PROTOCOL_USES_ALIASES)

    @staticmethod
    def test_protocol_header_binds_bare_and_renamed_annotation_providers(
        tmp_path: Path,
    ) -> None:
        """A real protocol binds decorators and deferred annotation providers."""
        source = (
            "from __future__ import annotations\n\n"
            "@runtime_checkable\n"
            "class Reader(Protocol):\n"
            "    def read(self, callback: Callback[[str], str])"
            " -> contextlib.AbstractContextManager[str]: ...\n"
        )
        imports = (
            ("typing", "Protocol", True),
            ("typing", "runtime_checkable", True),
            ("collections.abc", "Callable as Callback", False),
            (None, "contextlib", False),
        )
        updated = source
        for module, alias, runtime in imports:
            updated = u.Infra.ensure_alias_import(
                updated, module, alias, runtime_required=runtime
            )
        repeated = updated
        for module, alias, runtime in imports:
            repeated = u.Infra.ensure_alias_import(
                repeated, module, alias, runtime_required=runtime
            )
        tm.that(repeated, eq=updated)
        (tmp_path / "protocol_header.py").write_text(updated, encoding="utf-8")
        probe = (
            "from protocol_header import Reader\n"
            "class Consumer:\n"
            "    def read(self, callback): return callback('value')\n"
            "print(isinstance(Consumer(), Reader))\n"
        )
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(outcome.stdout.strip(), eq="True")

    @staticmethod
    def test_renamed_module_import_remains_available_to_runtime_bases(
        tmp_path: Path,
    ) -> None:
        """A plain module import keeps its declared binding and runtime placement."""
        source = (
            "from __future__ import annotations\n\n"
            "class Resource(resources.AbstractContextManager[str]):\n"
            "    def __enter__(self) -> str: return 'value'\n"
            "    def __exit__(self, exc_type, exc_value, traceback) -> None: pass\n"
        )
        alias = "contextlib as resources"
        updated = u.Infra.ensure_alias_import(source, None, alias)
        tm.that(u.Infra.ensure_alias_import(updated, None, alias), eq=updated)
        (tmp_path / "resource_header.py").write_text(updated, encoding="utf-8")
        probe = (
            "from resource_header import Resource\n"
            "with Resource() as value: print(value)\n"
        )
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(outcome.stdout.strip(), eq="value")

    @staticmethod
    def test_local_imports_do_not_supply_a_module_runtime_binding(
        tmp_path: Path,
    ) -> None:
        """Function and class namespaces cannot satisfy a module-level base."""
        source = (
            "from __future__ import annotations\n\n"
            "def local_provider():\n"
            "    from collections.abc import Callable\n"
            "    return Callable\n"
            "class LocalNamespace:\n"
            "    from collections.abc import Callable\n"
            "class Consumer(Callable[[str], str]):\n"
            "    def __call__(self, value: str) -> str: return value\n"
        )
        updated = u.Infra.ensure_alias_import(source, "collections.abc", "Callable")
        tm.that(
            u.Infra.ensure_alias_import(updated, "collections.abc", "Callable"),
            eq=updated,
        )
        (tmp_path / "lexical_header.py").write_text(updated, encoding="utf-8")
        probe = "from lexical_header import Consumer\nprint(Consumer()('value'))\n"
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(outcome.stdout.strip(), eq="value")
