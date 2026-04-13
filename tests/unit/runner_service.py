"""Real subprocess runner."""

from __future__ import annotations

from flext_core import p, r
from tests import t, u


class RealSubprocessRunner:
    subprocess_utility: type[u.Cli] = u.Cli
    allowed_commands: frozenset[str] = frozenset({"echo", "pwd", "ls", "git"})

    def execute(self) -> p.Result[str]:
        return r[str].ok("")

    def _validate_safe_command(self, cmd: t.StrSequence) -> p.Result[bool]:
        if not cmd:
            return r[bool].fail("empty command")
        if cmd[0] not in self.allowed_commands:
            return r[bool].fail("not allowed")
        return r[bool].ok(True)

    def _failure_message[T](self, result: p.Result[T]) -> str:
        return str(result.error) if result.error else "failed"

    def run_safe(self, cmd: t.StrSequence) -> p.Result[str]:
        v = self._validate_safe_command(cmd)
        if v.failure:
            return r[str].fail(v.error or "unsafe")
        res = self.subprocess_utility.run(cmd)
        if res.failure:
            return r[str].fail(self._failure_message(res))
        return r[str].ok(res.value.stdout.strip())

    def capture_output(self, cmd: t.StrSequence) -> p.Result[t.Pair[str, str]]:
        v = self._validate_safe_command(cmd)
        if v.failure:
            return r[t.Pair[str, str]].fail(v.error or "unsafe")
        res = self.subprocess_utility.run(cmd)
        if res.failure:
            return r[t.Pair[str, str]].fail(self._failure_message(res))
        o = res.value
        return r[t.Pair[str, str]].ok((o.stdout.strip(), o.stderr.strip()))


__all__: list[str] = ["RealSubprocessRunner"]
