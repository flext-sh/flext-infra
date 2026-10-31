"""Behavior tests for native Rope signature and nested expression refactoring.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeSignaturePatch:
    """Validate signature token walking against annotated call parameters."""

    @staticmethod
    def test_objects_walk_annotated_call_parameters(tmp_path: Path) -> None:
        """Two multiline annotated parameters no longer break the AST walk.

        rope 1.14 skipped annotation tokens and failed loudly once a second
        annotation carried a call (bead flext-4frn5).
        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "command.py"
        module_path.write_text(
            (
                "from typing import Annotated\n"
                "\n"
                "\n"
                "def command(\n"
                "    *,\n"
                "    log_level: Annotated[\n"
                '        str, create_option("cli_log_level")\n'
                '    ] = "INFO",\n'
                "    output_format: Annotated[\n"
                '        str, create_option("output_format")\n'
                '    ] = "TABLE",\n'
                ") -> None:\n"
                '    print(f"Command: {log_level}")\n'
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            objects = rope.objects(module_path)

        tm.that([item.name for item in objects], has=c.HandlerMode.COMMAND)

    @staticmethod
    def test_objects_walk_full_signature_shapes(tmp_path: Path) -> None:
        """Positional-only, vararg, keyword-only and kwargs walk in order."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "shapes.py"
        module_path.write_text(
            (
                "def shapes(\n"
                "    first,\n"
                "    second: int,\n"
                "    /,\n"
                "    third: int = 1,\n"
                "    *rest: int,\n"
                "    flag: bool = True,\n"
                "    tagged: int,\n"
                "    **extra: int,\n"
                ") -> None:\n"
                "    print(first, second, third, rest, flag, tagged, extra)\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            objects = rope.objects(module_path)

        tm.that([item.name for item in objects], has="shapes")

    @staticmethod
    def test_scope_at_walks_pep701_nested_quotes(tmp_path: Path) -> None:
        """Rope resolves scope when an f-string expression reuses quote style."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "quoted.py"
        source = (
            "def render(values: dict[str, str]) -> str:\n"
            '    return f"value={values["name"]}"\n'
        )
        module_path.write_text(source, encoding="utf-8")

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            pymodule = u.Infra.build_string_module(
                rope.rope_project,
                source,
                resource=rope.resource(module_path),
            )
            scope = u.Infra.scope_at(pymodule, source.index("values["))

        # A Rope scope is not a payload value; its observable identity is the
        # enclosing function's scope kind.
        tm.that(scope, none=False)
        tm.that(scope.get_kind(), eq=c.Infra.RopeScopeKind.FUNCTION)
