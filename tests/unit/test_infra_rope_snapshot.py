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
        with u.Infra.facade_source_project(root) as (project, _sources):
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

        with u.Infra.facade_source_project(root) as (project, _sources):
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
            pytest.raises(ValueError, match="is not in the subpath"),
            u.Infra.facade_source_project(root) as (project, _sources),
        ):
            tuple(project.get_python_files())

    @staticmethod
    @pytest.mark.parametrize("external", [False, True])
    @pytest.mark.parametrize("planned", [False, True])
    def test_declared_plan_overlays_without_touching_the_physical_source(
        tmp_path: Path,
        *,
        external: bool,
        planned: bool,
    ) -> None:
        """A declared plan is visible in the view; the live file keeps its bytes."""
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
        with u.Infra.facade_source_project(root, declared_files=declarations) as (
            project,
            _,
        ):
            tm.that(
                project.source_bytes(source),
                eq=proposed if planned else physical,
            )
            tm.that(project.source_state(source), eq=original)
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @staticmethod
    def test_source_view_retains_native_provider_epoch_and_rejects_live_edit(
        tmp_path: Path,
    ) -> None:
        """Rope and source planning share one capture; CAS preserves a later edit.

        Raises:
            TypeError: If Native source has no Rope module.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        original = b"class Original: pass\n"
        changed = b"class Concurrent: pass\n"
        source.write_bytes(original)
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            project = snapshot.engine
            resource = u.Infra.require_file_resource(
                project.get_resource(source.relative_to(root).as_posix()),
                source,
            )
            provider = project.get_pymodule(resource, force_errors=True)
            if not u.Infra.source_module(provider):
                message = f"Native source has no Rope module: {source}"
                raise TypeError(message)
            before = project.source_state(source)
            tm.that(provider.source_code, eq=original.decode())
            source.write_bytes(changed)

            tm.that(project.source_bytes(source), eq=original)
            tm.that(resource.read(), eq=provider.source_code)
            tm.that(project.source_state(source), eq=before)
            captured = u.Infra.workspace_source(snapshot, source)
            tm.that(captured.text, eq=provider.source_code)
            tm.that(captured.state, eq=before)
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=project.source_state(source),
                desired_content=original + b"# generated projection\n",
                desired_mode=before.mode,
            )
            tm.fail(
                u.Infra.publish_codegen_plans(root, (plan,)),
                has=f"atomic source changed: {source}",
            )
            tm.that(source.read_bytes(), eq=changed)


class TestsFlextInfraRopeCandidateViews:
    """Validate nested native candidate bindings and their retained witnesses."""

    @staticmethod
    def test_candidate_binding_reuses_native_project_and_unchanged_module(
        tmp_path: Path,
    ) -> None:
        """A candidate changes its module while retaining independent parses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        independent = package / "independent.py"
        physical = b"class Original: pass\n"
        proposed = b"class Projected: pass\n"
        source.write_bytes(physical)
        independent.write_text("class Independent: pass\n", encoding="utf-8")
        with u.Infra.facade_source_project(root) as (project, original_sources):
            resource = project.get_resource(source.relative_to(root).as_posix())
            other = project.get_resource(independent.relative_to(root).as_posix())
            original_module = project.get_pymodule(resource, force_errors=True)
            independent_module = project.get_pymodule(other, force_errors=True)
            before = project.source_state(source)
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=before,
                desired_content=proposed,
                desired_mode=before.mode,
            )
            with u.Infra.facade_source_project(
                root, declared_files=(plan,), source_project=project
            ) as (candidate, candidate_sources):
                tm.that(candidate is project, eq=True)
                projected_module = candidate.get_pymodule(resource, force_errors=True)
                tm.that(projected_module is not original_module, eq=True)
                tm.that(
                    candidate.get_pymodule(other, force_errors=True)
                    is independent_module,
                    eq=True,
                )
                tm.that(candidate_sources[source], eq=proposed.decode())
                tm.that(original_sources[source], eq=physical.decode())
                tm.that(candidate.source_state(source) is before, eq=True)
                tm.that(source.read_bytes(), eq=physical)
            tm.that(project.source_bytes(source), eq=physical)
            tm.that(
                project.get_pymodule(other, force_errors=True) is independent_module,
                eq=True,
            )

    @staticmethod
    def test_planned_override_preserves_bound_foreign_candidate(tmp_path: Path) -> None:
        """An owned override retains its provider candidate and entry witnesses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owned = package / "owned.py"
        provider = tmp_path / "external"
        provider.mkdir()
        foreign = provider / "provider.py"
        owned_physical = b"class Original: pass\n"
        foreign_physical = b"class Provider: pass\n"
        foreign_proposed = b"class ProposedProvider: pass\n"
        owned_proposed = "class ProposedOwned: pass\n"
        owned.write_bytes(owned_physical)
        foreign.write_bytes(foreign_physical)
        foreign_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(foreign, required=True)
        )
        foreign_plan = m.Infra.CodegenFilePlan(
            project=provider,
            path=foreign,
            before=foreign_before,
            desired_content=foreign_proposed,
            desired_mode=foreign_before.mode,
        )
        with u.Infra.facade_source_project(root, declared_files=(foreign_plan,)) as (
            project,
            _sources,
        ):
            owned_before = project.source_state(owned)
            provider_before = project.source_state(foreign)
            with u.Infra.facade_source_project(
                root,
                planned_sources={owned: owned_proposed},
                source_project=project,
            ) as (candidate, candidate_sources):
                tm.that(candidate is project, eq=True)
                tm.that(candidate_sources[owned], eq=owned_proposed)
                tm.that(candidate.source_bytes(foreign), eq=foreign_proposed)
                tm.that(candidate.source_state(owned) is owned_before, eq=True)
                tm.that(candidate.source_state(foreign) is provider_before, eq=True)
                tm.that(owned.read_bytes(), eq=owned_physical)
                tm.that(foreign.read_bytes(), eq=foreign_physical)
            tm.that(project.source_bytes(owned), eq=owned_physical)
            tm.that(project.source_bytes(foreign), eq=foreign_proposed)
            competing = m.Infra.CodegenFilePlan(
                project=root,
                path=owned,
                before=owned_before,
                desired_content=owned_physical,
                desired_mode=owned_before.mode,
            )
            with (
                pytest.raises(ValueError, match="competing declarations"),
                u.Infra.facade_source_project(
                    root,
                    declared_files=(competing,),
                    planned_sources={owned: owned_proposed},
                    source_project=project,
                ),
            ):
                pytest.fail("competing owned declarations were admitted")
            tm.that(project.source_bytes(owned), eq=owned_physical)
            tm.that(project.source_bytes(foreign), eq=foreign_proposed)
            tm.that(project.source_state(owned) is owned_before, eq=True)
            tm.that(project.source_state(foreign) is provider_before, eq=True)
        tm.that(owned.read_bytes(), eq=owned_physical)
        tm.that(foreign.read_bytes(), eq=foreign_physical)

    @staticmethod
    def test_nested_candidate_binding_restores_parent_after_consumer_failure(
        tmp_path: Path,
    ) -> None:
        """A failing nested consumer restores its parent, then the physical view."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        physical = b"class Original: pass\n"
        outer = b"class Outer: pass\n"
        inner = b"class Inner: pass\n"
        source.write_bytes(physical)
        consumer_failure = ValueError("consumer rejected the candidate")
        with u.Infra.facade_source_project(root) as (project, _sources):
            before = project.source_state(source)
            outer_plan = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=before,
                desired_content=outer,
                desired_mode=before.mode,
            )
            inner_plan = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=before,
                desired_content=inner,
                desired_mode=before.mode,
            )
            with u.Infra.facade_source_project(
                root, declared_files=(outer_plan,), source_project=project
            ) as (parent, parent_sources):
                with u.Infra.facade_source_project(
                    root, declared_files=(inner_plan,), source_project=project
                ) as (nested, nested_sources):
                    tm.that(nested is parent, eq=True)
                    tm.that(nested_sources[source], eq=inner.decode())
                    tm.that(parent_sources[source], eq=outer.decode())
                with (
                    pytest.raises(ValueError, match=str(consumer_failure)) as failure,
                    u.Infra.facade_source_project(
                        root, declared_files=(inner_plan,), source_project=project
                    ),
                ):
                    raise consumer_failure
                tm.that(failure.value is consumer_failure, eq=True)
                tm.that(parent.source_bytes(source), eq=outer)
                tm.that(parent_sources[source], eq=outer.decode())
            tm.that(project.source_bytes(source), eq=physical)
            tm.that(project.source_state(source) is before, eq=True)
        tm.that(source.read_bytes(), eq=physical)

    @staticmethod
    def test_candidate_membership_refreshes_negative_lookup_and_virtual_directory(
        tmp_path: Path,
    ) -> None:
        """A virtual package is resolvable only while its candidate is active."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        folder = package / "fresh"
        initializer = folder / "__init__.py"
        source = folder / "provider.py"
        module_name = f"{package.name}.{folder.name}.{source.stem}"
        with u.Infra.facade_source_project(root) as (project, _sources):
            tm.that(project.find_module(module_name), eq=None)
            plans = tuple(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=path,
                    before=project.source_state(path, required=False),
                    desired_content=content,
                    desired_mode=config.Infra.codegen.modes.file_default,
                )
                for path, content in (
                    (initializer, b""),
                    (source, b"class Added: pass\n"),
                )
            )
            with u.Infra.facade_source_project(
                root, declared_files=plans, source_project=project
            ) as (candidate, candidate_sources):
                resource = tm.not_none(candidate.find_module(module_name))
                tm.that(resource.real_path, eq=str(source))
                tm.that(candidate.source_query(folder, "isdir"), eq=True)
                tm.that(candidate_sources[source], eq="class Added: pass\n")
                with candidate.source_view():
                    tm.that(candidate.find_module(module_name), eq=None)
                    tm.that(candidate.source_query(folder, "isdir"), eq=False)
                tm.that(
                    tm.not_none(candidate.find_module(module_name)).real_path,
                    eq=str(source),
                )
            tm.that(project.find_module(module_name), eq=None)
            tm.that(project.source_query(folder, "isdir"), eq=False)
        tm.that(folder.exists(), eq=False)

    @staticmethod
    def test_candidate_source_roots_refresh_inferred_provider_and_restore_it(
        tmp_path: Path,
    ) -> None:
        """Changing lookup roots refreshes an existing consumer's superclass."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = package / "provider.py"
        consumer = package / "consumer.py"
        preferred_root = root / "!preferred"
        preferred_package = preferred_root / package.name
        preferred_package.mkdir(parents=True)
        preferred = preferred_package / provider.name
        for path in (provider, preferred):
            path.write_text("class Base: pass\n", encoding="utf-8")
        (preferred_package / "__init__.py").write_text("", encoding="utf-8")
        consumer.write_text(
            f"from {package.name}.provider import Base\nclass Child(Base): pass\n",
            encoding="utf-8",
        )
        with u.Infra.facade_source_project(root) as (project, _sources):
            resource = project.get_resource(consumer.relative_to(root).as_posix())
            original_module = project.get_pymodule(resource, force_errors=True)
            for roots, expected in (
                ((), provider),
                ((preferred_root.relative_to(root).as_posix(),), preferred),
                ((), provider),
            ):
                with project.source_view(additional_source_folders=roots) as candidate:
                    current_module = candidate.get_pymodule(resource, force_errors=True)
                    tm.that(current_module is original_module, eq=True)
                    child = u.Infra.require_class_object(
                        current_module.get_attribute("Child").get_object(),
                        "consumer child",
                    )
                    parent = u.Infra.require_source_object(
                        child.get_superclasses()[0], "provider base"
                    )
                    supplied = tm.not_none(parent.get_module().get_resource())
                    tm.that(supplied.real_path, eq=str(expected))

    @staticmethod
    def test_planned_reintroduction_preserves_retired_source_mode(
        tmp_path: Path,
    ) -> None:
        """Reintroducing a retired source retains its captured physical mode."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        physical = b"class Original: pass\n"
        proposed = "class Reintroduced: pass\n"
        source.write_bytes(physical)
        source.chmod(config.Infra.codegen.modes.file_default ^ 0o100)
        with u.Infra.facade_source_project(root) as (project, _sources):
            before = project.source_state(source)
            retirement = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=before,
                desired_content=None,
                desired_mode=None,
            )
            with u.Infra.facade_source_project(
                root, declared_files=(retirement,), source_project=project
            ) as (retired, retired_sources):
                tm.that(source in retired_sources, eq=False)
                with u.Infra.facade_source_project(
                    root,
                    planned_sources={source: proposed},
                    source_project=retired,
                ) as (candidate, candidate_sources):
                    tm.that(candidate is project, eq=True)
                    tm.that(candidate_sources[source], eq=proposed)
                    plan = next(
                        plan for plan in candidate.source_plans if plan.path == source
                    )
                    tm.that(plan.desired_mode, eq=before.mode)
                    tm.that(
                        plan.desired_mode != config.Infra.codegen.modes.file_default,
                        eq=True,
                    )
                    tm.that(plan.before is before, eq=True)
                    tm.that(candidate.source_state(source) is before, eq=True)
                    tm.ok(u.Cli.atomic_verify_binary_file_states((before,)))
                tm.that(retired.source_query(source, "exists"), eq=False)
                with pytest.raises(FileNotFoundError):
                    retired.source_bytes(source)
                tm.that(retired.source_state(source) is before, eq=True)
            tm.that(project.source_bytes(source), eq=physical)
            tm.ok(u.Cli.atomic_verify_binary_file_states((before,)))

    @staticmethod
    def test_candidate_retirement_hides_only_the_logical_source(tmp_path: Path) -> None:
        """A retirement removes native lookup without deleting the physical file."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        content = b"class Original: pass\n"
        source.write_bytes(content)
        module_name = f"{package.name}.{source.stem}"
        with u.Infra.facade_source_project(root) as (project, _sources):
            tm.not_none(project.find_module(module_name))
            before = project.source_state(source)
            retirement = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=before,
                desired_content=None,
                desired_mode=before.mode,
            )
            with u.Infra.facade_source_project(
                root, declared_files=(retirement,), source_project=project
            ) as (candidate, candidate_sources):
                tm.that(candidate.find_module(module_name), eq=None)
                tm.that(source in candidate_sources, eq=False)
                with pytest.raises(FileNotFoundError):
                    candidate.source_bytes(source)
                tm.that(source.read_bytes(), eq=content)
            tm.that(
                tm.not_none(project.find_module(module_name)).real_path,
                eq=str(source),
            )
            tm.that(project.source_bytes(source), eq=content)

    @staticmethod
    def test_candidate_rejects_conflicting_witness_without_overwriting_live_edit(
        tmp_path: Path,
    ) -> None:
        """A conflicting proposal leaves the captured view and foreign bytes intact."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        physical = b"class Original: pass\n"
        foreign = b"class Foreign: pass\n"
        source.write_bytes(physical)
        with u.Infra.facade_source_project(root) as (project, _sources):
            before = project.source_state(source)
            source.write_bytes(foreign)
            conflicting = m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(source, required=True)
                ),
                desired_content=b"class Projected: pass\n",
                desired_mode=before.mode,
            )
            with (
                pytest.raises(ValueError, match="conflicts with captured state"),
                u.Infra.facade_source_project(
                    root, declared_files=(conflicting,), source_project=project
                ),
            ):
                pytest.fail("a conflicting physical witness was admitted")
            tm.that(project.source_bytes(source), eq=physical)
            tm.that(project.source_state(source) is before, eq=True)
        tm.that(source.read_bytes(), eq=foreign)

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_lazy_planning_reads_both_overlay_routes(
        tmp_path: Path, *, declared: bool
    ) -> None:
        """Repeated export planning renders the proposed, never the physical, bytes."""
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
            declared_files=declarations,
            planned_sources=overlay,
        ) as (project, _):
            for _ in range(2):
                analysis = tm.ok(service.plan_files(source_project=project))
                initializer = next(
                    plan for plan in analysis if plan.path == package / "__init__.py"
                )
                rendered = tm.not_none(initializer.desired_content).decode("utf-8")
                tm.that(rendered, has=planned_name)
                tm.fail(physical_name in rendered)
                tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @staticmethod
    def test_native_lazy_ancestry_reads_unpublished_declared_source(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Proposed classes are planned from the overlay without being published."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
import pytest
from tests import c, m, t, tm, u
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
    root, declared_files=(declaration,)
) as (project, _):
    for _ in range(2):
        analysis = tm.ok(service.plan_files(source_project=project))
        initializer = next(
            plan for plan in analysis
            if plan.path == package / c.Infra.INIT_PY)
        tm.that(tm.not_none(initializer.desired_content).decode(
            c.DEFAULT_ENCODING), has=name)
        tm.that(project.source_bytes(source), eq=proposed)
        with pytest.raises(FileNotFoundError):
            project.source_bytes(package / "unplanned.py")
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
    def test_overlay_lists_planned_children_beside_live_entries(
        tmp_path: Path,
    ) -> None:
        """Each directory lists live entries plus its planned direct children."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        nested = package / "fresh" / "deep" / "module.py"
        sibling = package / "fresh" / "sibling.py"
        live = tuple(sorted(child.name for child in package.iterdir()))
        with u.Infra.facade_source_project(
            root,
            planned_sources={nested: "value = 1\n", sibling: "value = 2\n"},
        ) as (project, _):
            tm.that(
                tuple(child.name for child in project.source_children(package)),
                eq=tuple(sorted({*live, "fresh"})),
            )
            tm.that(
                tuple(
                    child.name for child in project.source_children(package / "fresh")
                ),
                eq=("deep", "sibling.py"),
            )
            tm.that(
                project.source_children(package / "fresh" / "deep"),
                eq=(nested,),
            )
        tm.that((package / "fresh").exists(), eq=False)

    @staticmethod
    def test_snapshot_admits_proposal_for_an_absent_source(tmp_path: Path) -> None:
        """A proposal for an absent path is visible only inside the view."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "proposed.py"
        content = "value = 1\n"
        with infra.rope_workspace(root) as rope:
            snapshot = u.Infra.snapshot_project(rope.rope_project, {source: content})
            try:
                resource = u.Infra.require_file_resource(
                    snapshot.get_resource(source.relative_to(root).as_posix()), source
                )
                tm.that(resource.read(), eq=content)
                tm.that(source.exists(), eq=False)
            finally:
                snapshot.close()

    @staticmethod
    def test_snapshot_rejects_sources_outside_the_project(tmp_path: Path) -> None:
        """A path outside the workspace root never enters the overlaid view."""
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
            outsider.resolve(): "value = 2\n",
        }
        with (
            infra.rope_workspace(repository_root) as rope,
            pytest.raises(
                ValueError,
                match=r"outside its project",
            ) as guard_error,
        ):
            u.Infra.snapshot_project(rope.rope_project, sources)

        tm.ok(str(outsider.resolve()) in str(guard_error.value))
