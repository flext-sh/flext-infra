"""Content-addressed class-name receipts for the lazy-init duplicate scan."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, cast

from flext_core import r
from flext_infra import c, u

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCodegenLazyInitClassReceipts:
    """Content-addressed cache of per-module top-level class names.

    The lazy-init duplicate scan is a pure function of module bytes: identical
    content yields identical top-level class names. Receipts key that function
    by SHA-256 so repeat ``make gen`` cycles stop re-parsing every module
    through Rope. The store is regenerable cache state under the ignored
    ``.state`` root: any read or decode failure fails open to an empty map and
    the next scan recomputes; a save failure is reported, never fatal.
    """

    def __init__(self, repository_root: Path) -> None:
        self._path = (
            repository_root
            / c.Infra.TRANSACTION_STATE_DIRNAME
            / c.Infra.LAZY_INIT_CLASS_RECEIPTS_RELPATH
        )
        self._entries: dict[str, list[str]] = {}
        self._dirty = False
        loaded = self._load()
        if loaded.failure:
            u.Cli.warning(
                f"lazy-init: discarding unreadable class receipts: {loaded.error}"
            )

    @staticmethod
    def content_key(content: bytes) -> str:
        """Return the content address of one module's bytes."""
        return hashlib.sha256(content).hexdigest()

    def class_names(self, content: bytes) -> tuple[str, ...] | None:
        """Return the cached class names for these bytes, or None on miss."""
        cached = self._entries.get(self.content_key(content))
        return tuple(cached) if cached is not None else None

    def record(self, content: bytes, class_names: t.StrSequence) -> None:
        """Record one module's class names under its content address."""
        key = self.content_key(content)
        candidate = list(class_names)
        if self._entries.get(key) != candidate:
            self._entries[key] = candidate
            self._dirty = True

    def save(self) -> p.Result[bool]:
        """Persist the receipt document when the scan recorded new entries."""
        if not self._dirty:
            return r[bool].ok(True)
        document = cast(
            "dict[str, t.JsonValue]",
            {
                "version": c.Infra.LAZY_INIT_CLASS_RECEIPTS_VERSION,
                "entries": self._entries,
            },
        )
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            dump = u.Cli.json_dumps(document, sort_keys=True, indent=1)
            if dump.failure:
                return r[bool].fail_op(
                    "lazy-init class receipt save", dump.error or "json dump failed"
                )
            written = u.Cli.atomic_write_text_file(self._path, dump.value + "\n")
        except OSError as exc:
            return r[bool].fail_op("lazy-init class receipt save", exc)
        if written.failure:
            return r[bool].fail_op(
                "lazy-init class receipt save", written.error or "atomic write failed"
            )
        self._dirty = False
        return r[bool].ok(True)

    def _load(self) -> p.Result[bool]:
        """Populate entries from disk; every failure mode fails open to empty."""
        read = u.Cli.atomic_read_binary_file_state(self._path, required=False)
        if read.failure:
            return r[bool].ok(True)
        content = read.value.content
        if content is None:
            return r[bool].ok(True)
        parsed = u.Cli.json_loads(content)
        if parsed.failure:
            return r[bool].fail_op(
                "lazy-init class receipt parse", parsed.error or "json parse failed"
            )
        document = parsed.value
        if not isinstance(document, dict):
            return r[bool].fail_op(
                "lazy-init class receipt parse", "document is not an object"
            )
        if document.get("version") != c.Infra.LAZY_INIT_CLASS_RECEIPTS_VERSION:
            return r[bool].ok(True)
        entries = document.get("entries")
        if not isinstance(entries, dict):
            return r[bool].fail_op(
                "lazy-init class receipt parse", "entries is not an object"
            )
        self._entries = {
            key: [item for item in value if isinstance(item, str)]
            for key, value in entries.items()
            if isinstance(value, list)
        }
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenLazyInitClassReceipts"]
