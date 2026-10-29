"""Observable recursive family generation through the public source owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenLazyInit
from tests import c, m, p, tm, u


class TestsFlextInfraRecursiveFamilyFacades:
    """Keep recursive compositions typed, importable and idempotent."""

    @staticmethod
    def _write(path: Path, source: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding=c.DEFAULT_ENCODING)

    @classmethod
    def _workspace(cls, tmp_path: Path) -> tuple[Path, Path, Path]:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(root))
        sentinel = root / "provider-imported"
        cls._write(
            package / "inaccessible_provider.py",
            "from pathlib import Path\n"
            f"Path({str(sentinel)!r}).write_text('imported')\n"
            "raise RuntimeError('Target provider must not be imported')\n",
        )
        for letter, family in u.Infra.facade_families().items():
            owners = package / family.directory
            declaration = f"{layout.class_stem}{family.suffix}"
            root_owner = f"{declaration}RootOwner"
            cls._write(
                owners / "base.py",
                cls._part(root_owner, letter, "Existing"),
            )
            cls._write(
                package / f"{family.module}.py",
                '"""Public family fixture."""\n'
                f"from {package.name}.{family.directory}.base import {root_owner}\n"
                f"class {declaration}:\n"
                f"    class Domain({root_owner}):\n"
                '        """Public domain namespace."""\n'
                f"{letter} = {declaration}\n"
                f"__all__ = [{declaration!r}, {letter!r}]\n",
            )
            cls._write(
                owners / "_domain" / "base.py",
                cls._part(f"{declaration}DomainBase", letter, "Anchor"),
            )
            for name in ("Left", "Right"):
                cls._write(
                    owners / "_domain" / "_nested" / f"{name.lower()}.py",
                    cls._part(
                        f"{declaration}DomainNested{name}Owner",
                        letter,
                        name,
                        package=package.name,
                    ),
                )
        cls._write(
            package / "consumer.py",
            "from __future__ import annotations\n"
            f"from {package.name} import p\n"
            "def deliver(left: p.Domain.Left, right: p.Domain.Right) -> str:\n"
            "    return left.deliver() + right.deliver()\n",
        )
        return root, package, sentinel

    @staticmethod
    def _part(owner: str, family: str, name: str, *, package: str | None = None) -> str:
        header = (
            '"""Declared family behavior and typed entities."""\n'
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING, ClassVar, Protocol\n"
            "from pydantic import BaseModel\n"
        )
        if package is not None:
            header += (
                f"if TYPE_CHECKING:\n    from {package} import inaccessible_provider\n"
            )
        members = {
            "c": f"    {name.upper()}: ClassVar[str] = {name.lower()!r}\n",
            "t": f"    type {name} = str\n",
            "p": (
                f"    class {name}(Protocol):\n        def deliver(self) -> str: ...\n"
            ),
            "m": (f"    class {name}(BaseModel):\n        value: str\n"),
            "u": (
                "    @classmethod\n"
                f"    def {name.lower()}(cls) -> str:\n"
                f"        return {name.lower()!r}\n"
            ),
        }
        return f"{header}\nclass {owner}:\n{members[family]}\n__all__ = [{owner!r}]\n"

    @staticmethod
    def _plans(
        root: Path,
        selection: tuple[Path, c.Infra.FacadeFamily] | None = None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            initial = FlextInfraCodegenLazyInit.plan_candidate(
                root, declared_files=(), snapshot=snapshot, selection=selection
            )
            if initial.failure:
                return initial
            return u.Infra.plan_component_facades(
                root,
                declared_files=initial.value,
                snapshot=snapshot,
                planners=(
                    FlextInfraCodegenLazyInit.plan_candidate,
                    u.Infra.facade_source_project,
                ),
                selection=selection,
            )

    @classmethod
    def test_uncomposed_type_publications_do_not_elect_a_holder(
        cls, tmp_path: Path
    ) -> None:
        """Ordinary class publications need a public MRO before composition election."""
        root, package, sentinel = cls._workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(root))
        directory = package / "_utilities" / "_dispatch"
        supplier = f"{layout.class_stem}DispatchRunner"
        name = f"{layout.class_stem}DispatchUtilities"
        cls._write(directory / c.Infra.INIT_PY, '"""Dispatch declarations."""\n')
        cls._write(directory / "runner.py", cls._part(supplier, "u", "Execute"))
        cls._write(
            directory / "namespace.py",
            f"from {package.name}._utilities._dispatch.runner import {supplier}\n"
            f"class {name}:\n"
            f"    {supplier} = {supplier}\n"
            f"__all__ = [{name!r}]\n",
        )
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            tm.that(u.Infra.family_subfacade_owners(snapshot.engine, directory), eq=[])
        tm.fail(sentinel.exists())

    @classmethod
    def _write_selected_composition(cls, root: Path, package: Path) -> tuple[str, str]:
        """Declare a published composition with behavior and a stateful helper.

        Returns:
            The authored composition and method-provider class names.

        """
        layout = tm.not_none(u.Infra.layout(root))
        directory = package / "_utilities" / "_dispatch"
        name = f"{layout.class_stem}DispatchUtilities"
        supplier = f"{layout.class_stem}DispatchRunner"
        stateful = f"{layout.class_stem}DispatchState"
        cls._write(directory / c.Infra.INIT_PY, '"""Dispatch capabilities."""\n')
        cls._write(directory / "runner.py", cls._part(supplier, "u", "Execute"))
        cls._write(
            directory / "stateful.py",
            f"class {stateful}:\n"
            "    def __init__(self, value: str) -> None:\n"
            "        self.value = value\n"
            f"__all__ = [{stateful!r}]\n",
        )
        origin = directory / "namespace.py"
        cls._write(
            origin,
            '"""Authored dispatch composition."""\n'
            f"from {package.name}._utilities._dispatch.runner import {supplier}\n"
            f"from {package.name}._utilities._dispatch.stateful import {stateful}\n"
            f"class {name}:\n"
            f"    {supplier} = {supplier}\n"
            f"    Stateful = {stateful}\n"
            f"__all__ = [{name!r}]\n",
        )
        destination = package / "utilities.py"
        declaration = f"{layout.class_stem}{u.Infra.facade_families()['u'].suffix}"
        root_owner = f"{declaration}RootOwner"
        cls._write(
            package / "_utilities" / c.Infra.INIT_PY,
            f"{c.Infra.AUTOGEN_HEADER}\n"
            f"from {package.name}._utilities._dispatch.namespace import {name}\n"
            f"from {package.name}._utilities.base import {root_owner}\n"
            f"__all__ = [{name!r}, {root_owner!r}]\n",
        )
        cls._write(
            destination,
            '"""Public composition authenticates its authored child holder."""\n'
            f"from {package.name}._utilities import {root_owner}, {name}\n"
            f"class {declaration}:\n"
            f"    class Domain({root_owner}, {name}):\n"
            '        """Public dispatch namespace."""\n'
            f"u = {declaration}\n"
            f"__all__ = [{declaration!r}, 'u']\n",
        )
        cls._write(
            package / c.Infra.INIT_PY,
            (package / c.Infra.INIT_PY).read_text(encoding=c.DEFAULT_ENCODING)
            + f"\nfrom {package.name}.utilities import {declaration}, u\n"
            + f"__all__ = ['r', {declaration!r}, 'u']\n",
        )
        consumer = package / "dispatch_consumer.py"
        cls._write(
            consumer,
            f"from {package.name} import u\n"
            "def dispatch() -> str:\n"
            f"    callback = u.Domain.{supplier}.execute\n"
            f"    return callback() + u.Domain.{supplier}.execute() + "
            f"u.Domain.{supplier}.execute()\n",
        )
        return name, supplier

    @staticmethod
    def _publication_names(namespace: ast.ClassDef) -> set[str]:
        """Observe the names assigned by the candidate's class-publication syntax.

        Returns:
            Assignment, annotated-assignment and native type-alias target names.

        """
        names: set[str] = set()
        for member in namespace.body:
            if isinstance(member, ast.Assign):
                names.update(
                    target.id
                    for target in member.targets
                    if isinstance(target, ast.Name)
                )
            elif isinstance(member, ast.AnnAssign) and isinstance(
                member.target, ast.Name
            ):
                names.add(member.target.id)
            elif isinstance(member, ast.TypeAlias) and isinstance(
                member.name, ast.Name
            ):
                names.add(member.name.id)
        return names

    @classmethod
    def test_initializer_projection_keeps_observed_composition_ownership(
        cls, tmp_path: Path
    ) -> None:
        """Move an observed owner even when pending exports hide its old route."""
        root, package, sentinel = cls._workspace(tmp_path)
        name, _supplier = cls._write_selected_composition(root, package)
        destination = package / "utilities.py"
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            initial = tm.ok(
                FlextInfraCodegenLazyInit.plan_candidate(
                    root,
                    declared_files=(),
                    snapshot=snapshot,
                    selection=(destination, c.Infra.FacadeFamily.U),
                )
            )
            with u.Infra.facade_source_project(root, declared_files=initial) as binding:
                namespace = u.Infra.require_class_object(
                    u.Infra
                    .facade_source_classes(
                        package.name, ("u",), source_project=binding[0]
                    )["u"]
                    .get_attributes()["Domain"]
                    .get_object(),
                    "projected public namespace",
                )
                tm.that(
                    any(
                        not u.Infra.abstract_class(base)
                        for base in namespace.get_superclasses()
                    )
                )
            planned = tm.ok(
                u.Infra.plan_component_facades(
                    root,
                    declared_files=initial,
                    snapshot=snapshot,
                    planners=(
                        FlextInfraCodegenLazyInit.plan_candidate,
                        u.Infra.facade_source_project,
                    ),
                    selection=(destination, c.Infra.FacadeFamily.U),
                )
            )
            repeated = tm.ok(
                u.Infra.plan_component_facades(
                    root,
                    declared_files=planned,
                    snapshot=snapshot,
                    planners=(
                        FlextInfraCodegenLazyInit.plan_candidate,
                        u.Infra.facade_source_project,
                    ),
                    selection=(destination, c.Infra.FacadeFamily.U),
                )
            )
            tm.that(
                {plan.path: (plan.before, plan.desired_content) for plan in repeated},
                eq={plan.path: (plan.before, plan.desired_content) for plan in planned},
            )
        tm.that(
            any(
                plan.path == package / "_utilities" / "dispatch.py"
                and plan.desired_content is not None
                and f"class {name}(".encode() in plan.desired_content
                for plan in planned
            )
        )
        tm.fail(sentinel.exists())

    @classmethod
    def test_unresolved_observed_provider_is_rejected(cls, tmp_path: Path) -> None:
        """An unresolved input provider never becomes an accepted native owner."""
        root, package, sentinel = cls._workspace(tmp_path)
        name, _supplier = cls._write_selected_composition(root, package)
        destination = package / "utilities.py"
        cls._write(
            destination,
            destination.read_text(encoding=c.DEFAULT_ENCODING).replace(
                f", {name}):", ", UnresolvedProvider):"
            ),
        )
        with pytest.raises(TypeError, match="expected a native Rope class:"):
            cls._plans(root, (destination, c.Infra.FacadeFamily.U))
        tm.fail(sentinel.exists())

    @classmethod
    def test_selected_family_retains_authored_child_composition(
        cls, tmp_path: Path
    ) -> None:
        """Keep the authored MRO alias-free and close its callable consumers."""
        root, package, sentinel = cls._workspace(tmp_path)
        name, supplier = cls._write_selected_composition(root, package)
        origin = package / "_utilities" / "_dispatch" / "namespace.py"
        destination = package / "utilities.py"
        consumer = package / "dispatch_consumer.py"
        planned = {
            plan.path: plan
            for plan in tm.ok(cls._plans(root, (destination, c.Infra.FacadeFamily.U)))
        }
        sibling = package / "_utilities" / "dispatch.py"
        tm.that(sibling in planned and destination in planned)
        tm.that(planned[origin].desired_content is None)
        tm.that(planned[sibling].before.content is None)
        tm.that(planned[origin].before.content, eq=origin.read_bytes())
        tm.that(
            f"class {name}(".encode() in tm.not_none(planned[sibling].desired_content)
        )
        candidate = tm.not_none(planned[sibling].desired_content).decode(
            c.DEFAULT_ENCODING
        )
        namespace = next(
            node
            for node in ast.parse(candidate).body
            if isinstance(node, ast.ClassDef) and node.name == name
        )
        publications = cls._publication_names(namespace)
        tm.fail(supplier in publications)
        tm.that("Stateful" in publications)
        tm.that(b"u.Domain.execute()" in tm.not_none(planned[consumer].desired_content))
        tm.that(
            b"callback = u.Domain.execute"
            in tm.not_none(planned[consumer].desired_content)
        )
        tm.fail(
            f"u.Domain.{supplier}.".encode()
            in tm.not_none(planned[consumer].desired_content)
        )
        tm.that(planned[consumer].before.content, eq=consumer.read_bytes())
        for family in u.Infra.facade_families().values():
            if family.letter != "u":
                tm.fail(package / f"{family.module}.py" in planned)
                tm.fail(
                    any(
                        path.is_relative_to(package / family.directory)
                        for path in planned
                    )
                )
        tm.fail(package / "_utilities" / "base.py" in planned)
        tm.fail(sentinel.exists())

    @classmethod
    def test_provider_mutations_reject_the_public_candidate(
        cls, tmp_path: Path
    ) -> None:
        """Reject each unsafe mutation without publishing or retargeting its owner."""
        root, package, sentinel = cls._workspace(tmp_path)
        _name, supplier = cls._write_selected_composition(root, package)
        consumer = package / "dispatch_consumer.py"
        destination = package / "utilities.py"
        original = consumer.read_text(encoding=c.DEFAULT_ENCODING)
        reference = f"u.Domain.{supplier}.execute"
        for statement in (
            f"{reference} = callback",
            f"del {reference}",
            f"{reference} += callback",
        ):
            mutated = (
                original
                + "\ndef mutations():\n"
                + f"    callback = {reference}\n    {statement}\n"
            )
            cls._write(consumer, mutated)
            with pytest.raises(
                (TypeError, ValueError),
                match=(
                    r"expected a native Rope class: facade component ancestry"
                    r"|provider publication has a surviving consumer:"
                ),
            ):
                cls._plans(root, (destination, c.Infra.FacadeFamily.U))
            tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=mutated)
        tm.fail(sentinel.exists())

    @staticmethod
    def test_planned_source_views_observe_changes_and_retirement(
        tmp_path: Path,
    ) -> None:
        """Read proposed bytes and tombstones without mutating the live source."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / c.Infra.INIT_PY
        physical = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        first = tm.ok(FlextInfraCodegenConform.Generate.file_plan(root, relative, "\n"))
        changed = tm.ok(
            FlextInfraCodegenConform.Generate.file_plan(root, relative, "\n\n")
        )
        retired = m.Infra.CodegenFilePlan(
            project=root,
            path=path,
            before=tm.ok(u.Infra.codegen_target_snapshot(path)),
            desired_content=None,
            desired_mode=None,
        )
        with (
            u.Infra.facade_source_project(root, declared_files=(first,)) as one,
            u.Infra.facade_source_project(root, declared_files=(changed,)) as two,
            u.Infra.facade_source_project(root, declared_files=(retired,)) as gone,
        ):
            tm.that(one[0].source_bytes(path), eq=first.desired_content)
            tm.that(two[0].source_bytes(path), eq=changed.desired_content)
            tm.fail(gone[0].source_query(path, "exists"))
            tm.fail(path in gone[1])
            tm.that(one[0].source_state(path), eq=first.before)
        tm.that(path.read_bytes(), eq=physical)

    @staticmethod
    def test_source_views_keep_each_repository_source_authority(tmp_path: Path) -> None:
        """Read each declared root's bytes without importing another root's sources."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        other, other_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-other-project",
            package_name="flext_other_project",
        )
        first_path = package / c.Infra.INIT_PY
        other_path = other_package / c.Infra.INIT_PY
        first_path.write_text("IDENTITY = 'first-root'\n", encoding=c.DEFAULT_ENCODING)
        other_path.write_text("IDENTITY = 'other-root'\n", encoding=c.DEFAULT_ENCODING)
        with (
            u.Infra.facade_source_project(root) as one,
            u.Infra.facade_source_project(other) as two,
        ):
            tm.that(Path(one[0].root.real_path), eq=root)
            tm.that(Path(two[0].root.real_path), eq=other)
            tm.that(one[0].source_bytes(first_path), eq=first_path.read_bytes())
            tm.that(two[0].source_bytes(other_path), eq=other_path.read_bytes())
            tm.fail(other_path in one[1])
            tm.fail(first_path in two[1])

    @classmethod
    def test_all_families_publish_two_recursive_levels_in_one_cohort(
        cls, tmp_path: Path
    ) -> None:
        """Test all families publish two recursive levels in one cohort."""
        root, package, sentinel = cls._workspace(tmp_path)
        plans = tm.ok(cls._plans(root))
        tm.ok(u.Infra.publish_codegen_plans(root, plans))
        for family in u.Infra.facade_families().values():
            tm.ok((package / family.directory / "domain.py").is_file())
            tm.ok((package / family.directory / "_domain" / "nested.py").is_file())
        tm.fail(sentinel.exists())
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import c, t, p, m, u\n"
                "print(c.Domain.LEFT + c.Domain.RIGHT)\n"
                "print(t.Domain.Left.__value__ is str)\n"
                "class Left(p.Domain.Left):\n"
                "    def deliver(self) -> str: return 'left'\n"
                "class Right(p.Domain.Right):\n"
                "    def deliver(self) -> str: return 'right'\n"
                "print(Left().deliver() + Right().deliver())\n"
                "print(m.Domain.Left(value='left').value)\n"
                "print(u.Domain.left() + u.Domain.right())\n",
                python_paths=(str(package.parent),),
            ),
            eq=["leftright", "True", "leftright", "left", "leftright"],
        )
        tm.fail(sentinel.exists())
        second = tm.ok(cls._plans(root))
        tm.that(u.Cli.pending_file_changes(second), eq=())
        tm.that(tm.ok(u.Infra.publish_codegen_plans(root, second)), eq=())

    @classmethod
    def test_ambiguous_recursive_owner_fails_before_publication(
        cls, tmp_path: Path
    ) -> None:
        """Test ambiguous recursive owner fails before publication."""
        root, package, _sentinel = cls._workspace(tmp_path)
        family = u.Infra.facade_families()["u"]
        nested = package / family.directory / "_domain" / "_nested"
        for name in ("left", "right"):
            cls._write(
                nested / f"{name}.py",
                cls._part("CompetingOwner", "u", name.title()),
            )
        before = {path: path.read_bytes() for path in root.rglob("*.py")}
        tm.fail(cls._plans(root), has="ambiguous")
        tm.that(
            {path: path.read_bytes() for path in root.rglob("*.py")},
            eq=before,
        )

    @classmethod
    def test_existing_composition_moves_to_its_canonical_sibling(
        cls, tmp_path: Path
    ) -> None:
        """Retain the existing class identity while correcting its module route."""
        root, package, sentinel = cls._workspace(tmp_path)
        family = u.Infra.facade_families()["u"]
        layout = tm.not_none(u.Infra.layout(root))
        owners = package / family.directory
        existing = owners / "legacy_domain.py"
        base = f"{layout.class_stem}{family.suffix}DomainBase"
        cls._write(
            owners / "_domain" / "bridge.py",
            '"""Intermediate inherited domain composition."""\n'
            f"from {package.name}.{family.directory}._domain.base import {base}\n"
            f"class IntermediateHolder({base}):\n"
            '    """Retain the inherited behavior."""\n'
            "__all__ = ['IntermediateHolder']\n",
        )
        cls._write(
            existing,
            '"""Existing domain composition."""\n'
            f"from {package.name}.{family.directory}._domain.bridge "
            "import IntermediateHolder\n"
            "class ExistingDomainFacade(IntermediateHolder):\n"
            '    """Inherited domain behavior."""\n'
            "__all__ = ['ExistingDomainFacade']\n",
        )
        plans = tm.ok(cls._plans(root))
        tm.ok(u.Infra.publish_codegen_plans(root, plans))
        tm.fail(existing.exists())
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.{family.directory}.domain "
                "import ExistingDomainFacade\n"
                "print(ExistingDomainFacade.anchor())\n",
                python_paths=(str(package.parent),),
            ),
            eq=["anchor"],
        )
        tm.fail(sentinel.exists())
        second = tm.ok(cls._plans(root))
        tm.that(u.Cli.pending_file_changes(second), eq=())
        tm.that(tm.ok(u.Infra.publish_codegen_plans(root, second)), eq=())
