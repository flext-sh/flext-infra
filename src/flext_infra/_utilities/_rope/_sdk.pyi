"""Typed consumed surface of the unchanged native Rope restructuring class.

The native change computer is private. Its returned capability is get_changed,
not ownership of its implementation class. No source-editing behavior lives here.
"""

from typing import Unpack

from flext_infra import p, t

class Restructure:
    """Native SDK class re-exported unchanged by the accompanying runtime module."""

    def __init__(self, *args: Unpack[t.Infra.RopeRestructureInitArguments]) -> None: ...
    def get_changes(
        self, *, resources: list[p.Infra.RopeResource]
    ) -> p.Infra.RopeChangeSet: ...
    def _compute_changes(
        self,
        matches: t.SequenceOf[t.Infra.RopeNativeMatch],
        pymodule: t.Infra.RopeNativeSourceModule,
    ) -> p.Infra.RopeChangeComputer: ...
    def _add_imports(
        self,
        resource: t.Infra.RopeNativeResource,
        source: str,
        imports: t.StrSequence,
    ) -> str: ...

__all__: list[str]
