"""Shared CLI flag models and parsers for flext-infra."""

from __future__ import annotations

from argparse import SUPPRESS, ArgumentParser
from pathlib import Path
from typing import Annotated

from pydantic import Field, model_validator

from flext_core import u
from flext_infra import FlextInfraModels as m, FlextInfraTypes as t


class FlextInfraUtilitiesCliShared:
    """Shared flag contracts used by CLI entrypoints and subcommands."""

    class SharedFlags(m.ContractModel):
        """Bundled CLI flag configuration for shared parser options."""

        include_apply: Annotated[
            bool, Field(description="Add apply/dry-run mutually exclusive flags")
        ] = True
        include_diff: Annotated[
            bool,
            Field(
                description="Include a diff flag, defaults to True if apply is included"
            ),
        ] = True
        include_format: Annotated[
            bool, Field(description="Add the format output option flag")
        ] = False
        include_check: Annotated[bool, Field(description="Add the check mode flag")] = (
            False
        )
        include_project: Annotated[
            bool, Field(description="Add the project filtering options")
        ] = False

        @model_validator(mode="before")
        @classmethod
        def _resolve_include_diff(
            cls,
            data: t.OptionalBoolMapping | FlextInfraUtilitiesCliShared.SharedFlags,
        ) -> t.OptionalBoolMapping | FlextInfraUtilitiesCliShared.SharedFlags:
            if u.is_mapping(data) and (
                "include_diff" not in data or data.get("include_diff") is None
            ):
                resolved: t.MutableOptionalBoolMapping = dict(data)
                resolved["include_diff"] = data.get("include_apply", True)
                return resolved
            return data

        def to_dict(self) -> t.MutableBoolMapping:
            """Convert the flag bundle to a mutable mapping."""
            return {
                "include_apply": self.include_apply,
                "include_diff": self.include_diff,
                "include_format": self.include_format,
                "include_check": self.include_check,
                "include_project": self.include_project,
            }

        @staticmethod
        def from_dict(
            data: t.BoolMapping,
        ) -> FlextInfraUtilitiesCliShared.SharedFlags:
            """Build a shared-flag bundle from a plain mapping."""
            return FlextInfraUtilitiesCliShared.SharedFlags.model_validate(data)

    @staticmethod
    def _add_shared_flags(
        parser: ArgumentParser,
        flags: FlextInfraUtilitiesCliShared.SharedFlags,
        *,
        suppress_defaults: bool = False,
    ) -> None:
        resolved_include_apply = flags.include_apply
        resolved_include_diff = flags.include_diff
        default_path = SUPPRESS if suppress_defaults else Path.cwd()
        default_bool = SUPPRESS if suppress_defaults else False
        default_text = SUPPRESS if suppress_defaults else "text"
        default_project = SUPPRESS if suppress_defaults else None
        _ = parser.add_argument(
            "--workspace",
            type=Path,
            default=default_path,
            help="Workspace root directory (default: cwd)",
        )
        if resolved_include_apply or resolved_include_diff:
            mode = parser.add_mutually_exclusive_group(required=False)
            if resolved_include_apply:
                _ = mode.add_argument(
                    "--dry-run",
                    action="store_true",
                    default=default_bool,
                    help="Plan/Scan only",
                )
                _ = mode.add_argument(
                    "--apply",
                    action="store_true",
                    default=default_bool,
                    help="Apply changes",
                )
            if resolved_include_diff:
                _ = mode.add_argument(
                    "--diff",
                    action="store_true",
                    default=default_bool,
                    help="Show unified diff of changes without applying",
                )
        if flags.include_format:
            _ = parser.add_argument(
                "--format",
                dest="output_format",
                choices=["json", "text"],
                default=default_text,
                help="Output format (default: text)",
            )
        if flags.include_check:
            _ = parser.add_argument(
                "--check",
                action="store_true",
                default=default_bool,
                help="Run in check mode",
            )
        if flags.include_project:
            _ = parser.add_argument(
                "--projects",
                type=str,
                default=default_project,
                help="Single project to process",
            )
            _ = parser.add_argument(
                "--projects",
                type=str,
                default=default_project,
                help="Multiple projects (comma-separated or glob pattern)",
            )

    @staticmethod
    def shared_flags_parser(
        flags: FlextInfraUtilitiesCliShared.SharedFlags,
        *,
        suppress_defaults: bool = False,
    ) -> ArgumentParser:
        """Build the shared-flags parser exposed to sibling CLI helpers."""
        base = ArgumentParser(add_help=False)
        FlextInfraUtilitiesCliShared._add_shared_flags(
            base,
            flags,
            suppress_defaults=suppress_defaults,
        )
        return base


__all__ = ["FlextInfraUtilitiesCliShared"]
