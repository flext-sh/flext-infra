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
from importlib.util import find_spec
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
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodNativeUtilities,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
)


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
            # C method descriptors (``str.join``) are routines without
            # ``__module__``; typeshed declares it on every object.
            routine_module: str = getattr(origin, "__module__", "")
            if routine_module in policy.type_constructor_modules:
                return kind.TYPE
            return (
                kind.MODEL_DECLARATION
                if routine_module in policy.model_declaration_modules
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
    def library_members_owned_by(cls, library: str, letter: str) -> t.StrTuple:
        """Name a library's public members whose runtime object a letter owns.

        Each member is read from the imported library itself, so ownership
        follows the object's kind exactly as for a facade member.

        Returns:
            The sorted public member names the letter owns.

        """
        module = import_module(library)
        return tuple(
            sorted(
                name
                for name in getattr(module, "__all__", dir(module))
                if not name.startswith("_")
                and cls.facade_member_owner(getattr(module, name)) == letter
            )
        )

    @staticmethod
    def specialized_aliases(package: str) -> t.StrTuple:
        """Name the ``p`` aliases that specialize the same-named ``t`` generic.

        Returns:
            The sorted alias names; empty when the package is not installed
            or does not bind both letters.

        """
        if find_spec(package) is None:
            return ()
        module = import_module(package)
        protocols = getattr(module, c.Infra.FacadeFamily.P, None)
        typings = getattr(module, c.Infra.FacadeFamily.T, None)
        if protocols is None or typings is None:
            return ()
        return tuple(
            sorted(
                name
                for name in dir(protocols)
                if not name.startswith("_")
                and name in dir(typings)
                and isinstance(alias := getattr(protocols, name), TypeAliasType)
                and get_origin(alias.__value__) is getattr(typings, name)
            )
        )

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
        if not isinstance(facade, type) or not cls.declared_by_package(
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
    def facade_member_census(
        cls, project: Path
    ) -> t.Triple[
        t.StrSequence,
        t.MappingKV[str, frozenset[str]],
        t.MappingKV[str, frozenset[str]],
    ]:
        """Derive every foreign facade reference over the project's lineage.

        A member a non-owner facade letter re-exports while its owner binds
        the identical object yields one exact ``letter.member`` reference
        under its owner letter; the project's own duplicates also yield their
        name under the non-owner letter that declares them. A member the
        owner letter declares for its own kind also yields the reference of
        every other letter that binds no object, or the identical object,
        under that name: the consumer still spelling the retired receiver
        moves to the owner. References are derived over the core facade
        package, the project's package and every package its facades inherit
        from, so a consumer relocates inherited duplicates too. A facade whose
        ancestry cannot be imported fails here, loudly.

        Returns:
            The lineage packages, the references by owner letter and the
            project's duplicate names by declaring letter.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        lineage = cls.facade_member_lineage(package, letters)
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
        for root in lineage:
            for owner, reference in cls._owned_references(root, letters):
                references.setdefault(owner, set()).add(reference)
        return (
            lineage,
            {owner: frozenset(found) for owner, found in sorted(references.items())},
            {letter: frozenset(found) for letter, found in sorted(names.items())},
        )

    @staticmethod
    def facade_member_lineage(package: str, letters: t.StrSequence) -> t.StrTuple:
        """Name the core package, ``package`` and every package its facades extend.

        A project whose package is not installed has no runtime facades of its
        own; its consumers still face the core facades. An installed package
        that fails to import raises here.

        Returns:
            The facade-publishing root packages of the composition lineage.

        """
        ancestry = (
            {
                klass.__module__.partition(".")[0]
                for letter in letters
                if isinstance(
                    facade := getattr(import_module(package), letter, None), type
                )
                for klass in facade.__mro__
            }
            if find_spec(package) is not None
            else set[str]()
        )
        return tuple(
            root
            for root in sorted({c.Infra.PKG_CORE_UNDERSCORE, *ancestry})
            if any(
                isinstance(getattr(import_module(root), letter, None), type)
                for letter in letters
            )
        )

    @staticmethod
    def facade_member_family_files(root: Path) -> t.MappingKV[str, t.StrSequence]:
        """Group the project's facade-family files by the letter they produce.

        Returns:
            Native globs of each letter's family files.

        """
        families: dict[str, list[str]] = {}
        for path in FlextInfraUtilitiesProjectDiscovery.discover_python_files(
            root, workspace_excluded_top_dirs=frozenset()
        ):
            relative = path.relative_to(root)
            letter = FlextInfraUtilitiesCodegenNamespace.facade_family_of_source(
                relative
            )
            if letter is not None:
                families.setdefault(letter, []).append(f"**/{relative.as_posix()}")
        return {letter: tuple(sorted(found)) for letter, found in families.items()}

    @classmethod
    def _owned_references(
        cls, root: str, letters: t.StrSequence
    ) -> t.SequenceOf[t.StrPair]:
        """Reference every owned member through each other letter of ``root``.

        A letter that binds no object, or the owner's identical object, under
        the member's name is a receiver the consumer relocates to the owner.

        Returns:
            Each owner letter with one foreign ``letter.member`` reference.

        """
        module = import_module(root)
        facades = {
            letter: (facade, frozenset(dir(facade)))
            for letter in letters
            if isinstance(facade := getattr(module, letter, None), type)
        }
        return tuple(
            (owner, f"{letter}.{member}")
            for owner, value, member in cls._owned_members(root, letters)
            for letter, (facade, members) in facades.items()
            if letter != owner
            and (
                member not in members
                or cls._same_binding(getattr(facade, member), value)
            )
        )

    @classmethod
    def _owned_members(
        cls, root: str, letters: t.StrSequence
    ) -> t.SequenceOf[t.Triple[str, p.AttributeProbe, str]]:
        """Collect each public member a letter of ``root`` declares as owner.

        Returns:
            The owner letter, the bound object and the member name.

        """
        module = import_module(root)
        owned: list[t.Triple[str, p.AttributeProbe, str]] = []
        for owner in letters:
            facade = getattr(module, owner, None)
            if not isinstance(facade, type):
                continue
            for member in dir(facade):
                if member.startswith("_") or not cls.declared_by_package(
                    facade, member, root
                ):
                    continue
                value: p.AttributeProbe = getattr(facade, member)
                if cls.facade_member_owner(value) == owner:
                    owned.append((owner, value, member))
        return tuple(owned)

    @classmethod
    def codemod_facade_member_ownership_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the retirement and wrong-layer rules, one document per letter.

        A family module of letter ``L`` declaring a member another letter owns
        is a duplicate to retire when the owner already binds the identical
        object, and a misplaced declaration while the owner binds nothing
        under that name; both name sets come from the project's runtime
        facades, and each document is scoped to the exact family files of
        its letter.

        Returns:
            The rendered rule documents keyed by rule id.

        """
        del snapshot
        root = project.absolute()
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
        _lineage, _references, exposed = cls.facade_member_census(root)
        missing = cls._misplaced_members(package)
        families = cls.facade_member_family_files(root)
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        documents: dict[str, t.JsonMapping] = {}
        shapes = (
            (
                c.Infra.FACADE_MEMBER_RETIRE_SHAPE,
                exposed,
                {"severity": "error", "fix": ""},
                (
                    "`$NAME` is re-exported by a facade that does not own it: "
                    "`make mod` deletes this duplicate and relocates every consumer "
                    "to the owner."
                ),
            ),
            (
                c.Infra.FACADE_MEMBER_WRONG_LAYER_SHAPE,
                missing,
                {"severity": "warning"},
                (
                    "`$NAME` is declared in a facade layer that does not own its "
                    "kind: move this declaration into the owner family's module."
                ),
            ),
        )
        for shape, names, effect, message in shapes:
            for letter, found in sorted(names.items()):
                files = list[t.JsonValue](sorted(families.get(letter, ())))
                if not files or not found:
                    continue
                rule_id = f"{shape}{separator}{package}{separator}{letter}"
                documents[rule_id] = {
                    "id": rule_id,
                    "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                    **effect,
                    "files": files,
                    "constraints": {
                        c.Infra.FACADE_MEMBER_NAME_VAR: {
                            "regex": cls.exact_alternation(sorted(found))
                        }
                    },
                    "utils": {
                        "class-member": {
                            "kind": "block",
                            "inside": {"kind": "class_definition"},
                        }
                    },
                    "rule": cls._class_member_declaration(),
                    "message": message,
                }
        return documents

    @staticmethod
    def _class_member_declaration() -> t.JsonDict:
        """Match an assignment or type alias statement in a class body.

        Returns:
            The native rule capturing the declared name as ``$NAME``.

        """
        name = f"${c.Infra.FACADE_MEMBER_NAME_VAR}"
        return {
            "any": [
                {
                    "kind": "expression_statement",
                    "has": {
                        "kind": "assignment",
                        "has": {"field": "left", "kind": "identifier", "pattern": name},
                    },
                    "inside": {"matches": "class-member"},
                },
                {
                    "kind": "type_alias_statement",
                    "has": {
                        "field": "left",
                        "has": {"kind": "identifier", "pattern": name},
                    },
                    "inside": {"matches": "class-member"},
                },
            ]
        }

    @classmethod
    def _misplaced_members(cls, package: str) -> t.MappingKV[str, frozenset[str]]:
        """Collect each letter's members whose owner binds nothing under the name.

        Returns:
            The misplaced member names by declaring letter; empty for a
            package that is not installed.

        """
        if find_spec(package) is None:
            return {}
        module = import_module(package)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        found: dict[str, frozenset[str]] = {}
        for letter in letters:
            facade = getattr(module, letter, None)
            if not isinstance(facade, type):
                continue
            names = frozenset(
                member
                for member in dir(facade)
                if cls.foreign_facade_member(
                    package, (letter, member), c.Infra.FacadeMemberPlacement.MISSING
                )
            )
            if names:
                found[letter] = names
        return found

    @classmethod
    def codemod_facade_member_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the one rule relocating every foreign facade reference.

        A reference matches only as one of the exact foreign ``letter.member``
        texts of the census, through a receiver letter and an owner letter a
        module-level import from the lineage or the project's own packages
        binds, neither rebound at module level nor shadowed by an enclosing
        function's parameters, and never assigned through. Inside ``Literal``
        type data it never moves; inside ``Annotated`` only the callable of a
        complete metadata call does. One rewriter per owner letter emits the
        owner reference.

        Returns:
            The single native rule document keyed by its rule id, or nothing
            when the lineage re-exports no foreign member.

        """
        del snapshot
        lineage, references, _names = cls.facade_member_census(project)
        if not references:
            return {}
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        sources = sorted({
            *lineage,
            *FlextInfraUtilitiesCodemodNativeUtilities.codemod_own_package_names(
                project
            ),
        })
        rule_id = (
            f"{c.Infra.FACADE_MEMBER_RELOCATE_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        variable = c.Infra.FACADE_MEMBER_REFERENCE_VAR
        owners = {
            owner: cls.exact_alternation(sorted(found))
            for owner, found in references.items()
        }
        return {
            rule_id: {
                "id": rule_id,
                "language": "python",
                "severity": "error",
                "rule": {
                    "all": [
                        {"kind": "attribute"},
                        {"pattern": f"${variable}"},
                        {"pattern": "$RECEIVER.$MEMBER"},
                        {
                            "has": {
                                "field": "object",
                                "all": [
                                    {"pattern": "$RECEIVER"},
                                    cls.facade_letter_bound_rule(
                                        {"pattern": "$RECEIVER"}, sources
                                    ),
                                ],
                            }
                        },
                        {
                            "any": [
                                {
                                    "regex": pattern,
                                    "all": [
                                        cls.facade_letter_bound_rule(
                                            {"regex": f"^{re.escape(owner)}$"},
                                            sources,
                                        ),
                                        {
                                            "not": {
                                                "inside": {
                                                    "kind": "module",
                                                    "stopBy": "end",
                                                    "has": {
                                                        "kind": "assignment",
                                                        "stopBy": "end",
                                                        "has": {
                                                            "field": "left",
                                                            "pattern": (
                                                                f"{owner}.$MEMBER"
                                                            ),
                                                        },
                                                    },
                                                }
                                            }
                                        },
                                    ],
                                }
                                for owner, pattern in owners.items()
                            ]
                        },
                        {
                            "not": {
                                "inside": {
                                    "kind": "module",
                                    "stopBy": "end",
                                    "has": {
                                        "kind": "assignment",
                                        "stopBy": "end",
                                        "has": {
                                            "field": "left",
                                            "pattern": f"${variable}",
                                        },
                                    },
                                }
                            }
                        },
                        {
                            "not": {
                                "inside": {
                                    "kind": "subscript",
                                    "stopBy": "end",
                                    "has": {
                                        "field": "value",
                                        "regex": r"^(?:typing\.)?Literal$",
                                    },
                                }
                            }
                        },
                        {
                            "any": [
                                {
                                    "not": {
                                        "inside": {
                                            "kind": "subscript",
                                            "stopBy": "end",
                                            "has": {
                                                "field": "value",
                                                "regex": r"^(?:typing\.)?Annotated$",
                                            },
                                        }
                                    }
                                },
                                {
                                    "inside": {
                                        "kind": "call",
                                        "field": "function",
                                        "nthChild": {"position": "n+3"},
                                        "inside": {
                                            "kind": "subscript",
                                            "has": {
                                                "field": "value",
                                                "regex": r"^(?:typing\.)?Annotated$",
                                            },
                                        },
                                    }
                                },
                            ]
                        },
                    ]
                },
                "rewriters": [
                    {
                        "id": f"to-{owner}",
                        "rule": {"regex": pattern, "pattern": "$LETTER.$MEMBER"},
                        "fix": f"{owner}.$MEMBER",
                    }
                    for owner, pattern in owners.items()
                ],
                "transform": {
                    "OWNED": {
                        "rewrite": {
                            "source": f"${variable}",
                            "rewriters": [f"to-{owner}" for owner in owners],
                        }
                    }
                },
                "fix": "$OWNED",
                "message": (
                    f"Consume `${variable}` through its owner facade: `$OWNED`."
                ),
            }
        }

    @staticmethod
    def facade_letter_bound_rule(
        name: t.JsonMapping, sources: t.StrSequence
    ) -> t.JsonDict:
        """Match where a module-level facade import binds a letter unshadowed.

        ``name`` is the native rule of the letter's spelling: an exact regex
        or the pattern of a captured metavariable. The import comes from one
        of ``sources`` or is package-relative; the module never rebinds the
        letter at its top level and no enclosing function declares it as a
        parameter.

        Returns:
            The native rule of a stable module-level facade letter binding.

        """
        packages = "|".join(re.escape(source) for source in sources)
        return {
            "all": [
                {
                    "inside": {
                        "kind": "module",
                        "stopBy": "end",
                        "all": [
                            {
                                "has": {
                                    "kind": "import_from_statement",
                                    "all": [
                                        {
                                            "any": [
                                                {
                                                    "has": {
                                                        "field": "module_name",
                                                        "kind": "dotted_name",
                                                        "regex": (
                                                            rf"^(?:{packages})(?:\.|$)"
                                                        ),
                                                    }
                                                },
                                                {
                                                    "has": {
                                                        "field": "module_name",
                                                        "kind": "relative_import",
                                                    }
                                                },
                                            ]
                                        },
                                        {
                                            "any": [
                                                {
                                                    "has": {
                                                        "kind": "dotted_name",
                                                        "not": {
                                                            "inside": {
                                                                "kind": (
                                                                    "aliased_import"
                                                                )
                                                            }
                                                        },
                                                        **name,
                                                    }
                                                },
                                                {
                                                    "has": {
                                                        "kind": "aliased_import",
                                                        "has": {
                                                            "field": "alias",
                                                            **name,
                                                        },
                                                    }
                                                },
                                            ]
                                        },
                                    ],
                                }
                            },
                            {
                                "not": {
                                    "has": {
                                        "any": [
                                            {
                                                "kind": "expression_statement",
                                                "has": {
                                                    "kind": "assignment",
                                                    "has": {"field": "left", **name},
                                                },
                                            },
                                            {
                                                "kind": "class_definition",
                                                "has": {"field": "name", **name},
                                            },
                                            {
                                                "kind": "function_definition",
                                                "has": {"field": "name", **name},
                                            },
                                        ]
                                    }
                                }
                            },
                        ],
                    }
                },
                {
                    "not": {
                        "inside": {
                            "kind": "function_definition",
                            "stopBy": "end",
                            "has": {
                                "field": "parameters",
                                "has": {
                                    "any": [
                                        {"kind": "identifier", **name},
                                        {
                                            "any": [
                                                {"kind": "typed_parameter"},
                                                {"kind": "list_splat_pattern"},
                                                {"kind": "dictionary_splat_pattern"},
                                            ],
                                            "has": {
                                                "kind": "identifier",
                                                "nthChild": 1,
                                                **name,
                                            },
                                        },
                                        {
                                            "any": [
                                                {"kind": "default_parameter"},
                                                {"kind": "typed_default_parameter"},
                                            ],
                                            "has": {"field": "name", **name},
                                        },
                                    ]
                                },
                            },
                        }
                    }
                },
            ]
        }

    @staticmethod
    def exact_alternation(texts: t.StrSequence) -> str:
        """Anchor an exact, sorted alternation of literal texts.

        Returns:
            A regex matching exactly one of ``texts``.

        """
        return "^(?:" + "|".join(re.escape(text) for text in texts) + ")$"

    @staticmethod
    def declared_by_package(facade: type, member: str, package: str) -> bool:
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
