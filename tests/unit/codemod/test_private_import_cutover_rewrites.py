"""Public utility evidence for semantic private-import facade rewrites.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

from flext_infra import t, u
from tests import tm
from tests.unit.codemod.private_import_cutover_support import (
    TestsFlextInfraFacadeNaming,
    TestsFlextInfraPrivateImportCutoverSupport,
)


class TestsFlextInfraPrivateImportCutoverRewrites(
    TestsFlextInfraPrivateImportCutoverSupport,
):
    """Exercise facade rewrites of private imports only through ``u.Infra``."""

    def test_rewires_unique_public_facade_binding(self, tmp_path: Path) -> None:
        """Derive the nested facade path and remove the private import atomically."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "utilities",
                "managers",
                "Sample",
                "u",
            ),
        )
        sources[consumer_path] = (
            "from flext_sample import p\n"
            f"{private_import}\n\n"
            "manager: FlextSampleUtilitiesManagers.ServiceManagers\n"
        )

        edits = self._edits(tmp_path, sources, consumer_path, private_import)
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source

        tm.that(
            "from flext_sample import p, u" in updated
            or "from flext_sample import u" in updated,
            eq=True,
        )
        tm.that(updated, has="manager: u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)
        tm.that(updated, lacks="FlextSampleUtilitiesManagers.ServiceManagers")

    def test_prefers_nested_facade_over_its_root_ancestor(self, tmp_path: Path) -> None:
        """Select the deepest public namespace when the root shares its base."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            dataclasses.replace(
                TestsFlextInfraFacadeNaming.from_family(
                    "utilities",
                    "managers",
                    "Sample",
                    "u",
                ),
                root_bases="(FlextSampleUtilitiesManagers)",
            ),
        )
        sources[consumer_path] = (
            f"{private_import}\n\n"
            "manager = FlextSampleUtilitiesManagers.ServiceManagers\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="manager = u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)

    def test_rewrites_only_the_imported_alias_binding(self, tmp_path: Path) -> None:
        """Keep a homonymous local binding outside the authenticated cutover."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "utilities",
                "managers",
                "Sample",
                "u",
            ),
            import_alias="managers",
        )
        sources[consumer_path] = (
            f"{private_import}\n\n"
            "manager = managers.ServiceManagers\n\n"
            "def identity(managers: str) -> str:\n"
            "    return managers\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="manager = u.Sample.ServiceManagers")
        tm.that(updated, has="def identity(managers: str) -> str:")
        tm.that(updated, has="    return managers")
        tm.that(updated, lacks=private_import)

    @pytest.mark.parametrize(
        "consumer",
        [
            (
                "def select(u: str) -> str:\n"
                "    return FlextSampleUtilitiesManagers.ServiceManagers or u\n"
            ),
            (
                "class Consumer:\n"
                "    def select(self, u):\n"
                "        return FlextSampleUtilitiesManagers.ServiceManagers or u\n"
            ),
            (
                "class Consumer:\n"
                "    def select(self):\n"
                "        u = 'local'\n"
                "        return FlextSampleUtilitiesManagers.ServiceManagers or u\n"
            ),
            "u = 'module'\nmanager = FlextSampleUtilitiesManagers.ServiceManagers\n",
            (
                "class Consumer:\n"
                "    def select[u](self):\n"
                "        return FlextSampleUtilitiesManagers.ServiceManagers\n"
            ),
            (
                "class Consumer[u]:\n"
                "    def select(self):\n"
                "        return FlextSampleUtilitiesManagers.ServiceManagers\n"
            ),
            (
                "class Consumer:\n"
                "    u = 'attribute'\n"
                "    class Nested("
                "metaclass=FlextSampleUtilitiesManagers.ServiceManagers):\n"
                "        pass\n"
            ),
            (
                "class Consumer:\n"
                "    u = 'attribute'\n"
                "    manager = FlextSampleUtilitiesManagers.ServiceManagers\n"
            ),
            (
                "class Consumer:\n"
                "    global u\n"
                "    u = 'module'\n"
                "    def select(self):\n"
                "        return FlextSampleUtilitiesManagers.ServiceManagers\n"
            ),
        ],
    )
    def test_rejects_shadowed_public_facade_alias(
        self,
        tmp_path: Path,
        consumer: str,
    ) -> None:
        """Fail before effects when a local binding would capture the facade alias."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "utilities",
                "managers",
                "Sample",
                "u",
            ),
        )
        sources[consumer_path] = f"{private_import}\n\n{consumer}"

        tm.fail(
            self._plan(tmp_path, sources, consumer_path, private_import),
            has="public facade alias u is shadowed",
        )

    @pytest.mark.parametrize(
        "class_binding",
        [
            "    u = 'attribute'\n",
            "    @property\n    def u(self):\n        return 'attribute'\n",
            "    class u:\n        pass\n",
        ],
    )
    def test_preserves_class_attributes_named_like_public_facade(
        self,
        tmp_path: Path,
        class_binding: str,
    ) -> None:
        """Class attributes do not capture module references inside methods."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "utilities",
                "managers",
                "Sample",
                "u",
            ),
        )
        sources[consumer_path] = (
            f"{private_import}\n\nclass Consumer:\n"
            f"{class_binding}"
            "    def select(self):\n"
            "        return FlextSampleUtilitiesManagers.ServiceManagers\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has=class_binding)
        tm.that(updated, has="return u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)

    @pytest.mark.parametrize(
        "mode", [(True, False), (True, True), (False, False), (False, True)]
    )
    @pytest.mark.parametrize(
        ("declaration", "evaluation", "scope"),
        [
            (
                (
                    "    select = staticmethod("
                    "lambda value=PrivateBinding.ServiceManagers: value)\n"
                ),
                "Consumer.select()",
                (True, False),
            ),
            (
                (
                    "    select = staticmethod("
                    "lambda *, value=PrivateBinding.ServiceManagers: value)\n"
                ),
                "Consumer.select()",
                (True, False),
            ),
            (
                (
                    "    class Nested(metaclass=PrivateBinding.ServiceManagers):\n"
                    "        pass\n"
                ),
                "type(Consumer.Nested)",
                (True, False),
            ),
            (
                (
                    "    class Nested(Base, "
                    "selection=PrivateBinding.ServiceManagers):\n"
                    "        pass\n"
                ),
                "Consumer.Nested.selected",
                (True, False),
            ),
            (
                "    select = staticmethod(lambda: PrivateBinding.ServiceManagers)\n",
                "Consumer.select()",
                (False, False),
            ),
            (
                (
                    "    class Nested:\n"
                    "        selected = PrivateBinding.ServiceManagers\n"
                ),
                "Consumer.Nested.selected",
                (False, False),
            ),
            *[
                (
                    f"    def select({parameters}){returns}:\n        pass\n",
                    f"Consumer.select.__annotations__[{key!r}]",
                    (True, True),
                )
                for parameters, returns, key in [
                    ("self, value: PrivateBinding.ServiceManagers, /", "", "value"),
                    ("self, value: PrivateBinding.ServiceManagers", "", "value"),
                    ("self, *, value: PrivateBinding.ServiceManagers", "", "value"),
                    ("self, *value: PrivateBinding.ServiceManagers", "", "value"),
                    ("self, **value: PrivateBinding.ServiceManagers", "", "value"),
                    ("self", " -> PrivateBinding.ServiceManagers", "return"),
                ]
            ],
            (
                "    value: PrivateBinding.ServiceManagers\n",
                "Consumer.__annotations__['value']",
                (True, True),
            ),
            (
                (
                    "    async def select(self) -> PrivateBinding.ServiceManagers:\n"
                    "        pass\n"
                ),
                "Consumer.select.__annotations__['return']",
                (True, True),
            ),
            (
                (
                    "    @decorate(PrivateBinding.ServiceManagers)\n"
                    "    def select(self):\n        pass\n"
                ),
                "Consumer.select.selected",
                (True, False),
            ),
            *[
                (
                    f"    def select[T{parameter}]():\n        pass\n",
                    f"Consumer.select.__type_params__[0].{attribute}",
                    (True, False),
                )
                for parameter, attribute in [
                    (": PrivateBinding.ServiceManagers", "__bound__"),
                    (
                        ": (PrivateBinding.ServiceManagers, int)",
                        "__constraints__[0]",
                    ),
                    (" = PrivateBinding.ServiceManagers", "__default__"),
                ]
            ],
            (
                (
                    "    class Nested[T: PrivateBinding.ServiceManagers]:\n"
                    "        pass\n"
                ),
                "Consumer.Nested.__type_params__[0].__bound__",
                (True, False),
            ),
            (
                (
                    "    def select[T](self, "
                    "value: PrivateBinding.ServiceManagers):\n        pass\n"
                ),
                "Consumer.select.__annotations__['value']",
                (True, True),
            ),
            (
                "    type Alias = PrivateBinding.ServiceManagers\n",
                "Consumer.Alias.__value__",
                (True, False),
            ),
            (
                (
                    "    @decorate(PrivateBinding.ServiceManagers)\n"
                    "    class Nested:\n        pass\n"
                ),
                "Consumer.Nested.selected",
                (True, False),
            ),
            (
                (
                    "    @staticmethod\n"
                    "    def select(value=PrivateBinding.ServiceManagers):\n"
                    "        return value\n"
                ),
                "Consumer.select()",
                (True, False),
            ),
        ],
    )
    def test_class_cutover_respects_definition_evaluation_scope(
        self,
        tmp_path: Path,
        declaration: str,
        evaluation: str,
        *,
        mode: t.Pair[bool, bool],
        scope: t.Pair[bool, bool],
    ) -> None:
        """Defaults and class keywords use the enclosing dictionary."""
        shadowed, future_annotations = mode
        enclosing_scope, annotation_scope = scope
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "utilities",
                "managers",
                "Sample",
                "u",
            ),
            import_alias="PrivateBinding",
        )
        source = (
            ("from __future__ import annotations\n" if future_annotations else "")
            + (
                f"{private_import}\n"
                "def decorate(selection):\n"
                "    def apply(function):\n"
                "        function.selected = selection\n"
                "        return function\n"
                "    return apply\n"
                "class Base:\n"
                "    def __init_subclass__(cls, *, selection):\n"
                "        cls.selected = selection\n"
                "class Consumer:\n"
            )
            + ("    u = 'attribute'\n" if shadowed else "")
            + declaration
        )
        sources[consumer_path] = source
        planned = self._plan(tmp_path, sources, consumer_path, private_import)
        rejected_capture = (
            shadowed
            and enclosing_scope
            and (not annotation_scope or not future_annotations)
        )
        if rejected_capture and planned.failure:
            tm.fail(planned, has="public facade alias u is shadowed")
            return
        updated = tm.ok(planned)[0].updated_source
        tm.that(updated, has="u.Sample.ServiceManagers")
        package = tmp_path / "flext-sample/src/flext_sample"
        sources[package / "_utilities/managers.py"] = (
            "class FlextSampleUtilitiesManagers:\n"
            "    class ServiceManagers(type):\n        pass\n"
        )
        sources[package / "__init__.py"] = "from .utilities import u\n"
        sources[consumer_path] = updated
        for path, content in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        executed = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys\nfrom runpy import run_path\n"
                        "sys.path.insert(0, sys.argv[1])\n"
                        "from flext_sample import u\n"
                        "Consumer = run_path(sys.argv[2])['Consumer']\n"
                        + (
                            f"assert {evaluation} == 'u.Sample.ServiceManagers'\n"
                            if annotation_scope and future_annotations
                            else f"assert {evaluation} is u.Sample.ServiceManagers\n"
                        )
                    ),
                    str(package.parent),
                    str(consumer_path),
                ],
                cwd=tmp_path,
            ),
        )
        if rejected_capture:
            tm.fail(u.Cli.process_succeeded(executed.outcome))
            tm.that(executed.stderr, has="AttributeError")
            tm.fail(planned, has="public facade alias u is shadowed")
            return
        tm.ok(u.Cli.process_succeeded(executed.outcome))
        tm.that(executed.stderr, eq="")

    def test_accepts_alias_owned_by_removed_private_import(
        self,
        tmp_path: Path,
    ) -> None:
        """Replace the old import binding with its public facade atomically."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "models",
                "base",
                "Metadata",
                "m",
            ),
            import_alias="m",
        )
        sources[consumer_path] = f"{private_import}\n\nmetadata = m.Metadata()\n"

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="from flext_sample import m")
        tm.that(updated, has="metadata = m.Metadata()")
        tm.that(updated, lacks=private_import)

    def test_preserves_type_checking_boundary_for_public_facade(
        self,
        tmp_path: Path,
    ) -> None:
        """Keep a type-only facade import in the original type-only boundary."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "models",
                "base",
                "Metadata",
                "m",
            ),
            import_alias="m",
        )
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            f"    {private_import}\n\n"
            "metadata: m.Metadata\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="if TYPE_CHECKING:\n    from flext_sample import m")
        tm.that(updated, lacks="\nfrom flext_sample import m\n")
        tm.that(updated, lacks=private_import)

    def test_preserves_multiple_type_only_facades_from_one_package(
        self,
        tmp_path: Path,
    ) -> None:
        """Rewire every type facade without promoting imports to runtime."""
        package_path = tmp_path / "flext-sample/src/flext_sample"
        consumer_path = tmp_path / "flext-consumer/src/flext_consumer/service.py"
        layers = (
            ("models", "m", "FlextSampleModelsBase", "Model"),
            ("protocols", "p", "FlextSampleProtocolsBase", "Protocol"),
            ("typings", "t", "FlextSampleTypesBase", "Type"),
        )
        sources: t.MutableMappingKV[Path, str] = {}
        private_imports: list[str] = []
        annotations: list[str] = []
        for layer, alias, private_class, nested_class in layers:
            private_module = f"flext_sample._{layer}.base"
            private_imports.append(
                f"from {private_module} import {private_class} as {alias}b",
            )
            sources[package_path / f"{layer}.py"] = self._facade_source(
                naming=TestsFlextInfraFacadeNaming(
                    private_module=private_module,
                    private_class=private_class,
                    root_class=f"FlextSample{layer.title()}",
                    nested_class=nested_class,
                    alias=alias,
                ),
            )
            annotations.append(f"value_{alias}: {alias}b.Member")
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n    "
            + "\n    ".join(private_imports)
            + "\n\n"
            + "\n".join(annotations)
            + "\n"
        )

        updated = self._updated_source(
            tmp_path,
            sources,
            consumer_path,
            *private_imports,
        )

        tm.that(updated, has="    from flext_sample import m, p, t")
        tm.that(updated.count("from flext_sample import"), eq=1)
        for _layer, alias, _private_class, nested_class in layers:
            tm.that(updated, has=f"value_{alias}: {alias}.{nested_class}.Member")
            tm.that(updated, lacks=f"\nfrom flext_sample import {alias}\n")
        for private_import in private_imports:
            tm.that(updated, lacks=private_import)

    def test_discovers_operational_facade_from_live_source(
        self,
        tmp_path: Path,
    ) -> None:
        """Rewire an operational family without a registered family-to-alias map."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "exceptions",
                "base",
                "Invalid",
                "e",
            ),
            import_alias="eb",
        )
        sources[consumer_path] = f"{private_import}\n\nerror: eb.Code\n"

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="from flext_sample import e")
        tm.that(updated, has="error: e.Invalid.Code")
        tm.that(updated, lacks=private_import)

    def test_replaces_public_long_alias_during_private_cutover(
        self,
        tmp_path: Path,
    ) -> None:
        """Delete the long public alias while wiring the canonical facade."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            TestsFlextInfraFacadeNaming.from_family(
                "models",
                "pydantic",
                "Pydantic",
                "m",
            ),
            import_alias="mp",
        )
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            f"{private_import}\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from flext_sample import FlextSampleModels as m\n\n"
            "value: m.Metadata\n"
            "model: mp.BaseModel\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated.count("from flext_sample import m"), eq=1)
        tm.that(updated, lacks="FlextSampleModels as m")
        tm.that(updated, lacks=private_import)
        tm.that(updated, has="model: m.Pydantic.BaseModel")

    def test_preserves_valid_relative_private_import(self, tmp_path: Path) -> None:
        """Leave an already-relative same-owner import outside the finding set."""
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        relative_import = (
            "from ._models.pydantic import FlextSampleModelsPydantic as mp"
        )

        edits = self._edits(
            tmp_path,
            {consumer_path: f"{relative_import}\n\nmodel = mp.BaseModel\n"},
            consumer_path,
        )

        tm.that(edits, eq=())
