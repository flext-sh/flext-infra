"""Local rope patch modeling the full modern signature token stream.

Rope 1.14's ``patchedast`` never modeled positional-only separators,
keyword-only parameters, or parameter annotations: its ``_arguments`` walks
only ``args``/``vararg``/``kwarg`` and its ``_arg`` consumes only the
parameter name. The skipped tokens are jumped over by the walker's forward
token search, which silently attaches wrong source regions for a single
annotated parameter and raises ``MismatchedTokenError`` once a second
annotation carries a call (bead flext-4frn5; first fleet victim
flext-cli/tests/utilities.py).

This module monkey-patches the two handlers once, idempotently, so every
signature token — ``/``, bare ``*``, ``**``, ``:`` annotations, defaults —
is consumed exactly where it appears in the source.

NOTE: lives beside ``pep695_patch`` for the same reason — rope 1.14 exposes
no public API to register patched-AST handlers, so these private slots are
the library's real interface (operator authorization 2026-08-08).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesRopeSignaturePatch:
    """Idempotent monkey-patch applying signature awareness to rope."""

    _applied: ClassVar[bool] = False

    @classmethod
    def apply(cls) -> None:
        """Install signature handlers on rope's AST walker once."""
        if cls._applied:
            return
        walker = FlextInfraUtilitiesRopeRuntime.signature_ast_walker()

        def _patched_arguments(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.ArgumentsNode,
        ) -> None:
            """Walk every signature token in source order."""
            children: list[p.AttributeProbe] = []
            positional: list[p.AttributeProbe] = [*node.posonlyargs, *node.args]
            defaults: list[p.AttributeProbe | None] = [None] * (
                len(positional) - len(node.defaults)
            ) + list(node.defaults)
            for index, (argument, default) in enumerate(
                zip(positional, defaults, strict=False)
            ):
                if index:
                    children.append(",")
                children.append(argument)
                if default is not None:
                    children.extend(["=", default])
                if node.posonlyargs and index + 1 == len(node.posonlyargs):
                    children.extend([",", "/"])
            if node.vararg is not None or node.kwonlyargs:
                if positional:
                    children.append(",")
                children.append("*")
                if node.vararg is not None:
                    children.append(node.vararg)
            for index, (argument, default) in enumerate(
                zip(node.kwonlyargs, node.kw_defaults, strict=False)
            ):
                if index or positional or node.vararg is not None:
                    children.append(",")
                children.append(argument)
                if default is not None:
                    children.extend(["=", default])
            if node.kwarg is not None:
                if positional or node.vararg is not None or node.kwonlyargs:
                    children.append(",")
                children.extend(["**", node.kwarg])
            self._handle(node, children)  # pyright: ignore[reportPrivateUsage]

        def _patched_arg(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.ArgumentNode,
        ) -> None:
            """Consume the parameter name and its annotation, if declared."""
            children: list[p.AttributeProbe] = [node.arg]
            if node.annotation is not None:
                children.extend([":", node.annotation])
            self._handle(node, children)  # pyright: ignore[reportPrivateUsage]

        walker._arguments = _patched_arguments  # pyright: ignore[reportPrivateUsage]
        walker._arg = _patched_arg  # pyright: ignore[reportPrivateUsage]
        cls._applied = True


__all__: list[str] = ["FlextInfraUtilitiesRopeSignaturePatch"]
