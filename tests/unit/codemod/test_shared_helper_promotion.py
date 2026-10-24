"""Public runtime contracts for promotion of shared test behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from flext_infra import p


class TestsFlextInfraSharedHelperPromotion:
    """Keep real consumers working while the original declaration changes owner."""

    @staticmethod
    def _workspace(tmp_path: Path, *, reexport: bool) -> t.Triple[Path, Path, str]:
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        # Promotion publishes through the codegen transaction, which coordinates
        # only inside an exact Git worktree root, exactly as in production.
        u.Tests.initialize_git_repo(root)
        tier = root / c.Infra.DIR_TESTS
        suite = tier / "unit"
        fixtures = suite / "_fixtures"
        fixtures.mkdir(parents=True)
        for directory in (tier, suite, fixtures):
            (directory / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        stem = f"{tier.name.title()}{u.derive_class_stem(root.name)}"
        owner = f"{stem}Utilities"
        (tier / c.Infra.UTILITIES_PY).write_text(
            f"class {owner}:\n"
            "    class Tests:\n"
            "        @staticmethod\n"
            "        def label() -> str:\n"
            "            return 'shared behavior'\n\n"
            f"u = {owner}\n__all__ = ['{owner}', 'u']\n",
            encoding="utf-8",
        )
        helper = f"{stem}Helper"
        source = fixtures / "behavior.py"
        source.write_text(
            "from tests import u\n\n"
            f"class {helper}:\n"
            '    """Shared documentation.\n\n    Original indentation.\n    """\n'
            "    def value(self) -> str:\n"
            "        return u.Tests.label()\n\n"
            "    def payload(self) -> str:\n"
            "        return '''first\n    literal indentation\nlast'''\n\n"
            f"__all__ = ['{helper}']\n",
            encoding="utf-8",
        )
        module = "._fixtures" if reexport else "._fixtures.behavior"
        (suite / "consumer.py").write_text(
            f"from {module} import {helper} as Shared\n\n"
            "class Consumer(Shared):\n"
            "    def read(self) -> str:\n"
            "        return self.value()\n\n"
            "    def echo(self, value: 'Shared') -> 'Shared':\n"
            "        Shared = type(None)\n"
            "        assert not isinstance(value, Shared)\n"
            "        return value\n",
            encoding="utf-8",
        )
        (suite / "quoted.py").write_text(
            "from typing import Annotated, Literal\n"
            f"from {module} import {helper} as Shared\n\n"
            "ORDINARY = 'Shared'\n\n"
            "def echo(value: 'Shared') -> 'Shared':\n"
            "    return value\n\n"
            "def annotated(value: \"Annotated[Shared, 'Shared']\")"
            " -> \"Literal['Shared']\":\n"
            "    return 'Shared'\n",
            encoding="utf-8",
        )
        (suite / "unrelated.py").write_text(
            f"class {helper}:\n"
            "    def value(self) -> str:\n"
            "        return 'homonym'\n\n"
            f"VALUE = {helper}().value()\n\n"
            f"def echo(value: '{helper}') -> '{helper}':\n"
            "    return value\n",
            encoding="utf-8",
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        # Semantic publication runs inside a codegen transaction, which only
        # coordinates through a real repository rooted at the project.
        u.Tests.initialize_git_repo(root)
        return root, source, helper

    @staticmethod
    def _run(root: Path, probe: str) -> str:
        return "\n".join(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(root), *sys.path),
                cwd=root,
            ),
        )

    @staticmethod
    def _sources(root: Path) -> t.MutableMappingKV[Path, str]:
        """Snapshot every python source under the workspace.

        Returns:
            Each python path mapped to its current text.

        """
        return {path: path.read_text(encoding="utf-8") for path in root.rglob("*.py")}

    @staticmethod
    def _unchanged(sources: t.MappingKV[Path, str]) -> None:
        """Prove planning left every snapshotted source byte-identical."""
        for path, original in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=original)

    @staticmethod
    def _plan(
        rope: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Plan the class-nesting cutover over the given sources.

        Returns:
            The planned file edits.

        """
        return tm.ok(
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources=sources,
            ),
        )

    def _converge(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> tuple[t.VariadicTuple[m.Infra.SemanticMigrationEdit], t.MappingKV[Path, str]]:
        """Plan a non-empty cutover and prove it is a fixed point.

        Returns:
            The planned edits and the proposed post-edit sources.

        """
        edits = self._plan(rope, sources)
        tm.that(edits, empty=False)
        proposed = dict(sources)
        proposed.update({edit.file_path: edit.updated_source for edit in edits})
        tm.that(self._plan(rope, proposed), empty=True)
        return edits, proposed

    def _publish(
        self,
        root: Path,
        edits: t.VariadicTuple[m.Infra.SemanticMigrationEdit],
    ) -> None:
        """Publish planned edits through the codegen transaction and re-materialize."""
        plans = tuple(
            m.Infra.SemanticFilePlan(
                project=root,
                path=edit.file_path,
                before=(
                    state := tm.ok(
                        u.Cli.atomic_read_binary_file_state(
                            edit.file_path,
                            required=True,
                        ),
                    )
                ),
                desired_content=edit.updated_source.encode(),
                desired_mode=state.mode,
                changes=edit.changes,
            )
            for edit in edits
        )
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=root,
            ),
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))

    def _rejects(self, root: Path, match: str) -> None:
        """Prove planning escapes loud with ``match`` and changes no source."""
        sources = self._sources(root)
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=match),
        ):
            self._plan(rope, sources)
        self._unchanged(sources)

    @staticmethod
    def _seed_quoted_collision(root: Path, helper: str) -> None:
        """Append a colliding quoted annotation binding to the quoted module."""
        quoted = root / c.Infra.DIR_TESTS / "unit" / "quoted.py"
        with infra.rope_workspace(root) as rope:
            resource = tm.not_none(rope.resource(quoted))
            _, binding = u.Infra.import_binding(
                rope.rope_project,
                u.Infra.resolve_pymodule(
                    rope.rope_project, u.Infra.require_file_resource(resource, quoted)
                ),
                rope.convention(
                    root / c.Infra.DIR_TESTS / c.Infra.UTILITIES_PY,
                ).module_name,
                helper,
            )
        primary = ast.parse(binding, mode="eval").body
        while isinstance(primary, ast.Attribute):
            primary = primary.value
        primary_name = ast.unparse(primary)
        tm.that(primary_name.isidentifier(), truth=True)
        quoted.write_text(
            quoted.read_text(encoding="utf-8")
            + f"\nclass Local:\n    {primary_name} = str\n    value: 'Shared'\n",
            encoding="utf-8",
        )

    @pytest.mark.parametrize("reexport", [False, True])
    @pytest.mark.parametrize("quoted_only", [False, True])
    @pytest.mark.parametrize("lexical_collision", [False, True])
    def test_original_identity_moves_without_effects_until_publication(
        self,
        tmp_path: Path,
        *,
        reexport: bool,
        quoted_only: bool,
        lexical_collision: bool,
    ) -> None:
        """Test original identity moves without effects until publication."""
        root, source, helper = self._workspace(tmp_path, reexport=reexport)
        if quoted_only:
            (root / c.Infra.DIR_TESTS / "unit" / "consumer.py").unlink()
        if lexical_collision:
            self._seed_quoted_collision(root, helper)
        probe = (
            "from typing import get_args, get_type_hints\n"
            "from tests.unit.quoted import ORDINARY, annotated, echo\n"
            "from tests.unit import unrelated\n"
            "Helper = get_type_hints(echo)['value']\n"
            "assert get_type_hints(echo)['return'] is Helper\n"
            "assert echo(Helper()).value() == 'shared behavior'\n"
            "hints = get_type_hints(annotated, include_extras=True)\n"
            "assert get_args(hints['value']) == (Helper, 'Shared')\n"
            "assert get_args(hints['return']) == ('Shared',)\n"
            "assert ORDINARY == 'Shared'\n"
            f"assert get_type_hints(unrelated.echo)['value'] is unrelated.{helper}\n"
            "print(Helper().value(), unrelated.VALUE)\n"
            "print(repr(Helper().payload()), repr(Helper.__doc__))\n"
        )
        if not quoted_only:
            probe += (
                "from tests.unit.consumer import Consumer\n"
                "assert Consumer.__bases__[0] is Helper\n"
                "assert get_type_hints(Consumer.echo)['value'] is Helper\n"
                "assert get_type_hints(Consumer.echo)['return'] is Helper\n"
                "assert Consumer().echo(Helper()).value() == Consumer().read()\n"
            )
        if lexical_collision:
            probe += (
                "from tests.unit.quoted import Local\n"
                "assert get_type_hints(Local)['value'] is Helper\n"
            )
        before = self._run(root, probe)
        if lexical_collision:
            # A collision is a planning defect: it escapes loud, before any
            # effect, instead of being folded into a failed result.
            self._rejects(root, "shadowed quoted type destination")
            tm.that(self._run(root, probe), eq=before)
            return
        sources = self._sources(root)
        with infra.rope_workspace(root) as rope:
            edits, _ = self._converge(rope, sources)
        self._unchanged(sources)
        self._publish(root, edits)
        tm.that(self._run(root, probe), eq=before)
        identity = (
            "from typing import get_type_hints\n"
            "from tests import u\n"
            "from tests.unit.quoted import echo\n"
            "from tests.unit._fixtures import behavior\n"
            f"assert get_type_hints(echo)['value'] is u.{helper}\n"
            f"assert not hasattr(behavior, '{helper}')\n"
            f"print(u.{helper}().value())\n"
        )
        tm.that(self._run(root, identity), eq="shared behavior")
        tm.that(source.exists(), eq=True)

    @pytest.mark.parametrize("test_case", [False, True])
    def test_unused_helpers_and_real_test_cases_keep_their_declared_owner(
        self,
        tmp_path: Path,
        *,
        test_case: bool,
    ) -> None:
        """Test unused helpers and real test cases keep their declared owner."""
        root, source, helper = self._workspace(tmp_path, reexport=True)
        if test_case:
            source.write_text(
                f"class {helper}:\n"
                "    def test_behavior(self) -> None:\n"
                "        assert self.value() == 'shared behavior'\n\n"
                "    def value(self) -> str:\n"
                "        return 'shared behavior'\n",
                encoding="utf-8",
            )
        else:
            (root / c.Infra.DIR_TESTS / "unit" / "consumer.py").unlink()
            (root / c.Infra.DIR_TESTS / "unit" / "quoted.py").unlink()
        sources = self._sources(root)
        with infra.rope_workspace(root) as rope:
            tm.that(self._plan(rope, sources), empty=True)
        self._unchanged(sources)

    def test_private_support_with_nested_behavior_moves_to_utilities(
        self,
        tmp_path: Path,
    ) -> None:
        """Test private support with nested behavior moves to utilities."""
        root, source, helper = self._workspace(tmp_path, reexport=False)
        destination = source.parent.parent / "_support.py"
        source.unlink()
        destination.write_text(
            f"class {helper}:\n"
            "    class Nested:\n"
            "        @staticmethod\n"
            "        def value() -> str:\n"
            "            return 'shared behavior'\n",
            encoding="utf-8",
        )
        consumer = root / c.Infra.DIR_TESTS / "unit" / "consumer.py"
        consumer.write_text(
            f"from tests.unit._support import {helper}\n\n"
            f"VALUE = {helper}.Nested.value()\n",
            encoding="utf-8",
        )
        (root / c.Infra.DIR_TESTS / "unit" / "quoted.py").unlink()
        sources = self._sources(root)
        with infra.rope_workspace(root) as rope:
            edits = self._plan(rope, sources)
        self._publish(root, edits)
        tm.that(
            self._run(
                root,
                "from tests import u\n"
                "from tests.unit.consumer import VALUE\n"
                f"assert VALUE == u.{helper}.Nested.value()\n"
                "print(VALUE)\n",
            ),
            eq="shared behavior",
        )

    def test_two_declared_utilities_owners_fail_without_changing_consumers(
        self,
        tmp_path: Path,
    ) -> None:
        """Test two declared utilities owners fail without changing consumers."""
        root, _, _ = self._workspace(tmp_path, reexport=True)
        u.Tests.write_lazy_init_namespace_module(
            root / c.Infra.DIR_TESTS / "other.py",
            class_name="OtherUtilities",
            alias="u",
        )
        self._rejects(root, "requires one utilities facade")

    def test_destination_import_of_the_moving_helper_is_replaced(
        self,
        tmp_path: Path,
    ) -> None:
        """Test a destination import of the helper is replaced by the move."""
        root, source, helper = self._workspace(tmp_path, reexport=False)
        utilities = root / c.Infra.DIR_TESTS / c.Infra.UTILITIES_PY
        imported = f"from tests.unit._fixtures.behavior import {helper}\n"
        utilities.write_text(
            imported + "\n" + utilities.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        sources = self._sources(root)
        with infra.rope_workspace(root) as rope:
            _, proposed = self._converge(rope, sources)
        tm.that(
            proposed[utilities],
            has=f"class {helper}",
            lacks=imported.strip(),
        )
        tm.that(proposed[source], lacks=f"class {helper}")
        self._unchanged(sources)

    def test_destination_homonym_still_rejects_the_move(
        self,
        tmp_path: Path,
    ) -> None:
        """Test a different object with the same name still rejects the move."""
        root, _, helper = self._workspace(tmp_path, reexport=False)
        utilities = root / c.Infra.DIR_TESTS / c.Infra.UTILITIES_PY
        utilities.write_text(
            f"class {helper}:\n"
            "    def value(self) -> str:\n"
            "        return 'other'\n\n" + utilities.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self._rejects(root, "already binds")
