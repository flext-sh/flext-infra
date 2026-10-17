"""Tests for canonical dependency source selection by topology role.

Published project metadata preserves Git requirements in every topology.
Generated native resolution views exclusively own development path bindings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import t, tm, u
from tests.unit.pyproject_conform_topology_support import (
    TestsFlextInfraPyprojectConformTopologySupport,
)


class TestsFlextInfraPyprojectConformTopologyOverlays(
    TestsFlextInfraPyprojectConformTopologySupport,
):
    """Overlay, candidate-commit, and render-context contracts by topology role."""

    def test_member_render_is_context_independent(self) -> None:
        """A member renders identically attached or standalone, without nesting.

        Authored native workspace and custom source declarations are retained;
        their spelling never grants the generator ownership of their contents.
        """
        runtime = self._member_ref("flext-web", "flext-web")
        dev = self._member_ref("flext-tests", "flext-tests")
        unused = self._member_ref("flext-unused", "flext-unused")
        consumer = self._member_ref("flext-api", "flext-api")
        standalone = u.Tests.workspace_spec(consumer)
        attached = standalone.model_copy(
            update={"repository": consumer.model_copy(update={"editable": True})},
        )
        source = (
            f'[project]\nname = "{consumer.distribution}"\nversion = "0.1.0"\n'
            f'dependencies = ["{self._inline_requirement(runtime)}"]\n'
            "\n[dependency-groups]\n"
            f'dev = ["{self._inline_requirement(dev)}"]\n'
            "\n[tool.uv.workspace]\nmembers = []\n"
            "\n[tool.uv.sources]\n"
            f'{unused.distribution} = {{path = "vendor/custom", editable = false}}\n'
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=attached,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        parsed = u.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(parsed.get("tool")).get("uv"))
        tm.that(u.Tests.toml_mapping(uv["workspace"]), eq={"members": []})
        tm.that(
            uv.get("sources"),
            eq={
                unused.distribution: {
                    "path": "vendor/custom",
                    "editable": False,
                },
            },
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
            eq=(self._inline_requirement(runtime),),
        )
        detached = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=standalone,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        tm.that(detached, eq=rendered)
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=attached,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=u.Infra.PyprojectConformOptions(
                        flext_line=u.Tests.integration(),
                    ),
                ),
            ),
            eq=rendered,
        )

    def test_standalone_preserves_declared_nonlocal_source(self) -> None:
        """Conformance owns local topology, not a user's independent Git source."""
        dependency = self._member_ref("flext-custom", "flext-custom")
        source_entry: dict[str, t.JsonValue] = {
            "git": dependency.url,
            "rev": u.Tests.provider_branch(),
        }
        document: dict[str, t.JsonValue] = {
            "project": {"name": "consumer", "version": "0.1.0", "dependencies": []},
            "tool": {"uv": {"sources": {dependency.distribution: source_entry}}},
        }
        source = u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(document))
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(role=self._ROLE.STANDALONE),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )
        tm.that(
            u.Tests.toml_table_at(rendered, "tool", "uv", "sources"),
            eq={dependency.distribution: source_entry},
        )
