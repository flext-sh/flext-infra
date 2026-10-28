"""Source export repair reaches an external consumer through lazy packages.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.slow
class TestsFlextInfraSingleClassExportRuntime:
    """Exercise the real catalog, publication and Python import boundaries."""

    @staticmethod
    @pytest.mark.parametrize("surface", tuple(c.Infra.NON_PUBLIC_LAZY_ROOTS))
    def test_internal_source_is_published_through_its_lazy_package(
        tmp_path: Path,
        surface: str,
    ) -> None:
        """The governed internal tiers use the same source export election."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_workspace_manifest(root, root.name)
        package = root / surface
        package.mkdir()
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        family = u.Infra.facade_families()["m"]
        declarations = package / family.directory
        declarations.mkdir()
        source = declarations / "binding_inventory.py"
        class_name = f"{u.Infra.project_prefix(source)}{family.suffix}Publication"
        source.write_text(
            '"""Internal consumer publication fixture."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"class {class_name}:\n"
            '    """A source identity published by its internal lazy package."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        report = tm.ok(FlextInfraModGateEngine.scan(root, fix=True))
        tm.that(
            {
                (root / entry.file).resolve()
                for entry in report.entries
                if entry.rule_id == "declare-single-class-export"
            },
            eq={source.resolve()},
        )
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        provider = f"{surface}.{family.directory}.{source.stem}"
        probe = (
            "import sys\n"
            f"sys.path.insert(0, {str(root)!r})\n"
            f"import {surface}.{family.directory} as exports\n"
            f"print({provider!r} in sys.modules)\n"
            f"from {surface}.{family.directory} import {class_name}\n"
            f"instance = {class_name}()\n"
            f"print(type(instance) is exports.{class_name})\n"
            f"print({class_name}.__module__ == {provider!r})\n"
        )
        consumer = tm.ok(u.Cli.run_raw([sys.executable, "-c", probe], cwd=root))
        tm.that(
            u.Cli.process_succeeded(consumer.outcome),
            eq=True,
            msg=consumer.stderr,
        )
        tm.that(consumer.stdout.splitlines(), eq=["False", "True", "True"])
        repeated = tm.ok(FlextInfraModGateEngine.scan(root, fix=True))
        tm.that(
            tuple(
                entry
                for entry in repeated.entries
                if entry.rule_id == "declare-single-class-export"
            ),
            empty=True,
        )
        tm.that(u.Tests.run_lazy_init(root, check_only=True), eq=0)

    @staticmethod
    @pytest.mark.parametrize(
        "project_name",
        ["flext-outer-sample", "flext-connector-example"],
    )
    @pytest.mark.parametrize("scope_kind", ["standalone", "workspace", "nested-member"])
    def test_canonical_source_is_published_for_an_external_consumer(
        tmp_path: Path,
        project_name: str,
        scope_kind: str,
    ) -> None:
        """Project-derived exports remain lazy and exclude unrelated classes."""
        package_name = project_name.replace("-", "_")
        workspace: Path | None = None
        base = tmp_path
        if scope_kind != "standalone":
            workspace, _ = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=f"{project_name}-workspace",
                package_name=f"{package_name}_workspace",
            )
            u.Tests.write_workspace_manifest(
                workspace,
                f"{project_name}-workspace",
                role=c.Infra.MakeProfile.WORKSPACE,
            )
            base = workspace / "members" if scope_kind == "nested-member" else workspace
        root, package = u.Tests.create_lazy_init_workspace(
            base,
            project_name=project_name,
            package_name=package_name,
        )
        u.Tests.write_workspace_manifest(root, project_name)
        if workspace is not None:
            u.Tests.declare_workspace_projects(
                workspace,
                (root.relative_to(workspace).as_posix(),),
            )
        scan_root = workspace if workspace is not None else root
        family = u.Infra.facade_families()["u"]
        class_name = f"{u.derive_class_stem(project_name)}{family.suffix}Publication"
        source = package / family.directory / "binding_inventory.py"
        source.parent.mkdir()
        source.write_text(
            '"""External consumer publication fixture."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"class {class_name}:\n"
            '    """The class an external consumer instantiates."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        unrelated = source.with_name("foreign.py")
        unrelated.write_text(
            '"""A foreign class is not elected by the owning project."""\n\n'
            "from __future__ import annotations\n\n\n"
            "class ForeignDeclaration:\n"
            '    """A declaration outside the project class stem."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        elected = {
            (scan_root / entry.file).resolve()
            for entry in tm.ok(
                FlextInfraModGateEngine.scan(scan_root, fix=True)
            ).entries
            if entry.rule_id == "declare-single-class-export"
        }
        tm.that(elected, eq={source.resolve()})
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        consumer = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys\n"
                        f"sys.path.insert(0, {str(package.parent)!r})\n"
                        f"import {package_name}.{family.directory} as exports\n"
                        "print("
                        f"{f'{package_name}.{family.directory}.{source.stem}'!r}"
                        " in sys.modules)\n"
                        f"from {package_name}.{family.directory} import {class_name}\n"
                        f"{class_name}()\n"
                        "print('consumer-ready')\n"
                        "print(hasattr(exports, 'ForeignDeclaration'))\n"
                    ),
                ],
                cwd=root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(consumer.outcome),
            eq=True,
            msg=consumer.stderr,
        )
        tm.that(consumer.stdout.splitlines(), eq=["False", "consumer-ready", "False"])
        before = source.read_bytes(), unrelated.read_bytes()
        repeated = tm.ok(FlextInfraModGateEngine.scan(scan_root, fix=True))
        tm.that(
            tuple(
                entry
                for entry in repeated.entries
                if entry.rule_id == "declare-single-class-export"
            ),
            empty=True,
        )
        tm.that((source.read_bytes(), unrelated.read_bytes()), eq=before)
        tm.that(u.Tests.run_lazy_init(root, check_only=True), eq=0)
