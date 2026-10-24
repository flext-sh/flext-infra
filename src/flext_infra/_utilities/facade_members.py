"""Single owner of every facade member, derived from the object it binds.

A facade letter (``c``, ``t``, ``p``, ``m``, ``u`` ...) may re-export a name a
lower layer already owns. The owner of a member is selected by the kind of the
runtime object the name binds, through the declarative ``facade-members``
policy; every other facade binding the same object is a duplicate that
``make mod`` retires, and its consumers are relocated to the owner. No member
or letter is listed here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import Enum
from importlib import import_module
from inspect import isroutine
from pathlib import Path
from typing import (
    Annotated,
    TypeAliasType,
    get_args,
    get_origin,
    is_protocol,
    is_typeddict,
)

from flext_infra import c, config, p, t
from flext_infra._utilities import FlextInfraUtilitiesPyproject


class FlextInfraUtilitiesFacadeMembers:
    """Derive facade member kinds and their single owner letter."""

    @staticmethod
    def facade_member_kind(value: p.AttributeProbe) -> c.Infra.FacadeMemberKind:
        """Classify the runtime object a facade member binds.

        A type alias is classified by the value it names, so an alias of an
        exception or model is a duplicate of that owner's binding. An alias
        whose value cannot be evaluated propagates its ``NameError``: an
        unresolvable alias is a declaration defect, never a default.

        Returns:
            The member kind the owner policy maps to a facade letter.

        """
        origin = FlextInfraUtilitiesFacadeMembers._typing_origin(value)
        kind = c.Infra.FacadeMemberKind
        policy = config.Infra.tooling.facade_members
        if isinstance(origin, type):
            module = origin.__module__
            classes = (
                (issubclass(origin, BaseException), kind.EXCEPTION),
                (issubclass(origin, Enum), kind.ENUM),
                (is_protocol(origin), kind.PROTOCOL),
                (isinstance(origin, p.ModelType) or is_typeddict(origin), kind.MODEL),
                # A subscripted wrapper (``SerializeAsAny[T]``) builds a type that
                # annotations in t itself need, so it is a type constructor.
                ("__class_getitem__" in vars(origin), kind.TYPE),
                # ADR-027: field specifiers and the Annotated validator and
                # serializer classes declare models.
                (module in policy.model_declaration_modules, kind.MODEL_DECLARATION),
            )
            return next((found for hit, found in classes if hit), kind.TYPE)
        if isroutine(origin):
            module = origin.__module__ if isinstance(origin, p.ModuleOwned) else ""
            if module in policy.type_constructor_modules:
                return kind.TYPE
            return (
                kind.MODEL_DECLARATION
                if module in policy.model_declaration_modules
                else kind.FUNCTION
            )
        return (
            kind.TYPE
            if type(origin).__module__ in c.Infra.FACADE_MEMBER_TYPING_MODULES
            else kind.CONSTANT
        )

    @staticmethod
    def _typing_origin(value: p.AttributeProbe) -> p.AttributeProbe:
        """Unwrap aliases, ``Annotated`` bases and generic origins to one object.

        Returns:
            The class, routine or typing form the member ultimately names.

        """
        current = value
        while True:
            if isinstance(current, TypeAliasType):
                current = current.__value__
                continue
            origin = get_origin(current)
            if origin is Annotated:
                current = get_args(current)[0]
                continue
            if origin is None or origin is current:
                return current
            current = origin

    @classmethod
    def facade_member_owner(cls, value: p.AttributeProbe) -> str:
        """Return the facade letter that owns a member's runtime object.

        Returns:
            The owner letter declared for the member's kind.

        """
        return config.Infra.tooling.facade_members.owners[cls.facade_member_kind(value)]

    @classmethod
    def library_member_owner(cls, module: str, member: str) -> str:
        """Return the facade letter that owns a library's public member.

        The member is read from the imported library itself, so the owner
        follows the object's kind exactly as for a facade member.

        Returns:
            The owner letter declared for the member's kind.

        """
        return cls.facade_member_owner(getattr(import_module(module), member))

    @classmethod
    def foreign_facade_member(
        cls,
        package: str,
        reference: t.StrPair,
        placement: c.Infra.FacadeMemberPlacement,
    ) -> bool:
        """Decide whether a facade letter binds a member another facade owns.

        ``reference`` is the facade letter and the member name of ``package``.
        ``EXPOSED`` holds when the owner already binds the identical object,
        so the duplicate is retired automatically. ``MISSING`` holds when the
        owner binds nothing under that name yet: the declaration moves to the
        owner family before consumers relocate.

        Returns:
            Whether the member is foreign to the letter with that placement.

        """
        letter, member = reference
        if member.startswith("_"):
            return False
        module = import_module(package)
        facade = getattr(module, letter, None)
        if not isinstance(facade, type) or not cls._declared_by(
            facade, member, package
        ):
            return False
        value: p.AttributeProbe = getattr(facade, member)
        owner = cls.facade_member_owner(value)
        owner_facade = getattr(module, owner, None)
        bound = isinstance(owner_facade, type) and member in dir(owner_facade)
        if placement is c.Infra.FacadeMemberPlacement.EXPOSED:
            return (
                owner != letter
                and bound
                and cls._same_binding(getattr(owner_facade, member), value)
            )
        kind = cls.facade_member_kind(value)
        # A ``type`` alias is a type declaration by construction (t), except an
        # alias of a structural contract, which p owns; only a strongly typed
        # object whose owner binds nothing yet must move.
        alias_kind = (
            c.Infra.FacadeMemberKind.PROTOCOL
            if kind is c.Infra.FacadeMemberKind.PROTOCOL
            else c.Infra.FacadeMemberKind.TYPE
        )
        declared_owner = (
            config.Infra.tooling.facade_members.owners[alias_kind]
            if isinstance(value, TypeAliasType)
            else owner
        )
        return (
            declared_owner != letter
            and not bound
            and kind is not c.Infra.FacadeMemberKind.TYPE
        )

    @classmethod
    def facade_member_constraints(
        cls, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Derive the native ast-grep utilities of the facade-member rules.

        A member a non-owner facade letter re-exports while its owner binds
        the identical object yields one exact ``letter.member`` reference for
        the owner's relocation rule; the project's own duplicates also yield
        their name for the non-owner's retirement rule. References are derived
        over the project's package and every package its facades inherit
        from, so a consumer relocates inherited duplicates too. Alternation is
        per exact reference: a rule never matches a letter that does not
        re-export the member.

        Returns:
            Utility id ``<rule id>--<metavariable>`` to its native rule object.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        lineage = sorted({
            klass.__module__.partition(".")[0]
            for letter in letters
            if isinstance(facade := getattr(import_module(package), letter, None), type)
            for klass in facade.__mro__
        })
        references: dict[str, set[str]] = {}
        names: dict[str, set[str]] = {}
        for root, letter in ((root, letter) for root in lineage for letter in letters):
            facade = getattr(import_module(root), letter, None)
            if not isinstance(facade, type):
                continue
            for member in dir(facade):
                if not cls.foreign_facade_member(
                    root, (letter, member), c.Infra.FacadeMemberPlacement.EXPOSED
                ):
                    continue
                owner = cls.facade_member_owner(getattr(facade, member))
                references.setdefault(owner, set()).add(f"{letter}.{member}")
                if root == package:
                    names.setdefault(letter, set()).add(member)
        return {
            **{
                cls._utility_id(
                    c.Infra.FACADE_MEMBER_RELOCATE_RULE.format(letter=owner),
                    c.Infra.FACADE_MEMBER_REFERENCE_VAR,
                ): {"regex": cls._alternation(sorted(found))}
                for owner, found in sorted(references.items())
            },
            **{
                cls._utility_id(
                    c.Infra.FACADE_MEMBER_RETIRE_RULE.format(letter=letter),
                    c.Infra.FACADE_MEMBER_NAME_VAR,
                ): {"regex": cls._alternation(sorted(found))}
                for letter, found in sorted(names.items())
            },
        }

    @staticmethod
    def _utility_id(rule: str, variable: str) -> str:
        """Name the generated utility constraining one rule metavariable.

        Returns:
            ``<rule id>--<metavariable>``.

        """
        return c.Infra.FACADE_MEMBER_UTILITY_ID.format(rule=rule, variable=variable)

    @staticmethod
    def _alternation(texts: t.StrSequence) -> str:
        """Anchor an exact, sorted alternation of literal texts.

        Returns:
            A regex matching exactly one of ``texts``.

        """
        return "^(?:" + "|".join(re.escape(text) for text in texts) + ")$"

    @staticmethod
    def _declared_by(facade: type, member: str, package: str) -> bool:
        """Whether a class of ``package`` declares ``member`` in the facade MRO.

        Members a facade inherits from a third-party base (``model_dump`` from
        the model library) are that library's surface, not a re-export, and so
        are overrides of such members (``model_config``).

        Returns:
            Whether only classes of the package bind ``member`` in the MRO.

        """
        root = package.partition(".")[0]
        holders = tuple(klass for klass in facade.__mro__ if member in vars(klass))
        return bool(holders) and all(
            klass.__module__.partition(".")[0] == root for klass in holders
        )

    @staticmethod
    def _same_binding(left: p.AttributeProbe, right: p.AttributeProbe) -> bool:
        """Compare two bindings through the objects their aliases name.

        Returns:
            Whether both names bind the identical runtime object.

        """
        targets = tuple(
            value.__value__ if isinstance(value, TypeAliasType) else value
            for value in (left, right)
        )
        return targets[0] is targets[1]


__all__: list[str] = ["FlextInfraUtilitiesFacadeMembers"]
