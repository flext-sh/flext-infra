"""Native Docker proofs admit both checkout and bare Git metadata.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraCiDockerMetadata:
    """Every generated distro keeps one fail-closed native bootstrap."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        "distro", ["ubuntu", "debian", "fedora", "alpine", "arch"]
    )
    def test_native_metadata_binding_preserves_checkout_inputs(distro: str) -> None:
        """Bare-only hydration preserves ordinary checkout/index semantics."""
        root = Path(__file__).resolve().parents[3]
        spec = m.Infra.DistroDockerRenderSpec.model_validate({
            "package_name": "fixture_package",
            "python_version": config.Infra.codegen.toolchain.python_version,
            "make": config.Infra.codegen.make,
        })
        rendered = tm.ok(
            u.Cli.template_render(
                root
                / "src/flext_infra/templates/project/base/tests/fixtures/ci/docker"
                / f"{distro}.Dockerfile.j2",
                spec,
            )
        )
        tm.that(rendered, has="--from=git")
        tm.that(rendered, has="rev-parse --is-bare-repository")
        tm.that(rendered, has="core.worktree /workspace")
        tm.that(rendered, has='if [ "$metadata_bare" = true ]; then')
        tm.that(
            rendered, has="git ls-files --deleted -z | git checkout-index -z --stdin"
        )
        tm.that(rendered, lacks="git reset")
        tm.that(rendered, lacks="git clean")
        tm.that(rendered, has="required=true")
        tm.that(rendered, has="make setup")
        tm.that(rendered, lacks="set +e")
        artifact = root / c.Infra.REPORTS_DIR_NAME / "docker-qualification"
        artifact.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(artifact / f"{distro}.Dockerfile", rendered))
