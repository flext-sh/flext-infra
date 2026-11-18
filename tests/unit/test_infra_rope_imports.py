"""Focused behavior tests for Rope import utilities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeImports:
    """Validate fail-fast behavior for Rope import utility wrappers."""

    @staticmethod
    def test_native_self_imports_preserve_recursive_protocol_hints(
        tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """Native import tools remove self qualification without losing recursion."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = package / "_protocols" / "_external"
        directory.mkdir(parents=True)
        for parent in (directory.parent, directory):
            (parent / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        path = directory / "combined.py"
        module_name = f"{package.name}._protocols._external.combined"
        owner = f"{module_name}.ProtocolsExternalCombined"
        path.write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n"
            f"import {module_name}\n"
            "class ProtocolsExternalCombined:\n"
            "    class ExternalPath(Protocol):\n        @property\n"
            f"        def parent(self) -> {owner}.ExternalDirectory: ...\n"
            "    class ExternalDirectory(Protocol):\n        @property\n"
            f"        def parent(self) -> {owner}.ExternalPath: ...\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            resource = tm.not_none(workspace.resource(path))
            module = u.Infra.require_source_module(
                workspace.rope_project.get_pymodule(resource)
            )
            source = u.Infra.import_organizer(
                workspace.rope_project
            ).import_tools.organize_imports(
                module, unused=False, duplicates=False, sort=False
            )
        tm.that(source, lacks=f"{module_name}.ProtocolsExternalCombined")
        path.write_text(
            tm.ok(u.Infra.normalize_python_text(path, source)),
            encoding=c.DEFAULT_ENCODING,
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from typing import get_type_hints\n"
            f"from {module_name} import ProtocolsExternalCombined as contracts\n"
            "assert (get_type_hints(contracts.ExternalPath.parent.fget)['return']\n"
            "        is contracts.ExternalDirectory)\n"
            "assert (get_type_hints(contracts.ExternalDirectory.parent.fget)\n"
            "        ['return']\n"
            "        is contracts.ExternalPath)\n",
            cwd=root,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("statements", [False, True])
    def test_projected_syntax_error_retains_source_resource(
        tmp_path: Path, *, statements: bool
    ) -> None:
        """Invalid planned bytes report their owner, not the valid physical file."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source_path = package / "consumer.py"
        physical = "import math\n"
        source_path.write_text(physical, encoding="utf-8")
        planned = "from .provider import Value\n\nvalue = )\n"
        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            resource = tm.not_none(rope.resource(source_path))
            inventory = (
                u.Infra.source_import_statements
                if statements
                else u.Infra.source_import_targets
            )
            with u.Tests.raises(u.Infra.rope_syntax_errors()) as rejected:
                inventory(rope.rope_project, planned, resource=resource)
            tm.that(str(rejected.value), has=f"<{resource.path}> line <3>")
            tm.that(str(rejected.value), has="unmatched ')'")
        tm.that(source_path.read_text(encoding="utf-8"), eq=physical)

    @staticmethod
    def test_projected_multiline_generics_preserve_import_source(
        tmp_path: Path,
    ) -> None:
        """Native PEP 695 and UTF-8 positions retain planned import declarations."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source_path = package / "consumer.py"
        physical = "import math\n"
        source_path.write_text(physical, encoding="utf-8")
        planned = (
            "type Values[\n    T: (str, bytes),\n] = tuple[T, ...]\n"
            "class Reader[\n    T,\n]:\n"
            "    label = 'caf\u00e9'; from .provider import Value\n"
            "    def read[U](self, value: U) -> U:\n"
            "        from ..shared import (\n            Item,\n        )\n"
            "        return value\n"
        )
        with u.Infra.facade_source_project(
            root, planned_sources={source_path: planned}
        ) as (project, _sources):
            resource = u.Infra.require_file_resource(
                project.get_resource(source_path.relative_to(root).as_posix()),
                source_path,
            )
            selected = project.source_text(source_path)
            tm.that(
                u.Infra.source_import_targets(project, selected, resource=resource),
                eq=((".provider", ("Value",)), ("..shared", ("Item",))),
            )
            declarations = u.Infra.source_import_statements(
                project, selected, resource=resource
            )
            tm.that(
                tuple(item.import_info.get_import_statement() for item in declarations),
                eq=(
                    "from .provider import Value",
                    "from ..shared import Item",
                ),
            )
            tm.that(
                tuple((item.start_line, item.end_line) for item in declarations),
                eq=((7, 8), (9, 12)),
            )
            module = u.Infra.build_string_module(project, selected, resource=resource)
            tm.ok(module.get_resource() is resource)
            tm.that(module.source_code, eq=planned)
        tm.that(source_path.read_text(encoding="utf-8"), eq=physical)

    @staticmethod
    def test_normalize_imports_removes_orphaned_imports_and_formats(
        tmp_path: Path,
    ) -> None:
        """Centralized import cleanup should leave one lint-clean module."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "import tempfile\n"
                "import os\n\n"
                "def keep() -> str:\n"
                "    return os.getcwd()\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            result = u.Infra.normalize_imports(
                rope.rope_project,
                file_paths=(module_path,),
            )

        tm.ok(result)
        tm.that(
            module_path.read_text(encoding="utf-8"),
            eq=(
                "from __future__ import annotations\n\n"
                "import os\n\n"
                "\n"
                "def keep() -> str:\n"
                "    return os.getcwd()\n"
            ),
        )

    @staticmethod
    def test_normalize_imports_preserves_quoted_cast_types(
        tmp_path: Path,
    ) -> None:
        """A type referenced only inside cast must retain its import."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            "from typing import Literal, cast\nimport tempfile\n\n"
            'value = cast("Literal[1]", 1)\n',
            encoding="utf-8",
        )
        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            tm.ok(
                u.Infra.normalize_imports(rope.rope_project, file_paths=(module_path,)),
            )
            source = module_path.read_text(encoding="utf-8")
            tm.that(source, has="from typing import Literal, cast")
            tm.that(source, lacks="tempfile")
            tm.that(
                tm.ok(
                    u.Infra.normalize_imports(
                        rope.rope_project,
                        file_paths=(module_path,),
                    ),
                ),
                eq=False,
            )

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("module_source", "expected_change"),
        [
            u.Tests.param(
                (
                    "from __future__ import annotations\n\n"
                    "import os\n\n\n"
                    "def keep() -> str:\n"
                    "    return os.getcwd()\n"
                ),
                False,
                id="already-clean",
            ),
            u.Tests.param(
                (
                    "from __future__ import annotations\n\n"
                    "import os\n"
                    "import sys\n\n\n"
                    "def keep() -> str:\n"
                    "    return os.getcwd()\n"
                ),
                True,
                id="unused-import",
            ),
        ],
    )
    def test_organize_imports_detection_matches_module_state(
        tmp_path: Path,
        module_source: str,
        *,
        expected_change: bool,
    ) -> None:
        """Detection reports a pending organize change only for unorganized modules."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(module_source, encoding="utf-8")

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            resource = rope.resource(module_path)
            resource = tm.not_none(resource)
            result = u.Infra.organize_imports(rope.rope_project, resource, apply=False)

        tm.ok(result, eq=expected_change, is_=bool)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("module_source", "occurrence", "expected"),
        [
            u.Tests.param(
                "from x import p\nclass A:\n    y = p.X\n", "p.X", True, id="class"
            ),
            u.Tests.param(
                "from x import p\ndef f():\n    return p.Z\n",
                "p.Z",
                True,
                id="function",
            ),
            u.Tests.param(
                "if flag:\n    from x import p\nq = p.Y\n",
                "p.Y",
                False,
                id="conditional",
            ),
            u.Tests.param(
                "from x import p\nfrom y import p\nq = p.Y\n",
                "p.Y",
                False,
                id="twice",
            ),
            u.Tests.param(
                "def f():\n    from x import p\n    return p.Z\nq = p.Y\n",
                "p.Y",
                False,
                id="local",
            ),
            u.Tests.param("q = p.Y\nfrom x import p\n", "p.Y", False, id="later"),
        ],
    )
    def test_single_module_import_binding_follows_python_scoping(
        module_source: str,
        occurrence: str,
        *,
        expected: bool,
    ) -> None:
        """Only one unconditional earlier declaration reaches the occurrence."""
        module = u.Infra.build_string_module(None, module_source)
        offset = module_source.index(occurrence)
        tm.that(
            u.Infra.single_reaching_binding(
                module, u.Infra.scope_at(module, offset), "p", offset
            ),
            eq=expected,
        )
