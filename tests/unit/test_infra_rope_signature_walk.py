"""Behavior tests for native Rope signature and nested expression refactoring.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m
from flext_infra.workspace.rope import FlextInfraRopeWorkspace
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

        tm.that([item.name for item in objects], has="command")

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
            "def render(values: t.StrDict) -> str:\n"
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
        assert scope is not None
        tm.that(scope.get_kind(), eq=c.Infra.RopeScopeKind.FUNCTION)

    @staticmethod
    def test_rename_writes_pep701_nested_quote_expression(tmp_path: Path) -> None:
        """Rope preserves f-string fragments while writing a renamed AST child.

        Raises:
            AssertionError: If Rope did not resolve the PEP 701 regression resource.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "quoted_rename.py"
        source = (
            "def render(values: t.StrDict) -> str:\n"
            '    return f"value={values["name"].upper()}"\n'
        )
        expected = (
            "def render(items: t.StrDict) -> str:\n"
            '    return f"value={items["name"].upper()}"\n'
        )
        module_path.write_text(source, encoding="utf-8")

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            resource = rope.resource(module_path)
            if resource is None:
                msg = "Rope did not resolve the PEP 701 regression resource"
                raise AssertionError(msg)
            changes = u.Infra.rename_changes(
                rope.rope_project,
                resource,
                source.index("values["),
                "items",
                options=m.Infra.RopeRenameOptions(resources=(resource,)),
            )
            rope.rope_project.do(changes)
            rewritten = resource.read()

        tm.that(rewritten, eq=expected)

    @staticmethod
    def test_rename_writes_generator_inside_format_spec(tmp_path: Path) -> None:
        """Rope patches generator scopes nested in an f-string format spec.

        Raises:
            AssertionError: If Rope did not resolve the format-spec regression resource.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "format_spec.py"
        source = (
            "def render(value: int, widths: list[int]) -> str:\n"
            '    return f"{value:{next(width for width in widths)}}"\n'
        )
        expected = (
            "def render(value: int, sizes: list[int]) -> str:\n"
            '    return f"{value:{next(width for width in sizes)}}"\n'
        )
        module_path.write_text(source, encoding="utf-8")

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            resource = rope.resource(module_path)
            if resource is None:
                msg = "Rope did not resolve the format-spec regression resource"
                raise AssertionError(msg)
            changes = u.Infra.rename_changes(
                rope.rope_project,
                resource,
                source.index("widths:"),
                "sizes",
                options=m.Infra.RopeRenameOptions(resources=(resource,)),
            )
            rope.rope_project.do(changes)
            rewritten = resource.read()

        tm.that(rewritten, eq=expected)

    @staticmethod
    def test_rename_keeps_nested_generator_bindings(tmp_path: Path) -> None:
        """Native rename follows the iterable without changing the generator local."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "nested_generator.py"
        source = 'widths = (1, 2)\nrendered = f"{next(width for width in widths)}"\n'
        expected = 'sizes = (1, 2)\nrendered = f"{next(width for width in sizes)}"\n'
        module_path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            resource = rope.resource(module_path)
            if resource is None:
                msg = "Rope did not resolve the nested generator resource"
                raise AssertionError(msg)
            changes = u.Infra.rename_changes(
                rope.rope_project,
                resource,
                source.index("widths"),
                "sizes",
                options=m.Infra.RopeRenameOptions(resources=(resource,)),
            )
            rope.rope_project.do(changes)
            rendered = resource.read()
        tm.that(rendered, eq=expected)
