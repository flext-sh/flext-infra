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
        """Declare a real published owner and a consumer of its behavior."""
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
        """Capture the actual public planner inputs once through atomic reads."""
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
                captured=m.Infra.CodemodBindingSnapshot(states=states),
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
                    snapshot.get_pymodule(published).source_code,
                    eq=content.decode(c.DEFAULT_ENCODING),
                )
                snapshot.validate()
                tm.that(
                    snapshot.get_pymodule(published).source_code,
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
                source: source.read_text(encoding=c.DEFAULT_ENCODING),
                provider: tm.not_none(provider_state.content).decode(
                    c.DEFAULT_ENCODING,
                ),
            },
            source_folders=(package.relative_to(root).as_posix(),),
            python_path_folders=(str(provider_root),),
        )
        try:
            resource = tm.not_none(snapshot.find_module(provider.stem))
            tm.that(resource.read(), eq=original)
            tm.that(
                snapshot.get_pymodule(resource)
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
                source, newer.decode(c.DEFAULT_ENCODING),
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
        with (
            FlextInfraRopeWorkspace.open_workspace(root) as workspace,
            pytest.raises(ValueError, match=message),
        ):
            sources, states = cls._module_move_inputs(workspace.rope_project)
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
            pytest.raises(ValueError, match="absent from the governed source inventory"),
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

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _non_module_files(package_root: Path) -> t.VariadicTuple[str]:
        """Return files the rewrite left beside the package modules.

        Returns:
            Files the rewrite left beside the package modules.

        """
        return tuple(
            sorted(
                path.name
                for path in package_root.iterdir()
                if path.is_file() and path.suffix != ".py"
            ),
        )

    @classmethod
    def _build_project(cls, tmp_path: Path) -> t.Pair[Path, Path]:
        project_root = tmp_path / "flext-demo"
        package_root = project_root / "src" / "demo_pkg"
        cls._write_file(
            project_root / "pyproject.toml",
            '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
        )
        cls._write_file(project_root / "Makefile", "check:\n\t@true\n")
        cls._write_file(
            package_root / "__init__.py",
            "from __future__ import annotations\n",
        )
        u.Tests.provision_checkout(project_root)
        return (project_root, package_root)

    def test_rewrite_manual_protocol_violations_uses_public_runtime_api(
        self,
        tmp_path: Path,
    ) -> None:
        """Test rewrite manual protocol violations uses public runtime api."""
        project_root, package_root = self._build_project(tmp_path)
        protocols_file = package_root / "protocols.py"
        source_file = package_root / "service.py"
        consumer_file = package_root / "consumer.py"
        self._write_file(
            protocols_file,
            "from __future__ import annotations\n\nclass ExistingProtocol:\n    pass\n",
        )
        self._write_file(
            source_file,
            (
                "from __future__ import annotations\n\n"
                "from typing import Protocol\n\n"
                "class External(Protocol):\n"
                "    def call(self) -> str:\n"
                '        """Return the external value."""\n'
                "        ...\n"
            ),
        )
        self._write_file(
            consumer_file,
            (
                "from __future__ import annotations\n\n"
                "from demo_pkg.service import External\n\n"
                "def use(dep: External) -> External:\n"
                "    return dep\n"
            ),
        )

        u.Infra.rewrite_manual_protocol_violations(
            project_root=project_root,
            py_files=[source_file, consumer_file],
            names_by_file={source_file: {"External"}},
        )

        tm.that(
            source_file.read_text(encoding="utf-8"),
            lacks="class External(Protocol):",
        )
        tm.that(
            consumer_file.read_text(encoding="utf-8"),
            has="from demo_pkg.protocols import External",
        )
        protocols_text = protocols_file.read_text(encoding="utf-8")
        tm.that(protocols_text, has="from typing import Protocol")
        tm.that(protocols_text, has="class External(Protocol):")
        tm.that(self._non_module_files(package_root), eq=())

    def test_rewrite_manual_typing_alias_violations_uses_public_runtime_api(
        self,
        tmp_path: Path,
    ) -> None:
        """Test rewrite manual typing alias violations uses public runtime api."""
        project_root, package_root = self._build_project(tmp_path)
        typings_file = package_root / "typings.py"
        source_file = package_root / "service.py"
        self._write_file(
            typings_file,
            "from __future__ import annotations\n\nTYPE_READY = True\n",
        )
        self._write_file(
            source_file,
            (
                "from __future__ import annotations\n\n"
                "from collections.abc import Mapping\n"
                "from typing import TypeAlias\n\n"
                "PayloadMap: TypeAlias = t.StrMapping\n"
                "value = 1\n"
            ),
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"PayloadMap"}},
        )

        source_text = source_file.read_text(encoding="utf-8")
        typings_text = typings_file.read_text(encoding="utf-8")
        tm.that(source_text, lacks="PayloadMap: TypeAlias = t.StrMapping")
        tm.that(typings_text, has="type PayloadMap = t.StrMapping")
        tm.that(typings_text, lacks="from typing import TypeAlias")
        tm.that(typings_text, has="from flext_core import t")
        tm.that(self._non_module_files(package_root), eq=())

    @pytest.mark.parametrize("existing_target", [False, True])
    def test_typing_alias_cutover_preserves_all_consumer_bindings(
        self,
        tmp_path: Path,
        *,
        existing_target: bool,
    ) -> None:
        """Publish aliases and mixed consumer imports as one protected move."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        typings_file = package_root / "typings.py"
        if existing_target:
            self._write_file(typings_file, "from __future__ import annotations\n")
        self._write_file(
            source_file,
            "type AnyAlias = str\n"
            "type CleanAlias = int\n"
            "type NestedAnyAlias = list[AnyAlias]\n"
            "value = 1\n"
            "__all__ = ('AnyAlias', 'CleanAlias', 'NestedAnyAlias', 'value')\n",
        )
        self._write_file(
            package_root / "consumer.py",
            "from typing import Annotated, Literal\n"
            "from demo_pkg.service import AnyAlias as Renamed, CleanAlias, value\n"
            "Published = Renamed\n"
            "Clean = CleanAlias\n"
            "PublishedValue = value\n"
            "Metadata = Annotated[CleanAlias, 'AnyAlias']\n"
            "Label = Literal['AnyAlias']\n"
            "def shadow(Renamed: str) -> str:\n"
            "    return Renamed\n",
        )
        self._write_file(
            package_root / "second.py",
            "from .service import AnyAlias, NestedAnyAlias as Nested\n"
            "Published = AnyAlias\n"
            "NestedPublished = Nested\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"AnyAlias", "CleanAlias", "NestedAnyAlias"}},
        )

        tm.that(source_file.read_text(encoding="utf-8"), lacks="import AnyAlias")
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from typing import get_args\n"
                "from demo_pkg import consumer, second, service, typings\n"
                "print(consumer.Published is second.Published is typings.AnyAlias)\n"
                "print(consumer.Clean is typings.CleanAlias)\n"
                "print(second.NestedPublished is typings.NestedAnyAlias)\n"
                "print(get_args(typings.NestedAnyAlias.__value__)[0] "
                "is typings.AnyAlias)\n"
                "print(get_args(consumer.Metadata)[1] == 'AnyAlias')\n"
                "print(get_args(consumer.Label) == ('AnyAlias',))\n"
                "print(consumer.shadow('local') == 'local')\n"
                "print(consumer.PublishedValue == service.value)\n"
                "print(not hasattr(service, 'AnyAlias'))\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 9,
        )

    @pytest.mark.parametrize("ambiguous_binding", [False, True])
    def test_rejected_typing_alias_cutover_restores_every_source(
        self,
        tmp_path: Path,
        *,
        ambiguous_binding: bool,
    ) -> None:
        """Planning ambiguity or real lint rejection leaves the complete move intact."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        typings_file = package_root / "typings.py"
        consumer_file = package_root / "consumer.py"
        originals = {
            source_file: (
                "type Alias = str\n"
                if ambiguous_binding
                else "class LocalType:\n    pass\n\ntype Alias = LocalType\n"
            ),
            typings_file: "from __future__ import annotations\ntype Existing = bytes\n",
            consumer_file: (
                (
                    "from demo_pkg.typings import Existing as Alias\n"
                    if ambiguous_binding
                    else ""
                )
                + "from demo_pkg.service import Alias\nPublished = Alias\n"
            ),
        }
        for path, source in originals.items():
            self._write_file(path, source)

        with pytest.raises(RuntimeError):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
                gates=("lint",),
            )

        for path, source in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.parametrize(
        "consumer_source",
        [
            "import demo_pkg.other\nPublished = demo_pkg.other.Value\n",
            "import demo_pkg.service as service\nPublished = service.value\n",
            "from demo_pkg import service\nPublished = service.value\n",
            "from demo_pkg import *\nPublished = Value\n",
            (
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n    from .unavailable import Unrelated\n"
                "value: 'Unrelated'\n"
            ),
            (
                "import demo_pkg.service as service\n"
                "def shadow(service):\n    return service.Alias\n"
            ),
            "from . import service\nLabel = 'service.Alias'\n",
            (
                "from typing import Literal, Annotated\n"
                "from . import service\n"
                "type Label = Literal['service.Alias']\n"
                "type Marked = Annotated[str, 'service.Alias']\n"
            ),
        ],
    )
    def test_unrelated_imports_leave_typing_alias_plan_unchanged(
        self,
        tmp_path: Path,
        consumer_source: str,
    ) -> None:
        """Module spelling alone does not establish a selected alias consumer."""
        root, package = self._build_project(tmp_path)
        source = package / "service.py"
        consumer = package / "consumer.py"
        self._write_file(source, "type Alias = str\nvalue = 1\n")
        self._write_file(package / "other.py", "class Value:\n    pass\n")
        self._write_file(
            package / "__init__.py",
            "from .other import Value\n__all__ = ('Value',)\n",
        )
        self._write_file(consumer, consumer_source)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            prepared = u.Infra.plan_from_import_aliases(
                rope.rope_project,
                tm.not_none(rope.resource(consumer)),
                source_module="demo_pkg.service",
                target_module="demo_pkg.typings",
                aliases=("Alias",),
            )

        tm.that(prepared is None, eq=True)
        tm.that(consumer.read_text(encoding="utf-8"), eq=consumer_source)
        tm.that(package.joinpath("typings.py").exists(), eq=False)

    @pytest.mark.parametrize("exposes_alias", [False, True])
    def test_ancestor_star_import_uses_selected_export_identity(
        self,
        tmp_path: Path,
        *,
        exposes_alias: bool,
    ) -> None:
        """An ancestor star is relevant only when its exports expose the alias."""
        root, package = self._build_project(tmp_path)
        self._write_file(package / "service.py", "type Alias = str\nvalue = 1\n")
        exports = "('Alias', 'value')" if exposes_alias else "('value',)"
        self._write_file(
            package / "__init__.py",
            f"from .service import Alias, value\n__all__ = {exports}\n",
        )
        consumer = package / "consumer.py"
        original = "from demo_pkg import *\nPublished = value\n"
        self._write_file(consumer, original)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            resource = tm.not_none(rope.resource(consumer))
            if exposes_alias:
                with pytest.raises(RuntimeError, match="unsupported Rope module/star"):
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    )
            else:
                tm.that(
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    ),
                    eq=None,
                )

        tm.that(consumer.read_text(encoding="utf-8"), eq=original)
        tm.that(package.joinpath("typings.py").exists(), eq=False)

    @pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\f"])
    def test_typing_alias_plan_preserves_physical_lines_and_import_comments(
        self,
        tmp_path: Path,
        separator: str,
    ) -> None:
        """Actual string separators and formfeed must not shift AST edit offsets."""
        root, package = self._build_project(tmp_path)
        self._write_file(package / "service.py", "type Alias = str\nvalue = 1\n")
        self._write_file(package / "typings.py", "type Alias = str\n")
        consumer = package / "consumer.py"
        prefix = f"Label = 'left{separator}right'\n"
        original = (
            prefix + "\ffrom .service import (\n"
            "    Alias as Bound,  # retain alias comment\n"
            "    value,  # retain value comment\n"
            ")  # retain trailing comment\n"
            "Published = Bound\nPublishedValue = value\n"
        )
        self._write_file(consumer, original)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            prepared = tm.not_none(
                u.Infra.plan_from_import_aliases(
                    rope.rope_project,
                    tm.not_none(rope.resource(consumer)),
                    source_module="demo_pkg.service",
                    target_module="demo_pkg.typings",
                    aliases=("Alias",),
                )
            )

        tm.that(consumer.read_text(encoding="utf-8"), eq=original)
        tm.that(prepared, has=prefix)
        for comment in (
            "# retain alias comment",
            "# retain value comment",
            "# retain trailing comment",
        ):
            tm.that(prepared, has=comment)
        self._write_file(consumer, prepared)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, service, typings\n"
                "print(consumer.Published is typings.Alias)\n"
                "print(consumer.PublishedValue == service.value)\n"
                f"print(consumer.Label == 'left{separator}right')\n",
                python_paths=(str(package.parent),),
            ),
            eq=["True"] * 3,
        )

    @pytest.mark.parametrize("mixed", [False, True])
    def test_non_ascii_inline_import_plan_preserves_bytes_or_rejects(
        self,
        tmp_path: Path,
        *,
        mixed: bool,
    ) -> None:
        """UTF-8 columns retain semicolons/comments; mixed inline forms fail intact."""
        root, package = self._build_project(tmp_path)
        self._write_file(package / "service.py", "type Alias = str\nvalue = 1\n")
        self._write_file(package / "typings.py", "type Alias = str\n")
        consumer = package / "consumer.py"
        names = "Alias, value" if mixed else "Alias"
        original = (
            f"Label = 'caf\u00e9'; from .service import {names}; "
            "Published = Alias  # retain trailing comment\n"
        )
        self._write_file(consumer, original)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            resource = tm.not_none(rope.resource(consumer))
            if mixed:
                with pytest.raises(RuntimeError, match="unsupported Rope inline mixed"):
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    )
            else:
                prepared = tm.not_none(
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    )
                )
                tm.that(
                    prepared,
                    eq=original.replace("from .service", "from demo_pkg.typings"),
                )

        tm.that(consumer.read_text(encoding="utf-8"), eq=original)

    def test_typing_alias_cutover_preserves_scoped_relative_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """Function, class and typing-only imports retain their original scopes."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        consumer_file = package_root / "consumer.py"
        self._write_file(source_file, "type Alias = str\nvalue = 1\n")
        self._write_file(package_root / "typings.py", "type Existing = bytes\n")
        self._write_file(
            consumer_file,
            "from typing import TYPE_CHECKING\n"
            "from .typings import Existing as Local\n"
            "PublishedExisting = Local\n"
            "if TYPE_CHECKING:\n"
            "    from .service import Alias as Annotation\n"
            "def typed(value: 'Annotation') -> 'Annotation':\n"
            "    return value\n"
            "def scoped():\n"
            "    from .service import Alias as Local, value\n"
            "    return Local, value\n"
            "class Owner:\n"
            "    from .service import Alias as Local\n"
            "    Published = Local\n"
            "def shadow(Local):\n"
            "    return Local\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Alias"}},
        )

        tm.that(
            consumer_file.read_text(encoding="utf-8"),
            has=(
                "if TYPE_CHECKING:\n"
                "    from demo_pkg.typings import Alias as Annotation"
            ),
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, service, typings\n"
                "print(consumer.scoped()[0] is typings.Alias)\n"
                "print(consumer.scoped()[1] == service.value)\n"
                "print(consumer.Owner.Published is typings.Alias)\n"
                "print(consumer.shadow('local') == 'local')\n"
                "print(consumer.PublishedExisting is typings.Existing)\n"
                "print(not hasattr(consumer, 'Annotation'))\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 6,
        )

    def test_typing_alias_cutover_preserves_interleaved_binding_captures(
        self,
        tmp_path: Path,
    ) -> None:
        """Repeated imports cannot be merged or sorted across runtime captures."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        consumer_file = package_root / "consumer.py"
        self._write_file(source_file, "type Alias = str\n")
        self._write_file(package_root / "other.py", "type Alias = bytes\n")
        self._write_file(
            consumer_file,
            "from .service import Alias as Bound\n"
            "Before = Bound\n"
            "from .other import Alias as Bound\n"
            "After = Bound\n"
            "from .service import Alias as Bound\n"
            "Last = Bound\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Alias"}},
        )

        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, other, typings\n"
                "print(consumer.Before is consumer.Last is typings.Alias)\n"
                "print(consumer.After is other.Alias)\n"
                "print(consumer.Before is not consumer.After)\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 3,
        )

    @pytest.mark.parametrize("moved_first", [False, True])
    def test_typing_alias_mixed_import_rejects_repeated_bound_names(
        self,
        tmp_path: Path,
        *,
        moved_first: bool,
    ) -> None:
        """Reject bindings whose order cannot survive native import normalization."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        self._write_file(source_file, "type Alias = str\nvalue = bytes\n")
        names = (
            "Alias as Bound, value as Bound"
            if moved_first
            else "value as Bound, Alias as Bound"
        )
        self._write_file(
            package_root / "consumer.py",
            f"from .service import {names}\nPublished = Bound\n",
        )

        originals = {
            path: path.read_bytes()
            for path in (source_file, package_root / "consumer.py")
        }
        with pytest.raises(RuntimeError, match="conflicting Rope imported binding"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
            )
        for path, original in originals.items():
            tm.that(path.read_bytes(), eq=original)
        tm.that((package_root / "typings.py").exists(), eq=False)

        expected = "service.value" if moved_first else "service.Alias"
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, service\n"
                f"print(consumer.Published is {expected})\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"],
        )

    @pytest.mark.parametrize("existing_target", [False, True])
    @pytest.mark.parametrize(
        "consumer_source",
        [
            "import demo_pkg.service as module\nPublished = module.Alias\n",
            "import demo_pkg.service\nPublished = demo_pkg.service.Alias\n",
            "from demo_pkg import service as module\nPublished = module.Alias\n",
            "from . import service\nPublished = service.Alias\n",
            "from .service import *\nPublished = Alias\n",
            "if True:\n    from .service import *\nPublished = Alias\n",
            (
                "def scoped():\n"
                "    import demo_pkg.service as module\n"
                "    return module.Alias\n"
            ),
            (
                "from . import service\n"
                "def consume(value: 'service.Alias'):\n"
                "    return value\n"
            ),
            (
                "from . import service\n"
                "def produce() -> 'service.Alias':\n"
                "    return 'value'\n"
            ),
        ],
    )
    def test_unsupported_typing_alias_consumers_reject_before_publication(
        self,
        tmp_path: Path,
        consumer_source: str,
        *,
        existing_target: bool,
    ) -> None:
        """Unsupported identities leave consumers, declarations and absence intact."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        typings_file = package_root / "typings.py"
        originals = {
            source_file: "type Alias = str\n",
            package_root / "consumer.py": consumer_source,
            package_root / "supported.py": (
                "from .service import Alias\nPublished = Alias\n"
            ),
        }
        if existing_target:
            originals[typings_file] = "from __future__ import annotations\n"
        for path, source in originals.items():
            self._write_file(path, source)

        with pytest.raises(RuntimeError, match="unsupported Rope"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
            )

        for path, source in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(typings_file.exists(), eq=existing_target)

    @pytest.mark.parametrize("existing_target", [False, True])
    @pytest.mark.parametrize(
        "mutation",
        [
            "__all__.append('Alias')",
            "__all__.extend(['Alias'])",
            "__all__ += ['Alias']",
        ],
    )
    def test_mutated_star_exports_reject_before_typing_alias_publication(
        self,
        tmp_path: Path,
        mutation: str,
        *,
        existing_target: bool,
    ) -> None:
        """A mutable export list never proves a selected binding is excluded."""
        root, package = self._build_project(tmp_path)
        source = package / "service.py"
        destination = package / "typings.py"
        originals = {
            source: (
                f"type Alias = str\nvalue = bytes\n__all__ = ['value']\n{mutation}\n"
            ),
            package / "consumer.py": "from .service import *\nPublished = Alias\n",
        }
        if existing_target:
            originals[destination] = "from __future__ import annotations\n"
        for path, content in originals.items():
            self._write_file(path, content)
        with pytest.raises(RuntimeError, match="unsupported Rope"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=root,
                names_by_file={source: {"Alias"}},
            )
        for path, original in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=original)
        tm.that(destination.exists(), eq=existing_target)

    @pytest.mark.parametrize("scoped", [False, True])
    def test_relative_target_binding_conflict_rejects_typing_alias_cutover(
        self,
        tmp_path: Path,
        *,
        scoped: bool,
    ) -> None:
        """Relative target imports participate in same-scope collision checks."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        imports = (
            "from .typings import Existing as Alias\n"
            "from .service import Alias\n"
            "Published = Alias\n"
        )
        consumer = (
            "def scoped():\n"
            + "".join(f"    {line}\n" for line in imports.splitlines())
            if scoped
            else imports
        )
        originals = {
            source_file: "type Alias = str\n",
            package_root / "typings.py": "type Existing = bytes\n",
            package_root / "consumer.py": consumer,
        }
        for path, source in originals.items():
            self._write_file(path, source)

        with pytest.raises(RuntimeError, match="ambiguous Rope target binding"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
            )

        for path, source in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
