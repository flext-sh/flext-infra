"""Render deterministic source modules for generated model protocols.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import inspect

from flext_infra import p, t
from flext_infra.codegen._protocol_model_annotations import (
    FlextInfraCodegenProtocolModelAnnotations,
)


class FlextInfraCodegenProtocolModelRender:
    """Render one bounded protocol owner and the aggregate MRO owner."""

    @classmethod
    def protocol_class(cls, name: str, model: type[p.BaseModel]) -> str:
        """Render every validated model field and owned public property."""
        members: list[str] = []
        for field_name, field in model.model_fields.items():
            annotation = FlextInfraCodegenProtocolModelAnnotations.render(
                field.annotation
            )
            members.extend(cls._property(field_name, annotation))
        for property_name, annotation in cls._owned_properties(model).items():
            if property_name in model.model_fields:
                continue
            members.extend(cls._property(property_name, annotation))
        body = members or ["        pass"]
        return "\n".join([
            "    @runtime_checkable",
            f"    class {name}(pc.BaseModel, Protocol):",
            f'        """Structural contract generated from ``m.Infra.{name}``."""',
            "",
            *body,
        ])

    @classmethod
    def owner_module(cls, outer_name: str, classes: t.StrSequence) -> str:
        """Render one generated protocol owner module."""
        body = "\n\n".join(classes)
        type_names = cls._type_names(body)
        checking_imports = cls._checking_imports(type_names)
        checking_block = (
            "\nif TYPE_CHECKING:\n" + "\n".join(checking_imports) + "\n"
            if checking_imports
            else ""
        )
        return (
            '"""Generated Pydantic model protocols; do not edit manually.\n\n'
            "Copyright (c) 2025 FLEXT Team. All rights reserved.\n"
            'SPDX-License-Identifier: MIT\n"""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING, Protocol, runtime_checkable\n\n"
            "from flext_cli import p as pc\n"
            f"{checking_block}\n"
            "@runtime_checkable\n"
            f"class {outer_name}(Protocol):\n"
            '    """Generated structural protocols grouped by model owner."""\n\n'
            f"{body}\n\n"
            f'__all__: list[str] = ["{outer_name}"]\n'
        )

    @staticmethod
    def aggregate_module(
        owners: t.StrMapping,
        aliases: t.MappingKV[str, t.StrSequence],
        model_owner: t.StrMapping,
    ) -> str:
        """Render the single generated owner composed into ``p.Infra``."""
        imports = "\n".join(
            f"from flext_infra._protocols.{module} import {outer}"
            for module, outer in sorted(owners.items())
        )
        bases = ",\n        ".join((*owners.values(), "Protocol"))
        alias_lines: list[str] = []
        for alias_name, members in sorted(aliases.items()):
            rendered_members = " | ".join(
                f"{model_owner[member]}.{member}" for member in members
            )
            alias_lines.extend(["", f"    type {alias_name} = {rendered_members}"])
        return (
            '"""Aggregate generated model protocols for ``p.Infra``.\n\n'
            "Copyright (c) 2025 FLEXT Team. All rights reserved.\n"
            'SPDX-License-Identifier: MIT\n"""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import Protocol, runtime_checkable\n\n"
            f"{imports}\n\n\n"
            "@runtime_checkable\n"
            "class FlextInfraProtocolsGeneratedModels(\n"
            f"        {bases},\n"
            "):\n"
            '    """All source-referenced Pydantic model protocols."""\n'
            f"{'\n'.join(alias_lines)}\n\n"
            '__all__: list[str] = ["FlextInfraProtocolsGeneratedModels"]\n'
        )

    @staticmethod
    def _owned_properties(model: type[p.BaseModel]) -> t.StrMapping:
        """Return model/mixin properties, excluding Pydantic base internals."""
        properties: dict[str, str] = {}
        for base in reversed(model.__mro__):
            if base.__module__.startswith(("pydantic", "flext_core._models.pydantic")):
                continue
            for name, value in vars(base).items():
                if name.startswith("_") or not isinstance(value, property):
                    continue
                getter = value.fget
                if getter is None:
                    continue
                annotation = inspect.signature(getter).return_annotation
                if annotation is inspect.Signature.empty:
                    msg = f"public property lacks a return annotation: {base.__name__}.{name}"
                    raise TypeError(msg)
                properties[name] = FlextInfraCodegenProtocolModelAnnotations.render(
                    annotation
                )
        return properties

    @staticmethod
    def _property(name: str, annotation: str) -> list[str]:
        """Render one concise protocol property."""
        return [
            "        @property",
            f"        def {name}(self) -> {annotation}: ...",
            "",
        ]

    @staticmethod
    def _type_names(body: str) -> frozenset[str]:
        """Return import-relevant annotation identifiers from a rendered body."""
        return frozenset(
            token
            for token in (
                "AbstractSet",
                "Callable",
                "Iterable",
                "Iterator",
                "Mapping",
                "MutableMapping",
                "MutableSequence",
                "MutableSet",
                "Sequence",
                "Path",
                "UUID",
                "date",
                "datetime",
                "Literal",
                "c.",
                "p.",
                "t.",
            )
            if token in body
        )

    @staticmethod
    def _checking_imports(type_names: frozenset[str]) -> list[str]:
        """Render only the imports used by postponed annotations."""
        imports: list[str] = []
        collections = sorted(
            type_names.intersection({
                "AbstractSet",
                "Callable",
                "Iterable",
                "Iterator",
                "Mapping",
                "MutableMapping",
                "MutableSequence",
                "MutableSet",
                "Sequence",
            })
        )
        if collections:
            imports.append(f"    from collections.abc import {', '.join(collections)}")
        dates = sorted(type_names.intersection({"date", "datetime"}))
        if dates:
            imports.append(f"    from datetime import {', '.join(dates)}")
        if "Path" in type_names:
            imports.append("    from pathlib import Path")
        if "UUID" in type_names:
            imports.append("    from uuid import UUID")
        if "Literal" in type_names:
            imports.append("    from typing import Literal")
        facades = [name[0] for name in ("c.", "p.", "t.") if name in type_names]
        if facades:
            imports.append(f"    from flext_infra import {', '.join(facades)}")
        return imports


__all__: list[str] = ["FlextInfraCodegenProtocolModelRender"]
