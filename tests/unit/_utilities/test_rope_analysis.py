"""Tests for Rope semantic analysis helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeAnalysis:
    """Behavior contract for Rope-backed semantic analysis."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("declarations", "base", "body", "expected"),
        [
            ("", "Exception", "pass", ()),
            ("", "object", "pass", ()),
            ("class Parent:\n    pass\n", "Parent", "pass", ()),
            (
                "class Parent(Exception):\n    class Shared:\n        pass\n",
                "Parent",
                "pass",
                ("Shared",),
            ),
            (
                (
                    "class Parent(object):\n    class Shared:\n        pass\n"
                    "class Middle(Parent):\n    pass\n"
                ),
                "Middle",
                "pass",
                ("Shared",),
            ),
            (
                "class Parent:\n    class Shared:\n        pass\n",
                "Parent",
                "class Shared:\n        pass",
                (),
            ),
            (
                (
                    "class Parent:\n    class Shared:\n        pass\n"
                    "class Left(Parent):\n    pass\n"
                    "class Right(Parent):\n    pass\n"
                ),
                "Left, Right",
                "pass",
                ("Shared",),
            ),
            (
                "from .provider import Parent\n",
                "Parent, Exception",
                "pass",
                ("Shared",),
            ),
        ],
    )
    def test_inherited_namespaces_require_source_scope_and_binding_identity(
        tmp_path: Path,
        declarations: str,
        base: str,
        body: str,
        expected: Sequence[str],
    ) -> None:
        """Builtin bases have no source scopes; actual nested bindings survive."""
        project, package = u.Tests.demo_project(tmp_path)
        (package / "provider.py").write_text(
            "class Parent(object):\n    class Shared:\n        pass\n",
            encoding="utf-8",
        )
        source = package / "consumer.py"
        content = declarations + f"class Consumer({base}):\n    " + body + "\n"
        source.write_text(content, encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            namespaces = u.Infra.inherited_facade_namespaces(
                rope_project,
                resource,
                class_name="Consumer",
            )
            tm.that(namespaces, eq=expected)
            tm.that(
                u.Infra.inherited_facade_namespaces(
                    rope_project,
                    resource,
                    class_name="Consumer",
                ),
                eq=namespaces,
            )
        tm.that(source.read_text(encoding="utf-8"), eq=content)

    @staticmethod
    def test_inherited_namespace_cycle_is_not_a_builtin_boundary(
        tmp_path: Path,
    ) -> None:
        """A source-defined cycle still fails instead of returning partial names."""
        project, package = u.Tests.demo_project(tmp_path)
        source = package / "consumer.py"
        source.write_text(
            "class Parent(Consumer):\n    pass\nclass Consumer(Parent):\n    pass\n",
            encoding="utf-8",
        )
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            with u.Tests.raises(
                ValueError, match="cyclic facade namespace inheritance"
            ):
                u.Infra.inherited_facade_namespaces(
                    rope_project,
                    resource,
                    class_name="Consumer",
                )

    @staticmethod
    def test_namespace_policy_retains_inherited_public_payload(tmp_path: Path) -> None:
        """The real policy consumer publishes inherited names without changing MRO."""
        project, package = u.Tests.demo_project(tmp_path)
        alias = next(iter(sorted(c.Infra.ALIAS_NAMES)))
        source = package / "api.py"
        content = (
            "class Parent(Exception):\n    class Shared:\n        pass\n"
            "class Consumer(Parent):\n    pass\n"
            f"{alias} = Consumer\n__all__ = ['Consumer', '{alias}']\n"
        )
        source.write_text(content, encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            policy = u.Infra.policy(source, rope_project=rope_project)
        tm.that(policy.inherited_namespaces, eq=("Shared",))
        tm.that(policy.expected_alias, eq=alias)
        tm.that(policy.model_dump()["inherited_namespaces"], eq=("Shared",))
        tm.that(source.read_text(encoding="utf-8"), eq=content)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("declaration", "expected"),
        [
            ("value = object", "object"),
            ("value = Exception", "Exception"),
            ("value = Exception()", "Exception"),
            ("class Parent:\n    pass\nvalue = Parent", "Parent"),
            ("class Parent:\n    pass\nvalue = Parent()", "Parent"),
            ("from .provider import Parent\nvalue = Parent", "Parent"),
            ("from .provider import Parent\nvalue = Parent()", "Parent"),
        ],
    )
    def test_superclass_name_uses_the_sdk_class_or_instance_type(
        tmp_path: Path,
        declaration: str,
        expected: str,
    ) -> None:
        """Real builtin, local, imported and inferred classes use public SDK APIs."""
        project, package = u.Tests.demo_project(tmp_path)
        (package / "provider.py").write_text(
            "class Parent:\n    pass\n",
            encoding="utf-8",
        )
        source = package / "consumer.py"
        source.write_text(declaration + "\n", encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            module = u.Infra.resolve_pymodule(rope_project, resource)
            value = module.get_attribute("value").get_object()
            tm.that(u.Infra.superclass_name(value), eq=expected)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("declaration", "message"),
        [
            ("def value():\n    pass\n", "not a class or inferred instance"),
            ("value = len\n", "not a class or inferred instance"),
            ("import os as value\n", "not a class or inferred instance"),
            ("value = missing\n", "cyclic Rope superclass type"),
        ],
    )
    def test_superclass_name_refuses_nonclass_or_unresolved_type(
        tmp_path: Path,
        declaration: str,
        message: str,
    ) -> None:
        """Unknown types and functions cannot masquerade as named superclasses."""
        project, package = u.Tests.demo_project(tmp_path)
        source = package / "consumer.py"
        source.write_text(declaration, encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            module = u.Infra.resolve_pymodule(rope_project, resource)
            value = module.get_attribute("value").get_object()
            with u.Tests.raises((TypeError, ValueError), match=message):
                u.Infra.superclass_name(value)

    @staticmethod
    @c.Tests.MARK.parametrize(
        "declaration",
        [
            "def invalid():\n    pass\nclass Consumer(invalid):\n    pass\n",
            "class Consumer(missing):\n    pass\n",
            "class Parent:\n    pass\nclass Consumer(Parent, missing):\n    pass\n",
        ],
    )
    def test_class_info_refuses_incomplete_superclass_lineage(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """SDK-omitted bases cannot turn an invalid class into a root namespace."""
        project, package = u.Tests.demo_project(tmp_path)
        source = package / "consumer.py"
        source.write_text(declaration, encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            with u.Tests.raises(ValueError, match="Unresolved Rope superclass lineage"):
                u.Infra.resolve_class_info(rope_project, resource)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("statement", "suffix"),
        [
            ("from . import Owner as Local", ".inner.leaf.Owner"),
            ("from .. import Owner as Local", ".inner.Owner"),
            ("from ... import Owner as Local", ".Owner"),
            ("from ..leaf import Owner as Local", ".inner.leaf.Owner"),
        ],
    )
    def test_declared_imports_preserve_relative_levels(
        tmp_path: Path,
        statement: str,
        suffix: str,
    ) -> None:
        """Bare dots and renamed symbols retain their actual package provenance."""
        project, package = u.Tests.demo_project(tmp_path)
        nested = package / "inner" / "leaf"
        nested.mkdir(parents=True)
        for directory in (package, nested.parent, nested):
            (directory / "__init__.py").write_text(
                "class Owner:\n    pass\n",
                encoding="utf-8",
            )
        source = nested / "consumer.py"
        source.write_text(
            statement + "\nimport os.path as path_alias\nfrom pathlib import Path\n",
            encoding="utf-8",
        )
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            imports = u.Infra.resolve_declared_module_imports(rope_project, resource)
        tm.that(imports["Local"], eq=package.name + suffix)
        tm.that(imports["path_alias"], eq="os.path")
        tm.that(imports["Path"], eq="pathlib.Path")

    @staticmethod
    def test_facade_namespaces_skip_builtin_bases(tmp_path: Path) -> None:
        """A builtin base has no source scope and contributes no namespace."""
        project, package = u.Tests.demo_project(tmp_path)
        source = package / "errors.py"
        source.write_text(
            "class Parent:\n"
            "    class Shared:\n        pass\n"
            "class Errors(Parent, Exception):\n    pass\n",
            encoding="utf-8",
        )
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            names = u.Infra.inherited_facade_namespaces(
                rope_project,
                resource,
                class_name="Errors",
            )
        tm.that(tuple(names), eq=("Shared",))

    @staticmethod
    def test_declared_imports_reject_relative_level_beyond_package(
        tmp_path: Path,
    ) -> None:
        """An invalid relative import is not converted into an absolute import."""
        project, package = u.Tests.demo_project(tmp_path)
        source = package / "consumer.py"
        source.write_text("from .. import Owner\n", encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            resource = tm.not_none(u.Infra.fetch_python_resource(rope_project, source))
            with u.Tests.raises(ImportError, match="beyond top-level package"):
                u.Infra.resolve_declared_module_imports(rope_project, resource)

    @staticmethod
    def test_ast_boundary_validates_before_traversal() -> None:
        """Accept actual ASTs and reject unrelated external runtime objects."""
        source_tree = ast.parse("value = 1")
        tree = u.Infra.ensure_ast_node(source_tree)
        tm.that(u.Infra.node_kind(tree), eq="Module")
        nodes = u.Infra.walk_ast_nodes(tree)
        tm.that(len(nodes), eq=len(list(ast.walk(source_tree))))
        parents = u.Infra.ast_parent_map(tree)
        child = u.Infra.ensure_ast_node(source_tree.body[0])
        tm.ok(u.Infra.module_level_node(child, parents))
        # The rejection names the offending runtime type; its prose is not a contract.
        with u.Tests.raises(TypeError, match=r"\bobject\b"):
            u.Infra.ensure_ast_node(object())
