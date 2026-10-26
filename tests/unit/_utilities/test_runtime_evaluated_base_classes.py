"""Public runtime-base discovery from unpublished, authoritative planned bytes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from contextlib import closing
from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraRuntimeEvaluatedBaseClasses:
    """Plan new packages without importing them or collapsing nested identities."""

    @staticmethod
    def test_namespace_lazy_provider_retains_its_full_import_identity(
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """A namespace prefix survives lazy provider lookup beside an SDK collision."""
        _ = u.Tests.standalone_workspace(tmp_path, "namespace-contract")
        _ = u.Tests.write_standalone_workspace_manifest(
            tmp_path,
            "namespace-contract",
            declaration=u.Tests.StandaloneManifestDeclaration(
                repository_namespace_packages=("infra",),
            ),
        )
        package = tmp_path / "infra" / "pulumi" / "lib"
        package.mkdir(parents=True)
        (package.parent / "__init__.py").write_text(
            'raise RuntimeError("project package must remain unimported")\n',
            encoding="utf-8",
        )
        (package / "__init__.py").write_text(
            "from types import MappingProxyType\n"
            "from flext_core.lazy import install_lazy_exports\n"
            "install_lazy_exports(__name__, globals(), "
            'MappingProxyType({"c": ".constants"}), public_exports=("c",))\n'
            'raise RuntimeError("lazy package must remain unimported")\n',
            encoding="utf-8",
        )
        (package / "constants.py").write_text(
            u.Tests.runtime_root_import()
            + "class Constants:\n    class Payload(RuntimeRoot): pass\n"
            "c = Constants\n",
            encoding="utf-8",
        )
        collision = installed_dependency_path / "pulumi"
        collision.mkdir()
        (collision / "__init__.py").write_text(
            'raise RuntimeError("colliding SDK must remain unimported")\n',
            encoding="utf-8",
        )
        consumer = tmp_path / "consumer"
        source = consumer / "src" / "namespace_consumer" / "models.py"
        imports_before = {
            name: name in sys.modules
            for name in ("infra", "infra.pulumi", "infra.pulumi.lib", "pulumi")
        }
        planned = {
            source: "from infra.pulumi.lib import c\nclass Consumer(c.Payload): pass\n",
        }
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(u.Infra.snapshot_project(original, planned)) as project,
        ):
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    consumer,
                    planned,
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(
                    sorted({
                        *u.Tests.runtime_evaluated_roots(),
                        "infra.pulumi.lib.c.Payload",
                    })
                ),
            )
        tm.that((tmp_path / "infra" / "__init__.py").exists(), eq=False)
        tm.that(
            {name: name in sys.modules for name in imports_before},
            eq=imports_before,
        )

    @staticmethod
    def test_external_relative_child_import_resolves_without_package_reentry(
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """An explicit child-module import reaches its class through static source."""
        provider = installed_dependency_path / "relative_child_provider"
        provider.mkdir()
        (provider / "__init__.py").write_text(
            "from . import runtime\n"
            'raise RuntimeError("provider initializer must remain unimported")\n',
            encoding="utf-8",
        )
        (provider / "runtime.py").write_text(
            u.Tests.runtime_root_import() + "class Contract(RuntimeRoot): pass\n"
            'raise RuntimeError("provider child must remain unimported")\n',
            encoding="utf-8",
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "child_consumer" / "models.py": (
                        "import relative_child_provider\n"
                        "class Consumer(relative_child_provider.runtime.Contract): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(
                sorted({
                    *u.Tests.runtime_evaluated_roots(),
                    "relative_child_provider.runtime.Contract",
                })
            ),
        )
        tm.fail("relative_child_provider" in sys.modules)
        tm.fail("relative_child_provider.runtime" in sys.modules)

    @staticmethod
    def test_external_data_mutation_preserves_the_unrelated_class_declaration(
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """External augmented data stays unknown while its real class is resolved."""
        (installed_dependency_path / "augmented_data_provider.py").write_text(
            u.Tests.runtime_root_import() + "config_keys = set()\n"
            "config_keys |= set(RuntimeRoot.__annotations__.keys())\n"
            "class Contract(RuntimeRoot): pass\n"
            'raise RuntimeError("data provider must remain unimported")\n',
            encoding="utf-8",
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "data_consumer" / "models.py": (
                        "from augmented_data_provider import Contract\n"
                        "class Consumer(Contract): pass\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            ),
            eq=tuple(
                sorted({
                    *u.Tests.runtime_evaluated_roots(),
                    "augmented_data_provider.Contract",
                })
            ),
        )
        with pytest.raises(ValueError, match="Unsupported class binding mutation"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    tmp_path / "src" / "captured_mutation" / "models.py": (
                        u.Tests.runtime_root_import()
                        + "class Contract(RuntimeRoot): pass\n"
                        "Contract |= RuntimeRoot\n"
                    ),
                },
                u.Tests.runtime_evaluated_roots(),
            )
        tm.fail("augmented_data_provider" in sys.modules)

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
    @staticmethod
    def test_runtime_guard_uses_import_identity_and_boolean_rebindings(
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
    @staticmethod
    def test_unknown_guard_cannot_borrow_standard_constant_semantics(
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
    @staticmethod
    def test_provider_guard_member_write_fails_before_stale_selection(
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
        tm.fail("guard_provider" in sys.modules)

    @pytest.mark.parametrize("replacement_model", [False, True])
    @staticmethod
    def test_provider_class_member_write_updates_exact_aliased_owner(
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
        expected = {
            *u.Tests.runtime_evaluated_roots(),
            "namespace_provider.Facade.Contract",
        }
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

    @staticmethod
    def test_provider_boolean_member_preserves_sdk_non_class_failure(
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

    @staticmethod
    def test_unpublished_project_is_not_imported_or_created(
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
            u.Infra.runtime_evaluated_base_classes(
                root, planned, u.Tests.runtime_evaluated_roots()
            ),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "unpublished_contract.models.Contract",
                    "unpublished_contract.models.Derived",
                )),
            ),
        )
        tm.fail(root.exists())
        tm.fail("unpublished_contract" in sys.modules)

    @staticmethod
    def test_import_aliases_relative_generic_bases_and_planned_disk_convergence(
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
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, {}, u.Tests.runtime_evaluated_roots()
            ),
            eq=actual,
        )

    @pytest.mark.parametrize("model_on_right", [False, True])
    @staticmethod
    def test_nested_member_lookup_obeys_c3_not_depth_first(
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

    @staticmethod
    def test_nested_bare_names_do_not_collide(tmp_path: Path) -> None:
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

    @staticmethod
    @pytest.mark.parametrize(
        "mapping",
        [
            'MappingProxyType({"m": ".models"})',
            'MappingProxyType({"m": (".models", "m")})',
            (
                "MappingProxyType({\n# Preserve colon: and comma, inside comments.\n"
                '"m": (".models", "m"),\n})'
            ),
            'MappingProxyType({"m": ".mo" + "dels"})',
            'MappingProxyType({("m"): (".models", # provider comment\n"m")})',
            'build_lazy_import_map({".models": ("m",)}, sort_keys=True)',
            'build_lazy_import_map({".models": ("m",)}, sort_keys=False)',
        ],
    )
    def test_generated_lazy_bindings_are_indexed_without_importing(
        tmp_path: Path,
        mapping: str,
    ) -> None:
        """Generated package exports bind the same source-defined model identity."""
        package = tmp_path / "src" / "generated_contract"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            c.Infra.AUTOGEN_HEADER
            + "\nfrom types import MappingProxyType\n"
            + "from typing import TYPE_CHECKING\n"
            + "from flext_core.lazy import (\n"
            + "    build_lazy_import_map, install_lazy_exports,\n)\n"
            + "if TYPE_CHECKING:\n    from .models import m\n"
            + "__getattr__, __dir__ = install_lazy_exports(__name__, globals(), "
            + f'{mapping}, public_exports=("m",))\n'
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
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            ),
            eq=tuple(
                sorted((
                    *u.Tests.runtime_evaluated_roots(),
                    "generated_contract.models.Contract",
                    "generated_contract.m",
                )),
            ),
        )
        tm.fail("generated_contract" in sys.modules)

    @pytest.mark.parametrize(
        ("target", "values"),
        [
            ("Alias, other", "None, None"),
            ("Alias, (other, *rest)", "None, (None, None)"),
        ],
    )
    @staticmethod
    def test_computed_unpacking_cannot_preserve_a_shadowed_class_base(
        tmp_path: Path,
        target: str,
        values: str,
    ) -> None:
        """Opaque iterable elements cannot inherit an earlier class identity."""
        source = u.Tests.runtime_root_import() + (
            "class Alias(RuntimeRoot): pass\n"
            f"def values(): return {values}\n"
            f"{target} = values()\n"
            "class Consumer(Alias): pass\n"
        )
        with pytest.raises(ValueError, match="Non-class binding used as a base"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "unpacked_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    @pytest.mark.parametrize("qualified", [False, True])
    @staticmethod
    def test_generated_lazy_member_keeps_the_export_binding(
        tmp_path: Path,
        *,
        qualified: bool,
    ) -> None:
        """Provider members resolve through the exported class, not its module."""
        package = tmp_path / "src" / "flext"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            c.Infra.AUTOGEN_HEADER
            + "\nfrom types import MappingProxyType\n"
            + "from typing import TYPE_CHECKING\n"
            + "from flext_core.lazy import install_lazy_exports\n"
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
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            ),
            eq=tuple(sorted({*u.Tests.runtime_evaluated_roots(), "flext.m.BaseModel"})),
        )
        tm.that("flext" in sys.modules, eq=was_imported)

    @staticmethod
    def test_missing_direct_package_base_is_not_invented(tmp_path: Path) -> None:
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
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            )

    @staticmethod
    @pytest.mark.parametrize("duplicate", [False, True])
    def test_planned_barrel_chain_preserves_the_leaf_class_identity(
        tmp_path: Path, *, duplicate: bool
    ) -> None:
        """Generation follows explicit exports without inventing a second base."""
        package = tmp_path / "src" / "barrel_contract"
        planned = {
            package / "__init__.py": "from .services import Base\n",
            package / "services" / "__init__.py": (
                "from typing import TYPE_CHECKING\n"
                "from types import MappingProxyType\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "if TYPE_CHECKING:\n    from ._parts import Base\n"
                "install_lazy_exports(__name__, globals(), "
                "MappingProxyType({'Base': '._parts'}), public_exports=('Base',))\n"
            ),
            package / "services" / "_parts" / "__init__.py": (
                "from .base import Base\n"
            ),
            package / "services" / "_parts" / "base.py": (
                u.Tests.runtime_root_import() + "class Base(RuntimeRoot): pass\n"
            ),
            package / "services" / "_parts" / "release.py": (
                "from barrel_contract.services import Base\nclass Release(Base): pass\n"
            ),
            package / "consumer.py": (
                "from barrel_contract import Base\n"
                "from barrel_contract.services._parts.base import Base as Leaf\n"
                + (
                    "class Consumer(Base, Leaf): pass\n"
                    if duplicate
                    else "class Consumer(Base): pass\n"
                )
            ),
        }
        if duplicate:
            with pytest.raises(ValueError, match="Duplicate class base:"):
                u.Infra.runtime_evaluated_base_classes(
                    tmp_path, planned, u.Tests.runtime_evaluated_roots()
                )
            return
        tm.that(
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            ),
            eq=tuple(
                sorted({
                    *u.Tests.runtime_evaluated_roots(),
                    "barrel_contract.Base",
                    "barrel_contract.services.Base",
                })
            ),
        )

    @staticmethod
    def test_planned_barrel_cannot_borrow_a_removed_live_export(tmp_path: Path) -> None:
        """A stale export plan fails even when the live barrel is valid."""
        package = tmp_path / "src" / "removed_export"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            "from .base import Base\n", encoding=c.DEFAULT_ENCODING
        )
        (package / "base.py").write_text(
            "class Base: pass\n", encoding=c.DEFAULT_ENCODING
        )
        with pytest.raises(
            ValueError, match=r"Unresolved planned base: removed_export\.Base$"
        ):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    package / "__init__.py": "",
                    package / "consumer.py": (
                        "from removed_export import Base\nclass Consumer(Base): pass\n"
                    ),
                },
                (),
            )

    @staticmethod
    def test_native_stdlib_aliases_preserve_the_same_qualified_bases(
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
        tm.ok(set(u.Tests.runtime_evaluated_roots()).issubset(aliased))

    @staticmethod
    def test_value_shadowing_is_a_visible_invalid_base(tmp_path: Path) -> None:
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


class TestsFlextInfraLazyAliasOrdering:
    """Validate the native lazy-builder literal ordering contract."""

    @staticmethod
    @pytest.mark.parametrize(
        "ordering",
        [
            c.ParserBooleanToken.ZERO,
            c.ParserBooleanToken.ONE,
            "None",
            "c.ParserBooleanToken.TRUE",
            "True and False",
        ],
    )
    def test_builder_rejects_non_boolean_literals(
        tmp_path: Path, ordering: str
    ) -> None:
        """Truthy values and boolean expressions retain the exact failure."""
        package = tmp_path / "src" / "ordering_contract"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            "from flext_core.lazy import (\n"
            "    build_lazy_import_map, install_lazy_exports,\n)\n"
            "install_lazy_exports(__name__, globals(), "
            'build_lazy_import_map({".models": ("m",)}, '
            f"sort_keys={ordering}))\n",
            encoding="utf-8",
        )
        with pytest.raises(
            ValueError, match=r"^Lazy builder ordering requires a literal boolean$"
        ):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {
                    package / "models.py": u.Tests.runtime_root_import()
                    + "class Contract(RuntimeRoot): pass\nm = Contract\n",
                },
                u.Tests.runtime_evaluated_roots(),
            )
