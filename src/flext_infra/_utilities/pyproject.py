"""Pyproject.toml parsing helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from functools import cache, lru_cache
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesManagedConflicts,
)


class FlextInfraUtilitiesPyproject:
    """Static helpers for reading and normalizing ``pyproject.toml`` payloads."""

    @staticmethod
    def managed_mise_binary(name: str, owner_root: Path) -> p.Result[Path]:
        """Resolve one declared tool's executable through Mise in ``owner_root``.

        Mise resolves the release the committed mise.lock pins wherever it pins
        one and the declared selector otherwise, so a stale or incomplete lock
        never stops a verb (operator-ruling-2026-10-09-setup-resilient);
        ``make audit`` (codegen mise-proof) proves the pins.

        Returns:
            The absolute executable inside the tool's install root, never a
            PATH shim.
        """
        tool = next(
            (
                item
                for item in config.Infra.codegen.toolchain.tools
                if item.name == name
            ),
            None,
        )
        if tool is None:
            return r[Path].fail(f"tool is not declared by the toolchain owner: {name}")
        reader = shutil.which(c.Infra.MISE)
        if reader is None:
            return r[Path].fail("Mise executable is absent; run make setup")
        return FlextInfraUtilitiesPyproject._managed_mise_path(
            tool.version_probe.binary,
            owner_root,
            Path(reader),
        )

    @staticmethod
    def managed_mise_self(owner_root: Path) -> p.Result[Path]:
        """Qualify the physical Mise reader before it loads project locks.

        The reader is the release the committed tree pins: the self-managed
        entry its ``.mise.toml`` declares, authenticated by the ``mise.lock``
        beside it. The generator's own target release never qualifies the
        reader: ``make upg`` runs this generator while the tree still declares
        the previous release, or none before self-management, and only the
        upgrade renders and locks the new one (C19). A committed manifest that
        declares no self-managed entry reads its locks with the host Mise.

        Returns:
            The installed self-managed executable, never a tool shim.
        """
        selected = shutil.which(c.Infra.MISE)
        if selected is None:
            return r[Path].fail("Mise executable is absent; run make setup")
        reader = Path(selected)
        return FlextInfraUtilitiesPyproject._committed_mise_self_release(
            owner_root,
        ).flat_map(
            lambda declared: FlextInfraUtilitiesPyproject._qualified_mise_reader(
                reader,
                owner_root,
                declared,
            ),
        )

    @staticmethod
    def _qualified_mise_reader(
        reader: Path,
        owner_root: Path,
        declared: str | None,
    ) -> p.Result[Path]:
        """Authenticate the reader and its installed release against the lock pin.

        Returns:
            The installed self-managed executable, or the physical reader when
            the committed manifest declares no self-managed release.
        """
        if declared is None:
            return r[Path].ok(reader.resolve(strict=True))
        return FlextInfraUtilitiesPyproject._locked_mise_version(
            owner_root,
            config.Infra.codegen.toolchain.mise_selector,
            declared,
        ).flat_map(
            lambda pinned: (
                FlextInfraUtilitiesPyproject
                ._mise_self_identity(reader, pinned, owner_root)
                .flat_map(
                    lambda qualified: FlextInfraUtilitiesPyproject._managed_mise_path(
                        c.Infra.MISE,
                        owner_root,
                        qualified,
                    ),
                )
                .flat_map(
                    lambda installed: FlextInfraUtilitiesPyproject._mise_self_identity(
                        installed,
                        pinned,
                        owner_root,
                    ),
                )
            ),
        )

    @staticmethod
    def _committed_mise_self_release(owner_root: Path) -> p.Result[str | None]:
        """Return the self-managed Mise release the committed manifest declares.

        The manifest is the ``.mise.toml`` beside the nearest ``mise.lock``.
        A tree without that lock and manifest pair, or whose manifest declares
        no self-managed entry, pins no reader release (typed absence).

        Returns:
            The declared release, or None when the tree declares none.
        """
        lock_path = FlextInfraUtilitiesPyproject._mise_lock_path(owner_root)
        manifest = (
            None if lock_path is None else lock_path.parent / c.Infra.MISE_TOML_FILENAME
        )
        if manifest is None or not manifest.is_file():
            return r[str | None].ok(None)
        payload = u.Cli.toml_mapping_from_text(
            manifest.read_text(encoding=c.Cli.ENCODING_DEFAULT),
        )
        if payload is None:
            return r[str | None].fail(f"{manifest} is not valid TOML")
        tools = payload.get("tools", {})
        if not isinstance(tools, Mapping):
            return r[str | None].fail(f"{manifest} has a malformed [tools] table")
        release = tools.get(config.Infra.codegen.toolchain.mise_selector)
        if release is None:
            return r[str | None].ok(None)
        if not isinstance(release, str) or not release:
            return r[str | None].fail(
                f"{manifest} declares a malformed self-managed Mise entry: {release!r}",
            )
        return r[str | None].ok(release)

    @staticmethod
    def _mise_self_identity(
        binary: Path, pinned: str, owner_root: Path
    ) -> p.Result[Path]:
        """Check the physical reader without invoking a lock-consuming command.

        Returns:
            The physical executable matching the committed self pin.
        """
        binary = binary.resolve(strict=True)
        identity = u.Cli.run_raw(
            (str(binary), "--version"),
            cwd=owner_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(env=c.Infra.MISE_IDENTITY_PROBE_ENVIRONMENT),
        )
        if identity.failure:
            return r[Path].from_failure(identity)
        output = identity.value
        if not u.Cli.process_succeeded(output.outcome) or output.stderr.strip():
            return r[Path].fail(output.stderr or output.stdout)
        if output.stdout.split()[:1] != [pinned]:
            return r[Path].fail(
                f"Mise reader {binary} differs from lock: expected={pinned} "
                f"observed={output.stdout.strip()}; run make setup"
            )
        return r[Path].ok(binary)

    @staticmethod
    def _managed_mise_path(name: str, owner_root: Path, reader: Path) -> p.Result[Path]:
        located = u.Cli.run_raw(
            (str(reader), "-C", str(owner_root), "which", name),
            cwd=owner_root,
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if located.failure:
            return r[Path].from_failure(located)
        if (
            not u.Cli.process_succeeded(located.value.outcome)
            or located.value.stderr.strip()
        ):
            return r[Path].fail(located.value.stderr or located.value.stdout)
        binary = Path(located.value.stdout.strip())
        if not binary.is_absolute() or not binary.is_file():
            return r[Path].fail(f"managed executable is not an absolute file: {binary}")
        return r[Path].ok(binary.resolve(strict=True))

    @staticmethod
    def recover_live_pyproject_text(raw: str) -> p.Result[str]:
        """Return live pyproject text with merge-control lines resolved.

        Unconflicted text is returned unchanged. A conflict is resolved only
        inside owner-declared managed TOML sections
        (``config.Infra.codegen.managed_files``) via
        ``FlextInfraUtilitiesManagedConflicts.recover_managed_toml``; a
        conflict outside those sections fails loud through that utility's
        own contract. Read-only: no file is written here.

        Returns:
            Live pyproject text with merge-control lines resolved.

        """
        spec_result = FlextInfraUtilitiesManagedConflicts.pyproject_managed_file()
        if spec_result.failure:
            return r[str].from_failure(spec_result)
        return FlextInfraUtilitiesManagedConflicts.recover_managed_toml(
            raw,
            conflict_sections=spec_result.value.conflict_sections,
        )

    @staticmethod
    def live_pyproject_text(
        pyproject_path: Path,
        *,
        regenerate_managed_tools: bool = False,
    ) -> p.Result[str]:
        """Read one live pyproject and resolve managed merge conflicts.

        Returns:
            The resulting ``p.Result[str]``.

        """
        raw = u.Cli.atomic_read_binary_file_state(pyproject_path, required=True)
        if raw.failure:
            return r[str].from_failure(raw)
        content = raw.value.content
        if content is None:
            return r[str].fail(f"pyproject is absent: {pyproject_path}")
        live = FlextInfraUtilitiesPyproject.recover_live_pyproject_text(
            content.decode(c.Cli.ENCODING_DEFAULT),
        )
        if live.failure or not regenerate_managed_tools:
            return live
        return FlextInfraUtilitiesManagedConflicts.pyproject_regeneration_source(
            live.value,
        )

    @staticmethod
    def read_project_metadata_result(project_root: Path) -> p.Result[p.ProjectMetadata]:
        """Read one project's metadata through the canonical owner chain.

        flext-core retired its Result-returning compatibility wrapper; this is
        the consuming project's typed ingress, keeping every metadata reader on
        one failure contract instead of three ad-hoc try/except blocks. The
        declared contract is the canonical structural protocol (the producer
        builds the exact model behind it), matching every ``p.ProjectMetadata``
        consumer.

        The document is the live text with managed merge conflicts resolved
        (``live_pyproject_text``); the file is never written here.

        Returns:
            The resulting ``p.Result[p.ProjectMetadata]``.

        """
        live = FlextInfraUtilitiesPyproject.live_pyproject_text(
            project_root / c.PYPROJECT_FILENAME,
        )
        if live.failure:
            return r[p.ProjectMetadata].from_failure(live)
        # The facade returns None for unparseable text rather than raising, so
        # the invalid case is named here instead of reaching model_validate as
        # a None that fails with a shape error about the wrong subject.
        payload = u.Cli.toml_mapping_from_text(live.value)
        if payload is None:
            return r[p.ProjectMetadata].fail(
                f"cannot read project metadata from {project_root}: "
                f"{c.PYPROJECT_FILENAME} is not valid TOML",
            )
        try:
            document = u.PyprojectDocument.model_validate(payload)
            metadata = u.build_project_metadata(project_root, document)
        except (OSError, ValueError) as exc:
            return r[p.ProjectMetadata].fail(
                f"cannot read project metadata from {project_root}: {exc}",
                exception=exc,
            )
        return r[p.ProjectMetadata].ok(metadata)

    @staticmethod
    def validate_infra_payload(payload: p.AttributeProbe) -> t.JsonMapping:
        """Validate one plain mapping through the infra adapter.

        Centralizes the adapter choice so every caller validates through the
        same typed boundary; validation failures escape with the precise
        pydantic error instead of a sentinel.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        result: t.JsonMapping = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
        return result

    @classmethod
    def format_toml_source(
        cls,
        source: str,
        *,
        path: Path,
        toolchain_root: Path,
        taplo_version: str,
        process_timeout_seconds: int = c.Infra.TIMEOUT_DEFAULT,
    ) -> p.Result[str]:
        """Format TOML through the configured workspace Taplo toolchain.

        ``taplo_version`` is the declared selector and keys the format cache;
        Mise resolves the executable, through the committed mise.lock wherever
        it pins Taplo (``managed_mise_binary``).

        Returns:
            The resulting ``p.Result[str]``.

        """
        config_path = toolchain_root / c.Infra.TAPLO_CONFIG_FILENAME
        config_content = config_path.read_bytes() if config_path.is_file() else b""
        resolved_path = path.resolve()
        resolved_toolchain_root = toolchain_root.resolve()
        execution_root = next(
            candidate
            for candidate in (resolved_toolchain_root, *resolved_toolchain_root.parents)
            if candidate.is_dir()
        )
        relative_path = (
            resolved_path.relative_to(resolved_toolchain_root).as_posix()
            if resolved_path.is_relative_to(resolved_toolchain_root)
            else resolved_path.relative_to(resolved_path.parent).as_posix()
        )
        return cls._format_toml_source_cached(
            source,
            relative_path=relative_path,
            config=(
                config_path.resolve() if config_content else None,
                u.Cli.sha256_bytes(config_content),
            ),
            taplo=(taplo_version, process_timeout_seconds, execution_root),
        )

    @staticmethod
    @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
    def _format_toml_source_cached(
        source: str,
        *,
        relative_path: str,
        config: t.Pair[Path | None, str],
        taplo: t.Triple[str, int, Path],
    ) -> p.Result[str]:

        taplo_result = FlextInfraUtilitiesPyproject._taplo_binary(taplo[2])
        if taplo_result.failure:
            return r[str].from_failure(taplo_result)
        config_path, _config_digest = config
        _taplo_version, process_timeout_seconds, execution_root = taplo
        command = [
            str(taplo_result.value),
            "format",
            "-",
            "--stdin-filepath",
            relative_path,
        ]
        if config_path is not None:
            command.extend(("--config", str(config_path)))
        # Generated content must not pass through normalized text model fields.
        result = u.Cli.run_bytes(
            command,
            cwd=execution_root,
            options=m.Cli.ProcessOptions(
                input_data=source.encode(c.Cli.ENCODING_DEFAULT),
            ),
            timeout=process_timeout_seconds,
        )
        if result.failure:
            return r[str].from_failure(result)
        output = result.value
        if not u.Cli.process_succeeded(output.outcome):
            detail = (
                (output.stderr or output.stdout)
                .decode(c.Cli.ENCODING_DEFAULT, errors="backslashreplace")
                .strip()
            )
            return r[str].fail(
                f"taplo format failed ({output.outcome.raw_return_code}): {detail}",
            )
        try:
            formatted = output.stdout.decode(c.Cli.ENCODING_DEFAULT)
        except UnicodeDecodeError as exc:
            return r[str].fail(
                f"taplo format returned non-UTF-8 output: {exc}",
                exception=exc,
            )
        return r[str].ok(formatted)

    @classmethod
    def _locked_mise_version(
        cls,
        execution_root: Path,
        tool: str,
        selector: str,
    ) -> p.Result[str]:
        """Resolve the selector's pinned version from the committed mise.lock.

        Only ``make upg`` resolves a moving selector and writes mise.lock;
        every other execution must authenticate exactly what the lock pins,
        because a version taken from the selector itself sends the shim's
        resolution over the network on a cold cache.

        Returns:
            The resulting ``p.Result[str]``.

        """
        lock_path = cls._mise_lock_path(execution_root)
        if lock_path is None:
            return r[str].fail(
                f"no {c.Infra.MISE_LOCK_FILENAME} above {execution_root} pins "
                f"{tool}; run make upg so generation stays offline",
            )
        return cls._pinned_mise_lock_version(lock_path, tool=tool, selector=selector)

    @staticmethod
    def _mise_lock_path(execution_root: Path) -> Path | None:
        """Return the nearest committed mise.lock above the execution root.

        Returns:
            The resulting ``Path | None``.

        """
        return next(
            (
                candidate / c.Infra.MISE_LOCK_FILENAME
                for candidate in (execution_root, *execution_root.parents)
                if (candidate / c.Infra.MISE_LOCK_FILENAME).is_file()
            ),
            None,
        )

    @classmethod
    def _pinned_mise_lock_version(
        cls,
        lock_path: Path,
        *,
        tool: str,
        selector: str,
    ) -> p.Result[str]:
        """Authenticate the committed mise.lock version one selector pins.

        Returns:
            The resulting ``p.Result[str]``.

        """
        entries_result = cls._mise_lock_tool_entries(lock_path, tool=tool)
        if entries_result.failure:
            return r[str].from_failure(entries_result)
        for entry in entries_result.value:
            locked = cls._locked_entry_version(entry)
            if locked is None:
                return r[str].fail(
                    f"{lock_path} has a malformed [[tools.{tool}]] entry: {entry!r}",
                )
            pinned, specifiers = locked
            if selector in specifiers or selector == pinned:
                return r[str].ok(pinned)
        return r[str].fail(
            f"{lock_path} pins no {tool} for selector {selector!r}; run make upg",
        )

    @staticmethod
    def _mise_lock_tool_entries(
        lock_path: Path,
        *,
        tool: str,
    ) -> p.Result[t.SequenceOf[t.JsonValue]]:
        """Read one tool's lock entries from the committed mise.lock.

        Returns:
            The resulting ``p.Result[t.SequenceOf[t.JsonValue]]``.

        """
        payload = u.Cli.toml_mapping_from_text(
            lock_path.read_text(encoding=c.Cli.ENCODING_DEFAULT),
        )
        if payload is None:
            return r[t.SequenceOf[t.JsonValue]].fail(f"{lock_path} is not valid TOML")
        tools = payload.get("tools", {})
        if not isinstance(tools, Mapping):
            return r[t.SequenceOf[t.JsonValue]].fail(
                f"{lock_path} has a malformed [tools] table",
            )
        entries = tools.get(tool)
        if not isinstance(entries, list):
            return r[t.SequenceOf[t.JsonValue]].fail(
                f"{lock_path} pins no [[tools.{tool}]] entry",
            )
        return r[t.SequenceOf[t.JsonValue]].ok(entries)

    @staticmethod
    def _locked_entry_version(
        entry: t.JsonValue,
    ) -> t.Pair[str, t.SequenceOf[t.JsonValue]] | None:
        """Return one lock entry's pinned version and specifiers when wellformed.

        Returns:
            The resulting ``t.Pair | None``.

        """
        if not isinstance(entry, Mapping):
            return None
        pinned = entry.get("version")
        specifiers = entry.get("specifiers", ())
        if not isinstance(pinned, str) or not isinstance(specifiers, (list, tuple)):
            return None
        return pinned, specifiers

    @staticmethod
    def _taplo_binary(execution_root: Path) -> p.Result[Path]:
        """Resolve Make's declared Taplo executable through Mise.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        return FlextInfraUtilitiesPyproject.managed_mise_binary(
            c.Infra.TAPLO_MISE_TOOL_NAME,
            execution_root,
        )

    @staticmethod
    def pyproject_payload(pyproject_path: Path) -> t.JsonMapping:
        """Return one parsed ``pyproject.toml`` payload validated against ``t.Infra``.

        The payload is parsed from the live text with managed merge
        conflicts resolved (``live_pyproject_text``).

        Returns:
            One parsed ``pyproject.toml`` payload validated against ``t.Infra``.

        Raises:
            RuntimeError: If failed to read pyproject payload at; or if pyproject
                payload at.

        """
        if not pyproject_path.is_file():
            return {}
        live = FlextInfraUtilitiesPyproject.live_pyproject_text(pyproject_path)
        if live.failure:
            msg = f"failed to read pyproject payload at {pyproject_path}: {live.error}"
            raise RuntimeError(msg)
        # The parse is memoized by the live text, never by the path alone: a
        # process that rewrites a manifest (gen, mod, a test) reads its new
        # content on the next call instead of a stale parse.
        return FlextInfraUtilitiesPyproject._parsed_pyproject_payload(
            pyproject_path,
            live.value,
        )

    @staticmethod
    @cache
    def _parsed_pyproject_payload(pyproject_path: Path, text: str) -> t.JsonMapping:
        """Parse and validate one manifest text (memoized per exact content).

        Returns:
            The validated ``t.Infra`` payload of ``text``.

        Raises:
            RuntimeError: If ``text`` is not valid TOML.

        """
        payload = u.Cli.toml_mapping_from_text(text)
        if payload is None:
            msg = f"pyproject payload at {pyproject_path} is not valid TOML"
            raise RuntimeError(msg)
        return FlextInfraUtilitiesPyproject.validate_infra_payload(payload)

    @staticmethod
    def normalized_toml_payload(document: t.Cli.TomlDocument) -> t.JsonMapping:
        """Return one TOML document normalized through the infra adapter.

        Returns:
            One TOML document normalized through the infra adapter.

        """
        payload = u.Cli.toml_as_mapping(document)
        if not payload:
            return {}
        return FlextInfraUtilitiesPyproject.validate_infra_payload(payload)

    @staticmethod
    def tool_flext_meta(project_root: Path) -> t.JsonMapping:
        """Return the normalized ``tool.flext`` table from a project root.

        Returns:
            The normalized ``tool.flext`` table from a project root.

        """
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(
            project_root / c.PYPROJECT_FILENAME,
        )
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        return flext if isinstance(flext, dict) else {}

    @staticmethod
    def docs_meta_from_payload(payload: t.JsonMapping) -> t.JsonMapping:
        """Extract ``tool.flext.docs`` metadata from an already-parsed payload.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        if not isinstance(flext, dict):
            return {}
        docs = flext.get("docs")
        return docs if isinstance(docs, dict) else {}

    @staticmethod
    def project_name_from_payload(entry: Path, payload: t.JsonMapping) -> str:
        """Return the declared project name from ``[project].name``.

        Returns:
            The declared project name from ``[project].name``.

        Raises:
            TypeError: If ``not isinstance(project_section, dict)``.
            ValueError: If ``not isinstance(raw_name, str) or not raw_name.strip()``.

        """
        project_section = payload.get("project")
        if not isinstance(project_section, dict):
            msg = f"{entry}: missing [project] table in pyproject.toml"
            raise TypeError(msg)
        raw_name = project_section.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            msg = f"{entry}: missing or empty [project].name in pyproject.toml"
            raise ValueError(msg)
        return raw_name.strip()

    @staticmethod
    def _hatch_wheel_package(payload: t.JsonMapping) -> str | None:
        """Return the package name the hatch wheel targets declare.

        Returns:
            The resulting ``str | None``.

        """
        current: t.JsonMapping | None = payload
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            if current is None:
                break
            candidate = current.get(key)
            current = candidate if isinstance(candidate, dict) else None
        packages = current.get("packages") if current is not None else None
        if not isinstance(packages, list):
            return None
        for item in packages:
            package_path = Path(str(item).strip())
            if package_path.parts:
                return package_path.parts[-1]
        return None

    @staticmethod
    def _src_dir_package(project_root: Path) -> str | None:
        """Return the first ``src`` child package carrying an initializer.

        Returns:
            The resulting ``str | None``.

        """
        src_dir = project_root / c.Infra.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.INIT_PY).is_file():
                return child.name
        return None

    @staticmethod
    def package_name_from_payload(
        project_root: Path,
        payload: t.JsonMapping,
        docs_meta: t.JsonMapping,
    ) -> str:
        """Return the primary package name using pre-loaded pyproject payload.

        Returns:
            The primary package name using pre-loaded pyproject payload.

        Raises:
            ValueError: If ``project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN)``.

        """
        configured = docs_meta.get("package_name")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        wheel_package = FlextInfraUtilitiesPyproject._hatch_wheel_package(payload)
        if wheel_package is not None:
            return wheel_package
        source_package = FlextInfraUtilitiesPyproject._src_dir_package(project_root)
        if source_package is not None:
            return source_package
        project_name = FlextInfraUtilitiesPyproject.project_name_from_payload(
            project_root,
            payload,
        )
        if project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN):
            msg = (
                f"{project_root}: cannot resolve package name — "
                "no [tool.flext.docs].package_name, no hatch wheel packages, "
                "and no src/<pkg>/__init__.py present"
            )
            raise ValueError(msg)
        return ""

    @staticmethod
    def project_package_name(project_root: Path) -> str:
        """Return the primary Python package name for a project root.

        Returns:
            The primary Python package name for a project root.

        """
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(
            project_root / c.PYPROJECT_FILENAME,
        )
        docs_meta = FlextInfraUtilitiesPyproject.docs_meta_from_payload(payload)
        return FlextInfraUtilitiesPyproject.package_name_from_payload(
            project_root,
            payload,
            docs_meta,
        )

    @staticmethod
    @cache
    def workspace_project_paths(repository_root: Path) -> t.StrSequence:
        """Return governed project paths declared by this directory's ``.gitmodules``.

        A missing file denotes a standalone project and therefore an empty
        sequence. A malformed declaration is an invalid workspace contract and
        remains a loud error; no pyproject table or parent directory is used as
        an alternate topology source. A submodule that opts out through
        ``flext-managed`` is not a workspace project, the same contract the
        workspace detector applies; every governed path stays in the sequence
        so a missing or unreadable member pyproject still fails at its reader.

        Returns:
            Governed project paths declared by this directory's ``.gitmodules``.

        Raises:
            ValueError: If ``declared.failure``.

        """
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(repository_root)
        if declared.failure:
            msg = declared.error or f"invalid workspace topology: {repository_root}"
            raise ValueError(msg)
        return tuple(
            item.path.as_posix() for item in declared.value if item.managed is not False
        )


__all__: list[str] = ["FlextInfraUtilitiesPyproject"]
