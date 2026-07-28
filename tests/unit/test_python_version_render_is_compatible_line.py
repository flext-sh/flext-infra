r"""Tests that ``.python-version`` carries only the compatible Python line.

``.python-version`` is consumed by tooling that reads the file as a bare version
string. A Jinja comment line in the template ends with a newline, so the render
began with an empty line and the file gained permanent generated drift. That made
``codegen conform`` report a permanent pending change, which blocks the whole
transaction and therefore every other generator fix.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_tests import tm
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from flext_infra import config


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
    return template.render(
        python_minor_version=config.Infra.codegen.toolchain.python_minor_version
    )


class TestsFlextInfraPythonVersionRenderIsCompatibleLine:
    def test_render_is_the_compatible_line_and_nothing_else(self) -> None:
        """Render exactly the configured compatible line plus one newline."""
        expected = f"{config.Infra.codegen.toolchain.python_minor_version}\n"

        tm.that(_render_python_version(), eq=expected)
