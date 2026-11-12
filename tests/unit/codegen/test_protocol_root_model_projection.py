"""Protocol projection of models rooted in the ``m.RootModel`` preset.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import p, tm, u


class TestsProtocolRootModelProjection:
    """Generic RootModel presets project; stale facade bases fail loud."""

    @staticmethod
    def _workspace(tmp_path: Path, facade_bases: str) -> tuple[Path, Path]:
        """Build one package whose model extends ``m.RootModel[dict[str, V]]``.

        Returns:
            The repository root and the package directory.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        name = package.name
        imports = (
            f"from {name}._protocols import ProtocolsRetired\n" if facade_bases else ""
        )
        sources = {
            "_models/__init__.py": "",
            "_models/ingest.py": (
                "from flext_core import m\n"
                "class ModelsIngest:\n"
                "    class SummaryPerFile[V](m.RootModel[dict[str, V]]):\n"
                '        """One value per ingested file."""\n'
                "__all__ = ['ModelsIngest']\n"
            ),
            "models.py": (
                f"from {name}._models.ingest import ModelsIngest\n"
                "class Models(ModelsIngest): pass\n"
                "m = Models\n__all__ = ['Models', 'm']\n"
            ),
            "_protocols/__init__.py": "",
            "protocols.py": (
                imports
                + f"class Protocols{facade_bases}: pass\n"
                + "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
        }
        for relative, source in sources.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        return root, package

    @classmethod
    def test_generic_root_model_preset_projects_its_protocol(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A PEP 695 subclass of ``m.RootModel[...]`` reaches the public facade."""
        root, package = cls._workspace(tmp_path, "")
        with u.Infra.facade_source_project(root) as binding:
            projected = tm.ok(
                u.Infra.protocol_model_sources_from_source(root, binding[0])
            )
        holder = (package / "_protocols/ingest.py").relative_to(root)
        tm.ok(holder in projected)
        tm.ok("class SummaryPerFile" in projected[holder])
        for relative, source in projected.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, source))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}.protocols import p\n"
            "from flext_tests import tm\n"
            "summary = m.SummaryPerFile[int].model_validate({'a.csv': 1})\n"
            "tm.ok(isinstance(summary, p.SummaryPerFile))\n"
            "tm.that(summary.root, eq={'a.csv': 1})\n",
            cwd=root,
        )

    @classmethod
    def test_facade_base_without_source_class_names_file_class_and_base(
        cls, tmp_path: Path
    ) -> None:
        """A facade base whose declaring module is gone fails with its location."""
        root, _ = cls._workspace(tmp_path, "(ProtocolsRetired)")
        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(
                ValueError,
                match=(
                    r"protocols\.py:Protocols base ProtocolsRetired resolves to "
                    r"no source class"
                ),
            ),
        ):
            u.Infra.protocol_model_sources_from_source(root, binding[0])
