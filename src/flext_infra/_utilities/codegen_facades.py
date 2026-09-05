"""Discovery-driven projection of utility owners onto the public facade."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraUtilitiesCodegenFacades:
    """Project utility owners required by real public-facade consumers."""

    @classmethod
    def project_semantic_utility_owners(
        cls, *, pkg_dir: Path, ctx: m.Infra.FixContext
    ) -> None:
        """Project uniquely discovered semantic owners without a registry.

        The executable ``codemod/semantic_apply.py`` consumer selects methods.
        Definitions under ``_utilities`` select their unique owners. Existing
        handwritten facade content remains unchanged except for missing imports
        and bases.
        """
        semantic_path = pkg_dir / "codemod" / "semantic_apply.py"
        facade_path = pkg_dir / c.Infra.UTILITIES_PY
        owners_dir = pkg_dir / c.Infra.FAMILY_DIRECTORIES["u"]
        semantic_exists, facade_exists = semantic_path.is_file(), facade_path.is_file()
        if semantic_exists != facade_exists:
            message = f"incomplete semantic utility artifacts in {pkg_dir}"
            raise ValueError(message)
        if not semantic_exists:
            return
        owners, ancestors = cls._utility_owners(owners_dir)
        source = facade_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        reachable = cls._reachable_bases(
            tuple(cls._base_name(base) for base in namespace.bases), ancestors
        )
        additions: list[tuple[str, str]] = []
        for method in sorted(cls._semantic_methods(semantic_path)):
            candidates = tuple(
                (module, class_name)
                for module, class_name, methods in owners
                if method in methods
            )
            if not candidates or any(
                class_name in reachable for _module, class_name in candidates
            ):
                continue
            if len(candidates) != 1:
                detail = ", ".join(f"{module}:{name}" for module, name in candidates)
                message = f"ambiguous u.Infra owner for {method}: {detail}"
                raise ValueError(message)
            module, class_name = candidates[0]
            additions.append((module, class_name))
            reachable.update(cls._reachable_bases((class_name,), ancestors))
        if not additions:
            return
        updated = cls._insert_imports(source, facade, additions)
        _, namespace = cls._facade_classes(
            ast.parse(updated, filename=str(facade_path)), facade_path
        )
        updated = cls._insert_bases(updated, namespace, additions)
        written = u.Cli.atomic_write_text_file(facade_path, updated)
        if written.failure:
            message = written.error or f"writing utility facade {facade_path}"
            raise OSError(message)
        ctx.files_modified.add(str(facade_path))
        for module, class_name in additions:
            ctx.fix(
                module=str(facade_path),
                rule="UTILITY-FACADE",
                line=facade.lineno,
                message=f"projected {module}.{class_name} from semantic consumer",
            )

    @staticmethod
    def _semantic_methods(path: Path) -> frozenset[str]:
        tree = ast.parse(
            path.read_text(encoding=c.Cli.ENCODING_DEFAULT), filename=str(path)
        )
        return frozenset(
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "u"
            and node.func.value.attr == "Infra"
        )

    @staticmethod
    def _utility_owners(
        owners_dir: Path,
    ) -> tuple[
        tuple[tuple[str, str, frozenset[str]], ...],
        t.MappingKV[str, frozenset[str]],
    ]:
        owners: list[tuple[str, str, frozenset[str]]] = []
        ancestors: dict[str, frozenset[str]] = {}
        for path in sorted(owners_dir.glob("*.py")):
            if path.name == c.Infra.INIT_PY:
                continue
            tree = ast.parse(
                path.read_text(encoding=c.Cli.ENCODING_DEFAULT), filename=str(path)
            )
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                methods = frozenset(
                    member.name
                    for member in node.body
                    if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
                    and not member.name.startswith("_")
                )
                owners.append((path.stem, node.name, methods))
                ancestors[node.name] = frozenset(
                    name
                    for base in node.bases
                    if (name := FlextInfraUtilitiesCodegenFacades._base_name(base))
                )
        return tuple(owners), ancestors

    @staticmethod
    def _facade_classes(
        tree: ast.Module, path: Path
    ) -> tuple[ast.ClassDef, ast.ClassDef]:
        facades = tuple(node for node in tree.body if isinstance(node, ast.ClassDef))
        if len(facades) != 1:
            message = f"expected one utility facade class in {path}"
            raise ValueError(message)
        nested = tuple(
            node for node in facades[0].body if isinstance(node, ast.ClassDef)
        )
        if len(nested) != 1:
            message = f"expected one utility namespace class in {path}"
            raise ValueError(message)
        return facades[0], nested[0]

    @staticmethod
    def _base_name(base: ast.expr) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        message = f"unsupported utility facade base: {ast.dump(base)}"
        raise ValueError(message)

    @staticmethod
    def _reachable_bases(
        roots: t.SequenceOf[str], ancestors: t.MappingKV[str, frozenset[str]]
    ) -> set[str]:
        reachable = set(roots)
        pending = list(roots)
        while pending:
            for base in ancestors.get(pending.pop(), frozenset()):
                if base not in reachable:
                    reachable.add(base)
                    pending.append(base)
        return reachable

    @staticmethod
    def _insert_imports(
        source: str,
        facade: ast.ClassDef,
        additions: t.SequenceOf[tuple[str, str]],
    ) -> str:
        lines = source.splitlines(keepends=True)
        rendered = [
            f"from flext_infra._utilities.{module} import (\n"
            f"    {class_name},\n"
            ")\n"
            for module, class_name in additions
        ]
        lines[facade.lineno - 1 : facade.lineno - 1] = [*rendered, "\n"]
        return "".join(lines)

    @staticmethod
    def _insert_bases(
        source: str,
        namespace: ast.ClassDef,
        additions: t.SequenceOf[tuple[str, str]],
    ) -> str:
        if not namespace.bases:
            message = "utility namespace has no canonical base chain"
            raise ValueError(message)
        last_base = namespace.bases[-1]
        if last_base.end_lineno is None:
            message = "utility namespace base has no source span"
            raise ValueError(message)
        lines = source.splitlines(keepends=True)
        indent = " " * last_base.col_offset
        lines[last_base.end_lineno : last_base.end_lineno] = [
            f"{indent}{class_name},\n" for _module, class_name in additions
        ]
        return "".join(lines)


__all__: list[str] = ["FlextInfraUtilitiesCodegenFacades"]
