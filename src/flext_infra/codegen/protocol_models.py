"""Generate structural ``p.Infra`` contracts from referenced Pydantic models.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, TypeAliasType, get_args, get_origin

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen._protocol_model_render import (
    FlextInfraCodegenProtocolModelRender,
)


class FlextInfraCodegenProtocolModels:
    """Plan and apply a bounded, deterministic generated protocol layer."""

    _REFERENCE = c.Infra.compile(r"\bp\.Infra\.([A-Z][A-Za-z0-9_]*)")
    _DECLARATION = c.Infra.compile(r"(?m)^\s{4}class ([A-Z][A-Za-z0-9_]*)\(")
    _MAX_BODY_LINES = 170

    @classmethod
    def plan(cls, package_root: Path) -> p.Result[t.MappingKV[Path, str]]:
        """Render every source-referenced model protocol without writing files."""
        try:
            return cls._build_plan(package_root)
        except (AttributeError, OSError, TypeError, ValueError) as exc:
            return r[t.MappingKV[Path, str]].fail_op("generate model protocols", exc)

    @classmethod
    def _build_plan(cls, package_root: Path) -> p.Result[t.MappingKV[Path, str]]:
        """Build and format the generated model protocol file plan."""
        protocols_root = package_root / "_protocols"
        referenced = cls._referenced_names(package_root)
        manual = cls._manual_protocol_names(protocols_root)
        required = sorted(referenced.difference(manual))
        models, aliases = cls._resolve_models(required)
        plans, owners, model_owner = cls._render_owner_plans(protocols_root, models)
        aggregate = protocols_root / "generated_models.py"
        plans[aggregate] = FlextInfraCodegenProtocolModelRender.aggregate_module(
            owners, aliases, model_owner
        )
        formatted: dict[Path, str] = {}
        for path, source in plans.items():
            format_result = cls._format(path, source)
            if format_result.failure:
                return r[t.MappingKV[Path, str]].fail(
                    format_result.error or f"failed to format {path}"
                )
            formatted[path] = format_result.value
        return r[t.MappingKV[Path, str]].ok(formatted)

    @classmethod
    def apply(cls, package_root: Path, *, check_only: bool) -> p.Result[int]:
        """Check or write the generated protocol fixed point."""
        plan_result = cls.plan(package_root)
        if plan_result.failure:
            return r[int].fail(plan_result.error or "protocol generation failed")
        changed = tuple(
            (path, source)
            for path, source in plan_result.value.items()
            if not path.exists()
            or path.read_text(encoding=c.Cli.ENCODING_DEFAULT) != source
        )
        if check_only and changed:
            return r[int].fail(
                "generated model protocol drift: "
                + ", ".join(str(path) for path, _source in changed)
            )
        for path, source in changed:
            write_result = u.Cli.files_write_text(path, source)
            if write_result.failure:
                return r[int].fail(write_result.error or f"failed to write {path}")
        return r[int].ok(len(changed))

    @classmethod
    def _referenced_names(cls, package_root: Path) -> frozenset[str]:
        """Discover the exact public protocol names consumed by source."""
        names: set[str] = set()
        for path in sorted(package_root.rglob(c.Infra.EXT_PYTHON_GLOB)):
            if path.name.startswith("_generated_models_"):
                continue
            names.update(
                cls._REFERENCE.findall(path.read_text(encoding=c.Cli.ENCODING_DEFAULT))
            )
        return frozenset(names)

    @classmethod
    def _manual_protocol_names(cls, protocols_root: Path) -> frozenset[str]:
        """Return handwritten protocol declarations, excluding generated owners."""
        names: set[str] = set()
        for path in sorted(protocols_root.glob(c.Infra.EXT_PYTHON_GLOB)):
            if path.name.startswith("_generated_models_"):
                continue
            names.update(
                cls._DECLARATION.findall(
                    path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
                )
            )
        return frozenset(names)

    @classmethod
    def _resolve_models(
        cls, required: t.StrSequence
    ) -> tuple[t.MappingKV[str, type[p.BaseModel]], t.StrSequenceMapping]:
        """Resolve required models and expand discriminated union aliases."""
        models: dict[str, type[p.BaseModel]] = {}
        aliases: dict[str, t.StrSequence] = {}
        for name in required:
            value = getattr(m.Infra, name)
            if isinstance(value, TypeAliasType):
                members = cls._alias_model_names(value)
                aliases[name] = members
                for member in members:
                    models[member] = getattr(m.Infra, member)
                continue
            if not isinstance(value, type) or not issubclass(value, m.BaseModel):
                msg = f"p.Infra.{name} has no Pydantic model owner"
                raise TypeError(msg)
            models[name] = value
        return models, aliases

    @classmethod
    def _alias_model_names(cls, alias: TypeAliasType) -> t.StrSequence:
        """Return every Pydantic leaf in a validated model union alias."""
        value = alias.__value__
        if get_origin(value) is Annotated:
            value = get_args(value)[0]
        members = tuple(
            argument.__name__
            for argument in get_args(value)
            if isinstance(argument, type) and issubclass(argument, m.BaseModel)
        )
        if not members:
            msg = f"model protocol alias has no Pydantic members: {alias.__name__}"
            raise TypeError(msg)
        return members

    @classmethod
    def _render_owner_plans(
        cls, protocols_root: Path, models: t.MappingKV[str, type[p.BaseModel]]
    ) -> tuple[dict[Path, str], dict[str, str], dict[str, str]]:
        """Split model protocols by canonical model module and bounded part size."""
        grouped: dict[str, list[tuple[str, str]]] = {}
        for name, model in sorted(models.items()):
            owner = model.__module__.rsplit(".", maxsplit=1)[-1]
            rendered = FlextInfraCodegenProtocolModelRender.protocol_class(name, model)
            grouped.setdefault(owner, []).append((name, rendered))
        plans: dict[Path, str] = {}
        owners: dict[str, str] = {}
        model_owner: dict[str, str] = {}
        for owner, classes in sorted(grouped.items()):
            chunks = cls._chunks(classes)
            owner_stem = "".join(token.title() for token in owner.split("_"))
            for index, chunk in enumerate(chunks, start=1):
                module = f"_generated_models_{owner}_part_{index:02d}"
                outer = f"FlextInfraProtocolsGenerated{owner_stem}Part{index:02d}"
                owners[module] = outer
                for name, _source in chunk:
                    model_owner[name] = outer
                plans[protocols_root / f"{module}.py"] = (
                    FlextInfraCodegenProtocolModelRender.owner_module(
                        outer, tuple(source for _name, source in chunk)
                    )
                )
        return plans, owners, model_owner

    @classmethod
    def _chunks(
        cls, classes: t.SequenceOf[tuple[str, str]]
    ) -> tuple[tuple[tuple[str, str], ...], ...]:
        """Keep each generated owner below the configured logical-size ceiling."""
        chunks: list[tuple[tuple[str, str], ...]] = []
        current: list[tuple[str, str]] = []
        lines = 0
        for item in classes:
            item_lines = item[1].count("\n") + 2
            if current and lines + item_lines > cls._MAX_BODY_LINES:
                chunks.append(tuple(current))
                current = []
                lines = 0
            current.append(item)
            lines += item_lines
        if current:
            chunks.append(tuple(current))
        return tuple(chunks)

    @staticmethod
    def _format(path: Path, source: str) -> p.Result[str]:
        """Format and lint generated source through the canonical Ruff binary."""
        result = u.Cli.run_raw(
            [c.Infra.RUFF, c.Infra.FORMAT, "--stdin-filename", str(path), "-"],
            cwd=path.parent,
            input_data=source.encode(c.Cli.ENCODING_DEFAULT),
        )
        if result.failure:
            return r[str].fail(result.error or f"ruff format failed for {path}")
        output = result.value
        if output.exit_code != 0:
            return r[str].fail(output.stderr or output.stdout)
        return r[str].ok(output.stdout.rstrip() + "\n")


__all__: list[str] = ["FlextInfraCodegenProtocolModels"]
