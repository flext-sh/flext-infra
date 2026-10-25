"""Facade-member census and ownership rules derive exactly from the real core facades.

The generated native rules constrain their metavariables through the census
instead of an engine predicate, so every alternative must be a name the
declaring letter really binds foreign to it, each document is scoped to that
letter's family files, and nothing the owner itself binds may match.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path

from tests import c, t, tm, u


class TestsFlextInfraFacadeMemberConstraints:
    """``u.Infra.facade_member_census`` and its ownership rules over flext-core."""

    PACKAGE: str = "flext_core"

    @classmethod
    def _project(cls) -> Path:
        package_dir = Path(import_module(cls.PACKAGE).__file__ or "").parent
        return package_dir.parent.parent

    @classmethod
    def _ownership_rules(cls) -> t.MappingKV[str, t.JsonMapping]:
        project = cls._project()
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            return u.Infra.codemod_facade_member_ownership_rules(snapshot, project)

    @staticmethod
    def _alternatives(pattern: str) -> tuple[str, ...]:
        body = pattern.removeprefix("^(?:").removesuffix(")$")
        tm.that(f"^(?:{body})$", eq=pattern)
        return tuple(re.sub(r"\\(.)", r"\1", text) for text in body.split("|"))

    @classmethod
    def _by_shape(cls, shape: str) -> dict[str, tuple[str, ...]]:
        rules = cls._ownership_rules()
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        found: dict[str, tuple[str, ...]] = {}
        for rule_id, rule in rules.items():
            rule_shape, _package, letter = rule_id.split(separator)
            if rule_shape != shape:
                continue
            constraints = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                rule["constraints"]
            )
            constraint = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                constraints[c.Infra.FACADE_MEMBER_NAME_VAR]
            )
            found[letter] = cls._alternatives(str(constraint["regex"]))
        return found

    @classmethod
    def test_relocations_name_only_foreign_references(cls) -> None:
        """Each census reference is a non-owner reference bound to its owner."""
        core = import_module(cls.PACKAGE)
        _lineage, relocations, _names = u.Infra.facade_member_census(cls._project())
        tm.that(relocations, empty=False)
        for owner, references in relocations.items():
            for reference in references:
                letter, member = reference.split(".")
                value = getattr(getattr(core, letter), member)
                tm.that(letter, ne=owner)
                tm.that(u.Infra.facade_member_owner(value), eq=owner)
                tm.that(f"{owner}.{member}" in references, eq=False)

    @classmethod
    def test_retirements_match_their_relocations(cls) -> None:
        """Every retired name of the package is a relocated reference of its letter.

        Relocation also covers receivers that bind no object under the
        owner's name, so retirements are a subset of the references.
        """
        _lineage, relocations, _names = u.Infra.facade_member_census(cls._project())
        references = {
            reference for found in relocations.values() for reference in found
        }
        retirements = cls._by_shape(c.Infra.FACADE_MEMBER_RETIRE_SHAPE)
        retired = {
            f"{letter}.{name}"
            for letter, names in retirements.items()
            for name in names
        }
        tm.that(retired, empty=False)
        tm.that(retired - references, empty=True)

    @classmethod
    def test_wrong_layer_names_are_unbound_by_their_owner(cls) -> None:
        """A wrong-layer name is declared by its letter and absent from its owner."""
        core = import_module(cls.PACKAGE)
        misplaced = cls._by_shape(c.Infra.FACADE_MEMBER_WRONG_LAYER_SHAPE)
        retirements = cls._by_shape(c.Infra.FACADE_MEMBER_RETIRE_SHAPE)
        for letter, names in misplaced.items():
            for name in names:
                owner = u.Infra.facade_member_owner(
                    getattr(getattr(core, letter), name)
                )
                tm.that(name in dir(getattr(core, owner)), eq=False)
                tm.that(name in retirements.get(letter, ()), eq=False)

    @classmethod
    def test_documents_scope_their_letter_family(cls) -> None:
        """Every document lists only files of its declaring letter's family."""
        rules = cls._ownership_rules()
        tm.that(rules, empty=False)
        for rule_id, rule in rules.items():
            letter = rule_id.rsplit(c.Infra.CODEMOD_GENERATED_ID_SEPARATOR, 1)[1]
            for pattern in u.Cli.JSON_LIST_ADAPTER.validate_python(rule["files"]):
                relative = Path(str(pattern).removeprefix("**/"))
                tm.that(u.Infra.facade_family_of_source(relative), eq=letter)

    @classmethod
    def test_derivation_is_a_fixed_point(cls) -> None:
        """Two derivations publish identical rules and census."""
        first = cls._ownership_rules()
        tm.that(cls._ownership_rules(), eq=first)
        census = u.Infra.facade_member_census(cls._project())
        tm.that(u.Infra.facade_member_census(cls._project()), eq=census)
