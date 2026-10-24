"""Public planning contracts for immutable Rope family flattening.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m, t


class TestsFlextInfraFamilyFlatten:
    """Exercise the real module graph, not mocked semantic identities."""

    @dataclasses.dataclass(frozen=True)
    class ComposedFacadeFixture:
        """The seeded wrapper, composed facade, consumer, and their sources."""

        root: Path
        path: Path
        facade_path: Path
        consumer: Path
        source: str
        facade: str
        references: str
        project: str

    @dataclasses.dataclass(frozen=True)
    class WrapperFamilyFixture:
        """The seeded wrapper family and every source its consumers declare."""

        root: Path
        path: Path
        consumer: Path
        homonym: Path
        source: str
        references: str
        unrelated: str

    @staticmethod
    def _payload(
        tmp_path: Path,
        facade_py: str = c.Infra.MODELS_PY,
    ) -> tuple[Path, Path, str, Path, str]:
        """Seed one workspace with an empty facade family and its payload path.

        Returns:
            The root, package, family directory name, payload path and owner name.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = u.Infra.facade_family_declared_by(facade_py).directory
        family = package / directory
        family.mkdir()
        (family / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        owner = (
            f"{u.derive_class_stem(root.name)}{facade_py.removesuffix('.py').title()}"
            "Payload"
        )
        return root, package, directory, family / "payload.py", owner

    @staticmethod
    def _plan(
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Plan the class-nesting cutover over the given sources.

        Returns:
            The planned file edits.

        """
        with infra.rope_workspace(root) as rope:
            return tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )

    @staticmethod
    def _apply(
        sources: t.MappingKV[Path, str],
        edits: t.VariadicTuple[m.Infra.SemanticMigrationEdit],
    ) -> t.MutableMappingKV[Path, str]:
        """Overlay planned edits on the sources without touching the disk.

        Returns:
            The proposed post-edit sources.

        """
        proposed = dict(sources)
        proposed.update({edit.file_path: edit.updated_source for edit in edits})
        return proposed

    @staticmethod
    def _unchanged(sources: t.MappingKV[Path, str]) -> None:
        """Prove planning left every snapshotted source byte-identical."""
        for item, original in sources.items():
            tm.that(item.read_text(encoding="utf-8"), eq=original)

    @staticmethod
    def test_duplicate_facade_namespace_uses_declared_inherited_owner(
        tmp_path: Path,
    ) -> None:
        """Consolidate consumers without publishing or altering a homonym."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        tier = root / "tests"
        tier.mkdir()
        (tier / "__init__.py").write_text(
            "from tests.utilities import u\n", encoding="utf-8"
        )
        directory = (
            tier / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        directory.mkdir()
        (directory / "__init__.py").write_text("", encoding="utf-8")
        declaration = directory / "support.py"
        declaration.write_text(
            "class Support:\n    pass\n\n__all__ = ['Support']\n",
            encoding="utf-8",
        )
        owner = f"Tests{u.derive_class_stem(root.name)}Utilities"
        path = tier / "utilities.py"
        path.write_text(
            "import tests._utilities.support\n\n"
            f"class {owner}:\n"
            "    class Support:\n"
            "        class Entity:\n"
            "            VALUE = 'payload'\n"
            "    class Tests(tests._utilities.support.Support):\n"
            "        pass\n\n"
            f"u = {owner}\n__all__ = ['{owner}', 'u']\n",
            encoding="utf-8",
        )
        consumer = tier / "consumer.py"
        consumer.write_text(
            "from tests import u\n\n"
            "class Consumer(u.Support):\n    pass\n"
            "VALUE = u.Support.Entity.VALUE\n",
            encoding="utf-8",
        )
        sources = {
            item: item.read_text(encoding="utf-8")
            for item in (path, declaration, consumer, tier / "__init__.py")
        }
        proposed = TestsFlextInfraFamilyFlatten._apply(
            sources,
            TestsFlextInfraFamilyFlatten._plan(root, sources),
        )
        tm.that(proposed[consumer], has="class Consumer(u.Tests):")
        tm.that(proposed[consumer], has="VALUE = u.Tests.Entity.VALUE")
        tm.that(proposed[declaration], has="class Entity:")
        tm.that(proposed[path], lacks="class Support:")
        TestsFlextInfraFamilyFlatten._unchanged(sources)

    @staticmethod
    def _seed_wrapper_family(
        tmp_path: Path,
        *,
        collision: bool,
    ) -> TestsFlextInfraFamilyFlatten.WrapperFamilyFixture:
        """Seed the wrapper family, its consumers, and one unrelated homonym.

        Imports and MRO must resolve the proposed wrapper, not its disk name.

        Returns:
            The seeded wrapper family fixture.

        """
        root, package, directory, path, owner = TestsFlextInfraFamilyFlatten._payload(
            tmp_path,
        )
        parent = package / "entities.py"
        parent.write_text("class Parent:\n    Entity = 'inherited'\n", encoding="utf-8")
        inheritance = "(Parent)" if collision else ""
        source = (
            "from enum import Enum\n"
            f"from {package.name}.entities import Parent\n\n"
            f"class {owner}{inheritance}:\n"
            "    class Wrapper:\n"
            "        class Entity(Enum):\n"
            "            VALUE = 'member'\n"
            "        TEXT = '''first\n        literal indentation\n        last'''\n"
            f"\n__all__ = ['{owner}']\n"
        )
        path.write_text(source, encoding="utf-8")
        consumer = package / "consumer.py"
        references = (
            f"from {package.name}.{directory}.payload import {owner} as Part\n\n"
            "class Public(Part):\n    pass\n\n"
            "VALUE = Public.Wrapper.Entity.VALUE\n"
            "TEXT = Part.Wrapper.TEXT\n"
        )
        consumer.write_text(references, encoding="utf-8")
        homonym = package / "unrelated.py"
        unrelated = (
            "class Other:\n    class Wrapper:\n        TEXT = 'unrelated'\n"
            "VALUE = Other.Wrapper.TEXT\n"
        )
        homonym.write_text(unrelated, encoding="utf-8")
        return TestsFlextInfraFamilyFlatten.WrapperFamilyFixture(
            root=root,
            path=path,
            consumer=consumer,
            homonym=homonym,
            source=source,
            references=references,
            unrelated=unrelated,
        )

    @staticmethod
    def _seed_composed_facade(
        tmp_path: Path,
    ) -> TestsFlextInfraFamilyFlatten.ComposedFacadeFixture:
        """Seed the nested wrapper, its composed facade, and one consumer.

        Returns:
            The composed facade fixture.

        """
        root, package, directory, path, owner = TestsFlextInfraFamilyFlatten._payload(
            tmp_path,
        )
        source = (
            f"class {owner}:\n"
            "    class VerbReceipt:\n"
            "        class Stage:\n"
            "            pass\n"
            "        class Report:\n"
            "            pass\n"
            f"\n__all__ = ['{owner}']\n"
        )
        path.write_text(source, encoding="utf-8")
        facade_name = f"{u.derive_class_stem(root.name)}Models"
        project = u.derive_class_stem(root.name)
        facade = (
            f"from {package.name}.{directory}.payload import {owner}\n\n"
            f"class {facade_name}:\n"
            f"    class {project}({owner}):\n"
            "        pass\n\n"
            f"m = {facade_name}\n"
        )
        facade_path = package / "models.py"
        facade_path.write_text(facade, encoding="utf-8")
        consumer = package / "consumer.py"
        references = (
            "from __future__ import annotations\n"
            f"from {package.name} import m\n\n"
            f"def render() -> m.{project}.VerbReceipt.Stage:\n"
            f"    return m.{project}.VerbReceipt.Stage()\n"
        )
        consumer.write_text(references, encoding="utf-8")
        return TestsFlextInfraFamilyFlatten.ComposedFacadeFixture(
            root=root,
            path=path,
            facade_path=facade_path,
            consumer=consumer,
            source=source,
            facade=facade,
            references=references,
            project=project,
        )

    @staticmethod
    @pytest.mark.parametrize("collision", [False, True])
    def test_snapshot_rewrites_alias_and_inherited_consumers_without_effects(
        tmp_path: Path,
        *,
        collision: bool,
    ) -> None:
        """Test snapshot rewrites alias and inherited consumers without effects."""
        fixture = TestsFlextInfraFamilyFlatten._seed_wrapper_family(
            tmp_path,
            collision=collision,
        )
        path = fixture.path
        consumer = fixture.consumer
        homonym = fixture.homonym
        originals = {
            path: fixture.source,
            consumer: fixture.references,
            homonym: fixture.unrelated,
        }
        # Imports and MRO must resolve the proposed wrapper, not its disk name.
        sources = {
            **originals,
            path: fixture.source.replace("class Wrapper:", "class Grouping:"),
            consumer: fixture.references.replace(".Wrapper.", ".Grouping."),
        }
        edits = TestsFlextInfraFamilyFlatten._plan(fixture.root, sources)
        proposed = TestsFlextInfraFamilyFlatten._apply(sources, edits)
        expected_member = "GroupingEntity"
        tm.that(proposed[path], has=f"    class {expected_member}(Enum):")
        tm.that(
            proposed[path],
            has="'''first\n        literal indentation\n        last'''",
        )
        tm.that(proposed[consumer], has=f"VALUE = Public.{expected_member}.VALUE")
        tm.that(proposed[consumer], has="TEXT = Part.GroupingTEXT")
        tm.that(proposed[homonym], eq=fixture.unrelated)
        tm.that(
            TestsFlextInfraFamilyFlatten._plan(fixture.root, proposed),
            empty=True,
        )
        TestsFlextInfraFamilyFlatten._unchanged(originals)

    @staticmethod
    @pytest.mark.parametrize(
        "entity",
        [
            "class Entity(Enum):\n        VALUE = 'one'",
            "class Entity:\n        def value(self) -> int:\n            return 1",
        ],
    )
    def test_entity_classes_are_not_namespace_wrappers(
        tmp_path: Path,
        entity: str,
    ) -> None:
        """Test entity classes are not namespace wrappers."""
        root, _package, _directory, path, owner = TestsFlextInfraFamilyFlatten._payload(
            tmp_path
        )
        source = (
            f"from enum import Enum\nclass {owner}:\n    {entity}\n\n"
            f"__all__ = ['{owner}']\n"
        )
        path.write_text(source, encoding="utf-8")
        tm.that(TestsFlextInfraFamilyFlatten._plan(root, {path: source}), empty=True)

    @staticmethod
    @pytest.mark.parametrize(
        "reference",
        [
            "ALIAS = {owner}.Wrapper",
            "different_name = {owner}.Wrapper",
            "first = {owner}.Wrapper\nsecond = first",
            "instance = {owner}.Wrapper()",
            'alias: "{owner}.Wrapper"',
        ],
    )
    def test_wrapper_used_as_an_entity_is_preserved_without_edits(
        tmp_path: Path,
        reference: str,
    ) -> None:
        """Test wrapper used as an entity is preserved without edits."""
        root, _package, _directory, path, owner = TestsFlextInfraFamilyFlatten._payload(
            tmp_path, c.Infra.CONSTANTS_PY
        )
        source = (
            f"class {owner}:\n    class Wrapper:\n        VALUE = 1\n\n"
            f"{reference.format(owner=owner)}\n\n__all__ = ['{owner}']\n"
        )
        path.write_text(source, encoding="utf-8")
        tm.that(TestsFlextInfraFamilyFlatten._plan(root, {path: source}), empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_flatten_removes_wrapper_docstring_and_promotes_alias_member(
        tmp_path: Path,
    ) -> None:
        """Test flatten removes wrapper docstring and promotes alias member."""
        root, package, directory, path, owner = TestsFlextInfraFamilyFlatten._payload(
            tmp_path,
        )
        source = (
            "from enum import Enum\n\n"
            f"class {owner}:\n"
            '    """Owner doc."""\n'
            "    class Wrapper:\n"
            '        """Wrapper doc."""\n'
            "        class Entity(Enum):\n"
            "            VALUE = 'member'\n"
            "        type Grouped = Entity\n"
            f"\n__all__ = ['{owner}']\n"
        )
        path.write_text(source, encoding="utf-8")
        consumer = package / "consumer.py"
        references = (
            f"from {package.name}.{directory}.payload import "
            f"{owner} as Part\n\nmember: Part.Wrapper.Grouped\n"
        )
        consumer.write_text(references, encoding="utf-8")
        sources = {path: source, consumer: references}
        flattened = TestsFlextInfraFamilyFlatten._apply(
            sources,
            TestsFlextInfraFamilyFlatten._plan(root, sources),
        )
        tm.that(flattened[path], has='"""Owner doc."""')
        tm.that(flattened[path], has="type WrapperGrouped = WrapperEntity")
        tm.that(flattened[consumer], has="member: Part.WrapperGrouped")
        assert '"""Wrapper doc."""' not in flattened[path], flattened[path]

    @staticmethod
    def test_composed_facade_keeps_the_wrapper_callers_still_use(
        tmp_path: Path,
    ) -> None:
        """A facade alias that still names the wrapper is not flattened away."""
        fixture = TestsFlextInfraFamilyFlatten._seed_composed_facade(tmp_path)
        consumer = fixture.consumer
        sources = {
            fixture.path: fixture.source,
            fixture.facade_path: fixture.facade,
            consumer: fixture.references,
        }
        updated = TestsFlextInfraFamilyFlatten._apply(
            sources,
            TestsFlextInfraFamilyFlatten._plan(fixture.root, sources),
        )
        tm.that(updated[fixture.path], has="class VerbReceipt:")
        tm.that(updated[consumer], has=f"m.{fixture.project}.VerbReceipt.Stage")
        tm.that(consumer.read_text(encoding="utf-8"), eq=fixture.references)
