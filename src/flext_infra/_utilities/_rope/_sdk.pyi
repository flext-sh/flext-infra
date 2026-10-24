# Copyright (c) 2026 FLEXT Team. All rights reserved.
# SPDX-License-Identifier: MIT
# The native change computer is private; get_changed is its consumed capability.

from flext_infra import p, t

class Restructure:
    def __init__(self, *args: *t.Infra.RopeRestructureInitArguments) -> None: ...
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

__all__: list[str] = ["Restructure"]
