"""rsync-backed workspace snapshot helper.

Mirrors a workspace tree (typically ``flext`` → ``flext-base``) via
``rsync -a --delete`` so refactors can be tested in isolation before
propagating to the live workspace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from flext_infra import e, p, r


class FlextInfraUtilitiesSnapshot:
    """rsync wrapper for sandbox workspace mirroring."""

    @staticmethod
    def rsync(*, src: Path, dst: Path) -> p.Result[Path]:
        """Mirror ``src`` to ``dst`` via ``rsync -a --delete``.

        Returns ``r.ok(dst)`` on success or a typed failure when rsync is
        not installed, the source is missing, or the subprocess exits
        non-zero. Trailing slash on ``src`` is added so rsync copies the
        contents (not the directory itself) into ``dst``.
        """
        rsync_bin = shutil.which("rsync")
        if rsync_bin is None:
            return e.fail_not_found("rsync executable", "PATH", result_type=r[Path])
        if not src.is_dir():
            return e.fail_not_found("snapshot source", str(src), result_type=r[Path])
        dst.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [rsync_bin, "-a", "--delete", f"{src.resolve()}/", str(dst.resolve())],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return r[Path].fail_op("rsync snapshot", completed.stderr.strip())
        return r[Path].ok(dst.resolve())


__all__: list[str] = ["FlextInfraUtilitiesSnapshot"]
