"""Real Pydantic consumer evidence for native Rope contract migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeContracts:
    """Prove runtime values, failure contracts and the shared fixed point."""

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "values: list[str] = Field(default_factory=list)",
            "values: dict[str, list[int]] = Field(default_factory=dict)",
            "values: Meta[list[str], Field(default_factory=list)]",
            "values: Meta[int, Field(default=3)]",
        ],
    )
    def test_real_defaults_preserve_runtime_and_converge(
        tmp_path: Path, declaration: str
    ) -> None:
        """Native Rope retains independent instances and public JSON roundtrips."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from typing import Annotated as Meta\n"
            "from pydantic import BaseModel, Field\n"
            "class Payload(BaseModel):\n"
            f"    {declaration}\n"
            "first, second = Payload(), Payload()\n"
            "if isinstance(first.values, list):\n"
            "    first.values.append('consumer')\n"
            "elif isinstance(first.values, dict):\n"
            "    first.values['consumer'] = [1]\n"
            "restored = Payload.model_validate_json(first.model_dump_json())\n"
            "evidence = (first.model_dump_json(), second.model_dump_json(), "
            "restored.model_dump_json())\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: source},
                )
            )
            tm.that(len(edits), eq=1)
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
            updated = edits[0].updated_source
            path.write_text(updated, encoding=c.DEFAULT_ENCODING)
            tm.that(runpy.run_path(str(path))["evidence"], eq=before)
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: updated},
                )
            )
            tm.that(remaining, empty=True)

    @staticmethod
    def test_unrelated_field_factory_is_not_a_pydantic_field(tmp_path: Path) -> None:
        """Same-spelled functions do not establish a Pydantic identity."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "def Field(*, default_factory):\n"
            "    return default_factory()\n"
            "values: list[str] = Field(default_factory=list)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: source},
                )
            )
        tm.that(edits, empty=True)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_competing_utility_binding_refuses_publication(tmp_path: Path) -> None:
        """A new public utility import must not capture an existing consumer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from pydantic import Field\n"
            "u = 'existing consumer binding'\n"
            "values: list[str] = Field(default_factory=list)\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as rope:
            with pytest.raises(ValueError, match="destination u.empty is shadowed"):
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=rope,
                    sources={path: source},
                )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
