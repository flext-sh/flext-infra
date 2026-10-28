"""Planned submodule class discovery for runtime-evaluated bases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests import tm, u


class TestsFlextInfraRuntimeEvaluatedPlannedSubmodules:
    """Planned submodule imports resolve declared classes, never invented ones."""

    @pytest.mark.parametrize(
        "import_statement",
        [
            "from {module}.{parts} import document as part",
            "from .{parts} import document as part",
            "import {module}.{parts}.document as part",
        ],
    )
    @pytest.mark.parametrize("initialized", [True, False])
    @pytest.mark.parametrize(
        "package_binding",
        [
            ("src/binding_contract", "binding_contract", "parts"),
            ("tests/unit", "tests.unit", "_parts"),
        ],
    )
    @staticmethod
    def test_planned_submodule_import_resolves_its_declared_class(
        tmp_path: Path,
        import_statement: str,
        package_binding: tuple[str, str, ...],
        *,
        initialized: bool,
    ) -> None:
        """Private and namespace submodules do not require initializer exports."""
        package_path, module, parts = package_binding
        package = tmp_path / package_path
        planned = {
            package / parts / "document.py": u.Tests.runtime_root_import()
            + "class Document(RuntimeRoot): pass\n",
            package / "facade.py": (
                f"{import_statement.format(module=module, parts=parts)}\n"
                "class Facade(part.Document): pass\n"
                "class Consumer(Facade): pass\n"
            ),
        }
        if initialized:
            planned[package / "__init__.py"] = ""
            planned[package / parts / "__init__.py"] = ""
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            ),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    f"{module}.{parts}.document.Document",
                    f"{module}.facade.Facade",
                )),
            ),
        )
        tm.fail(package.exists())
        tm.fail(f"{module}.{parts}.document" in sys.modules)

    @staticmethod
    def test_missing_planned_private_module_is_not_a_similarly_named_provider(
        tmp_path: Path,
    ) -> None:
        """An existing private provider cannot validate an obsolete import path."""
        package = tmp_path / "tests" / "unit"
        with pytest.raises(
            ValueError, match=r"Unresolved planned base: tests\.unit\._retired$"
        ):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    package / "__init__.py": "",
                    package
                    / "_retired_parts"
                    / "document.py": "class Document: pass\n",
                    package / "consumer.py": (
                        "from tests.unit._retired import document as part\n"
                        "class Invalid(part.Document): pass\n"
                    ),
                },
                (),
            )

    @pytest.mark.parametrize(
        ("shadow", "diagnostic"),
        [
            ("document = 0", r"Unresolved planned base: shadowed_submodule\.document"),
            ("class document: pass", "Missing inherited class member:"),
        ],
    )
    @staticmethod
    def test_planned_package_binding_is_not_replaced_by_a_submodule(
        tmp_path: Path,
        shadow: str,
        diagnostic: str,
    ) -> None:
        """Explicit package values/classes retain precedence over file names."""
        package = tmp_path / "src" / "shadowed_submodule"
        planned = {
            package / "__init__.py": shadow + "\n",
            package / "document.py": u.Tests.runtime_root_import()
            + "class Document(RuntimeRoot): pass\n",
            package / "consumer.py": (
                "from . import document as part\nclass Invalid(part.Document): pass\n"
            ),
        }
        with pytest.raises(ValueError, match=diagnostic):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            )

    @staticmethod
    def test_planned_submodule_does_not_invent_a_missing_class(
        tmp_path: Path,
    ) -> None:
        """A captured submodule proves its location, not arbitrary class exports."""
        package = tmp_path / "src" / "missing_submodule_class"
        with pytest.raises(
            ValueError,
            match=(
                r"Unresolved planned base: missing_submodule_class\.parts"
                r"\.document\.Missing"
            ),
        ):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    package / "__init__.py": "",
                    package / "parts" / "__init__.py": "",
                    package / "parts" / "document.py": "class Document: pass\n",
                    package / "consumer.py": (
                        "from .parts import document as part\n"
                        "class Invalid(part.Missing): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )
