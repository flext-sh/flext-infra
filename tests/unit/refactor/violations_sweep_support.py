"""Shared recording-Makefile fixtures for the ``refactor violations-sweep`` contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from flext_infra import FlextInfraCli, config
from tests import c, m, tm, u

LOCAL_RULE_CATALOG = (
    f"{c.Infra.CODEMOD_SCOPE_KEY}: {c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n"
    "ruleDirs:\n  - rules\ntestConfigs: []\n"
)

LOCAL_GROWTH_RULE = (
    "id: sweep-growth\n"
    "language: Python\n"
    "rule:\n"
    "  pattern: marker = dict()\n"
    "fix: marker = tuple()\n"
    "severity: warning\n"
)


class TestsFlextInfraRefactorViolationsSweepSupport:
    """Prepare mod workspaces and drive the sweep verb for its behavior contract."""

    @staticmethod
    def _makefile(recipe: str = "", *, first_only: bool = False) -> str:
        """Provide the configured operations without freezing the Make policy.

        Returns:
            An executable Makefile derived from the current canonical verb policy.

        """
        verbs = tuple(
            dict.fromkeys(config.Infra.codegen.make.violations_sweep_repair_verbs)
        )
        names = " ".join(verbs)
        recording = "\t@printf '%s\\n' '$@' >> ran.txt\n"
        if first_only:
            return f".PHONY: {names}\n{verbs[0]}:\n{recording}{recipe}" + (
                f"{' '.join(verbs[1:])}:\n\t@true\n" if len(verbs) > 1 else ""
            )
        return f".PHONY: {names}\n{names}:\n{recording}{recipe}"

    @staticmethod
    def _prepare(root: Path, *, makefile: str, local_rule: bool) -> None:
        """Install the recording repair surface and the optional growth rule."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.MAKEFILE_FILENAME,
                makefile,
            ),
        )
        if local_rule:
            config_path = root / c.Infra.CODEMOD_CONFIG_RELPATH
            rules = config_path.parent / c.Cli.RULES_DIR_NAME
            tm.ok(u.Cli.ensure_dir(rules))
            tm.ok(u.Cli.atomic_write_text_file(config_path, LOCAL_RULE_CATALOG))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rules / "sweep.yml",
                    LOCAL_GROWTH_RULE,
                ),
            )

    @classmethod
    def _declare_members(cls, root: Path, names: tuple[str, ...]) -> tuple[Path, ...]:
        """Declare real member identities through the existing Git manifest owner.

        Returns:
            Fixture members with native project metadata and executable audits.

        """
        distribution, _dependencies = tm.ok(u.Infra.project_requirements(root))
        document = (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        members = tuple(root / name for name in names)
        for member in members:
            package = member / c.Infra.DEFAULT_SRC_DIR / member.name.replace("-", "_")
            tm.ok(u.Cli.ensure_dir(package))
            tm.ok(u.Cli.atomic_write_text_file(package / "__init__.py", ""))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    member / c.PYPROJECT_FILENAME,
                    document.replace(
                        f'name = "{distribution}"', f'name = "{member.name}"'
                    ),
                )
            )
            cls._prepare(
                member, makefile=".PHONY: audit\naudit:\n\t@true\n", local_rule=True
            )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.GITMODULES,
                "".join(
                    f'[submodule "{member.name}"]\n\tpath = {member.name}\n'
                    f"\turl = https://example.com/{member.name}.git\n"
                    for member in members
                ),
            )
        )
        return members

    @staticmethod
    def _sweep(root: Path, *options: str) -> int:
        """Run the public violations-sweep CLI once.

        Returns:
            The resulting ``int``.

        """
        return FlextInfraCli.infra_main([
            c.Infra.CLI_GROUP_REFACTOR,
            c.Infra.VIOLATIONS_SWEEP_ROUTE_NAME,
            "--repository-root",
            str(root),
            *options,
        ])

    @staticmethod
    def _receipt(root: Path) -> m.Infra.ViolationsSweepReport:
        """Load the typed receipt the verb publishes.

        Returns:
            The resulting ``m.Infra.ViolationsSweepReport``.

        """
        path = (
            tm.ok(u.Infra.refactor_report_evidence_root(root))
            / c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        )
        return m.Infra.ViolationsSweepReport.model_validate_json(
            path.read_bytes(),
        )

    @staticmethod
    def _verbs_ran(root: Path) -> Iterator[str]:
        """Yield the repair verbs the recording Makefile observed.

        Yields:
            Each recorded verb name.

        """
        lines = (root / "ran.txt").read_text(encoding="utf-8").splitlines()
        yield from (line for line in lines if line)
