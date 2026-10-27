"""Observable recursive family generation through the public source owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
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
    def test_selected_family_retains_authored_child_composition(
        cls, tmp_path: Path
    ) -> None:
        """Move a declared holder without deriving a replacement name or other families."""
        root, package, sentinel = cls._workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(root))
        directory = package / "_utilities" / "_dispatch"
        name = f"{layout.class_stem}DispatchUtilities"
        supplier = f"{layout.class_stem}DispatchRunner"
        cls._write(directory / c.Infra.INIT_PY, '"""Dispatch capabilities."""\n')
        cls._write(directory / "runner.py", cls._part(supplier, "u", "Execute"))
        origin = directory / "namespace.py"
        cls._write(
            origin,
            '"""Authored dispatch composition."""\n'
            f"from {package.name}._utilities._dispatch.runner import {supplier}\n"
            f"class {name}:\n"
            f"    {supplier} = {supplier}\n"
            f"__all__ = [{name!r}]\n",
        )
        destination = package / "utilities.py"
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
            existing,
            '"""Existing domain composition."""\n'
            f"from {package.name}.{family.directory}._domain.base import {base}\n"
            f"class ExistingDomainFacade({base}):\n"
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
