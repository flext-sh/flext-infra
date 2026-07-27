r"""Tests that the rendered ``.python-version`` carries only the pin.

``.python-version`` is consumed by tooling that reads the file as a bare version
string. A Jinja comment line in the template ends with a newline, so the render
began with an empty line and the file became ``"\\n3.13.11\\n"``. That made
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
        python_toolchain_version=config.Infra.codegen.toolchain.python_version
    )


class TestsFlextInfraPythonVersionRenderIsExact:
    def test_render_is_the_pin_and_nothing_else(self) -> None:
        """The rendered file is exactly the configured pin plus one newline."""
        expected = f"{config.Infra.codegen.toolchain.python_version}\n"

        tm.that(_render_python_version(), eq=expected)
