"""Facade members relocate to their derived owner with native source proofs.

The owner letter of a member is derived from the kind of the object it binds
(tooling ``facade-members``); these tests exercise the real core facades
through the public mod engine and publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from rope.base.exceptions import AttributeNotFoundError

from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from tests import p, tm


class TestsFlextInfraFacadeMemberRelocation:
    """The native scan and publisher preserve noncanonical source expressions."""

    RELOCATIONS: tuple[str, ...] = tuple(
        f"relocate-facade-member-to-{letter}" for letter in "ctpmu"
    )

    @staticmethod
    def test_canonical_and_derived_facades_preserve_arguments(
        mod_workspace: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Canonical and inherited references move to the owner, call data intact."""
        canonical = mod_workspace / "canonical.py"
        derived = mod_workspace / "derived.py"
        body = (
            "sentinel = []\n"
            "def validate(value):\n    return value\n"
            "field = u.field_validator('value', mode='before')\n"
            "model = u.model_validator(mode='after')\n"
            "before = u.BeforeValidator(validate)\n"
            "private = u.PrivateAttr(default=sentinel)\n"
            "declared = u.Field(default=None)\n"
            "after = u.AfterValidator(validate)\n"
            "computed = u.computed_field\n"
        )
        canonical.write_text(
            "from flext_core import m, t, u\n" + body, encoding="utf-8"
        )
        derived.write_text(
            "from flext_core import m, t, u as parent\n"
            "class Derived(parent):\n    pass\nu = Derived\n" + body,
            encoding="utf-8",
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=TestsFlextInfraFacadeMemberRelocation.RELOCATIONS,
                source_files=(canonical, derived),
            )
        )
        tm.that(report.actionable, eq=14)
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, report))
        owners = {
            "field_validator": "m",
            "model_validator": "m",
            "BeforeValidator": "m",
            "PrivateAttr": "m",
            "Field": "m",
            "AfterValidator": "m",
            "computed_field": "m",
        }
        expected = body
        for name, owner in owners.items():
            expected = expected.replace(f"u.{name}", f"{owner}.{name}")
        for path in (canonical, derived):
            tm.that(path.read_text(encoding="utf-8"), has=expected)
            native_consumer(
                "from runpy import run_path\n"
                f"observed = run_path({str(path)!r})\n"
                "if observed['before'].func is not observed['validate']:\n"
                "    raise RuntimeError('validator argument identity changed')\n"
                "if observed['private'].default is not observed['sentinel']:\n"
                "    raise RuntimeError('private default identity changed')\n",
                cwd=mod_workspace,
            )
        after = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=TestsFlextInfraFacadeMemberRelocation.RELOCATIONS,
                source_files=(canonical, derived),
            )
        )
        tm.that(after.findings, eq=0)

    @staticmethod
    def test_noncanonical_and_unstable_bindings_stay_unchanged(
        mod_workspace: Path,
    ) -> None:
        """Overrides, custom owners, missing targets and guarded imports fail closed."""
        cases = (
            (
                "from flext_core import m, u as parent\n"
                "class Derived(parent):\n    PrivateAttr = print\nu = Derived\n"
            ),
            "from flext_core import m\nclass Custom:\n    pass\nu = Custom\n",
            (
                "from flext_core import u\nclass Custom:\n"
                "    PrivateAttr = print\nm = Custom\n"
            ),
            "from flext_core import u\n",
            "from flext_core import m, u as parent\nu = parent\nu = parent\n",
            "from flext_core import m, u\nu.PrivateAttr = print\n",
            "from flext_core import m, u\nm.PrivateAttr = print\n",
            (
                "from flext_core import m as parent, u\n"
                "class Derived(parent):\n    PrivateAttr = None\nm = Derived\n"
            ),
            (
                "from typing import TYPE_CHECKING\nfrom flext_core import u\n"
                "if TYPE_CHECKING:\n    from flext_core import m\n"
            ),
            (
                "from typing import TYPE_CHECKING\nfrom flext_core import m\n"
                "if TYPE_CHECKING:\n    from flext_core import u\n"
            ),
            "from flext_core import m, u\ndef probe(u):\n    return u.PrivateAttr()\n",
            "from flext_core import m, u\ndef probe(m):\n    return u.PrivateAttr()\n",
        )
        paths: list[Path] = []
        for index, prefix in enumerate(cases):
            path = mod_workspace / f"rejected_{index}.py"
            path.write_text(prefix + "value = u.PrivateAttr()\n", encoding="utf-8")
            paths.append(path)
        before = tuple(path.read_text(encoding="utf-8") for path in paths)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=("relocate-facade-member-to-m",),
                source_files=tuple(paths),
            )
        )
        # Module-level calls in the two parameter-shadow cases remain eligible.
        tm.that(report.actionable, eq=2)
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, report))
        for index, path in enumerate(paths):
            expected = before[index]
            if index >= len(cases) - 2:
                expected = (
                    expected.removesuffix("value = u.PrivateAttr()\n")
                    + "value = m.PrivateAttr()\n"
                )
            tm.that(path.read_text(encoding="utf-8"), eq=expected)

    @staticmethod
    def test_only_complete_annotated_metadata_calls_relocate(
        mod_workspace: Path,
    ) -> None:
        """Protected type arguments, literals and bare markers retain their bytes."""
        path = mod_workspace / "annotations.py"
        source = (
            "from typing import Annotated, Literal\nfrom flext_core import m, t, u\n"
            "def validate(value):\n    return value\n"
            "eligible = Annotated[str, u.BeforeValidator(validate)]\n"
            "label = 'u.BeforeValidator(validate)'\n"
            "literal = Literal[u.BeforeValidator(validate)]\n"
            "first = Annotated[u.BeforeValidator(validate), 'metadata']\n"
            "bare = Annotated[str, u.BeforeValidator]\n"
            "other = Annotated[str, u.PrivateAttr()]\n"
            "wrapped = Annotated[str, [u.BeforeValidator(validate)]]\n"
            "nested = Literal[Annotated[str, u.BeforeValidator(validate)]]\n"
        )
        path.write_text(source, encoding="utf-8")
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=(
                    "relocate-facade-member-to-t",
                    "relocate-facade-member-to-m",
                ),
                source_files=(path,),
            )
        )
        tm.that(report.actionable, eq=2)
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, report))
        tm.that(
            path.read_text(encoding="utf-8"),
            eq=source.replace(
                "eligible = Annotated[str, u.BeforeValidator(validate)]",
                "eligible = Annotated[str, m.BeforeValidator(validate)]",
            ).replace(
                "other = Annotated[str, u.PrivateAttr()]",
                "other = Annotated[str, m.PrivateAttr()]",
            ),
        )

    @staticmethod
    def test_unproven_ancestry_never_publishes(mod_workspace: Path) -> None:
        """Unknown bases and contradictory C3 orders remain visible failures."""
        path = mod_workspace / "unknown.py"
        for bases in ("parent, Unknown", "Left, Right"):
            source = (
                "from flext_core import m, u as parent\n"
                "class Left(parent):\n    pass\n"
                "class Right(Left):\n    pass\n"
                f"class Derived({bases}):\n    pass\nu = Derived\n"
                "value = u.PrivateAttr()\n"
            )
            path.write_text(source, encoding="utf-8")
            with pytest.raises(
                (ValueError, AttributeNotFoundError),
                match=r"Unknown|Inconsistent class MRO",
            ):
                FlextInfraModGateEngine.scan(
                    mod_workspace,
                    fix=False,
                    selection=("relocate-facade-member-to-m",),
                    source_files=(path,),
                )
            tm.that(path.read_text(encoding="utf-8"), eq=source)
