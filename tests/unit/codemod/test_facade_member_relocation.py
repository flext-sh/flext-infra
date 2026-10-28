"""Facade members relocate to their derived owner through one native rule.

The owner letter of a member is derived from the kind of the object it binds
(tooling ``facade-members``); the generated relocation rule matches only the
census's foreign references through stable module-level facade bindings.
These tests exercise the real core facades through the public mod engine and
publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from tests import c, p, tm, u


class TestsFlextInfraFacadeMemberRelocation:
    """The native scan and publisher preserve noncanonical source expressions."""

    @staticmethod
    def _rule(workspace: Path) -> tuple[str, ...]:
        """Select the workspace's generated relocation rule.

        Returns:
            The resulting ``tuple[str, ...]``.

        """
        return (
            (
                f"{c.Infra.FACADE_MEMBER_RELOCATE_SHAPE}"
                f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}"
                f"{u.Infra.project_package_name(workspace)}"
            ),
        )

    @staticmethod
    def test_canonical_facades_preserve_arguments_and_derived_stay(
        mod_workspace: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Imported facade references move, call data intact; a rebound one stays."""
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
        names = (
            "field_validator",
            "model_validator",
            "BeforeValidator",
            "PrivateAttr",
            "Field",
            "AfterValidator",
            "computed_field",
        )
        # The census decides each move: a member relocates when its owner
        # letter binds it and the receiver binds no object or the identical one.
        with u.Infra.codemod_workspace_snapshot(mod_workspace) as snapshot:
            resolver_factory = u.Infra.source_member_resolver_factory(
                snapshot.engine, sources={}
            )
            _lineage, references, _names = u.Infra.facade_member_census(
                mod_workspace, source_project=snapshot.engine
            )
            owners = {
                name: u.Infra.facade_member_owner(
                    u.Infra.source_member_binding(
                        snapshot.engine,
                        f"{c.Infra.PKG_CORE_UNDERSCORE}.m.{name}",
                    ),
                    resolver_factory=resolver_factory,
                    source_project=snapshot.engine,
                )
                for name in names
            }
        moved = {
            name
            for name, owner in owners.items()
            if f"u.{name}" in references.get(owner, frozenset())
        }
        tm.that(moved, empty=False)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=TestsFlextInfraFacadeMemberRelocation._rule(mod_workspace),
                source_files=(canonical, derived),
            )
        )
        tm.that(report.actionable, eq=len(moved))
        derived_before = derived.read_text(encoding="utf-8")
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, report))
        # The publisher formats what it writes and prunes imports the move left
        # unused, so the contract is the relocated references, not the bytes.
        tm.that(derived.read_text(encoding="utf-8"), eq=derived_before)
        tm.that(
            canonical.read_text(encoding="utf-8"),
            has=(
                *(f"{owners[name]}.{name}" for name in moved),
                *(f"u.{name}" for name in set(names) - moved),
                "default=sentinel",
                "default=None",
            ),
            lacks=tuple(f"u.{name}" for name in moved),
        )
        native_consumer(
            "from runpy import run_path\n"
            f"observed = run_path({str(canonical)!r})\n"
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
                selection=TestsFlextInfraFacadeMemberRelocation._rule(mod_workspace),
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
                selection=TestsFlextInfraFacadeMemberRelocation._rule(mod_workspace),
                source_files=tuple(paths),
            )
        )
        # Module-level calls in the two parameter-shadow cases remain eligible.
        tm.that(report.actionable, eq=2)
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, report))
        shadowed = len(cases) - 2
        for index, path in enumerate(paths):
            published = path.read_text(encoding="utf-8")
            if index < shadowed:
                tm.that(published, eq=before[index])
            else:
                # Published files are formatted; only the module-level call moves
                # while the parameter-shadowed call keeps its receiver.
                tm.that(
                    published,
                    has=("value = m.PrivateAttr()", "return u.PrivateAttr()"),
                    lacks="value = u.PrivateAttr()",
                )

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
                selection=TestsFlextInfraFacadeMemberRelocation._rule(mod_workspace),
                source_files=(path,),
            )
        )
        tm.that(report.actionable, eq=2)
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, report))
        # The published file is formatted; complete metadata calls move and every
        # protected type argument, literal and bare marker keeps its receiver.
        tm.that(
            path.read_text(encoding="utf-8"),
            has=(
                "eligible = Annotated[str, m.BeforeValidator(validate)]",
                "other = Annotated[str, m.PrivateAttr()]",
                "u.BeforeValidator(validate)",
                "literal = Literal[u.BeforeValidator(validate)]",
                "first = Annotated[u.BeforeValidator(validate), ",
                "bare = Annotated[str, u.BeforeValidator]",
                "wrapped = Annotated[str, [u.BeforeValidator(validate)]]",
                "nested = Literal[Annotated[str, u.BeforeValidator(validate)]]",
            ),
            lacks=(
                "eligible = Annotated[str, u.BeforeValidator",
                "other = Annotated[str, u.PrivateAttr",
            ),
        )
