"""Public Rope constant declaration repairs preserve consumer behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, tm, u


class TestsFlextInfraConstantDeclarations:
    """Typing identities select class constants without capturing homonyms."""

    @staticmethod
    @pytest.mark.parametrize(
        ("imports", "qualifier"),
        [
            ("from typing import Final", "Final"),
            ("from typing import Final as Immutable", "Immutable"),
            ("import typing as types", "types.Final"),
        ],
    )
    def test_class_constants_do_not_become_pydantic_fields(
        tmp_path: Path, imports: str, qualifier: str
    ) -> None:
        """The migrated namespace publishes scalars and an immutable collection."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / u.Infra.facade_families()["c"].directory
        family.mkdir()
        path = family / "values.py"
        source = (
            f"{imports}\nfrom pydantic import BaseModel\n"
            "class Values(BaseModel):\n"
            f"    TOKEN: {qualifier}[str] = 'consumer-token'\n"
            f"    FIELDS: {qualifier}[frozenset[str]] = "
            "frozenset({'base_url', 'username'})\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources={path: source},
                )
            )
            tm.that(len(edits), eq=1)
            proposed = {path: edits[0].updated_source}
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources=proposed,
                )
            )
            tm.that(repeated, empty=True)
        path.write_text(proposed[path], encoding=c.DEFAULT_ENCODING)
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-W",
                    "error",
                    "-c",
                    (
                        f"from {package.name}._constants.values import Values; "
                        "assert Values.TOKEN == 'consumer-token'; "
                        "assert Values.FIELDS == frozenset({'base_url', 'username'}); "
                        "assert Values.model_fields == {}; "
                        "assert Values().model_dump() == {}"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize("relative", ["_constants/values.py", "consumer.py"])
    def test_nonconstant_final_bindings_keep_their_contract(
        tmp_path: Path, relative: str
    ) -> None:
        """Module values, locals and non-typing homonyms do not acquire ClassVar."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        source = (
            "from typing import Final as Immutable\n"
            "VALUE: Immutable[str] = 'module'\n"
            "class Final:\n"
            "    @classmethod\n"
            "    def __class_getitem__(cls, value):\n"
            "        return str\n"
            "class Values:\n"
            "    TOKEN: Final[str] = 'homonym'\n"
            "    @staticmethod\n"
            "    def consume():\n"
            "        local: Immutable[str] = 'local'\n"
            "        return local\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources={path: source},
                )
            )
        tm.that(edits, empty=True)

    @staticmethod
    def test_shadowed_classvar_fails_before_a_source_edit(tmp_path: Path) -> None:
        """An occupied binding cannot silently change an annotation's meaning."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / u.Infra.facade_families()["c"].directory
        family.mkdir()
        path = family / "values.py"
        source = (
            "from typing import Final\n"
            "ClassVar = str\n"
            "class Values:\n"
            "    TOKEN: Final[str] = 'consumer-token'\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match="ClassVar binding is shadowed"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=workspace,
                sources={path: source},
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
