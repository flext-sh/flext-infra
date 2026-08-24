"""Tests that lazy-init never generates a bootstrap into its own import chain.

Every generated initializer opens with ``from flext_core.lazy import ...``. That
module imports ``._lazy_parts`` at module scope, which reaches ``._typings`` and
the remaining private facets. Writing a generated bootstrap into any of those
packages therefore re-enters a module that is still initializing and raises
``cannot import name 'build_lazy_import_map' from partially initialized module``.
The private surface of the bootstrap-owning distribution keeps side-effect-free
initializers; private packages of every other distribution are unaffected.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm
from tests import c, u

if TYPE_CHECKING:
    from pathlib import Path


def _write_bootstrap_owner(package_root: Path, subpackage: str) -> Path:
    """Create a private facet of the bootstrap-owning distribution."""
    facet_dir = package_root / subpackage
    facet_dir.mkdir()
    (facet_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
    (facet_dir / "part.py").write_text(
        '"""Bootstrap implementation detail."""\n\n'
        "class FlextLazyPart:\n"
        '    """Bootstrap owner."""\n\n'
        '__all__ = ["FlextLazyPart"]\n',
        encoding=c.Cli.ENCODING_DEFAULT,
    )
    return facet_dir


class TestsFlextInfraLazyInitBootstrapPackage:
    """The bootstrap import chain is never generated into a cycle."""

    def test_bootstrap_owner_private_facets_stay_side_effect_free(
        self, tmp_path: Path
    ) -> None:
        """Private facets of the bootstrap owner never import the bootstrap."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name=c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE.replace("_", "-"),
            package_name=c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE,
        )
        lazy_parts = _write_bootstrap_owner(package_root, "_lazy_parts")
        typings = _write_bootstrap_owner(package_root, "_typings")

        result = u.Tests.run_lazy_init(workspace_root)

        tm.that(result, eq=0)
        for facet in (lazy_parts, typings):
            init_content = (facet / c.Infra.INIT_PY).read_text(
                encoding=c.Cli.ENCODING_DEFAULT
            )
            tm.that(init_content, lacks="from flext_core.lazy import")
            tm.that(init_content, lacks="install_lazy_exports")

    def test_generated_bootstrap_owner_facet_is_preserved_not_removed(
        self, tmp_path: Path
    ) -> None:
        """A generated facet initializer stays a generated facet initializer.

        The generator OWNS files carrying the autogen header: it re-renders
        them to the canonical form and retires obsolete ones, and it never
        preserves a previous byte-for-byte body. What must hold for the
        bootstrap chain is observed here, per the runtime contract: the run
        succeeds, the facet survives as a package initializer, it remains
        codegen-owned, and it still imports nothing from the bootstrap.
        """
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name=c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE.replace("_", "-"),
            package_name=c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE,
        )
        lazy_parts = _write_bootstrap_owner(package_root, "_lazy_parts")
        generated_stub = f'{c.Infra.AUTOGEN_HEADER}\n"""Lazy Parts package."""\n'
        init_path = lazy_parts / c.Infra.INIT_PY
        init_path.write_text(generated_stub, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Tests.run_lazy_init(workspace_root)

        tm.that(result, eq=0)
        tm.that(init_path.is_file(), eq=True)
        rendered = init_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        tm.that(rendered.startswith(c.Infra.AUTOGEN_HEADER), eq=True)
        tm.that(rendered, lacks="from flext_core.lazy import")
        tm.that(rendered, lacks="install_lazy_exports")

    def test_other_distributions_still_receive_the_lazy_bootstrap(
        self, tmp_path: Path
    ) -> None:
        """Private packages outside the bootstrap owner keep their generated map."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer_facet = _write_bootstrap_owner(package_root, "_models")

        result = u.Tests.run_lazy_init(workspace_root)

        init_content = (consumer_facet / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(result, eq=0)
        tm.that(init_content, contains="from flext_core.lazy import")
        tm.that(init_content, contains="FlextLazyPart")
