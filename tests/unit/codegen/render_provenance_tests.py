"""Render-provenance contracts: every emitted artifact names its generator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c
from flext_infra.__version__ import __version__
from flext_infra.codegen._conform.artifact_render import (
    FlextInfraCodegenConformArtifactRender,
)


class TestsFlextInfraRenderProvenance:
    """The pyproject composition stamps the running generator's identity."""

    def test_composed_pyproject_carries_the_rendered_by_stamp(
        self, tmp_path: Path
    ) -> None:
        """The one generated header names the motor version that rendered it.

        Why (aihub-l42it.11): a Makefile emitted by a template generation that
        exists in no commit poisoned every bootstrap; a stamped artifact makes
        the drift report name both sides (rendered-by vs consumed) instead of
        a bare byte diff.
        """
        stamp = FlextInfraCodegenConformArtifactRender.rendered_by_stamp()

        assert stamp == f"{c.Infra.RENDERED_BY_MARKER}{__version__}"
        assert c.Infra.RENDERED_BY_MARKER in stamp
        assert __version__ in stamp
