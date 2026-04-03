"""Subcommand parser utilities for flext-infra CLI.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence

from flext_core import u
from flext_infra._utilities.cli_shared import FlextInfraUtilitiesCliShared
from flext_infra.typings import FlextInfraTypes as t


class FlextInfraUtilitiesCliSubcommand:
    """Subcommand parser creation and argument validation utilities."""

    @staticmethod
    def _merge_shared_flag_options(
        base_options: t.BoolMapping,
        overrides: t.BoolMapping | None,
    ) -> t.MutableBoolMapping:
        """Merge per-subcommand shared-flag overrides onto base options."""
        merged: t.MutableBoolMapping = dict(base_options)
        if overrides is None:
            return merged
        unknown_keys = set(overrides) - set(base_options)
        if unknown_keys:
            msg = ", ".join(sorted(unknown_keys))
            error_msg = f"Unknown shared flag override(s): {msg}"
            raise ValueError(error_msg)
        for key, value in overrides.items():
            merged[key] = value
        return merged

    @staticmethod
    def _union_shared_flag_options(
        options: Sequence[t.BoolMapping],
    ) -> t.MutableBoolMapping:
        """Compute the union of enabled shared flags across subcommands."""
        union = FlextInfraUtilitiesCliShared.SharedFlags(
            include_apply=False,
            include_diff=False,
            include_format=False,
            include_check=False,
            include_project=False,
        ).to_dict()
        for option_set in options:
            for key, value in option_set.items():
                union[key] = union[key] or value
        return union

    @staticmethod
    def _shared_option_tokens(options: t.BoolMapping) -> t.StrSequence:
        """Return CLI option tokens enabled by the given shared-flag config."""
        tokens: MutableSequence[str] = []
        if options.get("include_apply", False):
            tokens.extend(["--dry-run", "--apply"])
        if options.get("include_diff", False):
            tokens.append("--diff")
        if options.get("include_format", False):
            tokens.append("--format")
        if options.get("include_check", False):
            tokens.append("--check")
        if options.get("include_project", False):
            tokens.extend(["--project", "--projects"])
        return tokens

    @staticmethod
    def create_subcommand_parser(
        prog: str,
        description: str,
        *,
        subcommands: t.StrMapping,
        flags: t.BoolMapping | None = None,
        subcommand_flags: Mapping[str, t.BoolMapping] | None = None,
    ) -> t.Infra.Pair[ArgumentParser, Mapping[str, ArgumentParser]]:
        """Create main parser with subcommands and shared flags."""
        resolved_flags = (
            FlextInfraUtilitiesCliShared.SharedFlags.from_dict(flags)
            if flags is not None
            else FlextInfraUtilitiesCliShared.SharedFlags()
        )
        base_options = resolved_flags.to_dict()
        command_options: MutableMapping[str, t.MutableBoolMapping] = {}
        for command in subcommands:
            overrides = subcommand_flags.get(command) if subcommand_flags else None
            command_options[command] = (
                FlextInfraUtilitiesCliSubcommand._merge_shared_flag_options(
                    base_options,
                    overrides,
                )
            )
        root_options = FlextInfraUtilitiesCliSubcommand._union_shared_flag_options(
            [base_options, *command_options.values()],
        )
        root_shared_tokens = tuple(
            FlextInfraUtilitiesCliSubcommand._shared_option_tokens(root_options),
        )
        shared = FlextInfraUtilitiesCliShared.shared_flags_parser(
            FlextInfraUtilitiesCliShared.SharedFlags.from_dict(root_options),
        )
        parser = ArgumentParser(prog=prog, description=description, parents=[shared])
        subparsers = parser.add_subparsers(dest="command")
        command_parsers: MutableMapping[str, ArgumentParser] = {}
        for command, command_help in subcommands.items():
            command_shared = FlextInfraUtilitiesCliShared.shared_flags_parser(
                FlextInfraUtilitiesCliShared.SharedFlags.from_dict(
                    command_options[command]
                ),
                suppress_defaults=True,
            )
            command_parsers[command] = subparsers.add_parser(
                command,
                help=command_help,
                parents=[command_shared],
            )
            command_parsers[command].set_defaults(
                _allowed_shared_option_tokens=tuple(
                    FlextInfraUtilitiesCliSubcommand._shared_option_tokens(
                        command_options[command],
                    ),
                ),
                _root_shared_option_tokens=root_shared_tokens,
            )
        return parser, command_parsers

    @staticmethod
    def _extract_used_shared_options(
        argv: t.StrSequence,
        candidate_tokens: t.StrSequence,
    ) -> t.StrSequence:
        """Extract shared-option tokens explicitly provided on the CLI."""
        used: MutableSequence[str] = []
        known_tokens = set(candidate_tokens)
        for token in argv:
            normalized = token.split("=", 1)[0]
            if normalized not in known_tokens or normalized in used:
                continue
            used.append(normalized)
        return used

    @staticmethod
    def _coerce_option_tokens(
        value: tuple[str, ...] | list[str] | None,
    ) -> t.StrSequence:
        """Normalize argparse metadata into a concrete list of option tokens."""
        if value is None:
            return list[str]()
        return list(value)

    @staticmethod
    def parse_subcommand_args(
        parser: ArgumentParser,
        argv: t.StrSequence | None = None,
        *,
        passthrough_subcommands: t.StrSequence | None = None,
    ) -> Namespace:
        """Parse and validate subcommand args against per-command shared flags."""
        args, unknown_args = parser.parse_known_args(argv)
        raw_argv = list(argv) if argv is not None else sys.argv[1:]
        allowed_tokens = FlextInfraUtilitiesCliSubcommand._coerce_option_tokens(
            getattr(args, "_allowed_shared_option_tokens", None),
        )
        root_tokens = FlextInfraUtilitiesCliSubcommand._coerce_option_tokens(
            getattr(args, "_root_shared_option_tokens", None),
        )
        if not root_tokens:
            return args
        used_tokens = FlextInfraUtilitiesCliSubcommand._extract_used_shared_options(
            raw_argv,
            root_tokens,
        )
        allowed_token_set = set(allowed_tokens)
        disallowed = [token for token in used_tokens if token not in allowed_token_set]
        if not disallowed:
            passthrough = set(passthrough_subcommands or ())
            command = getattr(args, "command", None)
            command_label = u.to_str(command)
            if unknown_args:
                if command_label in passthrough:
                    setattr(args, "_unknown_args", tuple(unknown_args))
                    return args
                parser.error(f"unrecognized arguments: {' '.join(unknown_args)}")
            return args
        command = getattr(args, "command", None)
        command_label = u.to_str(command, default="subcommand")
        parser.error(
            f"unrecognized arguments for '{command_label}': {' '.join(disallowed)}",
        )
        return args


__all__ = ["FlextInfraUtilitiesCliSubcommand"]
