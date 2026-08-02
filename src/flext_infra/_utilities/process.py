"""Canonical process-exit classification utilities."""

from __future__ import annotations

from flext_infra import c


class FlextInfraUtilitiesProcess:
    """Normalize external process exits into stable diagnostic classifications."""

    @staticmethod
    def process_diagnostics(*streams: str) -> str:
        """Join every non-empty process stream without duplicating diagnostics."""
        diagnostics: list[str] = []
        for stream in streams:
            normalized = stream.strip()
            if normalized and normalized not in diagnostics:
                diagnostics.append(normalized)
        return "\n".join(diagnostics)

    @staticmethod
    def classify_process_exit(exit_code: int) -> str:
        """Classify a process exit without discarding its original status."""
        if exit_code == 0:
            return "success"
        if exit_code == c.Infra.PROCESS_TIMEOUT_EXIT_CODE:
            return "timeout"
        if exit_code < 0:
            return f"signal={-exit_code}"
        if exit_code > c.Infra.PROCESS_SIGNAL_EXIT_OFFSET:
            return f"signal={exit_code - c.Infra.PROCESS_SIGNAL_EXIT_OFFSET}"
        return "failure"

    @staticmethod
    def normalize_process_exit_code(raw_exit_code: int) -> int:
        """Map a subprocess signal return code into the portable shell domain."""
        if raw_exit_code < 0:
            return c.Infra.PROCESS_SIGNAL_EXIT_OFFSET - raw_exit_code
        return raw_exit_code


__all__: list[str] = ["FlextInfraUtilitiesProcess"]
