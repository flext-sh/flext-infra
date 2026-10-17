"""Public contracts for the automatic duplicate cure and its manual plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from flext_infra.codemod import (
    FlextInfraCodemodDuplicateApply,
    FlextInfraDuplicateApplyPhase,
    FlextInfraModGateEngine,
)
from tests import c, m, tm, u

if TYPE_CHECKING:
    from flext_infra import p, t

_CORE_CONSTANT = "SHARED_LIMIT = 42\n"
_SIDE_CONSTANT = "SHARED_LIMIT = 42\n"


class TestsFlextInfraCodemodDuplicateApply:
    """Cure identity-proven duplicates; plan every structural clone."""

    def test_cure_models_preserve_native_definition_identity(
        self,
        tmp_path: Path,
    ) -> None:
        """Census cure contracts consume the same typed source objects directly."""
        path = tmp_path / "definition.py"
        path.write_text(_CORE_CONSTANT, encoding=c.DEFAULT_ENCODING)
        statement = u.Infra.logical_statements(_CORE_CONSTANT)[0]
        item = m.Infra.Object(
            file_path=str(path),
            line=1,
            project="fixture",
            name="SHARED_LIMIT",
            kind="constant",
        )
        definition = m.Infra.DuplicateDefinition(
            item=item,
            path=path,
            source=_CORE_CONSTANT,
            statement=statement,
            body=_CORE_CONSTANT,
            consumers=0,
            layer=0,
        )
        copy = m.Infra.DuplicateCopyCure(
            definition=definition,
            consumer_files=(),
            in_module_uses=0,
        )
        planned = m.Infra.DuplicateGroupCure(
            owner=copy,
            copies=(),
            edits=(),
        )
        assert planned.owner is copy
        assert planned.owner.definition is definition
        assert planned.owner.definition.statement is statement
        tm.that(
            planned.owner.definition.source
            == path.read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
            truth=True,
        )
        deletion = m.Infra.DuplicateDeletion(
            path=path,
            name=item.name,
            line=item.line,
            project=item.project,
        )
        tm.that(deletion.path == definition.path, truth=True)
        tm.that(deletion.name == definition.item.name, truth=True)

    @staticmethod
    def _module(summary: str) -> str:
        """Render one fixture module header with the policy copyright notice.

        Returns:
            The header text every governed module carries.

        """
        return (
            f'"""{summary}.\n\n'
            "Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
            'SPDX-License-Identifier: MIT\n"""\n\n'
        )

    @staticmethod
    def _workspace(duplicate_project: Path) -> tuple[Path, Path]:
        """One governed fixture workspace with a provisioned interpreter.

        The installed session owner provisions one physical worker environment.
        Each exclusive case restores source and report state at the same path,
        so editable imports resolve this case without cloning or running setup.

        Returns:
            The repository root and its source package.

        """
        return duplicate_project, duplicate_project / "src" / "flext_demo"

    @staticmethod
    def _objects(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        paths: t.SequenceOf[Path],
        name: str,
    ) -> t.VariadicTuple[m.Infra.Object]:
        """Collect one name's rope inventory objects across module paths.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.Object]``.

        """
        found = tuple(
            item
            for path in paths
            for item in rope_workspace.objects(
                path,
                include_local_scopes=True,
                include_references=False,
            )
            if item.name == name
        )
        tm.that(found, length=len(paths))
        return found

    @staticmethod
    def _group(
        objects: t.SequenceOf[m.Infra.Object],
        *,
        value_identical: bool,
    ) -> m.Infra.DuplicateGroup:
        """Build one census duplicate group over collected objects.

        Returns:
            The resulting ``m.Infra.DuplicateGroup``.

        """
        return m.Infra.DuplicateGroup(
            name=objects[0].name,
            kind=objects[0].kind,
            definitions=list(objects),
            value_identical=value_identical,
        )

    def test_trivial_group_keeps_owner_and_rewires_consumers(
        self,
        duplicate_project: Path,
    ) -> None:
        """The consumer-carrying definition wins and every copy disappears."""
        root, package = self._workspace(duplicate_project)
        core = package / "core.py"
        side = package / "side.py"
        core.write_text(
            self._module("Core module") + _CORE_CONSTANT,
            encoding=c.DEFAULT_ENCODING,
        )
        side.write_text(
            self._module("Side module") + _SIDE_CONSTANT,
            encoding=c.DEFAULT_ENCODING,
        )
        consumer_a = package / "consumer_a.py"
        consumer_a.write_text(
            self._module("Consumer A") + "from flext_demo.core import SHARED_LIMIT\n"
            "\n"
            "TOTAL = SHARED_LIMIT + 1\n",
            encoding=c.DEFAULT_ENCODING,
        )
        for name in ("consumer_b", "consumer_c"):
            (package / f"{name}.py").write_text(
                self._module(f"Consumer {name[-1].upper()}")
                + "from flext_demo.side import SHARED_LIMIT\n"
                "\n"
                "TOTAL = SHARED_LIMIT + 2\n",
                encoding=c.DEFAULT_ENCODING,
            )
        with infra.rope_workspace(root) as rope:
            group = self._group(
                self._objects(rope, (core, side), "SHARED_LIMIT"),
                value_identical=True,
            )
            sources = {
                Path(resource.real_path).resolve(): resource.read()
                for resource in rope.rope_project.get_python_files()
            }
            frozen = dict(sources)
            states = tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                for path in sources
            )
            planned, deletions = tm.ok(
                FlextInfraCodemodDuplicateApply.plan_census(
                    root,
                    rope,
                    (group,),
                    sources=sources,
                    source_states=states,
                )
            )
            tm.that(planned.edits, empty=False)
            tm.that(deletions, empty=False)
            tm.that(sources, eq=frozen)
            for edit in planned.edits:
                tm.that(
                    edit.file_path.read_text(encoding=c.DEFAULT_ENCODING),
                    eq=edit.original_source,
                )
            preview = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root,
                    rope,
                    (group,),
                    apply=False,
                )
            )
            tm.that(preview.edits, eq=planned.edits)
            outcome = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root,
                    rope,
                    (group,),
                    apply=True,
                ),
            )
        # The owner is the definition with the most existing consumers: the
        # two side.py consumers outvote the one core.py consumer, so the
        # core copy is deleted and its consumer rebinds to the owner.
        tm.that(outcome.copies_removed, eq=1)
        tm.that(outcome.bindings_rewired, eq=1)
        tm.that(outcome.files_changed, eq=2)
        tm.that(outcome.plans, empty=True)
        tm.that(side.read_text(encoding=c.DEFAULT_ENCODING), has=_SIDE_CONSTANT)
        tm.that(
            core.read_text(encoding=c.DEFAULT_ENCODING),
            lacks=_CORE_CONSTANT,
        )
        consumer_source = consumer_a.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(consumer_source, has="from flext_demo.side import SHARED_LIMIT")
        tm.that(consumer_source, lacks="from flext_demo.core import SHARED_LIMIT")
        for name in ("consumer_b", "consumer_c"):
            source = (package / f"{name}.py").read_text(encoding=c.DEFAULT_ENCODING)
            tm.that(source, has="from flext_demo.side import SHARED_LIMIT")

    def test_phase_cures_once_then_converges(self, duplicate_project: Path) -> None:
        """The mod-loop callback changes sources once and reports the fixed point."""
        root, package = self._workspace(duplicate_project)
        core = package / "core.py"
        side = package / "side.py"
        core.write_text(
            self._module("Core module") + _CORE_CONSTANT,
            encoding=c.DEFAULT_ENCODING,
        )
        side.write_text(
            self._module("Side module") + _SIDE_CONSTANT,
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(root) as rope:
            first = tm.ok(
                FlextInfraDuplicateApplyPhase.apply(
                    root, tm.ok(FlextInfraModGateEngine.scan(root, fix=False)), rope
                ),
            )
            second = tm.ok(
                FlextInfraDuplicateApplyPhase.apply(
                    root, tm.ok(FlextInfraModGateEngine.scan(root, fix=False)), rope
                ),
            )
        tm.that(first, eq=True)
        tm.that(second, eq=False)
        tm.that(core.read_text(encoding=c.DEFAULT_ENCODING), has=_CORE_CONSTANT)
        tm.that(side.read_text(encoding=c.DEFAULT_ENCODING), lacks=_SIDE_CONSTANT)

    def test_different_homonyms_are_planned_never_written(
        self,
        duplicate_project: Path,
    ) -> None:
        """Two same-name objects with different values stay untouched."""
        root, package = self._workspace(duplicate_project)
        first = package / "first.py"
        second = package / "second.py"
        first.write_text(
            self._module("First module") + "LIMIT = 42\n",
            encoding=c.DEFAULT_ENCODING,
        )
        second.write_text(
            self._module("Second module") + "LIMIT = 99\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = (first.read_bytes(), second.read_bytes())
        with infra.rope_workspace(root) as rope:
            group = self._group(
                self._objects(rope, (first, second), "LIMIT"),
                value_identical=False,
            )
            outcome = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root,
                    rope,
                    (group,),
                    apply=True,
                ),
            )
        tm.that(outcome.edits, empty=True)
        tm.that(outcome.copies_removed, eq=0)
        tm.that(outcome.plans, length=1)
        plan = outcome.plans[0]
        tm.that(plan.origin, eq="census")
        tm.that(plan.reason, has="value-identical")
        tm.that(plan.edits[0].action, eq="keep-owner")
        tm.that(
            (first.read_bytes(), second.read_bytes()),
            eq=before,
        )

    def test_byte_identical_body_with_free_name_is_planned_only(
        self,
        duplicate_project: Path,
    ) -> None:
        """Equal text reading a per-module global is never auto-unified."""
        root, package = self._workspace(duplicate_project)
        first = package / "left.py"
        second = package / "right.py"
        body = self._module("Module context trap") + "LIMIT = BASE\n"
        first.write_text(
            body + "\nBASE = 1\n",
            encoding=c.DEFAULT_ENCODING,
        )
        second.write_text(
            body + "\nBASE = 2\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = (first.read_bytes(), second.read_bytes())
        with infra.rope_workspace(root) as rope:
            group = self._group(
                self._objects(rope, (first, second), "LIMIT"),
                value_identical=True,
            )
            outcome = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root,
                    rope,
                    (group,),
                    apply=True,
                ),
            )
        tm.that(outcome.edits, empty=True)
        tm.that(outcome.plans, length=1)
        tm.that(outcome.plans[0].reason, has="free name")
        tm.that(
            (first.read_bytes(), second.read_bytes()),
            eq=before,
        )

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(
                "def str(value):\n    return value + 'custom'\n\nLIMIT = str('value')\n",
                id="shadowed-constructor",
            ),
            pytest.param(
                "LIMIT = str.upper('value')\n",
                id="attribute-call",
            ),
            pytest.param(
                "LIMIT = 42\nLIMIT = 99\n",
                id="rebound-module-definition",
            ),
        ],
    )
    def test_unprovable_cure_owner_never_cures(
        self,
        duplicate_project: Path,
        source: str,
    ) -> None:
        """Equal text without one provable cure owner plans but never writes."""
        root, package = self._workspace(duplicate_project)
        first, second = package / "left.py", package / "right.py"
        for path in (first, second):
            path.write_text(self._module("Binding trap") + source, encoding="utf-8")
        before = first.read_bytes(), second.read_bytes()
        with infra.rope_workspace(root) as workspace:
            group = self._group(
                self._objects(workspace, (first, second), "LIMIT"),
                value_identical=True,
            )
            outcome = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root, workspace, (group,), apply=True
                )
            )
        tm.that(outcome.edits, empty=True)
        tm.that(outcome.plans, length=1)
        tm.that((first.read_bytes(), second.read_bytes()), eq=before)

    def test_structural_clone_is_planned_without_writes(
        self,
        duplicate_project: Path,
    ) -> None:
        """A semantic jscpd clone becomes a plan; the sources never change."""
        root, package = self._workspace(duplicate_project)
        owner = package / "holder.py"
        clone = package / "mirror.py"
        owner_block = "def handle(seed):\n    total = seed + 1\n    return total * 2\n"
        clone_block = "def handle(seed):\n    total = seed + 2\n    return total * 2\n"
        owner.write_text(
            self._module("Holder") + owner_block,
            encoding=c.DEFAULT_ENCODING,
        )
        clone.write_text(
            self._module("Mirror") + clone_block,
            encoding=c.DEFAULT_ENCODING,
        )
        # The clone range covers the function bodies: executable statements
        # are the semantic-clone currency the duplication gate trades in.
        report = self._jscpd_report(
            owner,
            clone,
            owner_span=(8, 9),
            clone_span=(8, 9),
        )
        self._write_jscpd_report(root, report)
        before = (owner.read_bytes(), clone.read_bytes())
        with infra.rope_workspace(root) as rope:
            outcome = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root,
                    rope,
                    (),
                    apply=True,
                ),
            )
        tm.that(outcome.edits, empty=True)
        tm.that(outcome.plans, length=1)
        plan = outcome.plans[0]
        tm.that(plan.origin, eq="jscpd")
        assert plan.reason
        tm.that(plan.edits[0].action == c.Infra.DUPLICATE_KEEP_ACTION, truth=True)
        tm.that(plan.edits[1].action == c.Infra.DUPLICATE_DELETE_ACTION, truth=True)
        tm.that(plan.owner_file_path, eq=owner)
        tm.that(
            (owner.read_bytes(), clone.read_bytes()),
            eq=before,
        )

    def test_declaration_only_clone_is_filtered_out(
        self, duplicate_project: Path
    ) -> None:
        """A clone without executable python behavior produces no plan."""
        root, package = self._workspace(duplicate_project)
        owner = package / "typing_owner.py"
        clone = package / "typing_mirror.py"
        block = "from typing import ClassVar\n\nNAME: ClassVar[str] = 'x'\n"
        owner.write_text(
            self._module("Owner") + block,
            encoding=c.DEFAULT_ENCODING,
        )
        clone.write_text(
            self._module("Mirror") + block,
            encoding=c.DEFAULT_ENCODING,
        )
        self._write_jscpd_report(
            root,
            self._jscpd_report(owner, clone, owner_span=(3, 4), clone_span=(3, 4)),
        )
        with infra.rope_workspace(root) as rope:
            outcome = tm.ok(
                FlextInfraCodemodDuplicateApply.census_duplicates(
                    root,
                    rope,
                    (),
                    apply=True,
                ),
            )
        tm.that(outcome.plans, empty=True)

    def test_census_rule_applies_the_cure_through_the_public_verb(
        self,
        duplicate_project: Path,
    ) -> None:
        """``refactor census --rules duplicate --apply`` cures and reports."""
        root, package = self._workspace(duplicate_project)
        core = package / "core.py"
        side = package / "side.py"
        core.write_text(
            self._module("Core module") + _CORE_CONSTANT,
            encoding=c.DEFAULT_ENCODING,
        )
        side.write_text(
            self._module("Side module") + _SIDE_CONSTANT,
            encoding=c.DEFAULT_ENCODING,
        )
        report = tm.ok(
            infra.census(
                m.Infra.CensusInput(
                    repository_root=root,
                    rules=("duplicate",),
                    apply=True,
                ),
            ),
        )
        tm.that(report.duplicate_cure_copies, eq=1)
        tm.that(report.duplicate_cure_files, eq=1)
        tm.that(report.duplicate_cure_bindings, eq=0)
        tm.that(report.duplicate_cure_plans, empty=True)
        tm.that(core.read_text(encoding=c.DEFAULT_ENCODING), has=_CORE_CONSTANT)
        tm.that(side.read_text(encoding=c.DEFAULT_ENCODING), lacks=_SIDE_CONSTANT)

    # ------------------------------------------------------------- fixtures

    @staticmethod
    def _jscpd_report(
        owner: Path,
        clone: Path,
        *,
        owner_span: t.IntPair,
        clone_span: t.IntPair,
    ) -> t.JsonDict:
        """Build one typed-valid jscpd report over two clone sides.

        Returns:
            The report mapping ready for the report file.

        """
        owner_start, owner_end = owner_span
        clone_start, clone_end = clone_span
        summary: t.JsonDict = {
            "clones": 1,
            "duplicatedLines": 3,
            "duplicatedTokens": 40,
            "lines": 10,
            "tokens": 120,
            "newClones": 0,
            "newDuplicatedLines": 0,
            "sources": 2,
            "percentage": 30,
            "percentageTokens": 30,
        }
        return {
            "duplicates": [
                {
                    "format": "python",
                    "firstFile": {
                        "name": str(owner),
                        "start": 0,
                        "end": 100,
                        "startLoc": {"line": owner_start, "column": 0, "position": 0},
                        "endLoc": {"line": owner_end, "column": 0, "position": 100},
                    },
                    "secondFile": {
                        "name": str(clone),
                        "start": 0,
                        "end": 100,
                        "startLoc": {"line": clone_start, "column": 0, "position": 0},
                        "endLoc": {"line": clone_end, "column": 0, "position": 100},
                    },
                    "lines": 3,
                    "tokens": 40,
                    "fragment": "def handle(seed):",
                    "isNew": False,
                },
            ],
            "statistics": {
                "detectionDate": "2026-10-12T00:00:00Z",
                "formats": {"python": summary},
                "total": summary,
            },
        }

    @staticmethod
    def _write_jscpd_report(root: Path, report: t.JsonDict) -> None:
        """Write the report where the cure engine reads it."""
        report_dir = root / c.Infra.JSCPD_REPORT_DIRNAME
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / c.Infra.JSCPD_REPORT_FILENAME).write_text(
            json.dumps(report),
            encoding=c.DEFAULT_ENCODING,
        )
