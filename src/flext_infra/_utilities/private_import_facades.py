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
    def private_owner(module: str) -> str | None:
        """Return the owner preceding the first private module segment."""
        parts = module.split(".")
        private_index = next(
            (
                index
                for index, part in enumerate(parts)
                if len(part) > 1 and part.startswith("_") and part[1].isalpha()
            ),
            None,
        )
        if private_index in {None, 0}:
            return None
        return ".".join(parts[:private_index])

    @staticmethod
    def discover(
        sources: t.MappingKV[Path, str],
    ) -> t.MappingKV[str, tuple[tuple[ast.Module, str, str, str], ...]]:
        """Discover facade aliases and roots from live source assignments."""
        discovered: dict[str, list[tuple[ast.Module, str, str, str]]] = {}
        for path, source in sorted(sources.items()):
            source_index = next(
                (
                    index
                    for index in range(len(path.parts) - 1, -1, -1)
                    if path.parts[index] == c.Infra.DEFAULT_SRC_DIR
                ),
                None,
            )
            if source_index is None or path.name == c.Infra.INIT_PY:
                continue
            package = ".".join(path.parts[source_index + 1 : -1])
            if not package:
                continue
            tree = ast.parse(source, filename=str(path))
            class_names = {
                node.name for node in tree.body if isinstance(node, ast.ClassDef)
            }
            owners: set[tuple[str, str]] = set()
            for node in tree.body:
                target: ast.expr | None = None
                value: ast.expr | None = None
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target, value = node.targets[0], node.value
                elif isinstance(node, ast.AnnAssign):
                    target, value = node.target, node.value
                if (
                    isinstance(target, ast.Name)
                    and len(target.id) == 1
                    and target.id.islower()
                    and isinstance(value, ast.Name)
                    and value.id in class_names
                ):
                    owners.add((target.id, value.id))
            for alias, root_name in sorted(owners):
                discovered.setdefault(package, []).append((
                    tree,
                    alias,
                    root_name,
                    path.name,
                ))
        return {
            package: tuple(owners) for package, owners in sorted(discovered.items())
        }

    @staticmethod
    def public_reference(
        *,
        owners: t.SequenceOf[tuple[ast.Module, str, str, str]],
        package: str,
        qualified: str,
    ) -> str | None:
        """Resolve one private class to exactly one inherited facade path."""
        references: set[str] = set()
        for tree, facade_alias, root_name, facade_file in owners:
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
                continue

            def collect(
                node: ast.ClassDef,
                public_path: str,
                imports: dict[str, str] = imports,
                qualified: str = qualified,
            ) -> None:
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

    @staticmethod
    def public_root_name(
        *, owners: t.SequenceOf[tuple[ast.Module, str, str, str]], facade_alias: str
    ) -> str | None:
        """Return the public long name assigned to a canonical facade alias."""
        roots = {
            root_name
            for _tree, alias, root_name, _facade_file in owners
            if alias == facade_alias
        }
        if len(roots) > 1:
            msg = f"ambiguous public facade root for alias {facade_alias}"
            raise ValueError(msg)
        return next(iter(roots), None)

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
            elif isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):
                if node.name == alias:
                    break
        else:
            return
        msg = f"public facade alias {alias} is shadowed in {file_path}"
        raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportFacades"]
