"""The class-nesting cutover emits source the canonical gates accept.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

import flext_infra
from tests import c, tm, u


class TestsFlextInfraNestingCutoverOutput:
    """A cutover whose output fails ruff is not a repair.

    Every module the mover touched came back with findings a human then fixed
    by hand, which is the sweep this engine exists to eliminate. The defects
    pinned here were reproduced verbatim in a committed module on a member
    branch: a blank line carrying the block indent (W293), an export
    declaration rebuilt without its separation (E305), and a docstring left at
    the depth the class no longer has (D207).
    """

    @staticmethod
    def _planned_source(tmp_path: Path) -> str:
        """Plan one class-nesting cutover through the public cutover owner.

        Returns:
            The resulting ``str``.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        alias = min(u.Infra.facade_families())
        module_name = u.Tests.family_public_module(alias)
        owner_name = (
            f"{u.derive_class_stem(repository_root.name)}"
            f"{u.Infra.facade_families()[alias].suffix}"
        )
        module_path = package_root / f"{module_name}.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name=owner_name,
            alias=alias,
            extra_class_names=(f"{owner_name}Member",),
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module_path: module_path.read_text(encoding="utf-8")},
            )

        return tm.ok(planned)[0].updated_source

    def test_emitted_source_carries_no_blank_line_with_indentation(
        self,
        tmp_path: Path,
    ) -> None:
        """A separator line inside the owner block is empty, never indented."""
        emitted = self._planned_source(tmp_path)

        indented_blanks = [
            line for line in emitted.splitlines() if not line.strip() and line
        ]

        tm.that(indented_blanks, empty=True)

    def test_emitted_source_keeps_docstrings_at_their_new_depth(
        self,
        tmp_path: Path,
    ) -> None:
        """A moved class carries its docstring to the depth it now sits at."""
        emitted = self._planned_source(tmp_path)
        lines = emitted.splitlines()
        nested = next(
            index
            for index, line in enumerate(lines)
            if line.lstrip().startswith("class ") and line.startswith("    ")
        )
        depth = len(lines[nested]) - len(lines[nested].lstrip())

        for line in lines[nested + 1 :]:
            if not line.strip():
                continue
            if line.startswith(" " * (depth + 1)):
                continue
            tm.ok(line.startswith(" " * depth) or not line.startswith(" "))
            break

    def test_emitted_source_passes_the_whitespace_and_docstring_gates(
        self,
        tmp_path: Path,
    ) -> None:
        """Ruff finds none of the three defects the mover used to write.

        Formatting proper belongs to the publication stage, which runs the
        canonical formatter; what the planner emits must already be free of
        the defects no formatter should have to repair.
        """
        module = tmp_path / "emitted" / "nested_module.py"
        tm.ok(u.Cli.ensure_dir(module.parent))
        tm.ok(u.Cli.atomic_write_text_file(module, self._planned_source(tmp_path)))

        linted = u.Cli.run([
            "ruff",
            "check",
            "--isolated",
            "--select",
            "W291,W293,E301,E303,E305,D207",
            str(module),
        ])

        tm.ok(linted)

    @staticmethod
    @pytest.mark.parametrize(
        ("existing_owner", "documented"), [(False, False), (True, False), (True, True)]
    )
    def test_member_trivia_moves_with_code_not_classvar_payload(
        tmp_path: Path, *, existing_owner: bool, documented: bool
    ) -> None:
        """CST-owned prefixes stay attached without rewriting source payloads."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        policy = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        module = package / policy.directory / "trivia_helpers.py"
        tm.ok(u.Cli.ensure_dir(module.parent))
        tm.ok(u.Cli.atomic_write_text_file(module.parent / "__init__.py", ""))
        owner = (
            f"{u.derive_class_stem(root.name)}{policy.suffix}"
            f"{u.derive_class_stem(module.stem)}"
        )
        header = '# Copyright: retained at module scope.\n"""Owned trivia."""\n'
        source = (
            header
            + "from __future__ import annotations\n"
            + "# Import-only contract.\n"
            + "from functools import cache, lru_cache\n"
            + "from typing import Annotated\n\n"
            + "# Owner-only permission bits.\n"
            + '_MODE: Annotated[int, "permission: # unchanged"] = 0o640\n\n'
            + "# Original helper contract.\n"
            + "@cache\n"
            + "# Inner decorator contract.\n"
            + "@lru_cache(maxsize=1)\n"
            + "def payload() -> bytes:\n"
            + '    return b"\\x00:#\\xff"\n\n'
            + (
                f"class {owner}:\n"
                + ('    """Existing owner documentation."""\n' if documented else "")
                + "    # Existing member contract.\n"
                "    @staticmethod\n"
                "    def retained() -> int:\n"
                "        return 1\n\n"
                if existing_owner
                else ""
            )
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        with flext_infra.infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources={module: source},
                )
            )
        emitted = next(
            edit.updated_source for edit in planned if edit.file_path == module
        )
        tm.that(module.read_text(encoding="utf-8"), eq=source)
        tm.that(emitted, starts=header)
        tm.that(emitted, has="    # Owner-only permission bits.\n    _MODE:")
        tm.that(emitted, has='Annotated[int, "permission: # unchanged"]')
        tm.that(emitted, has='return b"\\x00:#\\xff"')
        tm.that(
            emitted,
            has=(
                "    # Original helper contract.\n    @staticmethod\n    @cache\n"
                "    # Inner decorator contract.\n    @lru_cache(maxsize=1)\n"
                "    def payload()"
            ),
        )
        if existing_owner:
            tm.that(
                emitted,
                has=(
                    "    # Existing member contract.\n    @staticmethod\n"
                    "    def retained()"
                ),
            )
        compile(emitted, str(module), "exec")
        tm.that(emitted, has="# Import-only contract.\nfrom functools")

    @staticmethod
    @pytest.mark.parametrize(
        ("declaration", "owner_body"),
        [
            ("type Self[Self] = tuple[Self]\n", "    pass\n"),
            (
                "type Item = int\ntype conflict[*Item] = tuple[*Item]\n",
                "    class Conflict:\n        pass\n",
            ),
        ],
    )
    def test_ambiguous_generic_declaration_scope_fails_before_source_effects(
        tmp_path: Path, declaration: str, owner_body: str
    ) -> None:
        """Never guess a replacement namespace or shadow an alias parameter."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "generic_scopes.py"
        source = declaration + "\nclass Holder:\n" + owner_body
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        with flext_infra.infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )
        tm.fail(planned, has="cannot preserve native type parameter scope")
        tm.that(module.read_text(encoding="utf-8"), eq=source)
