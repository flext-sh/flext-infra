"""Public utility evidence for the facade-base semantic cutover.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFacadeBaseCutover:
    """Exercise the facade-base phase only through ``u.Infra``.

    The canonical facade extends the upstream family letter
    (``from parent_pkg import m``; ``class ChildModels(m)``). A declared
    class-name alias is projected back to that letter; a secondary upstream
    facade class on a double composition is preserved.
    """

    PARENT_CLASS = "ParentDeclaredModelFacade"
    OTHER_CLASS = "OtherDeclaredModelFacade"

    @staticmethod
    def _lazy_publication(submodule: str, *names: str) -> str:
        """Render the lazy publication a generated package ``__init__`` carries.

        Generated initializers publish every name through one
        ``install_lazy_exports(__name__, globals(), MappingProxyType({...}))``
        call mapping each name to its provider submodule.

        Returns:
            The publication statements for ``names``.

        """
        entries = "".join(f'        "{name}": "{submodule}",\n' for name in names)
        return (
            "from types import MappingProxyType\n"
            "from flext_core.lazy import install_lazy_exports\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    MappingProxyType({\n"
            f"{entries}"
            "    }),\n"
            ")\n"
        )

    def test_class_name_alias_base_becomes_the_family_letter(
        self,
        tmp_path: Path,
    ) -> None:
        """A declared class-name alias is projected to the upstream letter."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import ParentDeclaredModelFacade as m\n\n\n"
            "class ChildModels(m):\n    pass\n\n\n"
            "m = ChildModels\n",
        )
        edits = self._edits(tmp_path, sources, child)
        tm.that(tuple(edit.file_path for edit in edits), eq=(child.resolve(),))
        updated = edits[0].updated_source
        tm.that(updated, has="from parent_pkg import m\n")
        tm.that(updated, has="class ChildModels(m):")
        tm.that(updated, has="\nm = ChildModels\n")
        tm.that(updated, lacks=self.PARENT_CLASS)
        tm.that(edits[0].changes, eq=("closed facade import and composition laws",))
        replanned = self._edits(tmp_path, {**sources, child: updated}, child)
        tm.that(replanned, empty=True)

    def test_bare_letter_base_is_already_canonical(self, tmp_path: Path) -> None:
        """A facade already extending the letter needs no cutover."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import m\n\n\nclass ChildModels(m):\n    pass\n\n\n"
            "m = ChildModels\n",
        )
        tm.that(self._edits(tmp_path, sources, child), empty=True)

    def test_double_composition_keeps_the_secondary_parent(
        self,
        tmp_path: Path,
    ) -> None:
        """The primary alias becomes the letter; the secondary class stays."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import ParentDeclaredModelFacade as m\n"
            "from other_pkg import FlextOtherModels\n\n\n"
            "class ChildModels(m, FlextOtherModels):\n    pass\n\n\n"
            "m = ChildModels\n",
        )
        other = tmp_path / "other/src/other_pkg"
        sources[other / "__init__.py"] = (
            "from other_pkg.models import FlextOtherModels\n"
            "__all__ = ['FlextOtherModels']\n"
        )
        sources[other / "models.py"] = (
            "class FlextOtherModels:\n    pass\n__all__ = ['FlextOtherModels']\n"
        )
        updated = self._edits(tmp_path, sources, child)[0].updated_source
        tm.that(updated, has="from parent_pkg import m\n")
        tm.that(updated, has="from other_pkg import FlextOtherModels\n")
        tm.that(updated, has="class ChildModels(m, FlextOtherModels):")
        tm.that(updated, lacks=self.PARENT_CLASS)
        replanned = self._edits(tmp_path, {**sources, child: updated}, child)
        tm.that(replanned, empty=True)

    def test_eager_reads_keep_the_letter_binding(self, tmp_path: Path) -> None:
        """Eager letter reads stay on the rebound letter, never the class name."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import ParentDeclaredModelFacade as m\n\n\n"
            "class ChildModels(m):\n"
            "    base = m.BaseModel\n\n"
            "    def later(self) -> object:\n        return m.BaseModel\n\n\n"
            "m = ChildModels\n",
        )
        updated = self._edits(tmp_path, sources, child)[0].updated_source
        tm.that(updated, has="from parent_pkg import m\n")
        tm.that(updated, has="class ChildModels(m):")
        tm.that(updated, has="    base = m.BaseModel\n")
        tm.that(updated, has="        return m.BaseModel\n")
        tm.that(updated, lacks=self.PARENT_CLASS)

    def test_lazy_published_letter_resolves_the_declared_class(
        self,
        tmp_path: Path,
    ) -> None:
        """The generated lazy map alone elects the declared parent owner."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import ParentDeclaredModelFacade as m\n\n\n"
            "class ChildModels(m):\n    pass\n\n\n"
            "m = ChildModels\n",
        )
        sources[tmp_path / "parent/src/parent_pkg/__init__.py"] = (
            f"__all__ = [{self.PARENT_CLASS!r}, 'm']\n"
            f"{self._lazy_publication('.models', self.PARENT_CLASS, 'm')}"
        )
        updated = self._edits(tmp_path, sources, child)[0].updated_source
        tm.that(updated, has="from parent_pkg import m\n")
        tm.that(updated, has="class ChildModels(m):")
        tm.that(updated, lacks=self.PARENT_CLASS)

    def test_undeclared_letter_owner_fails_the_plan(self, tmp_path: Path) -> None:
        """An owner the parent does not publish fails loud."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import m\n\n\nclass ChildModels(m):\n    pass\n\n\n"
            "m = ChildModels\n",
            parent_exports=(self.PARENT_CLASS,),
        )
        with pytest.raises(ValueError, match="is not declared"):
            self._plan(tmp_path, sources, child)

    def test_annotation_without_value_keeps_the_letter_base(
        self,
        tmp_path: Path,
    ) -> None:
        """A later annotation leaves the runtime letter binding intact."""
        child, sources = self._workspace(
            tmp_path,
            "from parent_pkg import ParentDeclaredModelFacade as m\n\n\n"
            "class ChildModels(m):\n    pass\n\n\n"
            "m = ChildModels\n",
        )
        parent = tmp_path / "parent/src/parent_pkg/models.py"
        sources[parent] += f"m: type[{self.PARENT_CLASS}]\n"
        updated = self._edits(tmp_path, sources, child)[0].updated_source
        tm.that(updated, has="from parent_pkg import m\n")
        tm.that(updated, has="class ChildModels(m):")
        tm.that(updated, lacks=self.PARENT_CLASS)

    def test_facade_classes_derive_every_published_letter(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Test facade classes derive every published letter."""
        _child, sources = self._workspace(tmp_path, "")
        for path, source in sources.items():
            if "parent_pkg" in path.parts:
                relative = path.relative_to(tmp_path / "parent/src")
                target = installed_dependency_path / c.Infra.DEFAULT_SRC_DIR / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Infra.facade_classes(
                "parent_pkg",
                source_root=installed_dependency_path,
            ),
            eq={"m": self.PARENT_CLASS},
        )

    @c.Tests.MARK.parametrize("consumer", ["workspace", "member"])
    def test_facade_classes_read_a_declared_sibling_without_installation(
        self,
        tmp_path: Path,
        consumer: str,
    ) -> None:
        """Derive the parent contract from the declared workspace source graph."""
        child, sources = self._workspace(tmp_path, "")
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        (tmp_path / ".gitmodules").write_text(
            '[submodule "parent"]\npath = parent\n'
            "url = https://example.org/parent.git\n"
            '[submodule "child"]\npath = child\n'
            "url = https://example.org/child.git\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            u.Infra.facade_classes(
                "parent_pkg",
                source_root=tmp_path if consumer == "workspace" else child.parents[2],
            ),
            eq={"m": self.PARENT_CLASS},
        )

    @c.Tests.MARK.parametrize(
        ("guard_import", "guard"),
        [
            ("from typing import TYPE_CHECKING", "TYPE_CHECKING"),
            ("import typing", "typing.TYPE_CHECKING"),
            ("import typing_extensions", "typing_extensions.TYPE_CHECKING"),
        ],
    )
    def test_type_only_self_import_does_not_override_lazy_publication(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        guard_import: str,
        guard: str,
    ) -> None:
        """Static self-imports do not create runtime facade binding cycles."""
        _child, sources = self._workspace(tmp_path, "")
        parent = tmp_path / "parent/src/parent_pkg"
        sources[parent / "__init__.py"] = (
            f"{guard_import}\n"
            f"{self._lazy_publication('.models', self.PARENT_CLASS, 'm')}"
            f"if {guard}:\n"
            f"    from parent_pkg import {self.PARENT_CLASS}, m\n"
            f"__all__ = [{self.PARENT_CLASS!r}, 'm']\n"
        )
        for path, source in sources.items():
            if "parent_pkg" in path.parts:
                target = (
                    installed_dependency_path
                    / c.Infra.DEFAULT_SRC_DIR
                    / path.relative_to(tmp_path / "parent/src")
                )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source, encoding=c.DEFAULT_ENCODING)

        tm.that(
            u.Infra.facade_classes(
                "parent_pkg",
                source_root=installed_dependency_path,
            ),
            eq={"m": self.PARENT_CLASS},
        )

    def _workspace(
        self,
        tmp_path: Path,
        child_source: str,
        *,
        parent_exports: Sequence[str] = (),
    ) -> tuple[Path, MutableMapping[Path, str]]:
        """Declare a parent whose class name no package naming could infer.

        Returns:
            The resulting ``tuple[Path, MutableMapping[Path, str]]``.

        """
        exports = parent_exports or (self.PARENT_CLASS, "m")
        parent = tmp_path / "parent/src/parent_pkg"
        child = tmp_path / "child/src/child_pkg/models.py"
        return child, {
            parent / "__init__.py": (
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                f"    from .models import {self.PARENT_CLASS}, m\n"
                f"{self._lazy_publication('.models', self.PARENT_CLASS, 'm')}"
                f"__all__ = [{self.PARENT_CLASS!r}, 'm']\n"
            ),
            parent / "models.py": (
                "from base_pkg import m\n"
                f"class {self.PARENT_CLASS}(m):\n    pass\n"
                f"m = {self.PARENT_CLASS}\n"
                f"__all__ = {list(exports)!r}\n"
            ),
            child: child_source,
        }

    @staticmethod
    def _finding(file_path: Path) -> p.Infra.ModOccurrence:
        """Build one detector finding for the facade module.

        Returns:
            The resulting ``m.Infra.ModOccurrence``.

        """
        return m.Infra.ModOccurrence(
            rule_file="namespace-structure.yml",
            rule_id="require-facade-mro-completeness",
            repository="child",
            file=file_path,
            range={},
            text="m = ChildModels",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

    @classmethod
    def _plan(
        cls,
        tmp_path: Path,
        sources: Mapping[Path, str],
        child: Path,
    ) -> p.ResultView[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan the facade-base phase for the detector finding in ``child``.

        Returns:
            The originating immutable result view of semantic migration edits.

        """
        u.Tests.declare_workspace_projects(tmp_path, ("parent", "child"))
        u.Tests.initialize_git_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test-root"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        root_package = tmp_path / "src" / "test_root"
        root_package.mkdir(parents=True, exist_ok=True)
        (root_package / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(tmp_path) as rope:
            return u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.FACADE_BASE,
                rope_workspace=rope,
                sources=sources,
                findings=(cls._finding(child.relative_to(tmp_path)),),
            )

    @classmethod
    def _edits(
        cls,
        tmp_path: Path,
        sources: Mapping[Path, str],
        child: Path,
    ) -> tuple[p.Infra.SemanticMigrationEdit, ...]:
        """Return the successful plan's edits.

        Returns:
            The successful plan's edits.

        """
        planned = cls._plan(tmp_path, sources, child)
        tm.ok(planned)
        return planned.value
