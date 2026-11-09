"""Public editor projections use their declared template and shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
from pathlib import Path

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraCodegenEditor:
    """Editor-only generation agrees with full conformance."""

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize("packaged", [True, False])
    def test_editor_surface_publishes_the_full_conform_manifest(
        infra_git_repo: Path,
        *,
        packaged: bool,
    ) -> None:
        """The editor surface publishes the full conform's manifest bytes.

        An ``examples`` root sorts before the source root, so disk discovery
        order differs from the declared scaffold order: a second analyzer
        context would publish other environments and ``extraPaths`` orders.
        """
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        manifest = root / c.PYPROJECT_FILENAME
        document = tm.ok(u.Cli.toml_read_document(manifest))
        build = u.Cli.toml_ensure_table(document, "build-system")
        build["build-backend"] = config.Infra.codegen.scaffold.build.backend
        build["requires"] = list(config.Infra.codegen.scaffold.build.requirements)
        uv = u.Cli.toml_ensure_table(
            u.Cli.toml_ensure_table(document, c.Infra.TOOL), c.Infra.UV
        )
        uv["package"] = packaged
        tm.ok(u.Cli.toml_write_document(manifest, document))
        package = root / c.Infra.DEFAULT_SRC_DIR / config.Infra.name.replace("-", "_")
        for module, family in (("models.py", "Models"), ("protocols.py", "Protocols")):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    package / module,
                    f"class FlextInfra{family}:\n    pass\n\n\n"
                    f"{family[0].lower()} = FlextInfra{family}\n",
                ),
            )
        example = root / "examples" / "usage.py"
        example.parent.mkdir()
        tm.ok(u.Cli.atomic_write_text_file(example, "VALUE = 1\n"))
        u.Tests.commit_git_changes(root, "Seed a root that sorts before src")
        full_request = u.Tests.conform_request(
            root, scope=c.Infra.CodegenConformScope.SELF
        )
        planned = tm.ok(
            tm.ok(
                FlextInfraCodegenConform.Generate.from_request(
                    full_request, execution_context=infra
                )
            ).plan(full_request),
        )
        tm.ok(
            u.Infra.publish_codegen_plans(
                root, tuple(file for file in planned.files if file.path == manifest)
            ),
        )
        full = manifest.read_text(encoding=c.DEFAULT_ENCODING)
        document = tm.not_none(u.Cli.toml_parse_text(full))
        stale = u.Cli.toml_ensure_table(
            u.Cli.toml_ensure_table(document, c.Infra.TOOL), c.Infra.PYRIGHT
        )
        stale["venvPath"] = "../stale-checkout"
        manifest.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
        editor = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.EDITOR,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(editor))
        edited = manifest.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            edited,
            eq=full,
            msg="\n".join(difflib.unified_diff(full.splitlines(), edited.splitlines())),
        )
        qlty = root / c.Infra.QLTY_CONFIG_DIRNAME / c.Infra.QLTY_CONFIG_FILENAME
        qlty_plan = next(file for file in planned.files if file.path == qlty)
        tm.ok(u.Cli.toml_read_document(qlty))
        tm.that(
            qlty.read_text(encoding=c.DEFAULT_ENCODING),
            eq=u.Tests.codegen_file_text(qlty_plan),
        )
        tm.that(tm.ok(infra.codegen_conform(editor)).written_files, eq=())
