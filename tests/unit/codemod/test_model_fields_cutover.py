"""Execute migrated public model-validation boundaries with real Pydantic types.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


class TestsFlextInfraModelFieldsCutover:
    """Migration preserves rejection semantics and reaches a stable source."""

    @staticmethod
    def _seed(tmp_path: Path) -> tuple[Path, Path]:
        """Seed one workspace and the module path the cutover plans over.

        Returns:
            The repository root and the validation module path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        return root, package / "validation.py"

    @staticmethod
    def _plan(
        root: Path,
        path: Path,
        source: str,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan the model-fields cutover over one source.

        Returns:
            The planning verdict, never published.

        """
        with infra.rope_workspace(root) as rope:
            return u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                rope_workspace=rope,
                sources={path: source},
            )

    @staticmethod
    @pytest.mark.parametrize(
        "access",
        [
            'getattr(candidate, "model_fields", None)',
            'getattr(candidate, "model_fields", {})',
            'getattr(candidate, "model_fields")',
            "candidate.model_fields",
        ],
    )
    def test_public_boundary_rejects_non_models_without_attribute_access(
        tmp_path: Path,
        access: str,
    ) -> None:
        """Test public boundary rejects non models without attribute access."""
        root, path = TestsFlextInfraModelFieldsCutover._seed(tmp_path)
        source = (
            "from flext_core import m\n"
            "def inspect_definition(candidate: object, *, label: str) -> None:\n"
            f"    fields = {access}\n"
            "    if not isinstance(fields, dict) or not fields:\n"
            "        raise ValueError(label)\n"
            "class Populated(m.BaseModel):\n"
            "    value: str\n"
            "class Empty(m.BaseModel):\n"
            "    pass\n"
            "class Pretender:\n"
            "    model_fields = {'value': None}\n"
            "class Poison:\n"
            "    def __getattr__(self, name: str) -> None:\n"
            "        raise RuntimeError('unexpected attribute access')\n"
            "inspect_definition(Populated, label='valid')\n"
            "for invalid in (None, object(), 1, str, Empty, Pretender, Poison(),"
            " Populated(value='x')):\n"
            "    try:\n"
            "        inspect_definition(invalid, label='original boundary error')\n"
            "    except ValueError as error:\n"
            "        assert str(error) == 'original boundary error'\n"
            "    else:\n"
            "        raise AssertionError('invalid model was accepted')\n"
        )
        edits = tm.ok(TestsFlextInfraModelFieldsCutover._plan(root, path, source))
        tm.that(len(edits), eq=1)
        tm.that(
            tm.ok(
                TestsFlextInfraModelFieldsCutover._plan(
                    root,
                    path,
                    edits[0].updated_source,
                ),
            ),
            empty=True,
        )
        path.write_text(edits[0].updated_source, encoding="utf-8")
        outcome = tm.ok(u.Cli.run_raw((sys.executable, "-I", str(path))))
        tm.that(outcome.exit_code, eq=0)
        tm.that(outcome.stderr, eq="")

    @staticmethod
    def test_ambiguous_rejection_keeps_the_source_untouched(
        tmp_path: Path,
    ) -> None:
        """Test ambiguous rejection keeps the source untouched."""
        root, path = TestsFlextInfraModelFieldsCutover._seed(tmp_path)
        source = (
            "def validate(candidate: object) -> None:\n"
            "    fields = candidate.model_fields\n"
            "    print(fields)\n"
        )
        path.write_text(source, encoding="utf-8")
        tm.fail(
            TestsFlextInfraModelFieldsCutover._plan(root, path, source),
            has="lacks a rejecting guard",
        )
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_conflicting_guard_binding_is_not_overwritten(tmp_path: Path) -> None:
        """Test conflicting guard binding is not overwritten."""
        root, path = TestsFlextInfraModelFieldsCutover._seed(tmp_path)
        source = (
            "u = 1\n"
            "def validate(candidate: object) -> None:\n"
            "    fields = candidate.model_fields\n"
            "    if not isinstance(fields, dict) or not fields:\n"
            "        raise ValueError('invalid')\n"
        )
        tm.fail(
            TestsFlextInfraModelFieldsCutover._plan(root, path, source),
            has="conflicts with a local binding",
        )

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "from another import type\n",
            "def isinstance(*args):\n    return True\n",
            "class object:\n    pass\n",
            "getattr = lambda *args: {}\n",
            "try:\n    pass\nexcept Exception as dict:\n    pass\n",
            "match None:\n    case type:\n        pass\n",
        ],
    )
    def test_shadowed_contract_is_rejected(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Test shadowed contract is rejected."""
        root, path = TestsFlextInfraModelFieldsCutover._seed(tmp_path)
        source = declaration + (
            "def validate(candidate: object) -> None:\n"
            "    fields = candidate.model_fields\n"
            "    if not isinstance(fields, dict) or not fields:\n"
            "        raise ValueError('invalid')\n"
        )
        tm.fail(TestsFlextInfraModelFieldsCutover._plan(root, path, source))

    @staticmethod
    @pytest.mark.parametrize(
        "body",
        [
            (
                "    candidate = object()\n"
                "    fields = candidate.model_fields\n"
                "    if not isinstance(fields, dict) or not fields:\n"
                "        raise ValueError('invalid')\n"
            ),
            (
                "    fields = candidate.model_fields\n"
                "    if not isinstance(fields, dict) or not fields:"
                " raise ValueError('invalid')\n"
            ),
        ],
    )
    def test_unsafe_statement_layout_or_receiver_rebinding_fails(
        tmp_path: Path,
        body: str,
    ) -> None:
        """Test unsafe statement layout or receiver rebinding fails."""
        root, path = TestsFlextInfraModelFieldsCutover._seed(tmp_path)
        tm.fail(
            TestsFlextInfraModelFieldsCutover._plan(
                root,
                path,
                "def validate(candidate: object) -> None:\n" + body,
            ),
        )
