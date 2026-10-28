"""Binding observes the consumer interpreter and rejects foreign environments.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import sysconfig
from pathlib import Path

from flext_infra import workspace
from tests import c, tm, u


class TestsFlextInfraWorktreeBinding:
    """The service resolves which distributions a worktree can supply."""

    @staticmethod
    def _consumer(tmp_path: Path) -> Path:
        """Return an external consumer declaring flext packages by pinned git URL.

        Returns:
            An external consumer declaring flext packages by pinned git URL.

        """
        provider = u.Tests.provider()
        consumer = tmp_path / "consumer"
        consumer.mkdir()
        (consumer / c.PYPROJECT_FILENAME).write_text(
            "[project]\n"
            'name = "consumer"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13"\n'
            "dependencies = [\n"
            f'  "flext-core @ git+{provider.base_url.rstrip("/")}/flext-core.git@'
            f'{u.Tests.provider_branch()}",\n'
            f'  "flext-cli @ git+{provider.base_url.rstrip("/")}/flext-cli.git@'
            f'{u.Tests.provider_branch()}",\n'
            '  "httpx>=0.27",\n'
            "]\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(consumer)
        tm.ok(u.Tests.create_python_environment(consumer))
        return consumer

    @staticmethod
    def _python(consumer: Path) -> Path:
        """Use the fixture consumer's physical environment.

        Returns:
            The resulting ``Path``.

        """
        environment = u.Infra.runtime_environment_dir(consumer)
        return (
            Path(
                sysconfig.get_path(
                    "scripts",
                    scheme="venv",
                    vars={"base": str(environment), "platbase": str(environment)},
                ),
            )
            / c.Infra.PromotedSelector.VENV_PYTHON
        )

    def test_binding_rejects_foreign_interpreter(self, tmp_path: Path) -> None:
        """A valid supplier cannot redirect installation to the running agent."""
        consumer = self._consumer(tmp_path)
        result = workspace.FlextInfraBindingService.consumer_marker_environment(
            consumer_root=consumer,
            python=Path(sys.executable),
        )
        tm.ok(result.failure)
        tm.that(result.error or "", has="must belong to the consumer")

    def test_consumer_markers_match_the_actual_interpreter(
        self,
        tmp_path: Path,
    ) -> None:
        """Marker selection uses full consumer interpreter facts."""
        consumer = self._consumer(tmp_path)
        facts = tm.ok(
            workspace.FlextInfraBindingService.consumer_marker_environment(
                consumer_root=consumer,
                python=self._python(consumer),
            ),
        )
        for key in ("python_full_version", "implementation_version", "sys_platform"):
            requirement = f"binding-candidate; {key} == '{facts[key]}'"
            tm.that(
                u.Infra.active_requirement(requirement, environment=facts),
                none=False,
            )
        tm.that(
            u.Infra.active_requirement(
                "binding-candidate; python_version < '0'",
                environment=facts,
            ),
            none=True,
        )
