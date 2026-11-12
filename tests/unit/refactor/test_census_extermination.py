"""Census extermination rows classify aliases, duplicates and shortest forms.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.refactor import FlextInfraRefactorCensus
from tests import m, p, tm


class TestsFlextInfraCensusExtermination:
    """Exercise the typed census rows directly over synthetic sources."""

    @staticmethod
    def _object(
        path: Path,
        name: str,
        kind: str = "assignment",
        module_name: str = "demo.module",
    ) -> p.Infra.Object:
        """Build one census object for the synthetic source.

        Returns:
            The census object anchored at line one of ``path``.

        """
        return m.Infra.Object(
            name=name,
            kind=kind,
            file_path=str(path),
            line=1,
            project="demo",
            module_name=module_name,
            payload_fingerprint="same",
        )

    @staticmethod
    def test_alias_assignment_and_import_alias_are_fixable(tmp_path: Path) -> None:
        """Simple aliases target a bound canonical name and remain fixable."""
        path = tmp_path / "module.py"
        source = (
            "from pkg import Canonical as ImportedAlias\n"
            "Canonical = object\n"
            "Legacy = Canonical\n"
            '__all__ = ["Canonical"]\n'
        )
        rows = FlextInfraRefactorCensus.extermination_rows(
            sources={path: source},
            objects=(
                TestsFlextInfraCensusExtermination._object(path, "Legacy"),
                TestsFlextInfraCensusExtermination._object(path, "ImportedAlias"),
            ),
            duplicates=(),
            census_kinds=None,
        )
        aliases, _duplicates, _shortest = rows
        by_name = {row.name: row for row in aliases}
        tm.that(by_name["Legacy"].kind, eq="assignment")
        tm.that(by_name["Legacy"].canonical, eq="Canonical")
        tm.ok(by_name["Legacy"].fixable)
        tm.that(by_name["ImportedAlias"].kind, eq="import-alias")
        tm.that(by_name["ImportedAlias"].canonical, eq="Canonical")
        tm.ok(by_name["ImportedAlias"].fixable)

    @staticmethod
    def test_public_export_and_duplicate_all_entry_are_review_only(
        tmp_path: Path,
    ) -> None:
        """Public aliases and duplicate ``__all__`` entries never auto-cure."""
        path = tmp_path / "public.py"
        source = (
            'Canonical = object\nLegacy = Canonical\n__all__ = ["Legacy", "Legacy"]\n'
        )
        aliases, _duplicates, _shortest = FlextInfraRefactorCensus.extermination_rows(
            sources={path: source},
            objects=(TestsFlextInfraCensusExtermination._object(path, "Legacy"),),
            duplicates=(),
            census_kinds=None,
        )
        by_kind = {row.kind: row for row in aliases}
        tm.that(by_kind["assignment"].reason, eq="public export requires review")
        tm.that(by_kind["assignment"].fixable, eq=False)
        tm.that(by_kind["all-entry"].fixable, eq=False)
        tm.that(by_kind["all-entry"].cure, eq="manual-review")

    @staticmethod
    def test_identity_duplicate_is_fixable_and_structural_is_review_only(
        tmp_path: Path,
    ) -> None:
        """Only identity-proven duplicate declarations become auto cures."""
        left = tmp_path / "left.py"
        right = tmp_path / "right.py"
        left_object = TestsFlextInfraCensusExtermination._object(
            left,
            "Shared",
            kind="function",
            module_name="pkg.left",
        )
        right_object = TestsFlextInfraCensusExtermination._object(
            right,
            "Shared",
            kind="function",
            module_name="pkg.right",
        )
        identity = m.Infra.DuplicateGroup.model_validate({
            "name": "Shared",
            "kind": "function",
            "definitions": [left_object, right_object],
            "canonical": "pkg",
            "value_identical": True,
        })
        structural = m.Infra.DuplicateGroup.model_validate({
            "name": "Other",
            "kind": "class",
            "definitions": [
                left_object,
                right_object,
            ],
            "canonical": "pkg",
            "value_identical": False,
            "semantic_candidate": True,
        })
        _aliases, duplicates, _shortest = FlextInfraRefactorCensus.extermination_rows(
            sources={left: "", right: ""},
            objects=(left_object, right_object),
            duplicates=(identity, structural),
            census_kinds=frozenset({"duplicate"}),
        )
        by_name = {row.name: row for row in duplicates}
        tm.ok(by_name["Shared"].fixable)
        tm.that(by_name["Shared"].cure, eq="duplicate-apply")
        tm.that(by_name["Other"].fixable, eq=False)
        tm.that(
            by_name["Other"].reason,
            eq="structural duplicate requires review",
        )

    @staticmethod
    def test_wrapper_and_ceremony_are_shortest_form_review_rows(
        tmp_path: Path,
    ) -> None:
        """Pass-through wrappers and behavior-free classes stay review-only."""
        path = tmp_path / "shapes.py"
        source = (
            "def forward(*args, **kwargs):\n"
            "    return owner(*args, **kwargs)\n"
            "class Ceremony:\n"
            "    '''No behavior.'''\n"
            "    pass\n"
        )
        _aliases, _duplicates, shortest = FlextInfraRefactorCensus.extermination_rows(
            sources={path: source},
            objects=(
                TestsFlextInfraCensusExtermination._object(
                    path, "forward", kind="function"
                ),
                TestsFlextInfraCensusExtermination._object(
                    path, "Ceremony", kind="class"
                ),
            ),
            duplicates=(),
            census_kinds=frozenset({"shortest"}),
        )
        by_kind = {row.kind: row for row in shortest}
        tm.that(by_kind["wrapper"].canonical_form, eq="owner")
        tm.that(by_kind["wrapper"].fixable, eq=False)
        tm.that(by_kind["ceremony"].target, eq="Ceremony")
        tm.that(by_kind["ceremony"].fixable, eq=False)
        tm.that(by_kind["wrapper"].reason, eq="requires delegation proof")

    @staticmethod
    def test_canonical_rebinds_shells_and_entrypoints_are_lawful(
        tmp_path: Path,
    ) -> None:
        """Family rebinds, MRO shells and console entrypoints are not defects."""
        path = tmp_path / "facade.py"
        source = (
            "class TestsDemoModels(Base):\n"
            "    pass\n"
            "m = TestsDemoModels\n"
            "def main(*args, **kwargs):\n"
            "    return Cli.run(*args, **kwargs)\n"
        )
        aliases, _duplicates, shortest = FlextInfraRefactorCensus.extermination_rows(
            sources={path: source},
            objects=(),
            duplicates=(),
            census_kinds=None,
        )
        tm.that(len(aliases), eq=0)
        tm.that(len(shortest), eq=0)

    @staticmethod
    def test_cross_package_family_alias_is_flagged_for_facade_cure(
        tmp_path: Path,
    ) -> None:
        """Importing another package's family under a new name needs the facade."""
        path = tmp_path / "consumer.py"
        source = "from flext_infra import m as infra_m\n"
        aliases, _duplicates, _shortest = FlextInfraRefactorCensus.extermination_rows(
            sources={path: source},
            objects=(),
            duplicates=(),
            census_kinds=frozenset({"alias"}),
        )
        tm.that(aliases[0].kind, eq="family-import-alias")
        tm.that(aliases[0].fixable, eq=False)
        tm.that(aliases[0].reason, eq="requires local facade namespace")
