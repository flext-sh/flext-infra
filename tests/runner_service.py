"""Real subprocess runner."""

from __future__ import annotations

from typing import override

from flext_tests import s

from flext_core import r
from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess


class RealSubprocessRunner(s[str]):
    subprocess_utility: type[FlextInfraUtilitiesSubprocess] = (
        FlextInfraUtilitiesSubprocess
    )
    allowed_commands: frozenset[str] = frozenset({"echo", "pwd", "ls", "git"})

    @override
    def execute(self) -> r[str]:
        return r[str].ok("")

    def _validate_safe_command(self, cmd: list[str]) -> r[bool]:
        if not cmd:
            return r[bool].fail("empty command")
        if cmd[0] not in self.allowed_commands:
            return r[bool].fail("not allowed")
        return r[bool].ok(True)

    def _failure_message[T](self, result: r[T]) -> str:
        return str(result.error) if result.error else "failed"

    def run_safe(self, cmd: list[str]) -> r[str]:
        v = self._validate_safe_command(cmd)
        if v.is_failure:
            return r[str].fail(v.error or "unsafe")
        res = self.subprocess_utility.run(cmd)
        if res.is_failure:
            return r[str].fail(self._failure_message(res))
        return r[str].ok(res.value.stdout.strip())

    def capture_output(self, cmd: list[str]) -> r[tuple[str, str]]:
        v = self._validate_safe_command(cmd)
        if v.is_failure:
            return r[tuple[str, str]].fail(v.error or "unsafe")
        res = self.subprocess_utility.run(cmd)
        if res.is_failure:
            return r[tuple[str, str]].fail(self._failure_message(res))
        o = res.value
        return r[tuple[str, str]].ok((o.stdout.strip(), o.stderr.strip()))


__all__ = ["RealSubprocessRunner"]
