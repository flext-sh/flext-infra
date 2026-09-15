"""Canonical import-layer classification for lazy-init alignment.

Ranks derive from the SSOT ``tooling.lazy-init.import-layer-order``
vocabulary (plan D3); segment aliases cover the fixed facade family
directories (``_constants``/``_typings``/``_protocols``/``_models``/
``_utilities``/``_settings``/``_config``). The order itself is never
frozen here: every rank is resolved through the config-owned list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: list[str] = ["layer_rank", "relative_import_dots", "unknown_rank"]

_SEGMENT_LAYERS: Final[frozenset[tuple[str, str]]] = frozenset({
    (segment, layer)
    for layer, segments in (
        ("settings", ("settings", "_settings")),
        ("config", ("config", "_config")),
        ("c", ("c", "constants", "_constants")),
        ("t", ("t", "typings", "_typings")),
        ("p", ("p", "protocols", "_protocols")),
        ("m", ("m", "models", "_models")),
        ("u", ("u", "utilities", "_utilities")),
        ("base", ("base",)),
        ("services", ("services",)),
        ("api", ("api",)),
        ("cli", ("cli",)),
    )
    for segment in segments
})


def _segment_layer(segment: str) -> str | None:
    for candidate, layer in _SEGMENT_LAYERS:
        if candidate == segment:
            return layer
    return None


def layer_rank(module_name: str, order: Sequence[str]) -> int | None:
    """Return the canonical layer rank of a module path, or ``None``.

    The deepest matching segment wins (reversed scan), so ``_config``
    parts outrank an enclosing ``_models`` directory.
    """
    known = {layer: index for index, layer in enumerate(order)}
    for segment in reversed(module_name.split(".")):
        layer = _segment_layer(segment)
        if layer is not None and layer in known:
            return known[layer]
    return None


def unknown_rank(order: Sequence[str]) -> int:
    """Rank for project modules outside the known family vocabulary.

    The plan maps "services/ and any other" to the services tier;
    without a ``services`` entry the highest non-terminal rank applies.
    """
    if "services" in order:
        return order.index("services")
    return max(len(order) - 1, 0)


def relative_import_dots(
    source_module: str, target_module: str
) -> tuple[int, str | None]:
    """Compute the relative form from one module file to another.

    Returns ``(ups, tail)``: ``ups`` leading-dot count and the dotted
    remainder after the lowest common ancestor (``None`` when the target
    is reached by dots alone). Only valid when both share the project
    root package; callers guard that before calling.
    """
    src_parts = source_module.rpartition(".")[0].split(".")
    tgt_parts = target_module.split(".")
    common = 0
    for src, tgt in zip(src_parts, tgt_parts, strict=False):
        if src != tgt:
            break
        common += 1
    tail = tgt_parts[common:]
    return len(src_parts) - common, ".".join(tail) if tail else None
