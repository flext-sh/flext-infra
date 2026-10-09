"""Public runtime-base discovery from unpublished, authoritative planned bytes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c
from tests import u


class TestsFlextInfraRuntimeEvaluatedBaseClasses:
    """Plan new packages without importing them or collapsing nested identities."""

    @pytest.mark.parametrize(
        ("setup", "condition", "selects_model"),
        [
            ("from typing import TYPE_CHECKING", "TYPE_CHECKING", False),
            ("from typing import TYPE_CHECKING as checking", "checking", False),
            ("import typing as annotations", "annotations.TYPE_CHECKING", False),
            (
                "from typing_extensions import TYPE_CHECKING as checking",
                "checking",
                False,
            ),
            (
                "from typing import TYPE_CHECKING as original\nchecking = original",
                "checking",
                False,
            ),
            ("", "True", True),
            ("", "False", False),
            (
                "from typing import TYPE_CHECKING\nTYPE_CHECKING = True",
                "TYPE_CHECKING",
                True,
            ),
            ("checking: bool = False", "checking", False),
            ("original = True\nchecking = original", "checking", True),
        ],
    )
    def test_runtime_guard_uses_import_identity_and_boolean_rebindings(
        self,
        tmp_path: Path,
        setup: str,
        condition: str,
        *,
        selects_model: bool,
    ) -> None:
        """Only the proven runtime branch supplies the consumer's class alias."""
        source = u.Tests.runtime_root_import() + (
            f"{setup}\n"
            "class Model(RuntimeRoot): pass\n"
            "class Plain: pass\n"
            f"if {condition}:\n    Alias = Model\n"
            "else:\n    Alias = Plain\n"
            "class Consumer(Alias): pass\n"
        )
        expected = set(u.Tests.runtime_evaluated_roots())
        if selects_model:
            expected.add("runtime_guard.models.Alias")
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "runtime_guard" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted(expected)),
        )

    @pytest.mark.parametrize(
        ("setup", "condition"),
        [
            (
                (
                    "from typing import TYPE_CHECKING\n"
                    "from os import getenv\n"
                    "TYPE_CHECKING = bool(getenv('COLLECTOR_GUARD'))"
                ),
                "TYPE_CHECKING",
            ),
            (
                (
                    "import typing\nfrom os import getenv\n"
                    "typing = getenv('COLLECTOR_GUARD')"
                ),
                "typing.TYPE_CHECKING",
            ),
            ("", "TYPE_CHECKING"),
        ],
    )
    def test_unknown_guard_cannot_borrow_standard_constant_semantics(
        self,
        tmp_path: Path,
        setup: str,
        condition: str,
    ) -> None:
        """Undecidable guards retain the original ambiguous-base failure."""
        source = u.Tests.runtime_root_import() + (
            f"{setup}\n"
            "class Model(RuntimeRoot): pass\n"
            "class Plain: pass\n"
            f"if {condition}:\n    Alias = Model\n"
            "else:\n    Alias = Plain\n"
            "class Consumer(Alias): pass\n"
        )
        with pytest.raises(ValueError, match="Non-class binding used as a base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "unknown_guard" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    @pytest.mark.parametrize(
        ("setup", "mutation", "condition"),
        [
            (
                "import typing as ty",
                "ty.TYPE_CHECKING = enabled",
                "ty.TYPE_CHECKING",
            ),
            (
                "import typing as ty\nreflected = ty",
                "reflected.TYPE_CHECKING = enabled",
                "ty.TYPE_CHECKING",
            ),
            (
                "import typing",
                "typing.TYPE_CHECKING = enabled",
                "typing.TYPE_CHECKING",
            ),
        ],
    )
    def test_provider_guard_member_write_fails_before_stale_selection(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        setup: str,
        mutation: str,
        condition: str,
    ) -> None:
        """Unsupported module stores cannot preserve stale constant provenance."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                installed_dependency_path / "guard_provider.py",
                u.Tests.runtime_root_import() + f"{setup}\nenabled = True\n{mutation}\n"
                "class Model(RuntimeRoot): pass\n"
                "class Plain: pass\n"
                f"if {condition}:\n    Alias = Model\n"
                "else:\n    Alias = Plain\n"
                "class Derived(Alias): pass\n",
            ),
        )
        with pytest.raises(
            ValueError,
            match="Unsupported class binding mutation",
        ) as failure:
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "guard_consumer" / "models.py": (
                        "from guard_provider import Derived\n"
                        "class Consumer(Derived): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )
        tm.that(
            str(failure.value),
            eq=f"Unsupported class binding mutation in guard_provider: {mutation}",
        )
        tm.that("guard_provider" in sys.modules, eq=False)

    @pytest.mark.parametrize("replacement_model", [False, True])
    def test_provider_class_member_write_updates_exact_aliased_owner(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        *,
        replacement_model: bool,
    ) -> None:
        """Member replacement neither retains old lineage nor changes bare names."""
        initial_base = "" if replacement_model else "(RuntimeRoot)"
        replacement = "Model" if replacement_model else "Plain"
        tm.ok(
            u.Cli.atomic_write_text_file(
                installed_dependency_path / "namespace_provider.py",
                u.Tests.runtime_root_import() + "class Facade:\n"
                "    class Contract(RuntimeRoot): pass\n"
                "    class Namespace:\n"
                f"        class Contract{initial_base}: pass\n"
                "        class Model(RuntimeRoot): pass\n"
                "        class Plain: pass\n"
                "    reflected = Namespace\n"
                f"    replacement = Namespace.{replacement}\n"
                "    reflected.Contract = replacement\n",
            ),
        )
        expected = {*u.Tests.runtime_evaluated_roots(), "namespace_provider.Facade.Contract"}
        if replacement_model:
            expected.add("namespace_provider.Facade.Namespace.Contract")
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "namespace_consumer" / "models.py": (
                        "from namespace_provider import Facade\n"
                        "class OuterConsumer(Facade.Contract): pass\n"
                        "class MemberConsumer(Facade.Namespace.Contract): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted(expected)),
        )

    def test_provider_boolean_member_preserves_sdk_non_class_failure(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """A real Boolean member reaches the SDK's original non-class boundary."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                installed_dependency_path / "boolean_member_provider.py",
                "class Facade:\n"
                "    class Namespace:\n"
                "        class Contract: pass\n"
                "    enabled = True\n"
                "    reflected = Namespace\n"
                "    reflected.Contract = enabled\n",
            ),
        )
        with pytest.raises(
            TypeError,
            match="Rope did not resolve a required base to a class",
        ):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "boolean_member_consumer" / "models.py": (
                        "from boolean_member_provider import Facade\n"
                        "class Invalid(Facade.Namespace.Contract): pass\n"
                        "class Later(Missing): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )

    def test_unpublished_project_is_not_imported_or_created(
        self,
        tmp_path: Path,
    ) -> None:
        root = tmp_path / "unpublished"
        package = root / "src" / "unpublished_contract"
        planned = {
            package / "__init__.py": "",
            package / "models.py": u.Tests.runtime_root_import()
            + (
                "class Contract(RuntimeRoot): pass\n"
                "class Derived(Contract): pass\n"
                "class Consumer(Derived): pass\n"
            ),
        }
        tm.that(
            u.Infra.runtime_evaluated_base_classes(root, planned, u.Tests.runtime_evaluated_roots()),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "unpublished_contract.models.Contract",
                    "unpublished_contract.models.Derived",
                )),
            ),
        )
        tm.that(root.exists(), eq=False)
        tm.that("unpublished_contract" in sys.modules, eq=False)

    def test_import_aliases_relative_generic_bases_and_planned_disk_convergence(
        self,
        tmp_path: Path,
    ) -> None:
        package = tmp_path / "src" / "planned_contract"
        package.mkdir(parents=True)
        (package / "models.py").write_text("class Contract: pass\n", encoding="utf-8")
        planned = {
            package / "__init__.py": "from .models import Facade as m\n",
            package / "models.py": u.Tests.runtime_root_import()
            + (
                "class Contract[T](RuntimeRoot): pass\n"
                "class Facade:\n"
                "    class Contract(Contract[int]): pass\n"
            ),
            package / "nested" / "__init__.py": "",
            package / "nested" / "consumer.py": (
                "from ..models import Contract as Alias\n"
                "from .. import m as models\n"
                "import planned_contract.models as module_alias\n"
                "class Direct(Alias[int]): pass\n"
                "class Nested(models.Contract): pass\n"
                "class Qualified(module_alias.Facade.Contract): pass\n"
            ),
        }
        expected = tuple(
            sorted((
                *u.Tests.runtime_evaluated_roots(),
                "planned_contract.models.Contract",
                "planned_contract.m.Contract",
                "planned_contract.models.Facade.Contract",
            )),
        )
        actual = u.Infra.runtime_evaluated_base_classes(
            tmp_path,
            planned,
            u.Tests.runtime_evaluated_roots(),
        )
        tm.that(actual, eq=expected)
        for path, source in planned.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, {}, u.Tests.runtime_evaluated_roots()),
            eq=actual,
        )

    @pytest.mark.parametrize("model_on_right", [False, True])
    def test_nested_member_lookup_obeys_c3_not_depth_first(
        self,
        tmp_path: Path,
        *,
        model_on_right: bool,
    ) -> None:
        origin_base = "" if model_on_right else "(RuntimeRoot)"
        right_base = "(RuntimeRoot)" if model_on_right else ""
        source = u.Tests.runtime_root_import() + (
            "class Origin:\n"
            f"    class Contract{origin_base}: pass\n"
            "class Left(Origin): pass\n"
            "class Right(Origin):\n"
            f"    class Contract{right_base}: pass\n"
            "class Joint(Left, Right): pass\n"
            "class Consumer(Joint.Contract): pass\n"
        )
        expected = tuple(
            sorted((
                *u.Tests.runtime_evaluated_roots(),
                *(("c3_contract.models.Joint.Contract",) if model_on_right else ()),
            )),
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "c3_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=expected,
        )

    def test_nested_bare_names_do_not_collide(self, tmp_path: Path) -> None:
        source = u.Tests.runtime_root_import() + (
            "class First:\n"
            "    class Contract(RuntimeRoot): pass\n"
            "    class Consumer(Contract): pass\n"
            "class Second:\n"
            "    class Contract: pass\n"
            "    class Consumer(Contract): pass\n"
            "class Positive(First.Contract): pass\n"
            "class Negative(Second.Contract): pass\n"
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "collision_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "collision_contract.models.Contract",
                    "collision_contract.models.First.Contract",
                )),
            ),
        )

    def test_generated_lazy_bindings_are_indexed_without_importing(
        self,
        tmp_path: Path,
    ) -> None:
        """Generated package exports bind the same source-defined model identity."""
        package = tmp_path / "src" / "generated_contract"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            c.Infra.AUTOGEN_HEADERS[0]
            + "\nfrom types import MappingProxyType\n"
            + "from typing import TYPE_CHECKING\n"
            + "from flext_core import install_lazy_exports\n"
            + "if TYPE_CHECKING:\n    from .models import m\n"
            + "install_lazy_exports(__name__, __file__, "
            'MappingProxyType({"m": ".models"}), public_exports=("m",))\n'
            + 'raise RuntimeError("This package must not be imported")\n',
            encoding="utf-8",
        )
        planned = {
            package / "models.py": u.Tests.runtime_root_import()
            + "class Contract(RuntimeRoot): pass\n"
            + "class Derived(Contract): pass\nm = Contract\n",
            package / "consumer.py": (
                "from generated_contract import m\nclass Consumer(m): pass\n"
            ),
        }
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots()),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "generated_contract.models.Contract",
                    "generated_contract.m",
                )),
            ),
        )
        tm.that("generated_contract" in sys.modules, eq=False)

    @pytest.mark.parametrize("qualified", [False, True])
    def test_generated_lazy_member_keeps_the_export_binding(
        self,
        tmp_path: Path,
        *,
        qualified: bool,
    ) -> None:
        """Provider members resolve through the exported class, not its module."""
        package = tmp_path / "src" / "flext"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            c.Infra.AUTOGEN_HEADERS[0]
            + "\nfrom types import MappingProxyType\n"
            + "from typing import TYPE_CHECKING\n"
            + "from flext_core import install_lazy_exports\n"
            + "if TYPE_CHECKING:\n    from .models import m\n"
            + "install_lazy_exports(__name__, __file__, "
            'MappingProxyType({"m": ".models"}), public_exports=("m",))\n'
            + 'raise RuntimeError("This package must not be imported")\n',
            encoding="utf-8",
        )
        source = (
            "import flext\nclass Consumer(flext.m.BaseModel): pass\n"
            if qualified
            else "from flext import m\nclass Consumer(m.BaseModel): pass\n"
        )
        planned = {
            package / "models.py": u.Tests.runtime_root_import()
            + "class Contract(RuntimeRoot): pass\n"
            + "class Facade:\n    BaseModel = Contract\nm = Facade\n",
            package / "consumer.py": source,
        }
        was_imported = "flext" in sys.modules
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots()),
            eq=tuple(sorted({*u.Tests.runtime_evaluated_roots(), "flext.m.BaseModel"})),
        )
        tm.that("flext" in sys.modules, eq=was_imported)

    def test_missing_direct_package_base_is_not_invented(self, tmp_path: Path) -> None:
        """An available provider class does not imply a package-level export."""
        package = tmp_path / "src" / "flext"
        planned = {
            package / "__init__.py": "",
            package / "models.py": u.Tests.runtime_root_import()
            + "class BaseModel(RuntimeRoot): pass\n",
            package / "consumer.py": (
                "import flext\nclass Invalid(flext.BaseModel): pass\n"
            ),
        }
        with pytest.raises(
            ValueError, match=r"Unresolved planned base: flext\.BaseModel"
        ):
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots())

    def test_native_stdlib_aliases_preserve_the_same_qualified_bases(
        self,
        tmp_path: Path,
    ) -> None:
        """A native stdlib provider has one identity through either import form."""
        path = tmp_path / "src" / "native_contract" / "models.py"
        direct = u.Infra.runtime_evaluated_base_classes(
            tmp_path,
            {
                path: (
                    "from collections.abc import Mapping\n"
                    "class Consumer(Mapping): pass\n"
                ),
            },
            u.Tests.runtime_evaluated_roots(),
        )
        aliased = u.Infra.runtime_evaluated_base_classes(
            tmp_path,
            {
                path: (
                    "import collections.abc as provider\n"
                    "class Consumer(provider.Mapping): pass\n"
                ),
            },
            u.Tests.runtime_evaluated_roots(),
        )
        tm.that(aliased, eq=direct)
        tm.that(set(u.Tests.runtime_evaluated_roots()).issubset(aliased), eq=True)

    def test_value_shadowing_is_a_visible_invalid_base(self, tmp_path: Path) -> None:
        source = u.Tests.runtime_root_import() + (
            "class Origin:\n"
            "    class Contract(RuntimeRoot): pass\n"
            "class Shadow(Origin): Contract = 0\n"
            "class Consumer(Shadow.Contract): pass\n"
        )
        with pytest.raises(ValueError, match="Non-class member shadows required base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "shadow_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    @pytest.mark.parametrize(
        "import_statement",
        [
            "from binding_contract.parts import document as part",
            "from .parts import document as part",
            "import binding_contract.parts.document as part",
        ],
    )
    def test_planned_submodule_import_resolves_its_declared_class(
        self,
        tmp_path: Path,
        import_statement: str,
    ) -> None:
        """An import-from submodule alias does not require an initializer export."""
        package = tmp_path / "src" / "binding_contract"
        planned = {
            package / "__init__.py": "",
            package / "parts" / "__init__.py": "",
            package / "parts" / "document.py": u.Tests.runtime_root_import()
            + "class Document(RuntimeRoot): pass\n",
            package / "facade.py": (
                f"{import_statement}\nclass Facade(part.Document): pass\n"
                "class Consumer(Facade): pass\n"
            ),
        }
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots()),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "binding_contract.parts.document.Document",
                    "binding_contract.facade.Facade",
                )),
            ),
        )
        tm.that(package.exists(), eq=False)
        tm.that("binding_contract" in sys.modules, eq=False)

    @pytest.mark.parametrize(
        ("shadow", "diagnostic"),
        [
            ("document = 0", r"Unresolved planned base: shadowed_submodule\.document"),
            ("class document: pass", "Missing inherited class member:"),
        ],
    )
    def test_planned_package_binding_is_not_replaced_by_a_submodule(
        self,
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
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots())

    def test_planned_submodule_does_not_invent_a_missing_class(
        self,
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
