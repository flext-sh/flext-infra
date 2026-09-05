"""Public-facade discovery for semantic private-import rewrites."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesPrivateImportFacades:
    """Derive public paths from live facade inheritance, never a registry."""

    @staticmethod
    def _facade_owner(
        *,
        sources: t.MappingKV[Path, str],
        package: str,
        facade_file: str,
        facade_alias: str,
    ) -> tuple[ast.Module, str] | None:
        """Return the live facade syntax tree and its assigned root class."""
        candidates = [
            source
            for path, source in sources.items()
            if path.name == facade_file
            and path.parent.name == package
            and path.parent.parent.name == "src"
        ]
        if len(candidates) > 1:
            msg = f"ambiguous public facade owner for {package}.{facade_file}"
            raise ValueError(msg)
        if not candidates:
            return None
        tree = ast.parse(candidates[0])
        root_name = next(
            (
                node.value.id
                for node in tree.body
                if isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == facade_alias
                and isinstance(node.value, ast.Name)
            ),
            None,
        )
        if root_name is None:
            return None
        return tree, root_name

    @staticmethod
    def private_layer(module: str) -> tuple[str, str, str] | None:
        """Derive package, facade filename, and alias from namespace law."""
        parts = module.split(".")
        for layer_name, layer_file in c.ENFORCEMENT_NAMESPACE_LAYER_MAP:
            family = f"_{layer_file}"
            if family not in parts:
                continue
            index = parts.index(family)
            package = ".".join(parts[:index])
            return package, f"{layer_file}.py", layer_name[0].lower()
        return None

    @classmethod
    def public_reference(
        cls,
        *,
        sources: t.MappingKV[Path, str],
        package: str,
        facade_file: str,
        facade_alias: str,
        qualified: str,
    ) -> str | None:
        """Resolve one private class to exactly one inherited facade path."""
        owner = cls._facade_owner(
            sources=sources,
            package=package,
            facade_file=facade_file,
            facade_alias=facade_alias,
        )
        if owner is None:
            return None
        tree, root_name = owner
        imports: dict[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if node.level > 1:
                msg = f"ambiguous relative facade import in {package}.{facade_file}"
                raise ValueError(msg)
            module = f"{package}.{node.module}" if node.level else node.module
            imports.update({
                imported.asname or imported.name: f"{module}.{imported.name}"
                for imported in node.names
            })
        root_class = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == root_name
            ),
            None,
        )
        if root_class is None:
            return None
        references: set[str] = set()

        def collect(node: ast.ClassDef, public_path: str) -> None:
            if any(
                isinstance(base, ast.Name) and imports.get(base.id) == qualified
                for base in node.bases
            ):
                references.add(public_path)
            for child in node.body:
                if isinstance(child, ast.ClassDef):
                    collect(child, f"{public_path}.{child.name}")

        collect(root_class, facade_alias)
        if not references:
            return None
        deepest = max(reference.count(".") for reference in references)
        canonical = {
            reference for reference in references if reference.count(".") == deepest
        }
        if len(canonical) > 1:
            msg = (
                f"ambiguous public facade references for {qualified}: "
                f"{sorted(canonical)}"
            )
            raise ValueError(msg)
        return canonical.pop()

    @classmethod
    def public_root_name(
        cls,
        *,
        sources: t.MappingKV[Path, str],
        package: str,
        facade_file: str,
        facade_alias: str,
    ) -> str | None:
        """Return the public long name assigned to a canonical facade alias."""
        owner = cls._facade_owner(
            sources=sources,
            package=package,
            facade_file=facade_file,
            facade_alias=facade_alias,
        )
        return owner[1] if owner is not None else None

    @staticmethod
    def require_unshadowed_alias(
        tree: ast.Module,
        package: str,
        alias: str,
        file_path: Path,
        removals: t.MappingKV[str, t.Infra.StrSet],
    ) -> None:
        """Reject any binding that would shadow the inserted public facade."""
        allowed_imports = {
            id(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and any(
                (
                    node.module == package
                    and imported.name == alias
                    and imported.asname is None
                )
                or (
                    node.module in removals
                    and imported.name in removals[node.module]
                    and (imported.asname or imported.name) == alias
                )
                for imported in node.names
            )
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom | ast.Import):
                if id(node) in allowed_imports:
                    continue
                if any(
                    (imported.asname or imported.name.split(".")[0]) == alias
                    for imported in node.names
                ):
                    break
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id == alias:
                    break
            elif isinstance(node, ast.arg) and node.arg == alias:
                break
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                if node.name == alias:
                    break
        else:
            return
        msg = f"public facade alias {alias} is shadowed in {file_path}"
        raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportFacades"]
