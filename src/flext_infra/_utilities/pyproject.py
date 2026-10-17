"""Pyproject.toml parsing helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache, lru_cache
from pathlib import Path

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesManagedConflicts,
)
from flext_infra._utilities.mise_binary import FlextInfraUtilitiesMiseBinary


class FlextInfraUtilitiesPyproject:
    """Static helpers for reading and normalizing ``pyproject.toml`` payloads."""

    @classmethod
    def declared_dependency_payload(
        cls,
        pyproject_path: Path,
    ) -> p.Result[t.JsonMapping]:
        """Read owner-recovered TOML without admitting generated group inputs.

        Returns:
            The parsed mapping with authored dependency-group entries only.

        """
        text = cls.live_pyproject_text(pyproject_path)
        if text.failure:
            return r[t.JsonMapping].from_failure(text)
        payload = u.Cli.toml_mapping_from_text(text.value)
        if payload is None:
            return r[t.JsonMapping].fail(
                f"pyproject is not valid TOML: {pyproject_path}",
            )
        groups = u.Cli.toml_mapping_path(payload, (c.Infra.DEPENDENCY_GROUPS,))
        if groups is not None:
            for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
                selected = cls.dependency_group_name(tuple(groups), str(group))
                if selected not in groups:
                    continue
                custom = cls.custom_dev_additions(payload, text.value, group=selected)
                if custom.failure:
                    return r[t.JsonMapping].from_failure(custom)
                groups[selected] = cls.dependency_group_wire(custom.value)
        return r[t.JsonMapping].ok(payload)

    @staticmethod
    def dependency_group_name(names: t.IterableOf[str], name: str) -> str:
        """Elect an existing native spelling using PEP 735 normalized identity.

        Returns:
            The declared spelling when one matches, else the requested name.

        Raises:
            ValueError: If dependency group names have colliding normalized
                identities.

        """
        matches = tuple(
            key for key in names if canonicalize_name(key) == canonicalize_name(name)
        )
        if len(matches) > 1:
            msg = "dependency group names have colliding normalized identities"
            raise ValueError(msg)
        return matches[0] if matches else name

    @staticmethod
    def dependency_group_wire(
        entries: t.SequenceOf[str | m.Infra.DependencyGroupInclude],
    ) -> list[t.JsonValue]:
        """Serialize native entries without turning inclusion tables into strings.

        Returns:
            The resulting ``list[t.JsonValue]``.

        """
        return [
            entry
            if isinstance(entry, str)
            else dict(
                t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    entry.model_dump(mode="json", by_alias=True),
                ),
            )
            for entry in entries
        ]

    @staticmethod
    def custom_dev_additions(
        live_payload: t.JsonMapping,
        live: str | None,
        *,
        group: str = str(c.Infra.DEV),
    ) -> p.Result[t.VariadicTuple[str | m.Infra.DependencyGroupInclude]]:
        """Remove only entries carrying this generator's explicit provenance.

        Returns:
            Native ordered CUSTOM entries, or their original parse failure.

        """
        groups = u.Cli.toml_mapping_child(live_payload, c.Infra.DEPENDENCY_GROUPS) or {}
        group = FlextInfraUtilitiesPyproject.dependency_group_name(tuple(groups), group)
        result_type = r[t.VariadicTuple[str | m.Infra.DependencyGroupInclude]]
        values = u.validate_value(
            m.Infra.DependencyGroupEntries,
            groups.get(group, ()),
        )
        if values.failure:
            return result_type.from_failure(values)
        entries = values.value.root
        if not entries or live is None:
            return (
                result_type.ok(())
                if not entries
                else result_type.fail("dev provenance requires its parsed source")
            )
        comments = FlextInfraUtilitiesPyproject._dependency_group_comments(live, group)
        if comments.failure:
            return result_type.from_failure(comments)
        if len(comments.value) != len(entries):
            return result_type.fail("dev provenance occurrence counts differ")
        return result_type.ok(
            tuple(
                value
                for value, comment in zip(entries, comments.value, strict=True)
                if not isinstance(value, str)
                or comment.removeprefix("#").strip() != c.Infra.MEMBER_DEV_PROVENANCE
            ),
        )

    @staticmethod
    def _dependency_group_comments(
        live: str,
        group: str,
    ) -> p.Result[t.StrSequence]:
        """Read native per-occurrence comments from the parsed dependency group.

        Returns:
            Ordered array comments or the original missing-source failure.

        """
        result_type = r[t.StrSequence]
        document = u.Cli.toml_parse_text(live)
        if document is None:
            return result_type.fail("dev provenance source is invalid TOML")
        group_table = u.Cli.toml_table_child(document, c.Infra.DEPENDENCY_GROUPS)
        if group_table is None:
            return result_type.fail("dev provenance dependency groups are missing")
        if group not in group_table:
            return result_type.fail("dev provenance group array is missing")
        return result_type.ok(u.Cli.toml_array_item_comments(group_table, group))

    @staticmethod
    def recover_live_pyproject_text(raw: str) -> p.Result[str]:
        """Return live pyproject text with merge-control lines resolved.

        Unconflicted text is returned unchanged. A conflict is resolved only
        inside owner-declared managed TOML sections
        (``config.Infra.codegen.managed_file_specs``) via
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
            content.decode(c.DEFAULT_ENCODING),
        )
        if live.failure or not regenerate_managed_tools:
            return live
        return FlextInfraUtilitiesManagedConflicts.pyproject_regeneration_source(
            live.value,
        )

    @staticmethod
    def read_project_metadata_result(
        project_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[p.ProjectMetadata]:
        """Read retained metadata from the canonical single-document ingress.

        Returns:
            The original structural metadata or its causal ingress failure.

        """
        state = FlextInfraUtilitiesPyproject.read_project_metadata_state(
            project_root,
            source_project=source_project,
        )
        if state.failure:
            return r[p.ProjectMetadata].from_failure(state)
        return r[p.ProjectMetadata].ok(state.value.metadata)

    @staticmethod
    def read_project_metadata_state(
        project_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.ProjectMetadataState]:
        """Parse metadata and packaging declarations without importing source exports.

        Returns:
            Retained typed metadata and packaging facts from one live TOML read.

        """
        result_type = r[m.Infra.ProjectMetadataState]
        live = (
            FlextInfraUtilitiesPyproject.live_pyproject_text(
                project_root / c.PYPROJECT_FILENAME
            )
            if source_project is None
            else FlextInfraUtilitiesPyproject.recover_live_pyproject_text(
                source_project.source_text(project_root / c.PYPROJECT_FILENAME),
            )
        )
        if live.failure:
            return result_type.from_failure(live)
        # The facade returns None for unparseable text rather than raising, so
        # the invalid case is named here instead of reaching model_validate as
        # a None that fails with a shape error about the wrong subject.
        payload = u.Cli.toml_mapping_from_text(live.value)
        if payload is None:
            return result_type.fail(
                f"cannot read project metadata from {project_root}: "
                f"{c.PYPROJECT_FILENAME} is not valid TOML",
            )
        try:
            document = u.PyprojectDocument.model_validate(payload)
            packaging = m.Infra.ProjectPackagingDeclaration.model_validate(payload)
            metadata = u.build_project_metadata(project_root, document)
        except (OSError, ValueError) as exc:
            return result_type.fail(
                f"cannot read project metadata from {project_root}: {exc}",
                exception=exc,
            )
        return result_type.ok(
            m.Infra.ProjectMetadataState(metadata=metadata, packaging=packaging),
        )

    @staticmethod
    def project_package_participation(
        declaration: m.Infra.ProjectPackagingDeclaration,
    ) -> bool:
        """Apply native project defaults without consulting directories or exports.

        Args:
            declaration: Packaging declaration read from the project payload.

        Returns:
            Whether the project participates in packaging under native defaults.

        """
        return (
            declaration.build_backend is not None
            if declaration.uv_package is None
            else declaration.uv_package
        )

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
                input_data=source.encode(c.DEFAULT_ENCODING),
            ),
            timeout=process_timeout_seconds,
        )
        if result.failure:
            return r[str].from_failure(result)
        output = result.value
        if not u.Cli.process_succeeded(output.outcome):
            detail = (
                (output.stderr or output.stdout)
                .decode(c.DEFAULT_ENCODING, errors="backslashreplace")
                .strip()
            )
            return r[str].fail(
                f"taplo format failed ({output.outcome.raw_return_code}): {detail}",
            )
        try:
            formatted = output.stdout.decode(c.DEFAULT_ENCODING)
        except UnicodeDecodeError as exc:
            return r[str].fail(
                f"taplo format returned non-UTF-8 output: {exc}",
                exception=exc,
            )
        return r[str].ok(formatted)

    @staticmethod
    def _taplo_binary(execution_root: Path) -> p.Result[Path]:
        """Resolve Make's declared Taplo executable through Mise.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        return FlextInfraUtilitiesMiseBinary.managed_mise_binary(
            c.Infra.TAPLO_MISE_TOOL_NAME,
            execution_root,
        )

    @staticmethod
    def pyproject_payload(
        pyproject_path: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.JsonMapping:
        """Return the shared TOML ingress's validated ``pyproject.toml`` mapping.

        The payload is parsed from the live text with managed merge
        conflicts resolved (``live_pyproject_text``).

        Returns:
            One mapping validated by the shared TOML ingress.

        Raises:
            RuntimeError: If failed to read pyproject payload at; or if pyproject
                payload at.

        """
        if not (
            pyproject_path.is_file()
            if source_project is None
            else source_project.source_query(pyproject_path, "isfile")
        ):
            return {}
        live = (
            FlextInfraUtilitiesPyproject.live_pyproject_text(pyproject_path)
            if source_project is None
            else FlextInfraUtilitiesPyproject.recover_live_pyproject_text(
                source_project.source_text(pyproject_path)
            )
        )
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
            The validated mapping of ``text``.

        Raises:
            RuntimeError: If ``text`` is not valid TOML.

        """
        payload = u.Cli.toml_mapping_from_text(text)
        if payload is None:
            msg = f"pyproject payload at {pyproject_path} is not valid TOML"
            raise RuntimeError(msg)
        return payload

    @staticmethod
    def normalized_toml_payload(document: t.Cli.TomlDocument) -> t.JsonMapping:
        """Return the shared TOML ingress's validated document mapping.

        Returns:
            One mapping validated by the shared TOML ingress.

        """
        payload = u.Cli.toml_as_mapping(document)
        if not payload:
            return {}
        return payload

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
        *,
        source_paths: t.SequenceOf[Path] | None = None,
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
        source_package = (
            next(
                (
                    path.parent.name
                    for path in sorted(source_paths)
                    if path.name == c.Infra.INIT_PY
                    and path.parent.parent == project_root / c.Infra.DEFAULT_SRC_DIR
                ),
                None,
            )
            if source_paths is not None
            else FlextInfraUtilitiesPyproject._src_dir_package(project_root)
        )
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
    def project_package_name(
        project_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> str:
        """Return the primary Python package name for a project root.

        Returns:
            The primary Python package name for a project root.

        """
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(
            project_root / c.PYPROJECT_FILENAME,
            source_project=source_project,
        )
        docs_meta = FlextInfraUtilitiesPyproject.docs_meta_from_payload(payload)
        source_paths: tuple[Path, ...] | None = None
        if source_project is not None:
            src = project_root / c.Infra.DEFAULT_SRC_DIR
            source_paths = (
                tuple(
                    child / c.Infra.INIT_PY
                    for child in source_project.source_children(src)
                    if source_project.source_query(child, "isdir")
                    and source_project.source_query(child / c.Infra.INIT_PY, "isfile")
                )
                if source_project.source_query(src, "isdir")
                else ()
            )
        return FlextInfraUtilitiesPyproject.package_name_from_payload(
            project_root,
            payload,
            docs_meta,
            source_paths=source_paths,
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
