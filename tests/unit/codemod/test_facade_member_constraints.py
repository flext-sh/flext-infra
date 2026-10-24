"""Facade-member utilities are derived exactly from the real core facades.

The generated native rules constrain their metavariables through these
utilities instead of an engine predicate, so every alternative must be a
reference a non-owner letter really re-exports and nothing the owner itself
binds may match.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraFacadeMemberConstraints:
    """``u.Infra.facade_member_constraints`` over the installed flext-core."""

    PACKAGE: str = "flext_core"

    @classmethod
    def _project(cls) -> Path:
        package_dir = Path(import_module(cls.PACKAGE).__file__ or "").parent
        return package_dir.parent.parent

    @staticmethod
    def _alternatives(pattern: str) -> tuple[str, ...]:
        body = pattern.removeprefix("^(?:").removesuffix(")$")
        tm.that(f"^(?:{body})$", eq=pattern)
        return tuple(re.sub(r"\\(.)", r"\1", text) for text in body.split("|"))

    @classmethod
    def _by_variable(cls, variable: str) -> dict[str, tuple[str, ...]]:
        utilities = u.Infra.facade_member_constraints(cls._project())
        suffix = c.Infra.FACADE_MEMBER_UTILITY_ID.format(rule="", variable=variable)
        return {
            utility.removesuffix(suffix).rsplit("-", 1)[1]: cls._alternatives(
                str(rule["regex"])
            )
            for utility, rule in utilities.items()
            if utility.endswith(suffix)
        }

    @classmethod
    def test_relocations_name_only_foreign_references(cls) -> None:
        """Each alternative is a non-owner reference bound to its owner's object."""
        core = import_module(cls.PACKAGE)
        relocations = cls._by_variable(c.Infra.FACADE_MEMBER_REFERENCE_VAR)
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
        """Every retired name of the package is a relocated reference of its letter."""
        references = {
            reference
            for found in cls._by_variable(c.Infra.FACADE_MEMBER_REFERENCE_VAR).values()
            for reference in found
        }
        retirements = cls._by_variable(c.Infra.FACADE_MEMBER_NAME_VAR)
        retired = {
            f"{letter}.{name}"
            for letter, names in retirements.items()
            for name in names
        }
        tm.that(retired, eq=references)

    @classmethod
    def test_derivation_is_a_fixed_point(cls) -> None:
        """Two derivations publish identical utilities."""
        first = u.Infra.facade_member_constraints(cls._project())
        tm.that(u.Infra.facade_member_constraints(cls._project()), eq=first)
