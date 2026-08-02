"""Verify the generated Make wrapper and engine consume one typed SSOT."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config
from flext_tests import tm
from tests import u as test_u

if TYPE_CHECKING:
    from flext_cli import p as cli_p


def _copy_generated_make(root: Path) -> tuple[Path, Path]:
    """Copy the catalog-owned Make projections into an isolated checkout."""
    checkout_root = Path(__file__).resolve().parents[3]
    surfaces = config.Infra.codegen.surfaces
    targets: list[Path] = []
    for relative_path in (surfaces.make_wrapper_path, surfaces.make_engine_path):
        source = checkout_root / relative_path
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        targets.append(target)
    return targets[0], targets[1]


class TestsWorkspaceRootMakeContract:
    """Protect the catalog-to-generated-runtime Make boundary."""

    def test_workspace_root_make_surfaces_come_from_one_catalog(self) -> None:
        """Resolve the sole wrapper and engine from ``codegen.surfaces``."""
        surfaces = config.Infra.codegen.surfaces
        entries_by_role = {
            entry.make_role: entry
            for entry in surfaces.entries
            if entry.make_role != "none"
        }

        tm.that(entries_by_role, len=2)
        tm.that(entries_by_role["wrapper"].path, eq=surfaces.make_wrapper_path)
        tm.that(entries_by_role["engine"].path, eq=surfaces.make_engine_path)
        for entry in entries_by_role.values():
            tm.that(entry.profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_generated_wrapper_and_engine_project_the_typed_graph(
        self, tmp_path: Path
    ) -> None:
        """Keep includes and public verbs derived from their typed owners."""
        wrapper, engine = _copy_generated_make(tmp_path)
        surfaces = config.Infra.codegen.surfaces
        make = config.Infra.codegen.make
        public_verbs = "PUBLIC_VERBS :=" + "".join(
            f" {verb.name}" for verb in make.verbs
        )

        tm.that(
            wrapper.read_text(encoding="utf-8"),
            has=f"include {surfaces.make_engine_path}",
        )
        tm.that(engine.read_text(encoding="utf-8"), has=public_verbs)

    def test_generated_engine_transports_one_declared_handler(
        self, tmp_path: Path
    ) -> None:
        """Forward a config-selected verb and handler to the sole serializer."""
        _copy_generated_make(tmp_path)
        make = config.Infra.codegen.make
        operations = {operation.name: operation for operation in make.operations}
        verb, handler = next(
            (verb, handler)
            for verb in make.verbs
            for handler in verb.handlers
            if handler.default
            and handler.apply_policy == "never"
            and operations[verb.operation].executor != "bootstrap"
        )
        invocation_log = tmp_path / "serializer-args.log"
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python",
            f'#!/bin/sh\nprintf "%s\\n" "$*" > "{invocation_log}"\n',
        )

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [verb.name, f"{make.selector}={handler.what}"], cwd=tmp_path
            )
        )
        output = process.stdout + process.stderr
        invocation = invocation_log.read_text(encoding="utf-8")

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(
            invocation,
            has=[
                f"{make.executor.group} {make.executor.route}",
                f"--verb {verb.name}",
                f"--selector-value {handler.what}",
                f"--apply-token {make.apply_absent_value}",
            ],
        )


__all__: tuple[str, ...] = ()
