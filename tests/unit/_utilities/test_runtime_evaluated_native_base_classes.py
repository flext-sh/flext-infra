"""Runtime-base discovery across native, provider and re-exported class lineage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flext_tests import tm

from tests import u


class TestsFlextInfraRuntimeEvaluatedNativeBaseClasses:
    """Native ancestry, provider metadata and aliases keep declared lineage."""

    @pytest.mark.parametrize("name", ["Structure", "Union", "Array"])
    def test_ctypes_native_private_parents_do_not_require_module_exports(
        self,
        tmp_path: Path,
        name: str,
    ) -> None:
        """Real ctypes classes retain their private native ancestry."""
        body = (
            "    _length_ = 1\n    _type_ = ctypes.c_byte\n"
            if name == "Array"
            else "    _fields_ = ()\n"
        )
        source = (
            "import ctypes\n"
            f"class Consumer(ctypes.{name}):\n{body}"
            "class NativeParentConsumer(ctypes.Structure.__base__): pass\n"
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "ctypes_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
        )

    def test_ctypes_inherited_alias_obeys_c3_with_shared_native_identity(
        self,
        tmp_path: Path,
    ) -> None:
        """Native wrapper identity cannot split the shared diamond ancestor."""
        source = u.Tests.runtime_root_import() + (
            "from ctypes import Structure\n"
            "class Origin(Structure):\n    class Contract: pass\n"
            "class Left(Origin): pass\n"
            "class Right(Origin):\n    class Contract(RuntimeRoot): pass\n"
            "class Joint(Left, Right): pass\n"
            "class Consumer(Joint.Contract): pass\n"
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "native_diamond" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted((*u.Tests.runtime_evaluated_roots(), "native_diamond.models.Joint.Contract"))),
        )

    def test_shared_private_native_parent_is_still_a_duplicate_base(
        self,
        tmp_path: Path,
    ) -> None:
        """Separate provider wrappers cannot invent distinct native classes."""
        with pytest.raises(ValueError, match="Duplicate class base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "duplicate_native" / "models.py": (
                        "from ctypes import Structure as First\n"
                        "import ctypes as provider\n"
                        "class Invalid(First.__base__, provider.Union.__base__): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )

    @pytest.mark.parametrize(
        ("module", "name"),
        [("_ctypes", "_CData"), ("ctypes", "MissingNativeClass")],
    )
    def test_missing_native_export_keeps_its_original_failure(
        self,
        tmp_path: Path,
        module: str,
        name: str,
    ) -> None:
        """An observed private parent is not an invented module-level export."""
        with pytest.raises(u.Infra.rope_attribute_not_found_error_types()) as failure:
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "missing_native" / "models.py": (
                        f"import {module}\nclass Invalid({module}.{name}): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )
        tm.that(str(failure.value), eq=f"Attribute {name} not found")

    @pytest.mark.parametrize("name", ["ABC", "ABCMeta"])
    def test_native_abc_provider_metadata_preserves_class_bases(
        self,
        tmp_path: Path,
        name: str,
    ) -> None:
        """CPython's ABCMeta metadata assignment is not a lineage mutation."""
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "abc_contract" / "models.py": (
                        f"from abc import {name}\nclass Consumer({name}): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
        )

    @pytest.mark.parametrize("declared", [False, True])
    @pytest.mark.parametrize(
        "metadata",
        [
            "Contract.__module__ = __name__",
            "Contract.__module__: str = 'published_metadata'",
            "Contract.__name__ = 'PublishedContract'",
            "Contract.__qualname__ = 'Published.Contract'",
            "Contract.__doc__ = 'Published documentation'",
        ],
    )
    def test_provider_class_metadata_preserves_imported_and_declared_lineage(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        metadata: str,
        *,
        declared: bool,
    ) -> None:
        """Metadata neither changes lexical class bindings nor publishes aliases."""
        provider = installed_dependency_path / "metadata_provider.py"
        declaration = (
            u.Tests.runtime_root_import() + "class Contract(RuntimeRoot): pass\n"
            if declared
            else u.Tests.runtime_root_import() + "Contract = RuntimeRoot\n"
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider,
                declaration + f"{metadata}\nclass Derived(Contract): pass\n"
                "raise RuntimeError('provider must not be imported')\n",
            ),
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "metadata_contract" / "models.py": (
                        "from metadata_provider import Derived\n"
                        "class Consumer(Derived): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted((*u.Tests.runtime_evaluated_roots(), "metadata_provider.Derived"))),
        )
        tm.that("metadata_provider" in sys.modules, eq=False)

    @pytest.mark.parametrize(
        "mutation",
        [
            "Contract.__bases__ = (Plain,)",
            "Contract.__bases__ = replacement",
            "Contract.__class__ = Plain",
            "Namespace.Contract = 0",
            "Contract.__module__ = Namespace.Contract = 'metadata'",
        ],
    )
    def test_provider_metadata_never_masks_the_first_binding_mutation(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        mutation: str,
    ) -> None:
        """The first unsupported store escapes before a later invalid base."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                installed_dependency_path / "mutating_provider.py",
                u.Tests.runtime_root_import()
                + "class Contract(RuntimeRoot): pass\nclass Plain: pass\n"
                "class Namespace:\n    Contract = Contract\n"
                "replacement = (Plain,)\n"
                "Contract.__module__ = __name__\n"
                f"{mutation}\nclass Derived(Contract): pass\n",
            ),
        )
        with pytest.raises(
            ValueError,
            match="Unsupported class binding mutation",
        ) as failure:
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "mutation_consumer" / "models.py": (
                        "from mutating_provider import Derived\n"
                        "class Consumer(Derived): pass\n"
                        "class Later(Missing): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )
        tm.that(
            str(failure.value),
            eq=f"Unsupported class binding mutation in mutating_provider: {mutation}",
        )

    def test_class_local_table_subscript_store_is_not_a_class_rebinding(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        r"""A subscript store into a class-local table binds no class.

        CPython's ``http.server.BaseHTTPRequestHandler`` builds
        ``_control_char_table = str.maketrans(...)`` and then writes
        ``_control_char_table[ord('\\')] = r'\\'`` in the class body; the
        inventory accepts it and keeps resolving the class lineage.
        """
        tm.ok(
            u.Cli.atomic_write_text_file(
                installed_dependency_path / "table_provider.py",
                u.Tests.runtime_root_import() + "class Handler(RuntimeRoot):\n"
                "    _control_char_table = str.maketrans(\n"
                f"        {c: fr'\\x{c:02x}' for c in range(32)})\n"
                "    _control_char_table[ord('\\\\')] = r'\\\\'\n",
            ),
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "table_consumer" / "models.py": (
                        "from table_provider import Handler\n"
                        "class Consumer(Handler): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted({*u.Tests.runtime_evaluated_roots(), "table_provider.Handler"})),
        )

    def test_inconsistent_mro_fails_visibly(self, tmp_path: Path) -> None:
        source = (
            "class Left: pass\nclass Right: pass\n"
            "class First(Left, Right): pass\nclass Second(Right, Left): pass\n"
            "class Invalid(First, Second): pass\n"
        )
        with pytest.raises(ValueError, match="Inconsistent class MRO"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "invalid_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    @pytest.mark.parametrize("aliased", [False, True])
    def test_qualified_provider_import_keeps_its_class_attributes(
        self,
        tmp_path: Path,
        *,
        aliased: bool,
    ) -> None:
        """A module binding is resolved with its attributes, never as a class."""
        root = u.Tests.runtime_evaluated_roots()[0]
        module, _, name = root.rpartition(".")
        source = (
            f"import {module} as provider\nclass Contract(provider.{name}): pass\n"
            if aliased
            else f"import {module}\nclass Contract({root}): pass\n"
        )
        source += "class Consumer(Contract): pass\n"
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "qualified_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted((*u.Tests.runtime_evaluated_roots(), "qualified_contract.models.Contract"))),
        )

    def test_libcst_module_alias_resolves_the_published_class(
        self,
        tmp_path: Path,
    ) -> None:
        """The original real-consumer base has a complete installed source identity."""
        source = "import libcst as cst\nclass Transformer(cst.CSTTransformer): pass\n"
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "transformer_contract" / "visitor.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
        )

    def test_provider_reexports_and_inherited_aliases_use_declared_source(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Static provider provenance supplies lazy exports without importing them."""
        provider = installed_dependency_path / "declared_provider"
        provider.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider / "__init__.py",
                "from .models import Facade as exports\n"
                "raise RuntimeError('provider must not be imported during planning')\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider / "models.py",
                u.Tests.runtime_root_import()
                + "class Contracts:\n    class Payload(RuntimeRoot): pass\n"
                "class Parent(Contracts): pass\n"
                "class Facade(Parent): Alias = Parent.Payload\n",
            ),
        )
        source = (
            "from declared_provider import exports as schemas\n"
            "class Consumer(schemas.Alias): pass\n"
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "provider_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(sorted((*u.Tests.runtime_evaluated_roots(), "declared_provider.exports.Alias"))),
        )
        tm.that("declared_provider" in sys.modules, eq=False)

    def test_planned_reexport_overrides_an_installed_provider(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """A same-name installed distribution cannot override the captured plan."""
        provider = installed_dependency_path / "planned_provider"
        provider.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider / "__init__.py",
                "from .models import Contract\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider / "models.py",
                "class Contract: pass\n",
            ),
        )
        bridge = installed_dependency_path / "declared_bridge"
        bridge.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                bridge / "__init__.py",
                "from planned_provider.models import Contract\nFacade = Contract\n",
            ),
        )
        package = tmp_path / "src" / "planned_provider"
        planned = {
            package / "__init__.py": "from .models import Contract\n",
            package / "models.py": u.Tests.runtime_root_import()
            + "class Contract(RuntimeRoot): pass\n",
            package / "consumer.py": (
                "from planned_provider import Contract\n"
                "from declared_bridge import Facade\n"
                "class Consumer(Contract): pass\n"
                "class BridgedConsumer(Facade): pass\n"
            ),
        }
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots()),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "planned_provider.Contract",
                    "declared_bridge.Facade",
                )),
            ),
        )

    def test_configured_root_can_be_an_unpublished_planned_class(
        self,
        tmp_path: Path,
    ) -> None:
        package = tmp_path / "src" / "unpublished_root"
        roots = ("unpublished_root.Contract",)
        planned = {
            package / "__init__.py": "from .models import Contract\n",
            package / "models.py": u.Tests.runtime_root_import()
            + "class Contract(RuntimeRoot): pass\n",
            package / "consumer.py": (
                "from unpublished_root import Contract\n"
                "class Consumer(Contract): pass\n"
            ),
        }
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, roots),
            eq=roots,
        )

    @pytest.mark.parametrize("value", ["0", "RuntimeRoot()"])
    def test_field_or_call_value_cannot_be_a_class_alias(
        self,
        tmp_path: Path,
        value: str,
    ) -> None:
        """A shadowing value fails instead of borrowing the ancestor's class."""
        source = u.Tests.runtime_root_import() + (
            "class Parent:\n    class Contract(RuntimeRoot): pass\n"
            f"class Shadow(Parent): Contract = {value}\n"
            "class Consumer(Shadow.Contract): pass\n"
        )
        with pytest.raises(ValueError, match="Non-class member shadows required base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "value_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    def test_missing_explicit_external_base_is_not_deselected(
        self,
        tmp_path: Path,
    ) -> None:
        source = u.Tests.runtime_root_import() + (
            "import absent_provider_contract as missing\n"
            "class Invalid(RuntimeRoot, missing.Required): pass\n"
        )
        with pytest.raises(u.Infra.rope_module_not_found_error_types()):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "missing_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    def test_imported_module_is_not_a_class_identity(self, tmp_path: Path) -> None:
        source = "import libcst as cst\nclass Invalid(cst): pass\n"
        with pytest.raises(ValueError, match="Module used as a class base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "module_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    def test_duplicate_class_identity_through_alias_fails(
        self,
        tmp_path: Path,
    ) -> None:
        source = u.Tests.runtime_root_import() + (
            "Alias = RuntimeRoot\nclass Invalid(RuntimeRoot, Alias): pass\n"
        )
        with pytest.raises(ValueError, match="Duplicate class base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "duplicate_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    def test_conditional_required_alias_is_not_chosen_from_one_branch(
        self,
        tmp_path: Path,
    ) -> None:
        source = u.Tests.runtime_root_import() + (
            "class Model(RuntimeRoot): pass\nclass Plain: pass\n"
            "if unknown_condition:\n    Alias = Model\n"
            "else:\n    Alias = Plain\n"
            "class Consumer(Alias): pass\n"
        )
        with pytest.raises(ValueError, match="Non-class binding used as a base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "conditional_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    @pytest.mark.parametrize(
        "mutation",
        [
            "del Contract",
            "Contract, other = (0, 1)",
            "[Contract] = [0]",
            "Namespace.Contract = Plain",
            "Namespace.Contract += Plain",
        ],
    )
    def test_unsupported_mutation_never_preserves_a_previous_class(
        self,
        tmp_path: Path,
        mutation: str,
    ) -> None:
        source = u.Tests.runtime_root_import() + (
            "class Contract(RuntimeRoot): pass\nclass Plain: pass\n"
            "class Namespace:\n    Contract = Contract\n"
            f"{mutation}\nclass Consumer(Contract): pass\n"
        )
        with pytest.raises(ValueError, match="Unsupported class binding mutation"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "mutation_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    def test_provider_reexport_enters_a_planned_class_once(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        provider = installed_dependency_path / "planned_bridge"
        provider.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider / "__init__.py",
                "from planned_destination.models import Contract\n"
                "raise RuntimeError('provider must not be imported')\n",
            ),
        )
        package = tmp_path / "src" / "planned_destination"
        planned = {
            package / "__init__.py": "",
            package / "models.py": u.Tests.runtime_root_import()
            + "class Contract(RuntimeRoot): pass\n",
            package / "consumer.py": (
                "from planned_bridge import Contract\nclass Consumer(Contract): pass\n"
            ),
        }
        tm.that(
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots()),
            eq=tuple(sorted((*u.Tests.runtime_evaluated_roots(), "planned_bridge.Contract"))),
        )
        tm.that(package.exists(), eq=False)
        tm.that("planned_bridge" in sys.modules, eq=False)

    def test_true_planned_reexport_cycle_fails_at_its_binding(
        self,
        tmp_path: Path,
    ) -> None:
        package = tmp_path / "src" / "cycle_contract"
        planned = {
            package / "__init__.py": "",
            package / "left.py": "from .right import Contract\n",
            package / "right.py": "from .left import Contract\n",
            package / "consumer.py": (
                "from .left import Contract\nclass Consumer(Contract): pass\n"
            ),
        }
        with pytest.raises(ValueError, match="Cyclic class alias"):
            u.Infra.runtime_evaluated_base_classes(tmp_path, planned, u.Tests.runtime_evaluated_roots())

    def test_missing_inherited_member_cannot_be_deselected(
        self,
        tmp_path: Path,
    ) -> None:
        source = "class Namespace: pass\nclass Invalid(Namespace.Missing): pass\n"
        with pytest.raises(ValueError, match="Missing inherited class member"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "member_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )
