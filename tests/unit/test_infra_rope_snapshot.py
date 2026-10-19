"""Behavior tests for the Rope snapshot inventory boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config, m
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeSnapshot:
    """Validate the closed snapshot inventory against governed entry files."""

    @staticmethod
    @pytest.mark.parametrize("external", [False, True])
    @pytest.mark.parametrize("planned", [False, True])
    @pytest.mark.parametrize("consumed", [False, True])
    def test_physical_receipt_never_becomes_the_planned_source(
        tmp_path: Path,
        *,
        external: bool,
        planned: bool,
        consumed: bool,
    ) -> None:
        """An overlay is not a publication receipt, even after same-inode drift."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = tmp_path / "external" if external else package
        provider.mkdir(exist_ok=True)
        source = provider / "provider.py"
        physical = b"value = 'physical'\n"
        proposed = b"value = 'planned!'\n"
        source.write_bytes(physical)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        declarations = (
            (
                m.Infra.CodegenFilePlan(
                    project=provider if external else root,
                    path=source,
                    before=original,
                    desired_content=proposed,
                    desired_mode=original.mode,
                ),
            )
            if planned
            else ()
        )
        with u.Infra.facade_source_project(
            root, source_states=(original,), declared_files=declarations
        ) as (project, receipts, _):
            with project.source_consumption() as consumer:
                tm.that(
                    project.source_text(source).encode("utf-8"),
                    eq=proposed if planned else physical,
                )
            tm.that(consumer.receipt().inputs, eq=(original,))
            tm.that(receipts()[0], eq=(original,))
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True)),
                eq=original,
            )

        with pytest.raises(ValueError, match="atomic source changed") as rejected:
            with u.Infra.facade_source_project(
                root, source_states=(original,), declared_files=declarations
            ) as (project, receipts, _):
                if consumed:
                    tm.that(project.source_state(source), eq=original)
                # Preserve inode, mode and length while changing the physical bytes.
                with source.open("r+b") as stream:
                    tm.that(stream.write(proposed), eq=len(physical))
                observed = tm.ok(
                    u.Cli.atomic_read_binary_file_state(source, required=True)
                )
                tm.that(
                    observed.model_dump(exclude={"content"}),
                    eq=original.model_dump(exclude={"content"}),
                )
                tm.that(observed.content, eq=proposed)
                if consumed:
                    tm.that(receipts()[0], eq=(original,))
                else:
                    project.source_state(source)
        tm.that(str(rejected.value), has=str(source))
        tm.that(str(rejected.value), has="content_changed=True")
        tm.that(str(rejected.value), has="same_model_type=True")

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_lazy_planning_keeps_physical_receipts_for_both_overlay_routes(
        tmp_path: Path, *, declared: bool
    ) -> None:
        """Repeated export planning never authenticates its own proposed bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(root))
        source = package / "provider.py"
        physical_name = f"{layout.class_stem}Original"
        planned_name = f"{layout.class_stem}Projected"
        physical = (
            f'class {physical_name}:\n    """Original declaration."""\n'
            f"__all__ = [{physical_name!r}]\n"
        ).encode("utf-8")
        proposed = (
            f'class {planned_name}:\n    """Projected declaration."""\n'
            f"__all__ = [{planned_name!r}]\n"
        ).encode("utf-8")
        source.write_bytes(physical)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        declarations = (
            (
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=source,
                    before=original,
                    desired_content=proposed,
                    desired_mode=original.mode,
                ),
            )
            if declared
            else ()
        )
        overlay = {} if declared else {source: proposed.decode("utf-8")}
        service = u.Tests.create_lazy_init_service(root)
        with u.Infra.facade_source_project(
            root,
            source_states=(original,),
            declared_files=declarations,
            planned_sources=overlay,
        ) as (project, receipts, _):
            for _ in range(2):
                analysis = tm.ok(service.plan_files(source_project=project))
                initializer = next(
                    plan
                    for plan in analysis.files
                    if plan.path == package / "__init__.py"
                )
                rendered = tm.not_none(initializer.desired_content).decode("utf-8")
                tm.that(rendered, has=planned_name)
                tm.that(physical_name in rendered, eq=False)
                tm.that(
                    tuple(state for state in receipts()[0] if state.path == source),
                    eq=(original,),
                )
                tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

        with pytest.raises(ValueError, match="atomic source changed"):
            with u.Infra.facade_source_project(
                root,
                source_states=(original,),
                declared_files=declarations,
                planned_sources=overlay,
            ) as (project, _, _):
                tm.ok(service.plan_files(source_project=project))
                with source.open("r+b") as stream:
                    stream.write(proposed)
                    stream.truncate()
                project.verify_source_states()

    @staticmethod
    def test_module_lookup_uses_declared_source_roots(tmp_path: Path) -> None:
        """Unrelated root packages never expand live or snapshot import roots."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        unrelated = repository_root / "unrelated"
        module_path = package_root / "declared.py"
        source = "value = 1\n"
        module_path.write_text(source, encoding="utf-8")
        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            project = rope.rope_project
            source_roots = tuple(
                folder.real_path for folder in project.get_source_folders()
            )
            unrelated.mkdir()
            (unrelated / "__init__.py").write_text("", encoding="utf-8")
            tm.that(
                tuple(folder.real_path for folder in project.get_source_folders()),
                eq=source_roots,
            )
            tm.that(str(unrelated) in source_roots, eq=False)
            package = tm.not_none(project.find_module("unrelated"))
            tm.that(package.is_folder(), eq=True)
            tm.that(package.real_path, eq=str(unrelated))
            resource = tm.not_none(project.find_module("flext_demo.declared"))
            tm.that(resource.real_path, eq=str(module_path))
            snapshot = u.Infra.snapshot_project(project, {module_path: source})
            try:
                tm.that(
                    tuple(folder.real_path for folder in snapshot.get_source_folders()),
                    eq=source_roots,
                )
                captured_package = tm.not_none(snapshot.find_module("unrelated"))
                tm.that(captured_package.is_folder(), eq=True)
                tm.that(captured_package.real_path, eq=package.real_path)
                captured = u.Infra.require_file_resource(
                    tm.not_none(snapshot.find_module("flext_demo.declared")),
                    module_path,
                )
                tm.that(captured.read(), eq=source)
            finally:
                snapshot.close()

    @staticmethod
    @pytest.mark.parametrize("root_name", config.Infra.source_scan.roots)
    def test_declared_package_root_keeps_qualified_imports(
        tmp_path: Path,
        root_name: str,
    ) -> None:
        """A configured scan root that is itself a package keeps its identity."""
        repository_root, _package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        declared_package = repository_root / root_name
        declared_package.mkdir(exist_ok=True)
        (declared_package / "__init__.py").write_text("", encoding="utf-8")
        module_path = declared_package / "declared.py"
        module_path.write_text("value = 1\n", encoding="utf-8")
        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            resource = tm.not_none(
                rope.rope_project.find_module(f"{root_name}.declared"),
            )
            tm.that(resource.real_path, eq=str(module_path))

    @staticmethod
    def test_snapshot_serves_project_root_entry_module(tmp_path: Path) -> None:
        """A governed root conftest.py joins the closed inventory from disk.

        Raises:
            TypeError: If the snapshot entry is not a Rope file resource.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        conftest = repository_root / "conftest.py"
        conftest.write_text(
            '"""Root entry module outside every source folder."""\n',
            encoding="utf-8",
        )
        package_init = package_root / "__init__.py"
        sources = {
            package_init.resolve(): package_init.read_text(encoding="utf-8"),
            conftest.resolve(): conftest.read_text(encoding="utf-8"),
        }
        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            snapshot = u.Infra.snapshot_project(rope.rope_project, sources)
            try:
                resource = snapshot.get_resource("conftest.py")
                if not u.Infra.file_resource(resource):
                    msg = "expected a Rope file resource: conftest.py"
                    raise TypeError(msg)
                tm.that(resource.read(), eq=sources[conftest.resolve()])
            finally:
                snapshot.close()

    @staticmethod
    def test_snapshot_rejects_sources_outside_the_project(tmp_path: Path) -> None:
        """A path outside the workspace root never enters the closed inventory."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        outsider = tmp_path / "outside.py"
        outsider.write_text("value = 1\n", encoding="utf-8")
        package_init = package_root / "__init__.py"
        sources = {
            package_init.resolve(): package_init.read_text(encoding="utf-8"),
            outsider.resolve(): "value = 1\n",
        }
        with (
            FlextInfraRopeWorkspace.open_workspace(repository_root) as rope,
            pytest.raises(
                ValueError,
                match=r"outside its input inventory",
            ) as guard_error,
        ):
            u.Infra.snapshot_project(rope.rope_project, sources)

        tm.that(str(outsider.resolve()) in str(guard_error.value), eq=True)
