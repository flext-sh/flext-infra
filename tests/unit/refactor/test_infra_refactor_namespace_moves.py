"""Tests for refactor namespace-move rewriting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations
import __future__

from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraCli
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p, t


@pytest.mark.slow
class TestsFlextInfraRefactorInfraRefactorNamespaceMoves:
    """Behavior contract for test_infra_refactor_namespace_moves."""

    @staticmethod
    @pytest.mark.parametrize("source_stem", ["parser", "_parser"])
    @pytest.mark.parametrize("class_name", ["DocumentReader", "_DocumentReader"])
    def test_class_relocation_keeps_modules_public_and_facade_directories_private(
        tmp_path: Path, source_stem: str, class_name: str
    ) -> None:
        """Relocation destinations follow module and facade ownership conventions."""
        package = tmp_path / "example"
        source = package / f"{source_stem}.py"
        tm.that(
            u.Infra.class_target_file(
                package_dir=package,
                source_file=source,
                class_name=class_name,
                family="",
            ),
            eq=package / "parser_document_reader.py",
        )
        for letter, family in u.Infra.facade_families().items():
            target = u.Infra.class_target_file(
                package_dir=package,
                source_file=source,
                class_name=class_name,
                family=letter,
            )
            tm.that(target, eq=package / family.directory / "document_reader.py")
            tm.that(target.parent.name.startswith("_"), eq=True)

    @staticmethod
    def _module_move_workspace(tmp_path: Path) -> t.Quad[Path, Path, Path, Path]:
        """Declare a real published owner and a consumer of its behavior.

        Returns:
            The repository, package, original source and declared destination.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        implementation = package / "_pieces"
        implementation.mkdir()
        (implementation / c.Infra.INIT_PY).write_text(
            '"""Original implementation package."""\n'
            "from .owned import DeclaredOwner\n\n"
            "__all__ = ('DeclaredOwner',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        source = implementation / "owned.py"
        source.write_text(
            '"""Published text normalization owner."""\n'
            "from __future__ import annotations\n\n"
            "class DeclaredOwner:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().upper()\n\n"
            "__all__ = ('DeclaredOwner',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "consumer.py").write_text(
            f"from {package.name}._pieces import DeclaredOwner\n\n"
            "class Consumer:\n"
            "    Owner = DeclaredOwner\n\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return Consumer.Owner.normalize(value)\n\n"
            "__all__ = ('Consumer',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        return root, package, source, package / "relocated" / "owned.py"

    @staticmethod
    def _module_move_inputs(
        project: p.Infra.RopeProject,
    ) -> t.Pair[t.MappingKV[Path, str], tuple[m.Cli.AtomicFileState, ...]]:
        """Capture the actual public planner inputs once through atomic reads.

        Returns:
            Captured source text and the original physical file states.

        """
        states = tuple(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    resource.real_path,
                    required=True,
                ),
            )
            for resource in project.get_python_files()
        )
        return (
            {
                state.path: tm.not_none(state.content).decode(c.DEFAULT_ENCODING)
                for state in states
            },
            states,
        )

    @classmethod
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize("via_cli", [False, True])
    def test_exact_module_destination_preserves_mixed_contents_and_identity(
        cls, tmp_path: Path, *, nested: bool, via_cli: bool
    ) -> None:
        """Publish complete modules and resolve real executable and quoted users."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        implementation = package / "_pieces"
        implementation.mkdir()
        (implementation / c.Infra.INIT_PY).write_text(
            '"""Implementation owners."""\n', encoding=c.DEFAULT_ENCODING
        )
        source = implementation / "_core.py"
        source.write_text(
            "from __future__ import annotations\n"
            "from pydantic import BaseModel\n"
            "FACTOR = 3\n"
            "type Label = str\n"
            "class Parent:\n    pass\n"
            "class DeclaredOwner(Parent):\n    pass\n"
            "class Payload(BaseModel):\n    value: str\n"
            "def normalize(value: Label) -> Label:\n"
            "    return value.strip().upper() * FACTOR\n"
            "__all__ = ('DeclaredOwner', 'Parent', 'Payload', 'normalize', 'FACTOR', 'Label')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "unrelated.py").write_text(
            "class DeclaredOwner:\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        other = package / "_other"
        other.mkdir()
        (other / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (other / "_core.py").write_text(
            "class DeclaredOwner:\n    pass\n", encoding=c.DEFAULT_ENCODING
        )
        consumer = package / "consumer.py"
        consumer.write_text(
            "from __future__ import annotations\n"
            f"from {package.name}._pieces import _core\n"
            f"from {package.name}._pieces import _core as module_alias\n"
            f"from {package.name}._pieces import _core as owner\n"
            f"from {package.name}._pieces._core import DeclaredOwner, normalize\n"
            f"from {package.name} import unrelated\n"
            f"from {package.name}._other import _core as unrelated_module\n"
            "PAYLOAD = '_core.DeclaredOwner'\n"
            f"{package.name} = 7\n"
            "class Consumer:\n"
            f"    {package.name} = 11\n"
            "    value: 'owner.DeclaredOwner'\n"
            "__all__ = ('_core', 'DeclaredOwner', 'normalize')\n"
            "def direct(value: '_core.DeclaredOwner') -> '_core.DeclaredOwner':\n"
            "    return value\n"
            "def aliased(value: 'module_alias.DeclaredOwner') -> 'module_alias.DeclaredOwner':\n"
            "    return value\n"
            "def other(value: 'unrelated.DeclaredOwner') -> 'unrelated.DeclaredOwner':\n"
            "    return value\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = (
            package / "_schema" / "elements.py"
            if nested
            else implementation / "core.py"
        )
        schema_program = (
            "import json\n"
            "print(json.dumps(owned.Payload.model_json_schema(), sort_keys=True))\n"
            "print(owned.Payload(value='payload').model_dump_json())\n"
        )
        original_schema = u.Tests.run_lazy_init_probe(
            f"import {package.name}._pieces._core as owned\n" + schema_program,
            python_paths=(str(package.parent),),
        )
        reference_program = (
            "from typing import get_type_hints\n"
            f"from {package.name} import consumer\n"
            "print(get_type_hints(consumer.Consumer)['value'] is consumer.owner.DeclaredOwner)\n"
            "print(get_type_hints(consumer.aliased)['value'] is consumer.owner.DeclaredOwner)\n"
            f"print(getattr(consumer, {package.name!r}))\n"
            f"print(getattr(consumer.Consumer, {package.name!r}))\n"
        )
        original_references = u.Tests.run_lazy_init_probe(
            reference_program,
            python_paths=(str(package.parent),),
        )
        tm.that(original_references, eq=["True", "True", "7", "11"])
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            plans = u.Infra.plan_module_move(
                workspace.rope_project,
                source,
                destination_file=target,
                sources=sources,
                source_states=states,
            )
        tm.fail(target.exists())
        if nested:
            tm.fail(target.parent.exists())
        for state in states:
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(state.path, required=True)),
                eq=state,
            )
        if via_cli:
            tm.that(
                FlextInfraCli().main([
                    "refactor",
                    "move-module",
                    "--repository-root",
                    str(root),
                    "--source-file",
                    str(source.relative_to(root)),
                    "--destination-file",
                    str(target.relative_to(root)),
                ]),
                eq=0,
            )
        else:
            tm.ok(
                FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                    plans,
                    repository_root=root,
                    options=m.Infra.SemanticPublicationOptions(
                        projection_roots=(root,)
                    ),
                )
            )
        tm.fail(source.exists())
        destination = (
            f"{package.name}._schema.elements"
            if nested
            else f"{package.name}._pieces.core"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {destination} as owned\n" + schema_program,
                python_paths=(str(package.parent),),
            ),
            eq=original_schema,
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                reference_program,
                python_paths=(str(package.parent),),
            ),
            eq=original_references,
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from typing import get_type_hints\n"
                f"from {package.name} import consumer\n"
                f"import {destination} as relocated\n"
                "print(consumer.DeclaredOwner is relocated.DeclaredOwner)\n"
                "print(consumer.normalize(' x '))\n"
                "print(relocated.FACTOR)\n"
                "print(relocated.Label.__value__ is str)\n"
                "print(relocated.DeclaredOwner.__bases__ == (relocated.Parent,))\n"
                "print(get_type_hints(consumer.direct)['value'] is relocated.DeclaredOwner)\n"
                "print(get_type_hints(consumer.aliased)['value'] is relocated.DeclaredOwner)\n"
                "print(get_type_hints(consumer.other)['value'] is consumer.unrelated.DeclaredOwner)\n"
                "print(consumer.unrelated_module.DeclaredOwner is relocated.DeclaredOwner)\n"
                "print(consumer.owner.DeclaredOwner is relocated.DeclaredOwner)\n"
                "print(getattr(consumer, consumer.__all__[0]) is relocated)\n"
                "print(consumer.PAYLOAD)\n",
                python_paths=(str(package.parent),),
            ),
            eq=[
                "True",
                "XXX",
                "3",
                "True",
                "True",
                "True",
                "True",
                "True",
                "False",
                "True",
                "True",
                "_core.DeclaredOwner",
            ],
        )

    @staticmethod
    @pytest.mark.parametrize("both", [False, True])
    def test_move_module_command_requires_one_explicit_destination(
        tmp_path: Path, *, both: bool
    ) -> None:
        """The public request rejects ambiguous and missing execution facts."""
        source, target = tmp_path / "source.py", tmp_path / "target.py"
        with pytest.raises(ValueError, match="exactly one"):
            m.Infra.ModuleMoveCommand(
                repository_root=tmp_path,
                source_file=source,
                destination_directory=tmp_path if both else None,
                destination_file=target if both else None,
            )
        for request in (
            m.Infra.ModuleMoveCommand(
                repository_root=tmp_path,
                source_file=source,
                destination_directory=tmp_path,
            ),
            m.Infra.ModuleMoveCommand(
                repository_root=tmp_path,
                source_file=source,
                destination_file=target,
            ),
        ):
            tm.that(
                m.Infra.ModuleMoveCommand.model_validate_json(
                    request.model_dump_json(round_trip=True)
                ),
                eq=request,
            )
        tm.fail(source.exists())
        tm.fail(target.exists())

    @classmethod
    @pytest.mark.parametrize("occupied_package", [False, True])
    def test_exact_module_destination_rejects_occupied_native_owner(
        cls, tmp_path: Path, *, occupied_package: bool
    ) -> None:
        """File and package collisions leave all captured owners untouched."""
        root, package, source, _ = cls._module_move_workspace(tmp_path)
        target = package / "elements.py"
        if occupied_package:
            occupied = target.with_suffix("")
            occupied.mkdir()
            occupied /= c.Infra.INIT_PY
        else:
            occupied = target
        occupied.write_text("VALUE = 'occupied'\n", encoding=c.DEFAULT_ENCODING)
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            with pytest.raises(FileExistsError):
                u.Infra.plan_module_move(
                    workspace.rope_project,
                    source,
                    destination_file=target,
                    sources=sources,
                    source_states=states,
                )
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    @pytest.mark.parametrize(
        "destination", ["invalid-name.py", "class.py", "owner.txt", "__init__.py"]
    )
    def test_exact_module_destination_rejects_invalid_file_identity(
        cls, tmp_path: Path, destination: str
    ) -> None:
        """Reject invalid Python owners without creating a destination package."""
        root, package, source, _ = cls._module_move_workspace(tmp_path)
        target = package / "_schema" / destination
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            with pytest.raises(ValueError, match="requires"):
                u.Infra.plan_module_move(
                    workspace.rope_project,
                    source,
                    destination_file=target,
                    sources=sources,
                    source_states=states,
                )
        tm.fail(target.parent.exists())
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_exact_module_destination_requires_complete_source_graph(
        cls, tmp_path: Path
    ) -> None:
        """A partial consumer graph cannot authorize a resource relocation."""
        root, package, source, _ = cls._module_move_workspace(tmp_path)
        target = package / "_schema" / "elements.py"
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            with pytest.raises(ValueError, match="complete source inventory"):
                u.Infra.plan_module_move(
                    workspace.rope_project,
                    source,
                    destination_file=target,
                    sources={source: sources[source]},
                    source_states=states,
                )
        tm.fail(target.parent.exists())
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_exact_module_destination_rejects_new_package_before_publication(
        cls, tmp_path: Path
    ) -> None:
        """A later package owner cannot displace the planned module identity."""
        root, package, source, _ = cls._module_move_workspace(tmp_path)
        target = package / "elements.py"
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            plans = u.Infra.plan_module_move(
                workspace.rope_project,
                source,
                destination_file=target,
                sources=sources,
                source_states=states,
            )
        occupied = target.with_suffix("")
        occupied.mkdir()
        initializer = occupied / c.Infra.INIT_PY
        content = "VALUE = 'newer package owner'\n"
        initializer.write_text(content, encoding=c.DEFAULT_ENCODING)
        tm.fail(
            FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=root,
                options=m.Infra.SemanticPublicationOptions(projection_roots=(root,)),
            )
        )
        tm.ok(source.exists())
        tm.fail(target.exists())
        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_exact_module_destination_rejects_consumer_name_capture(
        cls, tmp_path: Path
    ) -> None:
        """Native relocation never captures an independently owned local name."""
        root, package, source, _ = cls._module_move_workspace(tmp_path)
        consumer = package / "captured.py"
        consumer.write_text(
            f"from {package.name}._pieces import owned\n"
            "elements = 'independently owned'\n"
            "Published = owned.DeclaredOwner\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = source.with_name("elements.py")
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            with pytest.raises(ValueError, match="capture a consumer binding"):
                u.Infra.plan_module_move(
                    workspace.rope_project,
                    source,
                    destination_file=target,
                    sources=sources,
                    source_states=states,
                )
        tm.fail(target.exists())
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_snapshot_exposes_only_declared_virtual_nested_resources(
        cls,
        tmp_path: Path,
    ) -> None:
        """A closed snapshot resolves nested parents without filesystem effects."""
        root, package, source, _target = cls._module_move_workspace(tmp_path)
        target = package / "virtual" / "nested" / "owned.py"
        content = source.read_bytes()
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            original = next(state for state in states if state.path == source)
            declaration = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(u.Cli.atomic_plan_directory_chain(target.parent)),
                desired_content=content,
                desired_mode=tm.not_none(original.mode),
                source_states=states,
            )
            snapshot = u.Infra.snapshot_project(
                workspace.rope_project,
                sources,
                captured=u.Infra.codemod_source_epoch(
                    m.Infra.CodemodBindingSnapshot(states=states)
                ),
                declared_files=(declaration,),
            )
            try:
                parent = snapshot.get_resource(
                    target.parent.relative_to(root).as_posix(),
                )
                tm.ok(parent.is_folder())
                tm.ok(parent.exists())
                published = u.Infra.require_file_resource(
                    snapshot.get_resource(target.relative_to(root).as_posix()),
                    target,
                )
                tm.ok(published.exists())
                tm.that(published.read(), eq=content.decode(c.DEFAULT_ENCODING))
                tm.that(
                    u.Infra.resolve_pymodule(snapshot, published).source_code,
                    eq=content.decode(c.DEFAULT_ENCODING),
                )
                snapshot.validate()
                tm.that(
                    u.Infra.resolve_pymodule(snapshot, published).source_code,
                    eq=content.decode(c.DEFAULT_ENCODING),
                )
                with pytest.raises(u.Infra.rope_error_types()):
                    snapshot.get_resource(
                        (target.parent / "undeclared.py").relative_to(root).as_posix(),
                    )
            finally:
                snapshot.close()
        tm.fail(target.parent.parent.exists())
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_snapshot_external_provider_reads_captured_source_after_live_change(
        cls,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """External module resolution preserves captured declarations after drift."""
        root, _package, _source, _target = cls._module_move_workspace(tmp_path)
        provider = installed_dependency_path / "external_contract.py"
        original = "class CapturedProvider:\n    pass\n"
        newer = "class NewerProvider:\n    pass\n"
        provider.write_text(original, encoding=c.DEFAULT_ENCODING)
        provider_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(provider, required=True),
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            provider.write_text(newer, encoding=c.DEFAULT_ENCODING)
            snapshot = u.Infra.snapshot_project(
                workspace.rope_project,
                {**sources, provider: original},
                captured=u.Infra.codemod_source_epoch(
                    m.Infra.CodemodBindingSnapshot(states=(*states, provider_state))
                ),
            )
            try:
                resource = u.Infra.require_file_resource(
                    tm.not_none(snapshot.find_module(provider.stem)), provider
                )
                tm.that(resource.read(), eq=original)
                module = u.Infra.resolve_pymodule(snapshot, resource)
                tm.that(
                    module.get_attribute("CapturedProvider").get_object().get_name(),
                    eq="CapturedProvider",
                )
                snapshot.validate()
                tm.that(resource.read(), eq=original)
            finally:
                snapshot.close()
        tm.that(provider.read_text(encoding=c.DEFAULT_ENCODING), eq=newer)

    @classmethod
    def test_module_move_plan_is_observational_and_publishes_real_imports(
        cls,
        tmp_path: Path,
    ) -> None:
        """Planning creates nothing; joint publication preserves public behavior."""
        root, package, source, target = cls._module_move_workspace(tmp_path)
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            plans = u.Infra.plan_module_move(
                workspace.rope_project,
                source,
                target.parent,
                sources=sources,
                source_states=states,
            )
        for plan in plans:
            tm.that(
                any(
                    str(state.path) == tm.not_none(__future__.__file__)
                    for state in plan.source_states
                ),
                eq=True,
            )
        tm.fail(target.parent.exists())
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import consumer\n"
                "print(consumer.Consumer.normalize(' receiver '))\n",
                python_paths=(str(package.parent),),
            ),
            eq=["RECEIVER"],
        )
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=root,
                options=m.Infra.SemanticPublicationOptions(projection_roots=(root,)),
            ),
        )
        tm.fail(source.exists())
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import consumer\n"
                f"from {package.name}.relocated import DeclaredOwner\n"
                "print(consumer.Consumer.normalize(' receiver '))\n"
                "print(consumer.Consumer.Owner is DeclaredOwner)\n",
                python_paths=(str(package.parent),),
            ),
            eq=["RECEIVER", "True"],
        )

    @classmethod
    def test_module_move_stale_source_rejects_before_any_effect(
        cls,
        tmp_path: Path,
    ) -> None:
        """A newer source remains intact and the planned destination stays absent."""
        root, _package, source, target = cls._module_move_workspace(tmp_path)
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            plans = u.Infra.plan_module_move(
                workspace.rope_project,
                source,
                target.parent,
                sources=sources,
                source_states=states,
            )
        newer = source.read_bytes() + b"\n# Newer authored work.\n"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                newer.decode(c.DEFAULT_ENCODING),
            ),
        )
        tm.fail(
            FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=root,
                options=m.Infra.SemanticPublicationOptions(projection_roots=(root,)),
            ),
        )
        tm.that(source.read_bytes(), eq=newer)
        tm.fail(target.parent.exists())
        for state in states:
            if state.path != source:
                tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    @pytest.mark.parametrize(
        ("extra", "message"),
        [
            ("\nclass AnotherOwner:\n    pass\n", "requires one class"),
            ("\nprint('separate behavior')\n", "separate executable behavior"),
            ("\n__all__ = ('AnotherOwner',)\n", "exports are ambiguous"),
        ],
    )
    def test_module_move_rejects_ambiguous_or_executable_modules(
        cls,
        tmp_path: Path,
        extra: str,
        message: str,
    ) -> None:
        """An ineligible module is refused without creating relocation artifacts."""
        root, _package, source, target = cls._module_move_workspace(tmp_path)
        source.write_text(
            source.read_text(encoding=c.DEFAULT_ENCODING) + extra,
            encoding=c.DEFAULT_ENCODING,
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            sources, states = cls._module_move_inputs(workspace.rope_project)
            with pytest.raises(ValueError, match=message):
                u.Infra.plan_module_move(
                    workspace.rope_project,
                    source,
                    target.parent,
                    sources=sources,
                    source_states=states,
                )
        tm.fail(target.parent.exists())

    @staticmethod
    def test_class_move_preview_leaves_absent_destination_uncreated(
        tmp_path: Path,
    ) -> None:
        """A valid preview preserves sources and the original lazy consumer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "owned.py"
        class_name = "DeclaredOwner"
        source.write_text(
            f"class {class_name}:\n    pass\n\n__all__ = ({class_name!r},)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        originals = source.read_bytes(), (package / c.Infra.INIT_PY).read_bytes()
        destination = package / "destination" / "owned.py"
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            target = u.Infra.move_class(
                m.Infra.ClassMoveRequest(
                    rope_project=workspace.rope_project,
                    source_file=source,
                    target_file=destination,
                    class_name=class_name,
                    line=1,
                    apply=False,
                ),
            )
        tm.that(target, eq=destination)
        tm.fail(destination.parent.exists())
        tm.that(
            (source.read_bytes(), (package / c.Infra.INIT_PY).read_bytes()),
            eq=originals,
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import {class_name}\n"
                f"print(type({class_name}()).__name__)\n",
                python_paths=(str(package.parent),),
            ),
            eq=[class_name],
        )

    @staticmethod
    @pytest.mark.parametrize("apply", [False, True])
    def test_invalid_class_move_preserves_destination_absence(
        tmp_path: Path,
        *,
        apply: bool,
    ) -> None:
        """Identifier rejection creates no files or destination directories."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "owned.py"
        original = "class DeclaredOwner:\n    pass\n"
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        destination = package / "destination" / "owned.py"
        with (
            FlextInfraRopeWorkspace.open_workspace(root) as workspace,
            pytest.raises(ValueError, match="was not found at line"),
        ):
            _ = u.Infra.move_class(
                m.Infra.ClassMoveRequest(
                    rope_project=workspace.rope_project,
                    source_file=source,
                    target_file=destination,
                    class_name="MissingOwner",
                    line=1,
                    apply=apply,
                ),
            )
        tm.fail(destination.parent.exists())
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

    @staticmethod
    def test_class_move_plan_rejects_absent_owner_without_creating_it(
        tmp_path: Path,
    ) -> None:
        """A rejected immutable plan leaves its missing target owner absent."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "owned.py"
        original = "class DeclaredOwner:\n    pass\n"
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        destination = package / "destination" / "owned.py"
        with (
            FlextInfraRopeWorkspace.open_workspace(root) as workspace,
            pytest.raises(
                ValueError, match="absent from the governed source inventory"
            ),
        ):
            _ = u.Infra.plan_class_move(
                m.Infra.ClassMoveRequest(
                    rope_project=workspace.rope_project,
                    source_file=source,
                    target_file=destination,
                    class_name="DeclaredOwner",
                    line=1,
                    apply=False,
                ),
                sources={source: original},
            )
        tm.fail(destination.parent.exists())
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

    @staticmethod
    @pytest.mark.parametrize("class_name", ["DeclaredOwner", "AnotherDeclaredOwner"])
    def test_public_module_move_preserves_declarations_and_consumer_identity(
        tmp_path: Path,
        class_name: str,
    ) -> None:
        """Relocate actual modules with Rope, then import the rewritten consumer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        implementation = package / "_pieces"
        implementation.mkdir()
        implementation.joinpath("__init__.py").write_text(
            '"""Implementation package."""\n',
            encoding="utf-8",
        )
        source = implementation / "owned.py"
        source_text = f"class {class_name}:\n    pass\n\n__all__ = ({class_name!r},)\n"
        source.write_text(source_text, encoding="utf-8")
        consumer = package / "consumer.py"
        consumer.write_text(
            f"from {package.name}._pieces.owned import {class_name}\n"
            f"Published = {class_name}\n",
            encoding="utf-8",
        )
        tm.that(
            FlextInfraCli().main([
                "refactor",
                "move-module",
                "--repository-root",
                str(root),
                "--source-file",
                str(source),
                "--destination-directory",
                str(package),
            ]),
            eq=0,
        )
        tm.fail(source.exists())
        tm.that(
            package.joinpath("owned.py").read_text(encoding="utf-8"), eq=source_text
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import consumer, owned\n"
                f"print(consumer.Published is owned.{class_name})\n",
                python_paths=(str(package.parent),),
            ),
            eq=["True"],
        )
