"""The declared Ruff repair channel and rule policy have one generated owner.

The confirmed baseline enables unsafe fixes in ``make fix``. Rules whose fixes
destroy information remain governed by the tooling owner's ``unfixable`` policy,
which the generator must preserve without inventing a different consumer policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.check import FlextInfraGateRegistry
from flext_infra.gates import FlextInfraRuffLintGate
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodegenMakeLintFixSafety:
    """The mandatory unsafe lint-repair contract and its projection."""

    @staticmethod
    def test_lint_fix_requires_the_confirmed_unsafe_channel() -> None:
        """The declared baseline cannot silently disable its repair channel."""
        ruff = config.Infra.codegen.make.ruff
        tm.ok(c.Infra.RUFF_UNSAFE_FIXES_FLAG in ruff.lint_fix)
        payload = ruff.model_dump()
        payload["lint_fix"] = tuple(
            flag for flag in ruff.lint_fix if flag != c.Infra.RUFF_UNSAFE_FIXES_FLAG
        )

        with pytest.raises(m.ValidationError) as failure:
            _ = m.Infra.MakeRuffSpec.model_validate(payload)

        tm.that(str(failure.value), has=c.Infra.RUFF_UNSAFE_FIXES_FLAG)
        tm.that(str(failure.value), has="operator law 2026-10-05")

    @staticmethod
    def test_lint_fix_arguments_survive_typed_round_trip() -> None:
        """Typed JSON validation preserves the current SSOT repair arguments."""
        ruff = config.Infra.codegen.make.ruff
        restored = m.Infra.MakeRuffSpec.model_validate_json(ruff.model_dump_json())
        tm.that(restored.lint_fix, eq=ruff.lint_fix)

    @staticmethod
    @pytest.mark.slow
    def test_scaffold_pyproject_renders_the_fix_safety_policy(
        tmp_path: Path,
    ) -> None:
        """The rendered Ruff lint table carries the SSOT fix-safety lists."""
        policy = config.Infra.tooling.tools.ruff.lint
        make = config.Infra.codegen.make
        delegated = FlextInfraGateRegistry.default().delegated_lint_rules(
            policy.rule_owners,
            check_gates=make.check_gates_default,
            repair_gates=(*make.check_gates_fixable, *make.fmt_gates),
        )
        pyproject = u.Tests.scaffold_text(
            tmp_path / "fixture-project",
            c.PYPROJECT_FILENAME,
        )

        tm.that(
            list(
                u.Tests.toml_strings_at(pyproject, "tool", "ruff", "lint", "unfixable"),
            ),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling,
                "ruff.lint",
                "unfixable",
                t.TypeForm(Sequence[str]),
            ),
        )
        tm.that(
            list(
                u.Tests.toml_strings_at(
                    pyproject,
                    "tool",
                    "ruff",
                    "lint",
                    "extend-safe-fixes",
                ),
            ),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling,
                "ruff.lint",
                "extend-safe-fixes",
                t.TypeForm(Sequence[str]),
            ),
        )
        tm.that(
            list(u.Tests.toml_strings_at(pyproject, "tool", "ruff", "lint", "ignore")),
            eq=sorted({
                *delegated,
                *policy.ruling_disabled_rules,
                *u.Infra.native_tool_setting(
                    config.Infra.tooling,
                    "ruff.lint",
                    "ignore",
                    t.TypeForm(Sequence[str]),
                ),
            }),
        )
        tm.that(
            list(
                u.Tests.toml_strings_at(
                    pyproject,
                    "tool",
                    "ruff",
                    "lint",
                    "pylint",
                    "allow-dunder-method-names",
                ),
            ),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling,
                "ruff.lint.pylint",
                "allow-dunder-method-names",
                t.TypeForm(Sequence[str]),
            ),
        )

    @staticmethod
    @pytest.mark.slow
    def test_native_descriptor_policy_keeps_misspelled_dunders_visible(
        tmp_path: Path,
    ) -> None:
        """Generated policy permits native properties, not a misspelled dunder."""
        root = tmp_path / "fixture-project"
        pyproject = u.Tests.scaffold_text(root, c.PYPROJECT_FILENAME)
        config_file = root / c.PYPROJECT_FILENAME
        config_file.write_text(pyproject, encoding="utf-8")
        module = root / c.Infra.DEFAULT_SRC_DIR / "native_descriptors.py"
        module.parent.mkdir()
        properties = "".join(
            "    @property\n"
            f"    def {name}(self) -> "
            f"{'tuple[type, ...]' if name == '__bases__' else 'type | None'}: ...\n"
            for name in (
                u.Infra.native_tool_setting(
                    config.Infra.tooling,
                    "ruff.lint.pylint",
                    "allow-dunder-method-names",
                    list[str],
                )
            )
        )
        module.write_text(
            "from typing import Protocol\n\n"
            "class NativeType(Protocol):\n"
            f"{properties}"
            "    @property\n"
            "    def __basse__(self) -> type | None: ...\n",
            encoding="utf-8",
        )
        checked = FlextInfraRuffLintGate(root).check(
            root,
            m.Infra.GateContext(
                repository_root=root,
                reports_dir=root,
                ruff_args=(
                    "--select",
                    "bad-dunder-method-name",
                    "--config",
                    str(config_file),
                ),
            ),
        )

        tm.fail(checked.result.passed)
        tm.that(len(checked.issues), eq=1)
        tm.that(checked.issues[0].code, eq="bad-dunder-method-name")
        tm.that(checked.issues[0].message, has="__basse__")
