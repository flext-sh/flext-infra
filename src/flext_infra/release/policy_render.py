"""Release policy rendering from the typed configuration SSOT.

The hash-pinned build-backend policy consumed by ``uv build
--require-hashes`` is rendered here from
``config.Infra.release.build_constraints`` at release time. No repository
carries a ``config/build-constraints.txt`` projection: the typed config is
the single owner (flext-gufl8).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import m, t

__all__: list[str] = ["FlextInfraReleasePolicyRender"]


class FlextInfraReleasePolicyRender:
    """Render release policy artifacts from typed configuration."""

    @staticmethod
    def build_constraints(pins: t.SequenceOf[m.Infra.BuildConstraintSpec]) -> str:
        """Render the ``uv build --require-hashes`` constraints bytes.

        One ``name==version`` record per pin, continued with exactly one
        ``--hash=sha256:`` line per digest; the final digest carries no
        continuation. Deterministic for identical pin tuples, so the policy
        snapshot digest is stable across renders.
        """
        header = (
            "# Rendered by flext_infra release policy from "
            "config.Infra.release.build_constraints.\n"
            "# Release build policy: the isolated `uv build "
            "--build-constraints … --require-hashes`\n"
            "# of every release artifact resolves its build backend from "
            "exactly these pins.\n"
        )
        records: list[str] = []
        for pin in pins:
            lines = [f"{pin.name}=={pin.version} \\"]
            for index, digest in enumerate(pin.hashes):
                continuation = " \\" if index < len(pin.hashes) - 1 else ""
                lines.append(f"    --hash=sha256:{digest}{continuation}")
            records.append("\n".join(lines))
        return header + "\n".join(records) + "\n"
