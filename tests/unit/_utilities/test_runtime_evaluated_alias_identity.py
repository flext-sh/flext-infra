"""Alias identity and re-export cycle behavior for runtime-evaluated bases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from pathlib import Path

import pytest

from tests import tm, u


class TestsFlextInfraRuntimeEvaluatedAliasIdentity:
    """Alias, mutation, and re-export cycle misuse fails visibly."""

    @staticmethod
    def test_duplicate_class_identity_through_alias_fails(
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

    @staticmethod
    def test_conditional_required_alias_is_not_chosen_from_one_branch(
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

    @staticmethod
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
        tmp_path: Path,
        mutation: str,
    ) -> None:
        source = u.Tests.runtime_root_import() + (
            "class Contract(RuntimeRoot): pass\nclass Plain: pass\n"
            "class Namespace:\n    Contract = Contract\n"
            f"{mutation}\nclass Consumer(Contract): pass\n"
        )
        expected = (
            u.Infra.rope_attribute_not_found_error_types()
            if mutation == "del Contract"
            else (ValueError,)
        )
        message = (
            "Attribute Contract not found"
            if mutation == "del Contract"
            else "Unsupported class binding mutation"
        )
        with pytest.raises(expected, match=message):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "mutation_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )

    @staticmethod
    def test_provider_reexport_enters_a_planned_class_once(
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
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            ),
            eq=tuple(
                sorted((*u.Tests.runtime_evaluated_roots(), "planned_bridge.Contract"))
            ),
        )
        tm.fail(package.exists())
        tm.fail("planned_bridge" in sys.modules)

    @staticmethod
    def test_true_planned_reexport_cycle_fails_at_its_binding(
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
            u.Infra.runtime_evaluated_base_classes(
                tmp_path, planned, u.Tests.runtime_evaluated_roots()
            )

    @staticmethod
    def test_missing_inherited_member_cannot_be_deselected(
        tmp_path: Path,
    ) -> None:
        source = "class Namespace: pass\nclass Invalid(Namespace.Missing): pass\n"
        with pytest.raises(ValueError, match="Missing inherited class member"):
            u.Infra.runtime_evaluated_base_classes(
                tmp_path,
                {tmp_path / "src" / "member_contract" / "models.py": source},
                u.Tests.runtime_evaluated_roots(),
            )
