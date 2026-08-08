"""Byte-exact process stream mirroring for ``u.Cli``."""

from __future__ import annotations

import os
import threading
from typing import IO, BinaryIO, ClassVar


class FlextCliUtilitiesRuntimeProcessStreamMixin:
    """Mirror combined child output to a live descriptor and durable log."""

    _STREAM_CHUNK_BYTES: ClassVar[int] = 64 * 1024
    _STREAM_POLL_SECONDS: ClassVar[float] = 0.01

    @classmethod
    def _pump_process_output(
        cls,
        source: IO[bytes],
        durable_log: BinaryIO,
        live_fd: int | None,
        failures: list[str],
        live_diagnostics: list[str],
        stop: threading.Event,
        wake: threading.Event,
    ) -> None:
        """Persist each chunk before bounded best-effort live mirroring."""
        live_available = live_fd is not None
        try:
            while not stop.is_set():
                chunk = cls._read_process_chunk(source, failures)
                if chunk is None:
                    return
                durable_error = cls._write_durable_chunk(durable_log, chunk)
                if durable_error is not None:
                    failures.append(durable_error)
                    return
                if live_available and live_fd is not None:
                    live_available = cls._write_live_chunk(
                        live_fd, chunk, stop, live_diagnostics
                    )
        finally:
            wake.set()

    @classmethod
    def _read_process_chunk(
        cls, source: IO[bytes], failures: list[str]
    ) -> bytes | None:
        try:
            chunk = source.read(cls._STREAM_CHUNK_BYTES)
        except (OSError, ValueError) as exc:
            failures.append(f"output read error: {exc}")
            return None
        return chunk or None

    @staticmethod
    def _write_durable_chunk(durable_log: BinaryIO, chunk: bytes) -> str | None:
        remaining = memoryview(chunk)
        try:
            while remaining:
                written = durable_log.write(remaining)
                if written <= 0:
                    return "durable log write made no progress"
                remaining = remaining[written:]
            durable_log.flush()
        except (OSError, ValueError) as exc:
            return f"durable log write error: {exc}"
        return None

    @classmethod
    def _write_live_chunk(
        cls, live_fd: int, chunk: bytes, stop: threading.Event, diagnostics: list[str]
    ) -> bool:
        remaining = memoryview(chunk)
        while remaining and not stop.is_set():
            try:
                written = os.write(live_fd, remaining)
            except BlockingIOError:
                stop.wait(cls._STREAM_POLL_SECONDS)
                continue
            except (BrokenPipeError, OSError, ValueError) as exc:
                diagnostics.append(f"live output unavailable: {exc}")
                return False
            if written <= 0:
                diagnostics.append("live output write made no progress")
                return False
            remaining = remaining[written:]
        if remaining:
            diagnostics.append("live output mirror stopped after durable persistence")
            return False
        return True


__all__: list[str] = ["FlextCliUtilitiesRuntimeProcessStreamMixin"]
