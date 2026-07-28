r"""Tests that the rendered ``.python-version`` carries only the minor line.

``.python-version`` is consumed by tooling that reads the file as a bare version
string. A Jinja comment line in the template ends with a newline, so the render
began with an empty line and the file became ``"\\n3.13\\n"``. That made
``codegen conform`` report a permanent pending change, which blocks the whole
transaction and therefore every other generator fix.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

import flext_infra
from flext_infra import c, config, u
from flext_tests import tm


def _render_python_version() -> str:
    """Render the shipped ``.python-version`` template from the config SSOT."""
    templates = Path(flext_infra.__file__).resolve().parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(str(templates)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=select_autoescape(default=False, default_for_string=False),
    )
    template = environment.get_template("project/base/python-version.j2")
    return template.render(python_version=config.Infra.codegen.toolchain.python_version)


class TestsFlextInfraPythonVersionRenderUsesMinorLine:
    def test_render_is_the_minor_line_and_nothing_else(self) -> None:
        """The rendered file is exactly the configured line plus one newline."""
        expected = f"{config.Infra.codegen.toolchain.python_version}\n"

        tm.that(_render_python_version(), eq=expected)

    def test_generated_artifact_matches_the_typed_selector(self) -> None:
        """Validate the real consumer file against the same typed SSOT."""
        expected = f"{config.Infra.codegen.toolchain.python_version}\n"
        rendered = tm.ok(u.Cli.files_read_text(Path(c.Infra.PYTHON_VERSION_FILENAME)))

        tm.that(rendered, eq=expected)
