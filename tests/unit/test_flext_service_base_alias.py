"""Tests for the FLEXT service-base alias.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraServiceBase
from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, m, t, tm, u


class TestsFlextInfraServiceBaseAlias:
    """Tests for ``FlextInfraServiceBaseAlias``."""

    @staticmethod
    def test_service_base_generic_alias_flext_is_permitted(
        mod_workspace: Path,
    ) -> None:
        """Generic service-root bases trigger no static facade rule finding."""
        project = u.Tests.mk_project(
            mod_workspace,
            "service-consumer",
            pyproject=(
                '[project]\nname = "service-consumer"\nversion = "0.1.0"\n'
                "dependencies = []\n"
            ),
            with_src=True,
        )
        u.Tests.initialize_git_repo(project)
        service = project / "service.py"
        permitted = (
            "from flext_cli import s\n"
            "from flext_infra import FlextInfraServiceBase\n"
            "class FlextDemoService(FlextInfraServiceBase[str]):\n"
            "    pass\n"
            "class FlextDemoCliService(s[str]):\n"
            "    pass\n"
        )
        service.write_text(permitted, encoding=c.DEFAULT_ENCODING)
        u.Tests.declare_workspace_projects(mod_workspace, (project.name,))
        rules = (
            "facade-base-by-class-name",
            "ban-class-wrong-facade-layer",
            "ban-long-facade-name-import",
        )
        clean = tm.ok(
            FlextInfraModGateEngine.scan(mod_workspace, fix=False, selection=rules)
        )
        tm.that(
            tuple(entry for entry in clean.entries if entry.repository == project.name),
            length=0,
        )
        service.write_text(
            permitted + "from flext_infra import FlextInfraModels\n",
            encoding=c.DEFAULT_ENCODING,
        )
        flagged = tm.ok(
            FlextInfraModGateEngine.scan(mod_workspace, fix=False, selection=rules)
        )
        tm.that(
            tuple(
                entry.rule_id
                for entry in flagged.entries
                if entry.repository == project.name
            ),
            eq=("ban-long-facade-name-import",),
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, None),
            ("", None),
            (" , \t\n", None),
            (" one, two\nthree ", "one,two,three"),
            ("one,one two", "one,one,two"),
            ((" one,two ", " three\tfour "), "one,two,three,four"),
            ((), None),
        ],
    )
    def test_command_filter_normalization(
        value: str | t.StrSequence | None,
        expected: str | None,
    ) -> None:
        """Services and public helpers consume the same selector normalization."""
        service = FlextInfraServiceBase[t.JsonPayload].model_validate(
            {"project_filter": value},
        )
        tm.that(service.project_filter, eq=expected)
        values = (value,) if isinstance(value, str) else value or ()
        normalized = u.Infra.normalize_cli_values(*values)
        tm.that(
            normalized,
            eq=tuple(expected.split(",")) if expected is not None else (),
        )
        tm.that(u.Infra.normalize_cli_values(None, *values, None), eq=normalized)

    @staticmethod
    def test_command_root_normalizes_files_and_new_paths(
        tmp_path: t.Infra.Path,
    ) -> None:
        """Root normalization keeps the invocation directory and accepts new paths."""
        source = tmp_path / "input.txt"
        source.write_text("input", encoding=c.DEFAULT_ENCODING)
        for supplied, expected in (
            (source, tmp_path.resolve()),
            (tmp_path, tmp_path.resolve()),
            (tmp_path / "not-created", (tmp_path / "not-created").resolve()),
        ):
            service = FlextInfraServiceBase[t.JsonPayload].model_validate(
                {"repository_root": str(supplied)},
            )
            tm.that(service.root, eq=expected)
            tm.that(u.Infra.resolve_repository_root_or_cwd(supplied), eq=expected)
        service = FlextInfraServiceBase[t.JsonPayload]()
        tm.that(service.root, eq=Path.cwd().resolve())
        tm.that(u.Infra.resolve_repository_root_or_cwd(), eq=service.root)

    @staticmethod
    @pytest.mark.parametrize(
        "value",
        [None, "", "   ", " result/../reports ", Path("reports")],
    )
    def test_command_optional_paths(value: t.Cli.TextPath | None) -> None:
        """Report paths resolve, whereas output directories preserve relative scope."""
        service = FlextInfraServiceBase[t.JsonPayload].model_validate(
            {"report_path": value, "output_dir": value},
        )
        expected_report = None if value is None else Path(value).resolve()
        expected_output = None
        if value is not None:
            expected_output = value if isinstance(value, Path) else Path(value.strip())
        tm.that(service.report_path, eq=expected_report)
        tm.that(service.output_dir, eq=expected_output)
        tm.that(u.Infra.normalize_optional_path(value), eq=expected_report)

    @staticmethod
    def test_command_absolute_output_directory(tmp_path: t.Infra.Path) -> None:
        """Absolute output directories use native path resolution."""
        supplied = tmp_path / "unused" / ".." / "reports"
        for value in (supplied, f" {supplied} "):
            service = FlextInfraServiceBase[t.JsonPayload].model_validate(
                {"output_dir": value},
            )
            tm.that(service.output_dir, eq=supplied.resolve())

    @staticmethod
    @pytest.mark.parametrize("apply", [False, True])
    @pytest.mark.parametrize("check", [False, True])
    @pytest.mark.parametrize("dry_run", [False, True])
    def test_command_write_mode_is_request_local(
        *,
        apply: bool,
        check: bool,
        dry_run: bool,
    ) -> None:
        """Mutable schema fields retain kernel behavior without shared request state."""
        first = FlextInfraServiceBase[t.JsonPayload].model_validate(
            {"apply": apply, "check": check, "dry_run": dry_run},
        )
        second = FlextInfraServiceBase[t.JsonPayload].model_validate(
            {"apply_changes": apply, "check_only": check, "dry_run": dry_run},
        )
        expected = dry_run or check or not apply
        tm.that(first.effective_dry_run, eq=expected)
        tm.that(second.effective_dry_run, eq=expected)
        first.apply_changes = not apply
        tm.that(first.effective_dry_run, eq=dry_run or check or apply)
        tm.that(second.apply_changes, eq=apply)
        tm.that(second.effective_dry_run, eq=expected)
        tm.that(first.fail_fast, eq=c.Infra.SERVICE_FAIL_FAST)
        tm.ok(first.log is first.logger)

    @staticmethod
    def test_command_aliases_payload_and_serialization(tmp_path: t.Infra.Path) -> None:
        """The MRO preserves aliases, computed values and the public payload shape."""
        service = FlextInfraServiceBase[t.JsonPayload].model_validate(
            {
                "repository_root": tmp_path,
                "apply": True,
                "check": False,
                "dry_run": False,
                "output_format": " JSON ",
                "project_filter": ("one,two",),
                "report_path": tmp_path / "report.json",
                "output_dir": " reports ",
            },
        )
        tm.that(service.output_format, eq="json")
        tm.that(
            service.command_payload(),
            eq={
                "repository_root": str(tmp_path.resolve()),
                "apply_changes": True,
                "check_only": False,
                "dry_run": False,
                "output_format": "json",
                "project_filter": "one,two",
                "report_path": str((tmp_path / "report.json").resolve()),
                "output_dir": "reports",
            },
        )
        serialized = service.model_dump(mode="json", by_alias=True)
        tm.that(serialized["apply"], eq=service.apply_changes)
        tm.that(serialized["check"], eq=service.check_only)
        tm.that(serialized["root"], eq=str(service.root))
        tm.that(serialized["effective_dry_run"], eq=service.effective_dry_run)
        tm.ok("project_filter" not in serialized)
        tm.ok("report_path" not in serialized)
        tm.ok("output_dir" not in serialized)
        schema = service.model_json_schema()
        context_schema = m.Infra.CommandContext.model_json_schema()
        for name in ("repository_root", "apply", "check"):
            tm.that(schema["properties"][name], eq=context_schema["properties"][name])
        tm.that(
            schema["properties"]["apply"]["typer_param_decls"],
            eq=list(c.Infra.CLI_APPLY_OPTION_DECLS),
        )

    @staticmethod
    def test_command_default_payload_omits_optional_fields() -> None:
        """Default construction retains the original compact command payload."""
        service = FlextInfraServiceBase[t.JsonPayload]()
        context = m.Infra.CommandContext()
        tm.that(
            service.command_payload(),
            eq={
                "repository_root": str(context.repository_root),
                "apply_changes": context.apply_changes,
                "check_only": context.check_only,
                "dry_run": context.dry_run,
                "output_format": context.output_format,
            },
        )
