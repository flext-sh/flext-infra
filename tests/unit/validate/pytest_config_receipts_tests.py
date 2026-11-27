"""Observable config-receipt contract of the per-test Testmon recorder.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, config, tm, u


class TestsFlextInfraPytestConfigReceipts:
    """A FLEXT checkout's config root always yields its leaf receipts."""

    @staticmethod
    @c.Tests.MARK.slow
    def test_lazily_published_config_root_writes_leaf_receipts(
        tmp_path: Path,
    ) -> None:
        """Binding the controller recorder writes one receipt per typed leaf.

        A FLEXT package publishes ``config`` as a lazy stand-in whose
        ``fetch_global()`` returns a settings model. Without receipts every
        test depends on every config file, so Testmon reselects the whole
        suite on each run and a fresh checkout never finishes inside its
        run budget.
        """
        root = u.Tests.infra_source_checkout(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        receipts = root / cache.config_receipts_directory
        recorder = u.Infra.ConfigDependencyRecorder(
            rootdir=root,
            receipts=receipts,
            insensitive=frozenset(cache.config_insensitive_executables),
            controller=True,
            executes=True,
        )

        recorder.bind()
        try:
            written = sorted(
                receipts.glob(f"*{c.Infra.PYTEST_CONFIG_RECEIPT_SUFFIX}"),
            )
        finally:
            recorder.unbind()

        tm.that(bool(written), truth=True)
        tm.that(bool(recorder.retained), truth=True)
