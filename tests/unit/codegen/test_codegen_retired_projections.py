"""Retired Python projections follow native repository source boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, t, tm, u


class TestsFlextInfraCodegenRetiredProjections:
    """Exercise configured retirement through real plans and publication."""

    @staticmethod
    @c.Tests.MARK.parametrize("relative_root", [False, True])
    def test_python_retirement_preserves_authored_and_foreign_sources(
        infra_git_repo: Path,
        monkeypatch: t.Tests.MonkeyPatch,
        *,
        relative_root: bool,
    ) -> None:
        """Retire generated copies in arbitrary tiers once, within their owner."""
        root = infra_git_repo
        u.Tests.standalone_workspace(root, config.Infra.name)
        monkeypatch.chdir(root.parent)
        selected_root = Path(root.name) if relative_root else root
        pattern = next(
            entry
            for entry in config.Infra.codegen.retired_projections
            if isinstance(entry, str)
            and entry.startswith("**/")
            and entry.endswith(".py")
        )
        relative = Path(pattern.removeprefix("**/"))
        generated = tuple(
            root / tier / relative for tier in ("src/owner", "custom/tier")
        )
        authored = root / "examples/owner" / relative
        foreign = root / "nested-repository" / relative
        for path in (*generated, authored, foreign):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"# {c.Infra.TEMPLATE_GENERATED_MARKERS[0]}\n"
                if path != authored
                else '"""An authored capability contract."""\n',
                encoding=c.DEFAULT_ENCODING,
            )
        (root / "nested-repository" / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'foreign'\nversion = '1.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )

        plans = tm.ok(
            FlextInfraCodegenConform.Generate.retired_projection_plans(
                selected_root, c.Infra.MakeProfile.STANDALONE
            )
        )
        tm.that({plan.path for plan in plans}, eq=set(generated))
        tm.ok(u.Infra.publish_codegen_plans(root, plans))
        for path in generated:
            tm.that(path.exists(), eq=False)
        tm.that(authored.is_file(), eq=True)
        tm.that(foreign.is_file(), eq=True)
        tm.that(
            tm.ok(
                FlextInfraCodegenConform.Generate.retired_projection_plans(
                    selected_root, c.Infra.MakeProfile.STANDALONE
                )
            ),
            eq=(),
        )
