"""Behavior tests for the Rope snapshot inventory boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, infra, m
from tests import p, tm, u


class TestsFlextInfraRopeSnapshot:
    """Validate the closed snapshot inventory against governed entry files."""

    @staticmethod
    def test_import_snapshot_keeps_each_relative_owner(tmp_path: Path) -> None:
        """Identical declarations keep distinct suppliers in the real import graph."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumers: list[Path] = []
        owners: list[Path] = []
        for name in ("left", "right"):
            folder = package / name
            folder.mkdir()
            (folder / "__init__.py").write_text("", encoding="utf-8")
            owner = folder / "owner.py"
            owner.write_text(f"Value = {name!r}\n", encoding="utf-8")
            consumer = folder / "consumer.py"
            consumer.write_text("from .owner import Value\n", encoding="utf-8")
            consumers.append(consumer)
            owners.append(owner)
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in consumers
        )
        snapshot = u.Infra.codemod_binding_snapshot(root, states)
        tm.that(
            {state.path for state in snapshot.states}.intersection(owners),
            eq=set(owners),
        )
        with u.Infra.codemod_binding_project(
            root, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, _sources):
            for consumer, owner in zip(consumers, owners, strict=True):
                resource = u.Infra.require_file_resource(
                    project.get_resource(consumer.relative_to(root).as_posix()),
                    consumer,
                )
                module = u.Infra.build_string_module(
                    project, project.source_text(consumer), resource=resource
                )
                supplier, _line = module.get_attribute(
                    "Value"
                ).get_definition_location()
                supplied_resource = tm.not_none(tm.not_none(supplier).get_resource())
                tm.that(supplied_resource.real_path, eq=str(owner))

    @staticmethod
    def test_import_snapshot_syntax_error_identifies_dependency(tmp_path: Path) -> None:
        """The capture caller passes the transitive supplier's resource to Rope."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / "broken_owner.py"
        owner.write_text("Value = 1\n\ninvalid = )\n", encoding="utf-8")
        consumer = package / "consumer.py"
        consumer.write_text("from .broken_owner import Value\n", encoding="utf-8")
        state = tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True))
        with pytest.raises(u.Infra.rope_syntax_errors()) as rejected:
            u.Infra.codemod_binding_snapshot(root, (state,))
        tm.that(
            str(rejected.value),
            has=f"<{owner.relative_to(root).as_posix()}> line <3>",
        )

    @staticmethod
    def test_native_observation_evidence_is_validated_and_independent() -> None:
        """Each capture owns its evidence and rejects incomplete bindings."""
        first = m.Infra.NativeObservationContext(paths=())
        second = m.Infra.NativeObservationContext(paths=())
        tm.that(first.evidence, eq=[])
        tm.that(second.evidence, eq=[])
        evidence = m.Infra.NativeBindingEvidence(
            binding="root",
            kind="module",
            supplier=__name__,
            name="capture",
            qualname="capture",
        )
        first.evidence.append(evidence)
        tm.that(tuple(first.evidence), eq=(evidence,))
        tm.that(second.evidence, eq=[])
        with pytest.raises(ValueError, match="binding"):
            m.Infra.NativeObservationContext.model_validate({
                "paths": (),
                "evidence": ({"kind": "module"},),
            })

    @staticmethod
    def test_governance_projection_alias_is_not_a_python_source(tmp_path: Path) -> None:
        """Agent projections never become source inputs through provider aliases."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = tmp_path / "provider"
        provider.mkdir()
        (provider / "external.py").write_text("value = 1\n", encoding="utf-8")
        skills = root / ".codex" / "skills"
        skills.mkdir(parents=True)
        (skills / "provider-helper").symlink_to(provider, target_is_directory=True)

        with u.Infra.facade_source_project(root) as (project, _receipts, _sources):
            paths = tuple(
                Path(resource.real_path) for resource in project.get_python_files()
            )
            tm.that(package / "__init__.py" in paths, eq=True)
            tm.that(
                any(path.is_relative_to(root / ".codex") for path in paths), eq=False
            )

    @staticmethod
    def test_python_source_alias_remains_rejected(tmp_path: Path) -> None:
        """Ignoring governance projections never admits aliases in project code."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = tmp_path / "provider"
        provider.mkdir()
        (provider / "external.py").write_text("value = 1\n", encoding="utf-8")
        (package / "provider_alias").symlink_to(provider, target_is_directory=True)

        with (
            pytest.raises(OSError, match="physical alias"),
            u.Infra.facade_source_project(root) as (project, _receipts, _sources),
        ):
            tuple(project.get_python_files())

    @staticmethod
    def test_source_queries_use_the_closed_snapshot(tmp_path: Path) -> None:
        """Snapshot membership follows captured inputs, never later disk state."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "captured.py"
        content = "value = 1\n"
        source.write_text(content, encoding="utf-8")
        late_source = package / "late.py"
        with infra.rope_workspace(root) as rope:
            snapshot = u.Infra.snapshot_project(rope.rope_project, {source: content})
            try:
                source.unlink()
                late_source.write_text(content, encoding="utf-8")
                tm.fail(snapshot.authenticated_sources)
                tm.ok(snapshot.source_query(source, "exists"))
                tm.ok(snapshot.source_query(source, "isfile"))
                tm.fail(snapshot.source_query(late_source, "exists"))
                tm.fail(snapshot.source_query(late_source, "isfile"))
                tm.fail(snapshot.source_query(source, "isdir"))
                tm.ok(snapshot.source_query(package, "exists"))
                tm.ok(snapshot.source_query(package, "isdir"))
                tm.fail(snapshot.source_query(package, "isfile"))
                with pytest.raises(
                    TypeError, match="does not own authenticated live reads"
                ):
                    snapshot.source_state(source)
            finally:
                snapshot.close()

    @staticmethod
    def test_unbound_live_source_query_requires_authentication(tmp_path: Path) -> None:
        """A native physical project is not an authenticated source inventory."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        with infra.rope_workspace(root) as rope:
            tm.fail(rope.rope_project.authenticated_sources)
            with pytest.raises(
                TypeError, match="does not own authenticated live reads"
            ):
                rope.rope_project.source_query(package, "isdir")

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
            root,
            source_options=m.Infra.StageSourceOptions(
                inputs=(original,), declared_files=declarations
            ),
        ) as (project, receipts, _):
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

        def consume_changed_source() -> None:
            with u.Infra.facade_source_project(
                root,
                source_options=m.Infra.StageSourceOptions(
                    inputs=(original,), declared_files=declarations
                ),
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

        with pytest.raises(ValueError, match="atomic source changed") as rejected:
            consume_changed_source()
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
        ).encode()
        proposed = (
            f'class {planned_name}:\n    """Projected declaration."""\n'
            f"__all__ = [{planned_name!r}]\n"
        ).encode()
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
            source_options=m.Infra.StageSourceOptions(
                inputs=(original,), declared_files=declarations
            ),
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
                tm.fail(physical_name in rendered)
                tm.that(
                    tuple(state for state in receipts()[0] if state.path == source),
                    eq=(original,),
                )
                tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

        def plan_changed_source() -> None:
            with u.Infra.facade_source_project(
                root,
                source_options=m.Infra.StageSourceOptions(
                    inputs=(original,), declared_files=declarations
                ),
                planned_sources=overlay,
            ) as (project, _, _):
                tm.ok(service.plan_files(source_project=project))
                with source.open("r+b") as stream:
                    stream.write(proposed)
                    stream.truncate()
                project.verify_source_states()

        with pytest.raises(ValueError, match="atomic source changed"):
            plan_changed_source()

    @staticmethod
    def test_native_lazy_ancestry_consumes_unpublished_declared_source(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Proposed classes retain physical absence without admitting missing inputs."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
import pytest
from tests import c, r
from tests import c, m, tm, u
root, package = u.Tests.create_lazy_init_workspace(Path(sys.argv[2]))
layout = tm.not_none(u.Infra.layout(root))
source = package / "provider.py"
name = f"{layout.class_stem}Projected"
proposed = (
    f"class {name}Base: pass\n"
    f"class {name}({name}Base): pass\n"
    f"__all__ = [{name!r}, '{name}Base']\n"
).encode(c.DEFAULT_ENCODING)
original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=False))
tm.that(original.content, eq=None)
declaration = m.Infra.CodegenFilePlan(
    project=root, path=source, before=original,
    desired_content=proposed, desired_mode=c.Infra.CONFIG_SPEC[1])
service = u.Tests.create_lazy_init_service(root)
with u.Infra.facade_source_project(
    root, source_options=m.Infra.StageSourceOptions(
        inputs=(original,), declared_files=(declaration,))
) as (project, receipts, _):
    for _ in range(2):
        analysis = tm.ok(service.plan_files(source_project=project))
        initializer = next(
            plan for plan in analysis.files
            if plan.path == package / c.Infra.INIT_PY)
        tm.that(tm.not_none(initializer.desired_content).decode(
            c.DEFAULT_ENCODING), has=name)
        tm.that(tuple(state for state in receipts()[0]
                      if state.path == source), eq=(original,))
        tm.that(tuple(state for state in initializer.source_states
                      if state.path == source), eq=(original,))
        tm.that(project.source_bytes(source), eq=proposed)
        with pytest.raises(FileNotFoundError, match="required source is absent"):
            project.source_state(source)
        with pytest.raises(FileNotFoundError):
            project.source_bytes(package / "unplanned.py")
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
tm.that(source.exists(), eq=False)
""",
            str(Path(__file__).resolve().parents[2]),
            str(tmp_path),
        )

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
        with infra.rope_workspace(repository_root) as rope:
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
            tm.fail(str(unrelated) in source_roots)
            package = tm.not_none(project.find_module("unrelated"))
            tm.ok(package.is_folder())
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
                tm.ok(captured_package.is_folder())
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
        with infra.rope_workspace(repository_root) as rope:
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
        with infra.rope_workspace(repository_root) as rope:
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
    def test_snapshot_admits_proposal_for_captured_absence(tmp_path: Path) -> None:
        """A descriptor-proven absence admits only its proposed virtual source."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        initializer = package / "__init__.py"
        source = package / "proposed.py"
        states = tuple(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(path, required=path == initializer)
            )
            for path in (initializer, source)
        )
        epoch = u.Infra.codemod_source_epoch(
            m.Infra.CodemodBindingSnapshot(states=states)
        )
        content = "value = 1\n"
        with infra.rope_workspace(root) as rope:
            snapshot = u.Infra.snapshot_project(
                rope.rope_project, {source: content}, captured=epoch
            )
            try:
                resource = u.Infra.require_file_resource(
                    snapshot.get_resource(source.relative_to(root).as_posix()), source
                )
                tm.that(resource.read(), eq=content)
                tm.that(source.exists(), eq=False)
                tm.ok(u.Cli.atomic_verify_binary_file_states(states))
            finally:
                snapshot.close()

    @staticmethod
    def test_snapshot_rejects_uncaptured_absent_proposal(tmp_path: Path) -> None:
        """No live path or absence is silently added to an authenticated epoch."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        initializer = package / "__init__.py"
        state = tm.ok(u.Cli.atomic_read_binary_file_state(initializer, required=True))
        epoch = u.Infra.codemod_source_epoch(
            m.Infra.CodemodBindingSnapshot(states=(state,))
        )
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match="outside its input inventory"),
        ):
            u.Infra.snapshot_project(
                rope.rope_project,
                {package / "uncaptured.py": "value = 1\n"},
                captured=epoch,
            )

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
            infra.rope_workspace(repository_root) as rope,
            pytest.raises(
                ValueError,
                match=r"outside its input inventory",
            ) as guard_error,
        ):
            u.Infra.snapshot_project(rope.rope_project, sources)

        tm.ok(str(outsider.resolve()) in str(guard_error.value))
