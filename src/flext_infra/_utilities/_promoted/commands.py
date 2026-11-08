"""Promoted-command header ingress: PEP 723 ``script`` TOML into commands.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, m
from flext_infra._utilities import FlextInfraUtilitiesScriptMetadata
from flext_infra._utilities._promoted import FlextInfraUtilitiesPromotedWorkspace

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraUtilitiesPromotedCommands(
    FlextInfraUtilitiesPromotedWorkspace,
    FlextInfraUtilitiesScriptMetadata,
):
    """Parse each verb-directory header once into canonical command models."""

    @classmethod
    def promoted_command_headers(
        cls,
        verb_dir: Path,
    ) -> Mapping[Path, t.JsonMapping | c.Infra.PromotedRegistryError]:
        """Parse the ``[tool.flext.command]`` table of every candidate file.

        Only the PEP 723 ``script`` block within the first
        ``PROMOTED_HEADER_SCAN_LINES`` lines is read.

        Returns:
            The command table of each file, or its typed header error.

        """
        headers: MutableMapping[
            Path,
            t.JsonMapping | c.Infra.PromotedRegistryError,
        ] = {}
        for path in verb_dir.iterdir():
            if (
                not path.is_file()
                or path.suffix not in c.Infra.PROMOTED_COMMAND_SUFFIXES
                or path.name in c.Infra.PROMOTED_NON_COMMAND_NAMES
            ):
                continue
            lines = path.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines(
                keepends=True
            )
            headers[path] = cls._promoted_command_header(
                path, "".join(lines[: c.Infra.PROMOTED_HEADER_SCAN_LINES])
            )
        return headers

    @classmethod
    def _promoted_command_header(
        cls,
        path: Path,
        text: str,
    ) -> t.JsonMapping | c.Infra.PromotedRegistryError:
        """Read the command table of one file's leading text.

        A file without a ``script`` block, or whose block declares no
        ``[tool.flext.command]``, is not a command. More than one ``script``
        block, invalid TOML or a command entry that is no table is a defect.

        Returns:
            The command table, or its typed header error.

        """
        message = c.Infra.PromotedMessage
        blocks = [
            block
            for block in cls.script_metadata_blocks(text)
            if block.group("type") == c.Infra.SCRIPT_METADATA_TYPE
        ]
        if len(blocks) > 1:
            return c.Infra.PromotedRegistryError(
                message.MULTIPLE_SCRIPT_BLOCKS.format(path=path),
            )
        parsed: t.JsonMapping | None = (
            u.Cli.toml_mapping_from_text(cls.script_metadata_toml(blocks[0]))
            if blocks
            else {}
        )
        if parsed is None:
            return c.Infra.PromotedRegistryError(
                message.INVALID_HEADER_TOML.format(path=path),
            )
        *owner_path, key = c.Infra.PROMOTED_HEADER_TABLE
        owner = u.Cli.toml_mapping_path(parsed, owner_path)
        command = owner.get(key) if owner is not None else None
        if command is None:
            return c.Infra.PromotedMissingHeaderError(
                message.MISSING_HEADER.format(path=path),
            )
        if not isinstance(command, Mapping):
            return c.Infra.PromotedRegistryError(
                message.INVALID_HEADER_TABLE.format(path=path),
            )
        return command

    @classmethod
    def promoted_load_command(
        cls,
        path: Path,
        expected_verb: str,
        data: t.JsonMapping,
    ) -> p.Infra.PromotedCommand:
        """Validate one header against its directory and file, once at ingress.

        Returns:
            The resulting ``p.Infra.PromotedCommand``.

        """
        key = c.Infra.PromotedHeader
        message = c.Infra.PromotedMessage
        verb = cls._promoted_text(data, key.VERB, path)
        what = cls.promoted_what_slug(cls._promoted_text(data, key.WHAT, path))
        for actual, expected, mismatch in (
            (verb, expected_verb, message.VERB_MISMATCH),
            (what, cls.promoted_what_slug(path.stem), message.WHAT_MISMATCH),
        ):
            if actual != expected:
                cls.promoted_fail(
                    mismatch,
                    path=path,
                    verb=verb,
                    what=what,
                    expected=expected,
                )
        params_raw = data.get(key.PARAMS, [])
        if not isinstance(params_raw, list):
            cls.promoted_fail(message.PARAMS_NOT_LIST, path=path)
        params: MutableSequence[p.Infra.PromotedParam] = []
        for item in params_raw:
            if not isinstance(item, dict):
                cls.promoted_fail(message.PARAMS_NOT_TABLE, path=path)
            required = item.get(key.REQUIRED, False)
            default = item.get(key.DEFAULT, "")
            if not isinstance(required, bool):
                cls.promoted_fail(message.PARAMS_REQUIRED_TYPE, path=path)
            if not isinstance(default, str):
                cls.promoted_fail(message.PARAMS_DEFAULT_TYPE, path=path)
            params.append(
                m.Infra.PromotedParam(
                    name=cls._promoted_text(item, key.NAME, path),
                    help=cls._promoted_text(item, key.HELP, path),
                    required=required,
                    default=default,
                    choices=cls._promoted_texts(
                        item.get(key.CHOICES, []),
                        key.PARAMS_CHOICES,
                        path,
                    ),
                ),
            )
        domain = cls._promoted_text(data, key.DOMAIN, path)
        summary = cls._promoted_text(data, key.SUMMARY, path)
        description = cls._promoted_text(data, key.DESCRIPTION, path)
        example = cls._promoted_text(data, key.EXAMPLE, path)
        mutates = data.get(key.MUTATES)
        if not isinstance(mutates, bool):
            cls.promoted_fail(message.REQUIRED_BOOL, path=path, key=key.MUTATES)
        return m.Infra.PromotedCommand(
            verb=verb,
            what=what,
            domain=domain,
            summary=summary,
            description=description,
            example=example,
            path=path,
            mutates=mutates,
            aliases=cls._promoted_texts(data.get(key.ALIASES, []), key.ALIASES, path),
            params=tuple(params),
            rules=cls._promoted_texts(data.get(key.RULES, []), key.RULES, path),
        )

    @staticmethod
    def promoted_what_slug(name: str) -> str:
        """Return the public WHAT slug of a header ``what``, request or file stem.

        A Python module stem cannot hold ``-``, so ``helm_drift.py`` and
        ``helm-drift.sh`` both publish ``helm-drift``; every WHAT comparison and
        registry key goes through this one normalizer.

        Returns:
            ``name`` with each stem separator replaced by the slug separator.

        """
        return name.replace(
            c.Infra.PROMOTED_STEM_SEPARATOR,
            c.Infra.PROMOTED_WHAT_SEPARATOR,
        )

    @classmethod
    def _promoted_text(
        cls,
        data: Mapping[str, t.JsonValue],
        key: str,
        path: Path,
    ) -> str:
        """Return one required non-blank stripped header string.

        Returns:
            One required non-blank stripped header string.

        """
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            cls.promoted_fail(
                c.Infra.PromotedMessage.REQUIRED_STRING,
                path=path,
                key=key,
            )
        return value.strip()

    @classmethod
    def _promoted_texts(
        cls,
        values: t.JsonValue,
        key: str,
        path: Path,
    ) -> tuple[str, ...]:
        """Return one optional header list of non-blank stripped strings.

        Returns:
            One optional header list of non-blank stripped strings.

        """
        if not isinstance(values, list):
            cls.promoted_fail(
                c.Infra.PromotedMessage.STRING_LIST_TYPE,
                path=path,
                key=key,
            )
        texts: list[str] = []
        for item in values:
            if not isinstance(item, str) or not item.strip():
                cls.promoted_fail(
                    c.Infra.PromotedMessage.STRING_LIST_ITEM,
                    path=path,
                    key=key,
                )
            texts.append(item.strip())
        return tuple(texts)


__all__: list[str] = ["FlextInfraUtilitiesPromotedCommands"]
