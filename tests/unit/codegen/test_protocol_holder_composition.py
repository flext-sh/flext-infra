"""Projected protocol holders compose into the public facade with one owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests import p, tm, u


class TestsProtocolHolderComposition:
    """Composition, collision ownership and copy-port derivation of the projector."""

    @staticmethod
    def _write(package: Path, sources: dict[str, str]) -> None:
        for relative, source in sources.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

    @staticmethod
    def _domain_workspace(
        tmp_path: Path, authored_scope: str | None
    ) -> tuple[Path, Path]:
        """Build one model domain whose part has no generated protocol yet.

        ``authored_scope`` optionally declares an authored public ``Scope``
        Protocol body that competes with the projected model contract.

        Returns:
            The repository root and the package directory.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        name = package.name
        authored = authored_scope is not None
        sources = {
            "models.py": (
                f"from {name}._models.git import ModelsGit\n"
                "class Models(ModelsGit): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            "protocols.py": (
                f"from {name}._protocols.git import ProtocolsGit\n"
                + (
                    f"from {name}._protocols.authored import ProtocolsAuthored\n"
                    "class Protocols(ProtocolsGit, ProtocolsAuthored): pass\n"
                    if authored
                    else "class Protocols(ProtocolsGit): pass\n"
                )
                + "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            "_models/git.py": (
                f"from {name}._models._git.part import ModelsGitPart\n"
                "class ModelsGit(ModelsGitPart): pass\n"
                "__all__ = ['ModelsGit']\n"
            ),
            "_models/_git/__init__.py": "",
            "_models/_git/part.py": (
                "from pydantic import BaseModel\n"
                "class ModelsGitPart:\n"
                "    class Scope(BaseModel):\n        root: str\n"
                "__all__ = ['ModelsGitPart']\n"
            ),
            "_protocols/__init__.py": "",
            "_protocols/git.py": (
                "class ProtocolsGit: pass\n__all__ = ['ProtocolsGit']\n"
            ),
            "_protocols/_git/__init__.py": "",
        }
        if authored_scope is not None:
            sources["_protocols/authored.py"] = (
                "from typing import Protocol, runtime_checkable\n"
                "class ProtocolsAuthored:\n"
                "    @runtime_checkable\n"
                "    class Scope(Protocol):\n"
                + authored_scope
                + "__all__ = ['ProtocolsAuthored']\n"
            )
        TestsProtocolHolderComposition._write(package, sources)
        return root, package

    @staticmethod
    def _class_bases(source: str, owner: str) -> tuple[str, ...]:
        return next(
            tuple(ast.unparse(base) for base in node.bases)
            for node in ast.parse(source).body
            if isinstance(node, ast.ClassDef) and node.name == owner
        )

    @staticmethod
    def _declares_member(source: str, member: str) -> bool:
        return any(
            isinstance(node, ast.ClassDef) and node.name == member
            for holder in ast.parse(source).body
            if isinstance(holder, ast.ClassDef)
            for node in holder.body
        )

    @classmethod
    def test_generated_part_holder_composes_into_public_facade(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A generated part holder is composed by its sibling and reached via ``p``."""
        root, package = cls._domain_workspace(tmp_path, None)
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        part = (package / "_protocols/_git/part.py").relative_to(root)
        sibling = (package / "_protocols/git.py").relative_to(root)
        tm.ok(part in projected)
        tm.ok(sibling in projected)
        holder = next(
            node.name
            for node in ast.parse(projected[part]).body
            if isinstance(node, ast.ClassDef)
        )
        family = f"{package.name}._protocols._git"
        tm.ok(f"from {family} import {holder}" in projected[sibling])
        tm.fail(f"from {family}.part import" in projected[sibling])
        tm.that(cls._class_bases(projected[sibling], "ProtocolsGit"), has=holder)
        for relative, source in projected.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            f"from {family} import {holder}\n"
            "from typing import is_protocol\n"
            "from flext_tests import tm\n"
            "tm.ok(is_protocol(p.Scope))\n"
            f"tm.ok(p.Scope is {holder}.Scope)\n"
            "tm.ok(isinstance(m.Scope(root='physical'), p.Scope))\n",
            cwd=root,
        )

    @classmethod
    def test_annotated_field_of_mutable_model_stays_writable(
        cls, tmp_path: Path
    ) -> None:
        """Pydantic metadata alone never turns a mutable field into a property."""
        root, package = cls._domain_workspace(tmp_path, None)
        cls._write(
            package,
            {
                "_models/_git/part.py": (
                    "from typing import Annotated\n"
                    "from pydantic import BaseModel, Field\n"
                    "class ModelsGitPart:\n"
                    "    class Scope(BaseModel):\n"
                    "        root: Annotated[str, Field(description='Root.')]\n"
                    "__all__ = ['ModelsGitPart']\n"
                ),
            },
        )
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        part = projected[(package / "_protocols/_git/part.py").relative_to(root)]
        scope = next(
            node
            for holder in ast.parse(part).body
            if isinstance(holder, ast.ClassDef)
            for node in holder.body
            if isinstance(node, ast.ClassDef) and node.name == "Scope"
        )
        attributes = {
            statement.target.id
            for statement in scope.body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        }
        tm.that(attributes, has="root")

    @classmethod
    def test_mirror_inherits_local_base_mirror_without_repeating_fields(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A model inheriting a sibling model gets a protocol inheriting its mirror."""
        root, package = cls._domain_workspace(tmp_path, None)
        cls._write(
            package,
            {
                "_models/_git/part.py": (
                    "from pydantic import BaseModel\n"
                    "class ModelsGitPart:\n"
                    "    class Scope(BaseModel):\n        root: str\n"
                    "    class Remote(Scope):\n        url: str\n"
                    "__all__ = ['ModelsGitPart']\n"
                ),
            },
        )
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        part = projected[(package / "_protocols/_git/part.py").relative_to(root)]
        holder = next(
            node for node in ast.parse(part).body if isinstance(node, ast.ClassDef)
        )
        contracts = {
            node.name: node for node in holder.body if isinstance(node, ast.ClassDef)
        }
        remote_bases = tuple(ast.unparse(base) for base in contracts["Remote"].bases)
        tm.that(remote_bases, has="Scope")
        remote_members = {
            node.name
            for node in contracts["Remote"].body
            if isinstance(node, ast.FunctionDef)
        }
        tm.that(remote_members, has="url")
        tm.fail("root" in remote_members)
        for relative, source in projected.items():
            path = root / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from flext_tests import tm\n"
            "remote = m.Remote(root='physical', url='git@host:r')\n"
            "tm.ok(isinstance(remote, p.Remote))\n"
            "tm.ok(isinstance(remote, p.Scope))\n",
            cwd=root,
        )

    @classmethod
    def test_new_mirror_package_receives_importable_initializer(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A mirror in a ``_protocols`` subpackage that does not exist yet imports."""
        root, package = cls._domain_workspace(tmp_path, None)
        (package / "_protocols/_git/__init__.py").unlink()
        (package / "_protocols/_git").rmdir()
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        part = (package / "_protocols/_git/part.py").relative_to(root)
        initializer = (package / "_protocols/_git/__init__.py").relative_to(root)
        tm.ok(initializer in projected)
        holder = next(
            node.name
            for node in ast.parse(projected[part]).body
            if isinstance(node, ast.ClassDef)
        )
        family = f"{package.name}._protocols._git"
        for relative, source in projected.items():
            path = root / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {family} import {holder}\n"
            "from flext_tests import tm\n"
            f"tm.ok({holder}.__module__ == {family + '.part'!r})\n",
            cwd=root,
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.protocols import p\n"
            f"from {family} import {holder}\n"
            "from flext_tests import tm\n"
            f"tm.ok(p.Scope is {holder}.Scope)\n",
            cwd=root,
        )

    @classmethod
    @pytest.mark.parametrize(
        ("authored_scope", "equivalent"),
        [
            ("        @property\n        def root(self) -> str: ...\n", True),
            ("        @property\n        def root(self) -> int: ...\n", False),
        ],
    )
    def test_authored_duplicate_resolves_to_one_owner(
        cls,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        authored_scope: str,
        *,
        equivalent: bool,
    ) -> None:
        """An equivalent authored port stays the owner; a divergent one blocks."""
        root, package = cls._domain_workspace(tmp_path, authored_scope)
        authored_path = package / "_protocols/authored.py"
        before = authored_path.read_text(encoding="utf-8")
        with u.Infra.facade_source_project(root) as binding:
            if not equivalent:
                with pytest.raises(ValueError, match="non-equivalent public Protocol"):
                    u.Infra.protocol_model_sources_from_source(root, binding[0])
                tm.that(authored_path.read_text(encoding="utf-8"), eq=before)
                return
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        tm.fail((package / "_protocols/_git/part.py").relative_to(root) in projected)
        for source in projected.values():
            tm.fail(cls._declares_member(source, "Scope"))
        sibling = projected[(package / "_protocols/git.py").relative_to(root)]
        tm.ok(f"from {package.name}._protocols import ProtocolsAuthored" in sibling)
        for relative, source in projected.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(authored_path.read_text(encoding="utf-8"), eq=before)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            f"from {package.name}._protocols import ProtocolsAuthored\n"
            "from flext_tests import tm\n"
            "tm.ok(p.Scope is ProtocolsAuthored.Scope)\n"
            "tm.ok(isinstance(m.Scope(root='physical'), p.Scope))\n",
            cwd=root,
        )

    @classmethod
    @pytest.mark.parametrize("upstream", [None, ("flext_cli", "FlextCliProtocols")])
    def test_copy_port_base_derives_from_facade_composition(
        cls, tmp_path: Path, upstream: tuple[str, str] | None
    ) -> None:
        """An unlisted package names the copy port through its own upstream chain."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-derived-sample",
            package_name="flext_derived_sample",
        )
        header, bases = (
            ("", "")
            if upstream is None
            else (f"from {upstream[0]} import {upstream[1]}\n", f"({upstream[1]})")
        )
        cls._write(
            package,
            {
                "models.py": (
                    "from flext_derived_sample._models.payload import "
                    "FlextDerivedSampleModelsPayload\n"
                    "class FlextDerivedSampleModels("
                    "FlextDerivedSampleModelsPayload): pass\n"
                    "m = FlextDerivedSampleModels\n"
                ),
                "protocols.py": (
                    f"{header}class FlextDerivedSampleProtocols{bases}: pass\n"
                    "p = FlextDerivedSampleProtocols\n"
                ),
                "_models/payload.py": (
                    "from pydantic import BaseModel\n"
                    "class FlextDerivedSampleModelsPayload:\n"
                    "    class Request(BaseModel):\n        name: str\n"
                ),
            },
        )
        with u.Infra.facade_source_project(root) as binding:
            planned = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        generated = planned[(package / "_protocols/payload.py").relative_to(root)]
        port = p.ModelCopy.__name__
        if upstream is None:
            supplier = p.ModelCopy.__module__.partition(".")[0]
            tm.ok(f"from {supplier} import " in generated)
            tm.ok(f".{port}, Protocol):" in generated)
        else:
            tm.ok(f"from {upstream[0]} import {upstream[1]}\n" in generated)
            tm.ok(f"class Request({upstream[1]}.{port}, Protocol):" in generated)
        tm.fail("from flext_core import p\n" in generated)
