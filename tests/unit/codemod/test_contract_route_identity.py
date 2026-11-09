"""Native contract routing retains resources and declared binding identity.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, p, tm, u


class TestsFlextInfraContractRouteIdentity:
    """Prove empty and populated routes with and without binding publication."""

    @staticmethod
    @c.Tests.MARK.parametrize("has_bindings", [False, True])
    @c.Tests.MARK.parametrize("empty", [False, True])
    def test_native_route_identity(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        *,
        has_bindings: bool,
        empty: bool,
    ) -> None:
        """A regular consumer keeps its rule and resource order without effects."""
        workspace, path = rope_contract_consumer
        source = "from pathlib import Path\nobserved = Path('retained')\n"
        tm.ok(u.Cli.atomic_write_text_file(path, source))
        rule = m.Infra.RopeContractRule(
            id="native-route-identity",
            pattern="Path(${value})",
            goal="Path(${value})",
            arguments={},
            bindings={"Path": "pathlib.Path"} if has_bindings else {},
        )
        project = workspace.rope_project
        resources = (
            ()
            if empty
            else (
                project.get_resource(
                    path.relative_to(workspace.repository_root).as_posix()
                ),
            )
        )
        routes = u.Infra.import_contract_routes(
            project, rule, resources, {path: source}
        )
        if empty:
            tm.that(routes, empty=True)
        else:
            tm.that(len(routes), eq=1)
            tm.that(routes[0][0] is rule, eq=True)
            tm.that(tuple(routes[0][1]), eq=resources)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
