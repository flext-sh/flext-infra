"""Discovery-driven projection of utility owners onto the public facade."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesCodegenFacades:
    """Project utility owners required by real public-facade consumers."""

    @classmethod
    def render_utility_facade(cls, pkg_dir: Path) -> str | None:
        """Render uniquely discovered utility owners without a registry.

        Real ``u.<Namespace>.<method>()`` consumers select methods. Definitions
        under ``_utilities`` select their unique owners. Existing handwritten
        facade content remains unchanged except for missing imports and bases.
        """
        facade_path = pkg_dir / c.Infra.UTILITIES_PY
        owners_dir = pkg_dir / c.Infra.FAMILY_DIRECTORIES["u"]
        owners_exist, facade_exists = owners_dir.is_dir(), facade_path.is_file()
        # Why: only owners-without-facade is incomplete -- the owners would have
        # no public surface at all. A facade with no owners directory is the
        # legitimate pure re-export shape this same generator emits for a package
        # that adds no local utilities (src/flext: `class FlextRootUtilities(u)`),
        # and there is simply nothing to project onto it.
        if owners_exist and not facade_exists:
            message = f"utility owners in {pkg_dir} have no public facade"
            raise ValueError(message)
        if not owners_exist:
            return None
        owners, ancestors = cls._utility_owners(owners_dir)
        source: str = facade_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        nested_namespace = namespace is not facade
        reachable = cls._reachable_bases(
            tuple(cls._base_name(base) for base in namespace.bases), ancestors
        )
        additions: list[tuple[str, str]] = []
        for method in sorted(
            cls._required_methods(
                pkg_dir, facade_path, nested_namespace=nested_namespace
            )
        ):
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
            return source
        updated = cls._insert_imports(source, facade, additions, package=pkg_dir.name)
        _, namespace = cls._facade_classes(
            ast.parse(updated, filename=str(facade_path)), facade_path
        )
        return cls._insert_bases(updated, namespace, additions)

    @staticmethod
    def _required_methods(
        pkg_dir: Path, facade_path: Path, *, nested_namespace: bool
    ) -> frozenset[str]:
        methods: set[str] = set()
        for path in sorted(pkg_dir.rglob(f"*{c.Infra.EXT_PYTHON}")):
            if path == facade_path:
                continue
            tree = ast.parse(
                path.read_text(encoding=c.Cli.ENCODING_DEFAULT), filename=str(path)
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(
                    node.func, ast.Attribute
                ):
                    continue
                receiver = node.func.value
                if nested_namespace:
                    selected = (
                        isinstance(receiver, ast.Attribute)
                        and isinstance(receiver.value, ast.Name)
                        and receiver.value.id == "u"
                    )
                else:
                    selected = isinstance(receiver, ast.Name) and receiver.id == "u"
                if selected:
                    methods.add(node.func.attr)
        return frozenset(method for method in methods if not method.startswith("_"))

    @staticmethod
    def _utility_owners(
        owners_dir: Path,
    ) -> tuple[
        tuple[tuple[str, str, frozenset[str]], ...], t.MappingKV[str, frozenset[str]]
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
        if len(nested) > 1:
            message = f"expected at most one utility namespace class in {path}"
            raise ValueError(message)
        return facades[0], nested[0] if nested else facades[0]

    @classmethod
    def _base_name(cls, base: ast.expr) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        # Why: a generic base carries the same owner as its unsubscripted form.
        # `class X(FlextLdifUtilitiesTransformer[m.Ldif.Entry])` names
        # FlextLdifUtilitiesTransformer exactly like the bare base does, and the
        # type argument decides nothing about facade reachability.
        if isinstance(base, ast.Subscript):
            return cls._base_name(base.value)
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
        *,
        package: str,
    ) -> str:
        # The owner lives in the package being rendered. Naming this project
        # instead made every generated consumer facade import from flext-infra,
        # a module that does not exist in the consumer's own distribution.
        lines = source.splitlines(keepends=True)
        rendered = [
            f"from {package}._utilities.{module} import (\n    {class_name},\n)\n"
            for module, class_name in additions
        ]
        lines[facade.lineno - 1 : facade.lineno - 1] = [*rendered, "\n"]
        return "".join(lines)

    @staticmethod
    def _insert_bases(
        source: str, namespace: ast.ClassDef, additions: t.SequenceOf[tuple[str, str]]
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
