"""Promoted-command framework: cosmos-command TOML header parsing and field extraction."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.promoted.base import (
    HEADER_END,
    HEADER_START,
    MissingHeaderError,
    RegistryError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from flext_infra import p, t


def header_data(path: Path) -> t.JsonMapping:
    """Parse one cosmos-command TOML header using the FLEXT TOML facade.

    Returns:
        The parsed header payload as a ``t.JsonMapping``.

    Raises:
        RegistryError: When the file carries no cosmos-command header or the
            header payload is not valid TOML.

    """
    from flext_infra import u

    lines = path.read_text(encoding="utf-8").splitlines()[:160]
    in_header = False
    payload: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        content = stripped[1:].strip() if stripped.startswith("#") else stripped
        if content == HEADER_START:
            in_header = True
            continue
        if in_header and content == HEADER_END:
            break
        if in_header:
            payload.append(content)
    if not payload:
        msg = f"{path}: sem header cosmos-command"
        raise MissingHeaderError(msg)
    parsed = u.Cli.toml_mapping_from_text("\n".join(payload))
    if parsed is None:
        msg = f"{path}: header TOML invalido"
        raise RegistryError(msg)
    try:
        return _normalize_toml_table(parsed)
    except TypeError as exc:
        msg = f"{path}: {exc}"
        raise RegistryError(msg) from exc


def _normalize_toml_table(data: t.JsonMapping) -> t.JsonMapping:
    """Normalize validated JSON-compatible TOML into framework types.

    Returns:
        A recursively validated TOML table without nullable JSON values.

    """

    def normalize(value: t.JsonValue) -> t.JsonValue:
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [normalize(item) for item in value]
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items()}
        msg = f"invalid TOML value: {value!r}"
        raise TypeError(msg)

    return {key: normalize(value) for key, value in data.items()}


def require_string(data: Mapping[str, t.JsonValue], key: str, path: Path) -> str:
    """Return a required string field from a command header.

    Raises:
        RegistryError: When the field is missing, not a string, or blank.

    """
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        msg = f"{path}: campo obrigatorio ausente: {key}"
        raise RegistryError(msg)
    return value.strip()


def require_bool(data: Mapping[str, t.JsonValue], key: str, path: Path) -> bool:
    """Return a required boolean field from a command header.

    Raises:
        RegistryError: When the field is missing or not a boolean.

    """
    value = data.get(key)
    if not isinstance(value, bool):
        msg = f"{path}: campo booleano obrigatorio ausente: {key}"
        raise RegistryError(msg)
    return value


def parse_aliases(value: t.JsonValue | None, path: Path) -> tuple[str, ...]:
    """Parse the aliases field from a command header.

    Returns:
        A tuple of alias specifications, empty when the header declares no
        aliases.

    """
    return parse_string_list(value, "aliases", path)


def parse_alias_spec(alias: str, command: p.Infra.Promoted.Command) -> tuple[str, str]:
    """Parse one alias specification into alias name and target WHAT.

    Returns:
        A ``(alias_name, target_what)`` tuple; the target WHAT defaults to the
        command's own WHAT when the spec has no ``=`` separator.

    Raises:
        RegistryError: When the alias name or the target WHAT is empty.

    """
    alias_name, separator, target_what = alias.partition("=")
    alias_name = alias_name.strip()
    target_what = target_what.strip() if separator else command.what
    if not alias_name or not target_what:
        msg = f"{command.path}: alias invalido {alias!r}; use alias ou alias=WHAT"
        raise RegistryError(msg)
    return alias_name, target_what


def parse_string_list(
    value: t.JsonValue | None, field: str, path: Path
) -> tuple[str, ...]:
    """Parse a TOML list of strings.

    Returns:
        A tuple of stripped strings, empty when ``value`` is ``None``.

    Raises:
        RegistryError: When the value is not a list or holds a non-string or
            blank item.

    """
    if value is None:
        return ()
    if not isinstance(value, list):
        msg = f"{path}: {field} deve ser lista de strings"
        raise RegistryError(msg)
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            msg = f"{path}: {field} invalido"
            raise RegistryError(msg)
        values.append(item.strip())
    return tuple(values)
