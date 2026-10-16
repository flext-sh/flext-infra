"""Tests for refactor namespace-move rewriting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations
import __future__

from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraCli
from flext_infra._utilities import FlextInfraRopeProject
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
    def _module_move_workspace(tmp_path: Path) -> t.Quad[Path, Path, Path, Path]:
        """Declare a real published owner and a consumer of its behavior.

        Returns:
            The repository, package, original source and declared destination.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        implementation = package / "_pieces"
        implementation.mkdir()
        (implementation / c.Infra.INIT_PY).write_text(
            '"""Original implementation package."""\n',
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
                tm.that(parent.is_folder(), eq=True)
                tm.that(parent.exists(), eq=True)
                published = u.Infra.require_file_resource(
                    snapshot.get_resource(target.relative_to(root).as_posix()),
                    target,
                )
                tm.that(published.exists(), eq=True)
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
        tm.that(target.parent.parent.exists(), eq=False)
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_snapshot_external_provider_reads_captured_source_after_live_change(
        cls,
        tmp_path: Path,
    ) -> None:
        """External module resolution preserves captured declarations after drift."""
        root, package, source, _target = cls._module_move_workspace(tmp_path)
        provider_root = tmp_path / "external_provider"
        provider_root.mkdir()
        provider = provider_root / "external_contract.py"
        original = "class CapturedProvider:\n    pass\n"
        newer = "class NewerProvider:\n    pass\n"
        provider.write_text(original, encoding=c.DEFAULT_ENCODING)
        provider_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(provider, required=True),
        )
        provider.write_text(newer, encoding=c.DEFAULT_ENCODING)
        snapshot = FlextInfraRopeProject.from_snapshot(
            str(root),
            {
                source: source.read_bytes(),
                provider: tm.not_none(provider_state.content),
            },
            source_folders=(package.relative_to(root).as_posix(),),
            python_path_folders=(str(provider_root),),
        )
        try:
            resource = u.Infra.require_file_resource(
                tm.not_none(snapshot.find_module(provider.stem)), provider
            )
            tm.that(resource.read(), eq=original)
            tm.that(
                snapshot
                .get_pymodule(resource)
                .get_attribute("CapturedProvider")
                .get_object()
                .get_name(),
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
        tm.that(target.parent.exists(), eq=False)
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
                projection_roots=(root,),
            ),
        )
        tm.that(source.exists(), eq=False)
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
                projection_roots=(root,),
            ),
        )
        tm.that(source.read_bytes(), eq=newer)
        tm.that(target.parent.exists(), eq=False)
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
        tm.that(target.parent.exists(), eq=False)

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
        tm.that(destination.parent.exists(), eq=False)
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
        tm.that(destination.parent.exists(), eq=False)
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
        tm.that(destination.parent.exists(), eq=False)
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
        tm.that(source.exists(), eq=False)
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
