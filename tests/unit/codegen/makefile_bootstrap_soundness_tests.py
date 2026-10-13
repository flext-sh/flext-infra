"""Soundness contracts for the rendered Makefile bootstrap recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests import c, tm, u

_TEMPLATES = Path(__file__).parents[3] / "src" / "flext_infra" / "templates"
_ASSIGNMENT = re.compile(r"(?<![-=!<>])\b([a-z_][a-z0-9_]*)=(?!=)")
_USE = re.compile(r"\$\$([a-z_][a-z0-9_]*)")
_TRAP_BODY = re.compile(r"trap '.*?' EXIT", re.DOTALL)
_FUNCTION_BODY = re.compile(r"\b[a-z_][a-z0-9_]*\(\) \{.*?\n\t?\};", re.DOTALL)


class TestsFlextInfraMakefileBootstrapSoundness:
    """Every emitted bootstrap variable is assigned before it is read."""

    def test_bootstrap_recipe_initializes_every_variable_it_reads(self) -> None:
        """The tool bootstrap recipe never reads an unassigned shell variable.

        Raises:
            AssertionError: If bootstrap recipe reads shell variables before assigning
                them.
        """
        recipe = (
            _TEMPLATES / "project" / "base" / ("tool_bootstrap_recipe.j2")
        ).read_text(encoding="utf-8")
        # Traps and function bodies read only when invoked, not when declared.
        text = _FUNCTION_BODY.sub(
            "function ... { };", _TRAP_BODY.sub("trap '...' EXIT", recipe)
        )
        bound: set[str] = set()
        violations: list[str] = []
        for line in text.splitlines():
            bound.update(assigned.group(1) for assigned in _ASSIGNMENT.finditer(line))
            violations.extend(
                f"{name} (line: {line.strip()[:80]})"
                for name in _USE.findall(line)
                if name not in bound
            )
        tm.that(violations, eq=[], msg=f"unassigned bootstrap reads: {violations}")
        tm.that(bool(recipe), eq=True)

    @pytest.mark.parametrize("verb", ["setup", "upg"])
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    @pytest.mark.parametrize("broken", [False, True])
    def test_borrowed_environment_blocks_bootstrap_before_effects(
        self,
        tmp_path: Path,
        verb: str,
        profile: c.Infra.MakeProfile,
        *,
        broken: bool,
    ) -> None:
        """Public provisioning rejects borrowed runtimes before bootstrap or hooks."""
        project, _ = u.Tests.render_make_environment(tmp_path, profile)
        environment = u.Infra.runtime_environment_dir(project)
        foreign = tmp_path / "foreign"
        if not broken:
            foreign.mkdir()
            (foreign / "owner.txt").write_bytes(b"foreign-owned bytes")
        environment.symlink_to(foreign, target_is_directory=True)
        (project / "custom.mk").write_text(
            "pre-setup pre-upg post-setup post-upg:\n\t@touch hook-effect\n",
            encoding=c.DEFAULT_ENCODING,
        )
        paths = set(project.rglob("*"))
        contents = {path: path.read_bytes() for path in paths if path.is_file()}
        process = tm.ok(u.Tests.run_isolated_make([verb], cwd=project))
        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has=f"physical, not a symlink: {environment}")
        tm.that(process.stdout, lacks="github-auth")
        tm.that(set(project.rglob("*")), eq=paths)
        for path, content in contents.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(environment.is_symlink(), eq=True)
        tm.that(foreign.exists(), eq=not broken)
        if not broken:
            tm.that(tuple(foreign.iterdir()), eq=(foreign / "owner.txt",))
            tm.that((foreign / "owner.txt").read_bytes(), eq=b"foreign-owned bytes")
