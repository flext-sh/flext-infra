"""The composition root fails when two unrelated services share one member.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodemodCompositionRootCollisionRules:
    """``<package>/api.py`` obeys the facade member-collision law."""

    SHAPE = "ban-composition-root-member-collision"
    PACKAGE = "flext_test_project"
    MANAGED = (
        "class ManagedService:\n"
        "    @classmethod\n"
        "    def _service(cls, tool_id):\n"
        "        return tool_id\n"
    )

    @staticmethod
    def scan(tmp_path: Path, sources: Mapping[str, str]) -> tuple[Sequence[str], str]:
        """Render the rule for a real project and scan it with ast-grep.

        Returns:
            ``<file>:<shape>`` per finding, and every rendered message.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        for name, source in sources.items():
            target = package / name
            target.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(target, source))
        with u.Infra.codemod_workspace_snapshot(repository) as snapshot:
            documents = u.Infra.codemod_composition_root_collision_rules(
                snapshot, repository
            )
        catalog = tmp_path / "catalog"
        (catalog / "rules").mkdir(parents=True)
        for rule_id, document in documents.items():
            tm.ok(u.Cli.yaml_dump(catalog / "rules" / f"{rule_id}.yml", document))
        tm.ok(u.Cli.yaml_dump(catalog / "sgconfig.yml", {"ruleDirs": ["rules"]}))
        output = u.Cli.capture([
            c.Infra.SG,
            "scan",
            "-c",
            str(catalog / "sgconfig.yml"),
            "--json=compact",
            str(repository),
        ]).unwrap()
        findings = sorted(
            f"{Path(finding['file']).name}:{finding['ruleId'].partition('--')[0]}"
            for finding in json.loads(output)
        )
        messages = "\n".join(
            str(document["message"]) for document in documents.values()
        )
        return findings, messages

    @classmethod
    def api(cls, package: str) -> str:
        """Return the composition root composing both services.

        Returns:
            The ``api.py`` source.

        """
        return (
            f"from {package}.services.managed import ManagedService\n"
            f"from {package}.services.daemon import DaemonService\n"
            "class Hub(DaemonService, ManagedService):\n"
            "    pass\n"
            "__all__ = ['Hub']\n"
        )

    def test_unrelated_services_sharing_a_member_fail(self, tmp_path: Path) -> None:
        """Two unrelated services declaring ``_service`` fail on ``api.py``."""
        findings, messages = self.scan(
            tmp_path,
            {
                "services/__init__.py": "",
                "services/managed.py": self.MANAGED,
                "services/daemon.py": (
                    "class DaemonService:\n"
                    "    @classmethod\n"
                    "    def _service(cls):\n"
                    "        return 'daemon'\n"
                ),
                "api.py": self.api(self.PACKAGE),
            },
        )
        tm.that(findings, eq=[f"api.py:{self.SHAPE}"])
        tm.that(
            messages,
            has=(
                "declares '_service' in unrelated parts "
                "['DaemonService', 'ManagedService']"
            ),
        )

    def test_service_extending_another_passes(self, tmp_path: Path) -> None:
        """A service that extends another overrides it and is no collision."""
        findings, messages = self.scan(
            tmp_path,
            {
                "services/__init__.py": "",
                "services/managed.py": self.MANAGED,
                "services/daemon.py": (
                    f"from {self.PACKAGE}.services.managed import ManagedService\n"
                    "class DaemonService(ManagedService):\n"
                    "    @classmethod\n"
                    "    def _service(cls, tool_id):\n"
                    "        return 'daemon'\n"
                ),
                "api.py": self.api(self.PACKAGE),
            },
        )
        tm.that(findings, eq=[])
        tm.that(messages, eq="")
