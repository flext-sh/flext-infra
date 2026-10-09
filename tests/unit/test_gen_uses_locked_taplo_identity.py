"""Generation formats TOML with the declared Taplo, through the lock when it pins one.

Mise resolves the formatter: the release the committed ``mise.lock`` pins
wherever it pins Taplo, the declared selector otherwise. A missing, stale or
incomplete lock never stops generation (operator-ruling-2026-10-09-setup-resilient);
``make audit`` proves the pins.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

import flext_infra
from flext_infra import c, config, p, t
from tests import u


class TestsFlextInfraGenUsesLockedTaploIdentity:
    """The formatter comes from the declared toolchain; the lock never blocks it."""

    _SOURCE = "a = 1\n\n[tool]\nb = 2\n"

    @staticmethod
    def _declared_root(tmp_path: Path, *, strip_from_lock: str | None) -> Path:
        """Seed the tracked Mise declaration and lock, optionally without one entry.

        Returns:
            The resulting ``Path``.

        """
        root = tmp_path / "declared"
        root.mkdir()
        u.Tests.copy_tracked_mise_seeds(root)
        (root / c.Infra.TAPLO_CONFIG_FILENAME).write_text("", encoding="utf-8")
        if strip_from_lock is not None:
            lock = root / c.Infra.MISE_LOCK_FILENAME
            payload = dict(
                tm.not_none(
                    u.Cli.toml_mapping_from_text(lock.read_text(encoding="utf-8")),
                ),
            )
            tools = dict(t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["tools"]))
            tools.pop(strip_from_lock)
            payload["tools"] = tools
            lock.write_text(
                u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
                encoding="utf-8",
            )
        return root

    def _format(self, root: Path) -> p.Result[str]:
        """Format through the public utility facade.

        Returns:
            The resulting ``p.Result[str]``.

        """
        return u.Infra.format_toml_source(
            self._SOURCE,
            path=root / c.PYPROJECT_FILENAME,
            toolchain_root=root,
            taplo_version=config.Infra.codegen.toolchain.tool_versions["taplo"],
        )

    def _assert_formatted(self, root: Path) -> None:
        """Assert the formatter ran and kept the document's meaning."""
        formatted = tm.ok(self._format(root))
        payload = tm.not_none(u.Cli.toml_mapping_from_text(formatted))
        tool = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["tool"])
        tm.that(dict(tool), eq={"b": 2})

    def test_declared_repository_lock_satisfies_the_identity(self) -> None:
        """The live checkout formats with its own committed lock, as configured."""
        self._assert_formatted(Path(flext_infra.__file__).resolve().parents[2])

    def test_lock_without_the_formatter_entry_still_formats(
        self,
        tmp_path: Path,
    ) -> None:
        """A lock that does not pin Taplo yet never stops generation."""
        self._assert_formatted(
            self._declared_root(
                tmp_path,
                strip_from_lock=c.Infra.TAPLO_MISE_TOOL_NAME,
            ),
        )

    def test_previous_generation_tree_resolves_its_formatter(
        self,
        tmp_path: Path,
    ) -> None:
        """A lock that predates Mise self-management still formats (C19).

        Premise: ``make upg`` runs this generator while the committed
        ``mise.lock`` still comes from the previous generation, without the
        self-managed Mise entry; generation renders the new manifest instead
        of dead-locking on a pin only the upgrade can write.
        """
        self._assert_formatted(
            self._declared_root(
                tmp_path,
                strip_from_lock=config.Infra.codegen.toolchain.mise_selector,
            ),
        )
