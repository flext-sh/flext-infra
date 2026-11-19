"""Primary model layout admission waits for the protocols facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import tm, u


class TestsProtocolModelLayoutAdmission:
    """The primary package follows the namespace and tier admission rule."""

    @staticmethod
    def _package(tmp_path: Path, files: dict[str, str]) -> Path:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        for relative, source in {"_models/__init__.py": "", **files}.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        return root

    def test_package_without_protocols_facade_owns_no_model_layout(
        self, tmp_path: Path
    ) -> None:
        """Models without their protocols facade are skipped until gen creates it."""
        root = self._package(
            tmp_path,
            {"models.py": "class Models: pass\nm = Models\n__all__ = ['m']\n"},
        )
        with u.Infra.facade_source_project(root) as binding:
            tm.that(u.Infra.protocol_model_package_names(root, binding[0]), eq=())

    def test_package_without_models_facade_still_fails_loud(
        self, tmp_path: Path
    ) -> None:
        """A protocols facade without its models facade is never skipped."""
        root = self._package(
            tmp_path,
            {"protocols.py": "class Protocols: pass\np = Protocols\n__all__ = ['p']\n"},
        )
        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(ValueError, match="public facade source is absent"),
        ):
            u.Infra.protocol_model_package_names(root, binding[0])
