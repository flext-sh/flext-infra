"""Manual-command blocker (AGENTS.md §5 Make Contract).

Two responsibilities:

- ``is_blocked`` — predicate flagging a bare tool invocation (ruff/pytest/git/…)
  that bypasses the ``make`` / ``python -m flext_infra`` monopoly. Backs both the
  pre-commit hook and the Claude PreToolUse guard.
- ``render_pre_commit_config`` — the canonical ``.pre-commit-config.yaml`` content
  (hooks call ``python -m flext_infra``, never standalone scripts).

``execute`` is a drift gate: the live ``.pre-commit-config.yaml`` MUST equal the
rendered canonical template.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, p, r, s

_TEMPLATE = Path(__file__).parent.parent / "templates" / "pre_commit_config.yaml.j2"


class FlextInfraManualCommandValidator(s[bool]):
    """Block bare tool invocations in automation and gate pre-commit drift."""

    _BLOCKED_TOOLS: ClassVar[frozenset[str]] = frozenset(
        {"ruff", "pytest", "pyrefly", "mypy", "pyright"},
    )
    _BLOCKED_GIT: ClassVar[frozenset[str]] = frozenset(
        {"commit", "add", "push", "tag"},
    )
    _REWRITE_TOOLS: ClassVar[frozenset[str]] = frozenset({"ast-grep", "sg"})
    _ALLOWED_PREFIX: ClassVar[str] = "make "
    _MONOPOLY_MARKER: ClassVar[str] = "flext_infra"

    @classmethod
    def is_blocked(cls, command: str) -> bool:
        """True if ``command`` runs a managed tool outside the make/flext_infra path."""
        stripped = command.strip()
        if (
            not stripped
            or stripped.startswith(cls._ALLOWED_PREFIX)
            or cls._MONOPOLY_MARKER in stripped
        ):
            return False
        tokens = stripped.split()
        head = tokens[0]
        rest = tokens[1:]
        if head in cls._BLOCKED_TOOLS:
            return True
        if head == "git" and rest and rest[0] in cls._BLOCKED_GIT:
            return True
        if head == "sed" and "-i" in rest:
            return True
        return head in cls._REWRITE_TOOLS and "--rewrite" in rest

    @classmethod
    def render_pre_commit_config(cls) -> str:
        """Return the canonical generated ``.pre-commit-config.yaml`` content."""
        return _TEMPLATE.read_text(encoding=c.Cli.ENCODING_DEFAULT)

    @override
    def execute(self) -> p.Result[bool]:
        """Fail when the live pre-commit config drifts from the canonical template."""
        config_path = self.workspace_root / ".pre-commit-config.yaml"
        if not config_path.exists():
            return r[bool].fail(
                ".pre-commit-config.yaml missing — run `make gen` to generate it",
            )
        try:
            actual = config_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        except OSError as exc:
            return r[bool].fail_op("pre-commit config read", exc)
        if actual.strip() != self.render_pre_commit_config().strip():
            return r[bool].fail(
                ".pre-commit-config.yaml drifted from canonical template — run `make gen`",
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraManualCommandValidator"]
