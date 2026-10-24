"""Behavior tests for the Rope snapshot inventory boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import nullcontext
from re import escape
from typing import TYPE_CHECKING, Literal

import pytest

from flext_infra import config, m
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeSnapshot:
    """Validate the closed snapshot inventory against governed entry files."""

    @staticmethod
    @pytest.mark.parametrize("physical", [False, True])
    @pytest.mark.parametrize("predicate", ["exists", "isfile", "isdir"])
    def test_directory_predicates_consume_payload_only_for_virtual_positive_answers(
        tmp_path: Path,
        predicate: Literal["exists", "isfile", "isdir"],
        *,
        physical: bool,
    ) -> None:
        """A false file-kind query is not a read of every directory descendant."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        dependency = package / "dependency.py"
        dependency.write_text("value = 1\n", encoding="utf-8")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(dependency, required=True))
        directory = package if physical else package / "planned"
        provider = directory / "provider.py"
        plan = tm.ok(FlextInfraCodegenConform.file_plan(
            root, provider.relative_to(root).as_posix(), "value = 2\n",
            source_states=(original,),
        ))
        with u.Infra.facade_source_project(root, declared_files=(plan,)) as binding:
            project = binding[0]
            with project.source_consumption() as consumer:
                tm.that(project.source_query(directory, predicate), eq=predicate != "isfile")
            receipt = consumer.receipt()
            tm.that(
                dependency in {state.path for state in receipt.inputs},
                eq=not physical and predicate != "isfile",
            )
            tm.that(
                any(
                    inventory.root.path == directory.parent
                    and (directory.name, predicate) in inventory.queries
                    for inventory in receipt.source_directories
                ),
                eq=True,
            )

    @staticmethod
    @pytest.mark.parametrize("changed_membership", [False, True])
    def test_repeated_overlay_reads_retain_every_original_receipt(
        tmp_path: Path,
        *,
        changed_membership: bool,
    ) -> None:
        """Import-once bookkeeping never skips consumer reads or epoch guards."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = package / "provider.py"
        provider.write_text("value = 1\n", encoding="utf-8")
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as observed:
                project.source_children(package)
                project.source_text(provider)
            receipt = observed.receipt()
        plan = tm.ok(FlextInfraCodegenConform.file_plan(
            root, provider.relative_to(root).as_posix(), "value = 2\n",
            source_states=receipt.inputs,
        )).model_copy(update={
            "source_directories": receipt.source_directories,
            "source_query_topology": receipt.source_query_topology,
        })
        rejection = (
            pytest.raises(ValueError, match=escape(str(package)))
            if changed_membership else nullcontext()
        )
        with rejection, u.Infra.facade_source_project(root, declared_files=(plan,)) as binding:
            project = binding[0]
            with project.source_consumption() as first:
                tm.that(project.source_text(provider), eq="value = 2\n")
            with project.source_consumption() as second:
                tm.that(project.source_text(provider), eq="value = 2\n")
            tm.that(second.receipt().inputs, eq=first.receipt().inputs)
            tm.that(second.receipt().source_directories, eq=first.receipt().source_directories)
            tm.that(second.receipt().source_query_topology, eq=first.receipt().source_query_topology)
            if changed_membership:
                (package / "new.py").write_text("value = 3\n", encoding="utf-8")

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
