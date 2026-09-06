"""Semantic compatibility-alias cutover planning."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m

from .._utilities.compatibility_alias_cst import (
    FlextInfraUtilitiesCompatibilityAliasCst,
)
from .._utilities.compatibility_alias_validation import (
    FlextInfraUtilitiesCompatibilityAliasValidation,
)

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesCompatibilityAliases:
    """Plan atomic removal of API aliases and their proven consumers."""

    @classmethod
    def plan_api_alias_cutover(
        cls,
        *,
        root: Path,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModScanFinding],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Plan API alias removals and AST-proven consumer rewrites."""
        specs_by_file: dict[Path, dict[str, str]] = {}
        specs_by_module: dict[str, dict[str, str]] = {}
        for finding in findings:
            relative = finding.file
            if finding.rule_id != "ban-compat-alias" or relative.name != c.Infra.API_PY:
                continue
            parsed = ast.parse(finding.text)
            statement = parsed.body[0] if len(parsed.body) == 1 else None
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and isinstance(statement.value, ast.Name)
            ):
                msg = f"invalid compatibility-alias finding: {finding.text}"
                raise ValueError(msg)
            alias, target = statement.targets[0].id, statement.value.id
            owner = (root / relative).resolve()
            parts = relative.parts
            if "src" not in parts:
                msg = f"API alias owner is outside src: {relative}"
                raise ValueError(msg)
            source_index = parts.index("src")
            module_parts = [*parts[source_index + 1 : -1], relative.stem]
            module = ".".join(module_parts)
            package = module_parts[0]
            specs_by_file.setdefault(owner, {})[alias] = target
            for import_module in (module, package):
                current = specs_by_module.setdefault(import_module, {})
                if alias in current and current[alias] != target:
                    msg = f"ambiguous API alias {import_module}.{alias}"
                    raise ValueError(msg)
                current[alias] = target

        edits: list[m.Infra.SemanticMigrationEdit] = []
        for file_path, source in sources.items():
            if source.startswith("# AUTO-GENERATED FILE"):
                continue
            local_aliases = specs_by_file.get(file_path.resolve(), {})
            tree = ast.parse(source, filename=str(file_path))
            import_aliases: dict[str, dict[str, str]] = {}
            attribute_aliases: dict[tuple[str, str], str] = {}
            qualified_aliases = dict(local_aliases)
            target_bindings = cls._bound_names(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module in specs_by_module:
                    module_rewrites = specs_by_module[node.module]
                    for imported in node.names:
                        # Distinct name: `target` is already bound as a plain
                        # str while collecting the specs above, so reusing it
                        # would make this guard unreachable to a type checker.
                        imported_target = module_rewrites.get(imported.name)
                        if imported_target is None:
                            continue
                        import_aliases.setdefault(node.module, {})[imported.name] = (
                            imported_target
                        )
                        if imported.asname not in {None, imported.name}:
                            msg = (
                                "ambiguous compatibility import alias "
                                f"{imported.name} as {imported.asname} in {file_path}"
                            )
                            raise ValueError(msg)
                        qualified_aliases[f"{node.module}.{imported.name}"] = (
                            imported_target
                        )
                elif isinstance(node, ast.Import):
                    for imported in node.names:
                        # Distinct name: the ImportFrom branch above binds
                        # module_rewrites from a subscript, which is never
                        # optional, so reusing it here would make this guard
                        # unreachable to a type checker.
                        imported_rewrites = specs_by_module.get(imported.name)
                        if imported_rewrites is None:
                            continue
                        bound = imported.asname or imported.name
                        attribute_aliases.update(
                            ((bound, alias), target)
                            for alias, target in imported_rewrites.items()
                        )
            if not (local_aliases or import_aliases or attribute_aliases):
                continue
            FlextInfraUtilitiesCompatibilityAliasValidation.require_static_compatibility_alias_exports(
                tree, file_path, frozenset(local_aliases)
            )
            rewritten = FlextInfraUtilitiesCompatibilityAliasCst.rewrite_compatibility_alias_source(
                source,
                local_aliases=local_aliases,
                import_aliases=import_aliases,
                attribute_aliases=attribute_aliases,
                qualified_aliases=qualified_aliases,
                target_bindings=target_bindings,
            )
            FlextInfraUtilitiesCompatibilityAliasValidation.require_zero_compatibility_alias_residue(
                rewritten,
                file_path,
                qualified_aliases=qualified_aliases,
                exported_aliases=frozenset(local_aliases),
            )
            if rewritten != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=file_path,
                        original_source=source,
                        updated_source=rewritten,
                        changes=tuple(
                            f"rewired {alias} to {target}"
                            for alias, target in sorted(qualified_aliases.items())
                        ),
                    )
                )
        return tuple(edits)

    @staticmethod
    def _bound_names(tree: ast.AST) -> frozenset[str]:
        """Return statically bound module names for redundant-import removal."""
        names: set[str] = set()
        for node in getattr(tree, "body", ()):
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                names.update(item.asname or item.name for item in node.names)
            elif isinstance(node, ast.Import):
                names.update(
                    item.asname or item.name.split(".")[0] for item in node.names
                )
        return frozenset(names)


__all__: list[str] = ["FlextInfraUtilitiesCompatibilityAliases"]
