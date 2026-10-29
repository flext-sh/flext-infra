"""Installed sibling providers resolve parents without expanding publication scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from tests import c, p, tm, u


class TestsFlextInfraLazyInitWorkspaceElection:
    """Workspace planning consumes installed parents without publishing them."""

    @staticmethod
    def _provision_runtime(
        workspace: Path,
        repositories: Sequence[str],
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Install real tooling and editable providers in the fixture runtime."""
        checkout = Path(__file__).resolve().parents[3]
        u.Tests.initialize_git_repo(workspace)
        tm.ok(
            u.Tests.create_python_environment(
                workspace,
                dependency_projects=(
                    *u.Tests.python_dependency_projects(checkout),
                    checkout,
                ),
                session_runtime=session_runtime,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                (
                    u.Tests.managed_uv(),
                    "pip",
                    "install",
                    "--python",
                    str(u.Infra.runtime_environment_dir(workspace)),
                    "--no-deps",
                    *(
                        argument
                        for root in repositories
                        for argument in ("--editable", root)
                    ),
                ),
                cwd=workspace,
            )
        )

    @staticmethod
    def _run_plan(
        workspace: Path, repository: Path, *, check_only: bool = False
    ) -> int:
        """Plan with installed providers and publish through the shared owner.

        Returns:
            The number of remaining effects, or zero after publication.

        """
        output = u.Tests.run_lazy_init_probe(
            "from pathlib import Path\n"
            "from flext_infra import u\n"
            "from flext_infra.codegen import FlextInfraCodegenLazyInit\n"
            "import sys\n"
            "root = Path(sys.argv[1])\n"
            "service = FlextInfraCodegenLazyInit(repository_root=root)\n"
            "plans = service.plan_files().unwrap()\n"
            "if sys.argv[2] == 'check':\n"
            "    print(sum(u.Infra.codegen_file_requires_effect(p) for p in plans))\n"
            "else:\n"
            "    u.Infra.publish_codegen_plans(root, plans).unwrap()\n"
            "    print(0)\n",
            arguments=(str(repository), "check" if check_only else "publish"),
            runtime_root=workspace,
        )
        return int(output[-1])

    @staticmethod
    def _write_constants(package_root: Path, *, parent: str, class_name: str) -> None:
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            f"from {parent} import c as parent_c\n\n"
            f"class {class_name}(parent_c):\n"
            "    pass\n\n"
            f"c = {class_name}\n"
            f'__all__: list[str] = ["{class_name}", "c"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )

    def test_workspace_plan_uses_installed_sibling_without_publishing_it(
        self,
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Installed parent chains converge without sibling publication effects."""
        workspace = tmp_path / "workspace"
        owner_repo, owner = u.Tests.create_lazy_init_workspace(
            workspace,
            project_name="flext-ws-owner",
            package_name="flext_ws_owner",
        )
        middle_repo, middle = u.Tests.create_lazy_init_workspace(
            workspace,
            project_name="flext-ws-middle",
            package_name="flext_ws_middle",
        )
        child_repo, child = u.Tests.create_lazy_init_workspace(
            workspace,
            project_name="flext-ws-child",
            package_name="flext_ws_child",
        )
        workspace.joinpath(c.Infra.GITMODULES).write_text(
            "".join(
                f'[submodule "{name}"]\n\tpath = {name}\n'
                for name in ("flext-ws-owner", "flext-ws-middle", "flext-ws-child")
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.write_lazy_init_namespace_module(
            owner / c.Infra.CONSTANTS_PY,
            class_name="FlextWsOwnerConstants",
            alias="c",
        )
        u.Tests.write_lazy_init_namespace_module(
            owner / "result.py",
            class_name="FlextWsOwnerResult",
            alias="r",
        )
        self._write_constants(
            middle,
            parent="flext_ws_owner",
            class_name="FlextWsMiddleConstants",
        )
        self._write_constants(
            child,
            parent="flext_ws_middle",
            class_name="FlextWsChildConstants",
        )

        # The owner has no cross-repository parent: two self-scoped planning
        # cycles reach the fixed point (the second writes nothing), and the
        # generated facade exports only the owner's own namespace.
        tm.that(u.Tests.run_lazy_init(owner_repo), eq=0)
        tm.that(u.Tests.run_lazy_init(owner_repo), eq=0)
        tm.that(u.Tests.run_lazy_init(owner_repo, check_only=True), eq=0)
        generated = owner.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        entries, _refs = u.Infra.lazy_import_mapping_source(generated)

        tm.that(dict(entries).get(".constants", ()), has="c")

        self._provision_runtime(
            workspace,
            (str(owner_repo), str(middle_repo), str(child_repo)),
            session_runtime,
        )
        tm.that(self._run_plan(workspace, middle_repo), eq=0)
        tm.that(self._run_plan(workspace, middle_repo, check_only=True), eq=0)
        tm.that(self._run_plan(workspace, child_repo), eq=0)
        tm.that(self._run_plan(workspace, child_repo, check_only=True), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_ws_child as child\n"
                "import flext_ws_middle as middle\n"
                "import flext_ws_owner as owner\n"
                "print(child.r is middle.r is owner.r)\n"
                "print(issubclass(child.c, middle.c))\n",
                runtime_root=workspace,
            ),
            eq=["True", "True"],
        )
        tm.that(
            owner.joinpath(c.Infra.INIT_PY).read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
            eq=generated,
        )

        # The workspace root owns no package dirs at all: its members are
        # declared submodules, consumed as installed libraries, and its
        # plan is empty by contract.
        tm.that(u.Tests.run_lazy_init(workspace), eq=0)
        tm.that(u.Tests.run_lazy_init(workspace, check_only=True), eq=0)
        self._write_constants(
            child,
            parent=f"{child.name}_absent",
            class_name="FlextWsChildConstants",
        )
        with pytest.raises(AssertionError, match="resolves nowhere"):
            _ = self._run_plan(workspace, child_repo, check_only=True)
