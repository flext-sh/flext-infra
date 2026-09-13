"""Promoted-command framework: promoted command discovery across configured script roots."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.promoted.base import (
    COMMAND_SUFFIXES,
    IGNORED_DIRS,
    PACKAGE_MARKERS,
    MissingHeaderError,
    RegistryError,
    discovered_workspace_spec,
)
from flext_infra.promoted.headers import (
    header_data,
    parse_aliases,
    parse_string_list,
    require_bool,
    require_string,
)
from flext_infra.promoted.registry import Registry

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flext_infra import p, t


def discover(
    *,
    script_roots: Sequence[Path] | None = None,
    spec: p.Infra.Promoted.WorkspaceSpec | None = None,
) -> Registry:
    """Discover promoted commands from all configured script roots.

    FLEXT-STRICT (p/ outro agente): o primeiro root configurado e autoritativo;
    os demais so preenchem lacunas via skip_existing. Assim o workspace pode
    injetar scripts/ antes dos subrepos, enquanto cada subrepo isolado continua
    autoritativo sobre seus proprios comandos. Duplicatas dentro do mesmo root
    continuam levantando RegistryError.

    Returns:
        A validated ``Registry`` holding every discovered command and alias.

    Raises:
        RegistryError: When no scripts directory exists, a scripts entry is
            neither file nor directory, or a discovered command header is
            invalid or duplicated.

    """
    resolved_spec = spec if spec is not None else discovered_workspace_spec()
    registry = Registry()
    roots = _script_roots(script_roots, resolved_spec)
    if not any(root.exists() for root in roots):
        msg = "nenhum diretorio scripts encontrado"
        raise RegistryError(msg)
    for root_index, scripts_root in enumerate(roots):
        if not scripts_root.exists():
            continue
        skip_existing = root_index > 0
        for path in sorted(scripts_root.iterdir()):
            if path.name == "__pycache__":
                continue
            if path.is_file():
                continue
            if not path.is_dir():
                msg = f"{path}: entrada invalida em {scripts_root}"
                raise RegistryError(msg)
            if path.name in IGNORED_DIRS:
                continue
            _discover_verb_dir(registry, path, skip_existing=skip_existing)
    registry.validate()
    return registry


def _script_roots(
    script_roots: Sequence[Path] | None, spec: p.Infra.Promoted.WorkspaceSpec
) -> list[Path]:
    """Return de-duplicated script roots in first-wins discovery order.

    FLEXT-STRICT (p/ outro agente): ordem injetada = prioridade first-wins. Sem
    injecao, spec.scripts vence; spec.submodule_script_roots vem depois;
    spec.consumer_scripts_root entra por ultimo e so preenche lacunas.
    """
    if script_roots is not None:
        return list(dict.fromkeys(script_roots))
    roots: list[Path] = [spec.scripts, *sorted(spec.submodule_script_roots, key=str)]
    consumer = spec.consumer_scripts_root
    if consumer is not None:
        roots.append(consumer)
    return roots


def _discover_verb_dir(
    registry: Registry, verb_dir: Path, *, skip_existing: bool = False
) -> None:
    """Discover commands inside one verb directory.

    FLEXT-STRICT (p/ outro agente): skip_existing=True faz o root consumidor so
    preencher lacunas (first-wins) sem ignore hint e sem mascarar erro: header
    invalido (load_command) continua levantando RegistryError; so colisoes de
    (verb, WHAT) ja registradas por root de maior prioridade sao ignoradas.

    Raises:
        RegistryError: When the verb directory holds a nested directory, a
            public file without a ``.sh``/``.py`` suffix, or an invalid or
            duplicated command header.

    """
    headers = _command_headers(verb_dir)
    # Why: so um diretorio em que NENHUM arquivo declara header e "nao e um
    # diretorio de comandos". Um header presente e invalido continua sendo
    # defeito e sobe pelo laco abaixo.
    if all(isinstance(header, MissingHeaderError) for header in headers.values()):
        return
    for path in sorted(verb_dir.iterdir()):
        if path.name == "__pycache__" or path.name in PACKAGE_MARKERS:
            continue
        if path.is_dir():
            msg = f"{path}: diretorio aninhado nao e comando publico"
            raise RegistryError(msg)
        if path.suffix not in COMMAND_SUFFIXES:
            msg = f"{path}: arquivo publico deve ser .sh ou .py"
            raise RegistryError(msg)
        header = headers[path]
        if isinstance(header, RegistryError):
            raise header
        command = load_command(path, verb_dir.name, header)
        if skip_existing and registry.has(command.verb, command.what):
            continue
        registry.add(command)


def _command_headers(
    verb_dir: Path,
) -> MutableMapping[Path, t.JsonMapping | RegistryError]:
    headers: MutableMapping[Path, t.JsonMapping | RegistryError] = {}
    for path in verb_dir.iterdir():
        if not path.is_file() or path.suffix not in COMMAND_SUFFIXES:
            continue
        if path.name in PACKAGE_MARKERS:
            continue
        try:
            headers[path] = header_data(path)
        except RegistryError as exc:
            headers[path] = exc
    return headers


def load_command(
    path: Path, expected_verb: str, data: t.JsonMapping
) -> p.Infra.Promoted.Command:
    """Load and validate one command definition from its header.

    Returns:
        The ``Command`` model built from the validated header fields.

    Raises:
        RegistryError: When the header is missing or invalid, or its
            ``verb``/``what`` diverge from the directory and file name.

    """
    from flext_infra import m

    verb = require_string(data, "verb", path)
    what = require_string(data, "what", path)
    if verb != expected_verb:
        msg = f"{path}: header verb={verb} differs from directory {expected_verb}"
        raise RegistryError(msg)
    if what != path.stem:
        msg = f"{path}: header what={what} differs from file {path.stem}"
        raise RegistryError(msg)
    # NOTE (multi-agent, cosmos-main-qpsq): validate and construct the canonical
    # Param models once at this TOML ingress; no protocol/model adapter helper.
    params_raw = data.get("params")
    params = []
    if params_raw is not None:
        if not isinstance(params_raw, list):
            msg = f"{path}: params must be a list of TOML objects"
            raise RegistryError(msg)
        for item in params_raw:
            if not isinstance(item, dict):
                msg = f"{path}: params must contain TOML objects"
                raise RegistryError(msg)
            required_raw = item.get("required", False)
            default_raw = item.get("default", "")
            if not isinstance(required_raw, bool):
                msg = f"{path}: params.required must be a boolean"
                raise RegistryError(msg)
            if not isinstance(default_raw, str):
                msg = f"{path}: params.default must be a string"
                raise RegistryError(msg)
            params.append(
                m.Infra.Promoted.Param(
                    name=require_string(item, "name", path),
                    help=require_string(item, "help", path),
                    required=required_raw,
                    default=default_raw,
                    choices=parse_string_list(
                        item.get("choices"), "params.choices", path
                    ),
                )
            )
    return m.Infra.Promoted.Command(
        verb=verb,
        what=what,
        domain=require_string(data, "domain", path),
        summary=require_string(data, "summary", path),
        description=require_string(data, "description", path),
        example=require_string(data, "example", path),
        path=path,
        mutates=require_bool(data, "mutates", path),
        aliases=parse_aliases(data.get("aliases"), path),
        params=tuple(params),
        rules=parse_string_list(data.get("rules"), "rules", path),
    )
