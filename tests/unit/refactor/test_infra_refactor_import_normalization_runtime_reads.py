"""Import-law engine: what the language never evaluates is never a runtime read.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import r, tm, u
from tests.unit.refactor.import_normalization_support import (
    TestsFlextInfraRefactorImportNormalizationSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalizationRuntimeReads(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Deferred annotations, lazy bounds and bootstrap typing are not edges."""

    @classmethod
    def _family_module(
        cls, tmp_path: Path, letter: str, body: str
    ) -> tuple[Path, Path, str]:
        """Write one family member whose reverse letter is typing-only.

        Returns:
            The project root, the member path and its source.

        """
        project, package = cls._project(tmp_path)
        family = u.Infra.facade_families()[letter]
        directory = package / family.directory
        cls._lazy_init(directory, {"DemoDeclaration": ".declaration"})
        source = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING, Protocol, runtime_checkable\n"
            "if TYPE_CHECKING:\n"
            "    from demo_pkg import m\n"
            f"{body}"
        )
        return project, directory / "declaration.py", source

    @classmethod
    def test_nested_protocol_attribute_annotation_is_deferred(
        cls, tmp_path: Path
    ) -> None:
        """A Protocol never evaluates its annotations, even nested in a facade."""
        project, module, source = cls._family_module(
            tmp_path,
            "p",
            "class DemoDeclaration:\n"
            "    @runtime_checkable\n"
            "    class HasRecord(Protocol):\n"
            "        record: p.DemoRecord\n",
        )
        tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=source
            ),
            eq=source,
        )

    @classmethod
    def test_annotation_only_fragment_routes_its_dependent_facade(
        cls, tmp_path: Path
    ) -> None:
        """Own-family annotations use their declaring owner without a back-import."""
        project, package = cls._project(tmp_path)
        family = u.Infra.facade_families()["p"]
        cls._lazy_init(package, {"p": f".{family.module}"})
        directory = package / family.directory
        cls._lazy_init(directory, {"DemoDeclaration": ".base"})
        (package / f"{family.module}.py").write_text(
            f"from demo_pkg.{family.directory} import DemoDeclaration\n"
            "class DemoProtocols(DemoDeclaration): pass\n"
            "p = DemoProtocols\n__all__ = ['p']\n",
            encoding="utf-8",
        )
        source = (
            "from __future__ import annotations\n"
            "from typing import Protocol\n"
            "from demo_pkg import p\n"
            "class DemoDeclaration:\n"
            "    class Reader(Protocol):\n"
            "        def read(self, value: p.Reader) -> p.Reader: ...\n"
            "__all__ = ['DemoDeclaration']\n"
        )
        module = directory / "base.py"
        module.write_text(source, encoding="utf-8")
        normalized = tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=source
            )
        )
        tm.that(normalized, lacks="from demo_pkg import p")
        tm.that(normalized, has="DemoDeclaration.Reader")
        module.write_text(normalized, encoding="utf-8")
        tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=normalized
            ),
            eq=normalized,
        )

    @classmethod
    def test_type_parameter_bound_is_lazy(cls, tmp_path: Path) -> None:
        """PEP 695 bounds are evaluated lazily, so they read nothing at runtime."""
        project, module, source = cls._family_module(
            tmp_path,
            "p",
            "class DemoDeclaration:\n"
            "    @runtime_checkable\n"
            "    class Converts(Protocol):\n"
            "        def to_model[U: p.DemoRecord](self, model: type[U]) -> U: ...\n",
        )
        tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=source
            ),
            eq=source,
        )

    @classmethod
    def test_function_local_annotation_is_never_evaluated(cls, tmp_path: Path) -> None:
        """A variable annotation inside a function body is never a runtime read."""
        project, module, source = cls._family_module(
            tmp_path,
            "t",
            "class DemoDeclaration:\n"
            "    @staticmethod\n"
            "    def narrow(value: str) -> str:\n"
            "        record: p.DemoRecord | None = None\n"
            "        return value if record is None else value\n",
        )
        tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=source
            ),
            eq=source,
        )

    @classmethod
    def test_runtime_read_of_reverse_letter_still_fails(cls, tmp_path: Path) -> None:
        """A real runtime read of a reverse letter keeps failing loud."""
        project, module, source = cls._family_module(
            tmp_path,
            "t",
            "class DemoDeclaration:\n    RECORD = m.DemoRecord\n",
        )
        tm.fail(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=source
            ),
            has="forbidden reverse namespace import",
        )

    @classmethod
    def test_lazy_loader_typing_import_is_outside_its_boundary(
        cls, tmp_path: Path
    ) -> None:
        """The lazy loader is layer zero for runtime re-entry only."""
        project, package = cls._project(tmp_path)
        source = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from demo_pkg import t\n"
            "class DemoLazy:\n"
            "    @staticmethod\n"
            "    def hooks(value: t.JsonValue) -> t.JsonValue:\n"
            "        return value\n"
        )
        tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=package / "lazy.py", source=source
            ),
            eq=source,
        )

    @classmethod
    def test_layer_zero_helper_with_foundation_imports_is_admitted(
        cls, tmp_path: Path
    ) -> None:
        """Foundation providers of an own helper are not own candidate edges."""
        project, package = cls._project(tmp_path)
        (package / "_settings.py").write_text(
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING\n"
            "from pydantic import BaseModel, JsonValue\n"
            "class DemoSettings(BaseModel):\n"
            "    value: JsonValue = None\n"
            "__all__: list[str] = ['DemoSettings']\n",
            encoding="utf-8",
        )
        source = (
            "from __future__ import annotations\n"
            "from demo_pkg._settings import DemoSettings\n"
            "class DemoConfig(DemoSettings):\n"
            "    pass\n"
        )
        normalized = tm.ok(
            u.Infra.normalize_import_source(
                project_root=project, file_path=package / "_config.py", source=source
            )
        )
        tm.that(normalized, has="DemoSettings")
        tm.that(normalized, lacks="from demo_pkg import")

    @classmethod
    def test_tests_fail_is_the_result_matcher(cls) -> None:
        """``u.Tests.fail`` validates a failed result; pytest's outcome never wins."""
        tm.that(tm.fail(r[int].fail("boom"), has="boom"), eq="boom")
