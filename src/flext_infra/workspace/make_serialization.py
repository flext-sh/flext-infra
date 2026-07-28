"""Portable per-checkout serialization for state-sensitive Make validation."""

from __future__ import annotations

from typing import Annotated, override

from filelock import FileLock, Timeout
from flext_core import r

from flext_infra import c, config, m, p, u
from flext_infra.base import s


class FlextInfraMakeSerializationService(s[bool]):
    """Run one configured private Make target under a native process lock."""

    verb: Annotated[
        str, m.Field(description="Configured public Make verb to serialize")
    ]

    @override
    def execute(self) -> p.Result[bool]:
        """Acquire the checkout lock, then stream the private Make dispatch."""
        serialization = config.Infra.codegen.make.serialization
        if self.verb not in serialization.verbs:
            allowed = ", ".join(serialization.verbs)
            return r[bool].fail(
                f"Make verb '{self.verb}' is not serialized (allowed: {allowed})"
            )

        checkout = self.root.resolve()
        lock_path = (checkout / serialization.lock_path).resolve()
        try:
            lock_path.relative_to(checkout)
        except ValueError:
            return r[bool].fail(
                f"Make serialization lock escapes checkout: {lock_path}"
            )

        try:
            with FileLock(
                lock_path,
                timeout=serialization.timeout_seconds,
                fallback_to_soft=False,
                preserve_lock_file=True,
            ):
                execution = u.Cli.run_live(
                    [c.Infra.MAKE, "--no-print-directory", f"_serialized_{self.verb}"],
                    cwd=checkout,
                )
        except Timeout:
            return r[bool].fail(
                "Timed out waiting for Make validation lock "
                f"'{lock_path}' after {serialization.timeout_seconds}s"
            )
        except OSError as exc:
            return r[bool].fail_op("Make validation lock acquisition", exc)

        if execution.failure:
            return r[bool].fail(
                execution.error or f"serialized Make {self.verb} failed"
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraMakeSerializationService"]
