"""Small Rope-driven text patch helpers for governed module aliases."""

from __future__ import annotations

import ast

from ._rope_analysis.exports import FlextInfraUtilitiesRopeAnalysisExports


class FlextInfraUtilitiesRopeModulePatch:
    """String-level patch helpers driven by Rope-discovered module rules."""

    @classmethod
    def ensure_runtime_alias(cls, source: str, *, alias: str, target_name: str) -> str:
        """Return source with one canonical runtime alias guaranteed."""
        updated = cls._ensure_alias_line(source, alias=alias, target_name=target_name)
        updated = cls._ensure_all_entry(updated, name=target_name)
        return cls._ensure_all_entry(updated, name=alias)

    @staticmethod
    def runtime_alias_bindings(
        source: str, *, alias: str
    ) -> tuple[ast.Assign | ast.AnnAssign, ...]:
        """Return only direct module bindings for the declared alias."""
        return tuple(
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == alias
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
        )

    @classmethod
    def _ensure_alias_line(cls, source: str, *, alias: str, target_name: str) -> str:
        """Repair module bindings without touching identically named class data."""
        bindings = cls.runtime_alias_bindings(source, alias=alias)
        if len(bindings) == 1:
            value = bindings[0].value
            if isinstance(value, ast.Name) and value.id == target_name:
                return source
        lines = source.splitlines(keepends=True)
        for binding in reversed(bindings):
            if isinstance(binding, ast.Assign) and len(binding.targets) != 1:
                message = f"ambiguous multi-target facade assignment for {alias}"
                raise ValueError(message)
            if binding.end_lineno is None or binding.end_col_offset is None:
                message = f"facade assignment has no complete source span: {alias}"
                raise ValueError(message)
            if lines[binding.lineno - 1][:binding.col_offset].strip() or (
                trailing := lines[binding.end_lineno - 1][binding.end_col_offset:].strip()
            ) and not trailing.startswith("#"):
                message = f"facade assignment shares a source line with another statement: {alias}"
                raise ValueError(message)
            del lines[binding.lineno - 1 : binding.end_lineno]
        return "".join(lines).rstrip() + f"\n\n{alias} = {target_name}\n"

    @staticmethod
    def _ensure_all_entry(source: str, *, name: str) -> str:
        """Publish the name using the canonical export parser and exact AST span."""
        exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(source)
        if name in exports:
            return source
        declarations = [
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
        ]
        if len(declarations) > 1:
            message = "ambiguous __all__ declarations during facade repair"
            raise ValueError(message)
        rendered = f"__all__: list[str] = {[*exports, name]!r}\n"
        if not declarations:
            return source.rstrip() + "\n\n" + rendered
        declaration = declarations[0]
        if (
            not isinstance(declaration.value, ast.List | ast.Tuple)
            or isinstance(declaration, ast.Assign) and len(declaration.targets) != 1
        ):
            message = "facade repair requires an explicit literal __all__ declaration"
            raise ValueError(message)
        lines = source.splitlines(keepends=True)
        if declaration.end_lineno is None or declaration.end_col_offset is None:
            message = "__all__ declaration has no complete source span"
            raise ValueError(message)
        if lines[declaration.lineno - 1][:declaration.col_offset].strip() or (
            trailing := lines[declaration.end_lineno - 1][declaration.end_col_offset:].strip()
        ) and not trailing.startswith("#"):
            message = "__all__ declaration shares a source line with another statement"
            raise ValueError(message)
        lines[declaration.lineno - 1 : declaration.end_lineno] = [rendered]
        return "".join(lines)


__all__: list[str] = ["FlextInfraUtilitiesRopeModulePatch"]
