"""Prove immutable candidate provenance retains its declared integration policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from tests import c, tm, u


class TestsFlextInfraCandidateDependencyLine:
    """Exercise candidate source detection through the public repository utility."""

    @staticmethod
    @pytest.mark.parametrize("declarations", [1, 2])
    def test_candidate_keeps_the_declared_integration_line(
        tmp_path: Path, declarations: int
    ) -> None:
        """An exact commit declares provenance, never a replacement branch selector."""
        distribution = config.Infra.codegen.infra_repository.distribution
        url = f"https://example.test/fixture/{distribution}.git"
        commit = "a" * 40
        u.Tests.initialize_git_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "candidate-consumer"\n'
            f'version = "{c.Tests.RELEASE_VERSION_BASE}"\n'
            f'dependencies = ["{distribution} @ git+{url}@{commit}"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (tmp_path / "config").mkdir(exist_ok=True)
        (tmp_path / "config" / "codegen.yaml").write_text(
            "Infra:\n  codegen:\n    repository:\n      candidate_dependencies:\n"
            + (
                f"      - distribution: {distribution}\n"
                f"        url: {url}\n"
                f"        commit: {commit}\n"
            )
            * declarations,
            encoding=c.DEFAULT_ENCODING,
        )
        line = u.Infra.flext_integration_line(
            codegen=config.Infra.codegen, repository_root=tmp_path
        )
        if declarations == 1:
            tm.that(
                tm.ok(line).branch,
                eq=config.Infra.codegen.branch_policy.integration_branch,
            )
        else:
            tm.fail(line, has="candidate dependency distributions must be unique")
