"""Public Rope constant declaration repairs preserve consumer behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests import c, m, p, t, tm, u


class TestsFlextInfraConstantDeclarations:
    """Typing identities select class constants without capturing homonyms."""

    @staticmethod
    @pytest.mark.parametrize(
        "provider",
        ["flext_tap_oracle_wms", "flext_target_oracle", "flext_dbt_oracle"],
    )
    @pytest.mark.parametrize(
        "binding",
        [
            ("from typing import Final", "Final"),
            ("from typing import Final as Immutable", "Immutable"),
            ("import typing as types", "types.Final"),
        ],
    )
    def test_class_constants_do_not_become_pydantic_fields(
        constants_workspace: tuple[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
        infra_subprocess: p.Cli.CommandRunner,
        binding: tuple[str, str],
        provider: str,
    ) -> None:
        """The migrated namespace publishes scalars and an immutable collection."""
        imports, qualifier = binding
        root, package = constants_workspace
        family = package / u.Infra.facade_families()["c"].directory
        family.mkdir()
        path = family / "values.py"
        source = (
            f"{imports}\nfrom pydantic import BaseModel\n"
            f"from {provider} import c as provider\n"
            "class Values(BaseModel):\n"
            f"    TOKEN: {qualifier}[str] = provider.DEFAULT_ENCODING\n"
            f"    FIELDS: {qualifier}[frozenset[str]] = "
            "frozenset({provider.DEFAULT_ENCODING})\n"
        )
        constant_candidate({path: source}, (path,))
        tm.ok(
            infra_subprocess.capture(
                (
                    sys.executable,
                    "-W",
                    "error",
                    "-c",
                    (
                        f"from {package.name}._constants.values import Values; "
                        f"from {provider} import c as provider; "
                        "assert Values.TOKEN == provider.DEFAULT_ENCODING; "
                        "assert Values.FIELDS == "
                        "frozenset({provider.DEFAULT_ENCODING}); "
                        "assert Values.model_fields == {}; "
                        "assert Values().model_dump() == {}"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )

    @staticmethod
    @pytest.mark.parametrize("relative", ["_constants/values.py", "consumer.py"])
    def test_nonconstant_final_bindings_keep_their_contract(
        constants_workspace: tuple[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
        relative: str,
    ) -> None:
        """Module values, locals and non-typing homonyms do not acquire ClassVar."""
        _root, package = constants_workspace
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
        constant_candidate({path: source}, ())

    @staticmethod
    def test_shadowed_classvar_fails_before_a_source_edit(
        constants_workspace: tuple[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
    ) -> None:
        """An occupied binding cannot silently change an annotation's meaning."""
        _root, package = constants_workspace
        family = package / u.Infra.facade_families()["c"].directory
        family.mkdir()
        path = family / "values.py"
        source = (
            "from typing import Final\n"
            "ClassVar = str\n"
            "class Values:\n"
            "    TOKEN: Final[str] = 'consumer-token'\n"
        )
        with pytest.raises(ValueError, match="destination ClassVar is shadowed"):
            constant_candidate({path: source}, ())
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
