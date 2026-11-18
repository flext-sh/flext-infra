"""Authenticated selection of a canonical protocol domain composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, p, tm, u


class TestsProtocolDomainProjection:
    """Domain projection retains the complete planner's collision contract."""

    @staticmethod
    def _workspace(
        tmp_path: Path,
        metadata_fields: str = (
            "        @property\n        def required(self) -> str: ...\n"
        ),
    ) -> tuple[Path, Path]:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        name = package.name
        sources = {
            "models.py": (
                f"from {name}._models.git import ModelsGit\n"
                f"from {name}._models.conflict import ModelsConflict\n"
                "class Models(ModelsGit, ModelsConflict): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            "protocols.py": (
                f"from {name}._protocols.git import ProtocolsGit\n"
                f"from {name}._protocols.authored import ProtocolsAuthored\n"
                "class Protocols(ProtocolsGit, ProtocolsAuthored): pass\n"
                "p = Protocols\n__all__ = ['Protocols', 'p']\n"
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
            "_models/conflict.py": (
                "from pydantic import BaseModel\n"
                "class ModelsConflict:\n"
                "    class Metadata(BaseModel):\n"
                "        required: str\n        missing: int\n"
                "__all__ = ['ModelsConflict']\n"
            ),
            "_protocols/git.py": (
                "class ProtocolsGit: pass\n__all__ = ['ProtocolsGit']\n"
            ),
            # The composed sibling imports its part through this family package.
            "_protocols/_git/__init__.py": (
                f"from {name}._protocols._git.part import ProtocolsGitPart\n"
                "__all__ = ['ProtocolsGitPart']\n"
            ),
            "_protocols/_git/part.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class ProtocolsGitPart:\n"
                "    @runtime_checkable\n"
                "    class Scope(Protocol):\n"
                "        @property\n        def root(self) -> str: ...\n"
                "__all__ = ['ProtocolsGitPart']\n"
            ),
            "_protocols/authored.py": (
                "from typing import Protocol, runtime_checkable\n"
                "class ProtocolsAuthored:\n"
                "    @runtime_checkable\n"
                "    class Metadata(Protocol):\n"
                + metadata_fields
                + "__all__ = ['ProtocolsAuthored']\n"
            ),
        }
        for relative, source in sources.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        return root, package

    @classmethod
    @c.Tests.MARK.parametrize(
        "metadata_fields",
        [
            "        @property\n        def required(self) -> str: ...\n",
            "        required: int\n        missing: int\n",
            (
                "        @property\n        def required(self) -> str: ...\n"
                "        @property\n        def missing(self) -> int: ...\n"
            ),
        ],
    )
    def test_selected_domain_is_public_and_global_collision_still_fails(
        cls,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        metadata_fields: str,
    ) -> None:
        """A real model satisfies the selected Protocol after its holder projection."""
        root, package = cls._workspace(tmp_path, metadata_fields)
        reference = m.Infra.SourceClassReference(
            target=f"{package.name}._models.git", attributes=("ModelsGit",)
        )
        with u.Infra.facade_source_project(root) as binding:
            for module, owner, source in (
                ("models", "Models.Metadata", "_models/conflict.py"),
                ("protocols", "Protocols.Metadata", "_protocols/authored.py"),
            ):
                declaration = u.Infra.qualified_name(
                    binding[0], owner, module_name=f"{package.name}.{module}"
                ).get_object()
                resource = tm.not_none(
                    tm.not_none(declaration.get_module()).get_resource()
                )
                tm.that(Path(resource.real_path), eq=package / source)
            with u.Tests.raises(ValueError, match="non-equivalent public Protocol"):
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(
                    root, binding[0], domain_owner=reference
                )
            )
        destination = package / "_protocols/git.py"
        tm.that(tuple(projected), eq=(destination.relative_to(root),))
        tm.ok(
            u.Cli.atomic_write_text_file(
                destination, projected[destination.relative_to(root)]
            )
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from typing import is_protocol\n"
            "from flext_tests import tm\n"
            "tm.ok(is_protocol(p.Scope))\n"
            "tm.ok(isinstance(m.Scope(root='physical'), p.Scope))\n",
            cwd=root,
        )

    @classmethod
    @c.Tests.MARK.parametrize("target", ["pydantic", "models"])
    def test_selection_rejects_owner_outside_public_domain(
        cls, tmp_path: Path, target: str
    ) -> None:
        """An exact source identity alone cannot authorize an unrelated holder."""
        root, package = cls._workspace(tmp_path)
        module, name = (
            ("pydantic", "BaseModel")
            if target == "pydantic"
            else (f"{package.name}.models", "Models")
        )
        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(ValueError, match="domain"),
        ):
            u.Infra.protocol_model_sources_from_source(
                root,
                binding[0],
                domain_owner=m.Infra.SourceClassReference(
                    target=module, attributes=(name,)
                ),
            )
