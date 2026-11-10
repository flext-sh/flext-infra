"""Validate and compose the declared native tool-option catalog.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import glob
import sysconfig
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import u
from typing_extensions import TypeForm

from flext_infra import p, r, t
from flext_infra._utilities import FlextInfraUtilitiesBase


class FlextInfraUtilitiesNativeTooling(FlextInfraUtilitiesBase):
    """Own native option values without file-discovery or projection behavior."""

    @staticmethod
    def native_tool_search_path_admission(
        document: p.Infra.ToolConfigDocument,
        repository_root: Path,
    ) -> p.Result[bool]:
        """Check rooted native search paths once, without copying the typed document.

        Returns:
            Admission of source paths and actual installed dependency typing.

        """
        pending: list[tuple[str, t.JsonValue]] = [
            (key, value) for pairs in document.settings.values() for key, value in pairs
        ]
        pending.extend(
            (key, value)
            for override in document.tools.mypy.overrides
            for key, value in override.settings
        )
        pyright = document.tools.pyright.path_rules
        pyrefly = document.tools.pyrefly.path_rules
        pending.extend(
            ("search-path", path)
            for path in (
                pyright.source_dir,
                pyright.project_root,
                *pyright.env_dirs,
                *pyright.test_like_dirs,
                *(entry.root for entry in pyright.diagnostic_path_exceptions),
                pyrefly.source_dir,
                pyrefly.project_root,
                *pyrefly.env_dirs,
                *pyrefly.workspace_include_child_env_dirs,
                *pyrefly.project_shared_search_paths,
            )
        )
        root = repository_root.resolve()
        installed_roots = tuple(
            Path(sysconfig.get_path(key)).resolve() for key in ("purelib", "platlib")
        )
        while pending:
            key, value = pending.pop()
            option = key.rsplit(".", 1)[-1].casefold().replace("-", "").replace("_", "")
            if isinstance(value, Mapping):
                pending.extend(value.items())
            elif isinstance(value, list):
                pending.extend((key, item) for item in value)
            elif isinstance(value, str) and (
                "path" in option
                or option in {"root", "sourcedir", "envdirs", "projectincludes"}
            ):
                for entry in value.replace("\\", "/").split(":"):
                    path = Path(entry).expanduser()
                    resolved = (path if path.is_absolute() else root / path).resolve()
                    if any(
                        resolved.is_relative_to(installed)
                        for installed in installed_roots
                    ):
                        continue
                    if any(
                        part in {"typings", "stubs"}
                        or part.endswith((".pyi", "-stubs"))
                        or "-stubs-" in part
                        for part in path.parts
                    ):
                        return r[bool].fail(
                            f"Local stub search roots are forbidden: {key}={value}"
                        )
        return r[bool].ok(value=True)

    @staticmethod
    def diagnostic_exception_levels(
        document: p.Infra.ToolConfigDocument,
        checker: str,
        project_root: Path | None,
    ) -> Sequence[tuple[str, Mapping[str, str]]]:
        """Resolve each authorized exception root to one checker's native levels.

        Roots are relative to the project that declares them. Without an
        on-disk project (a pre-write scaffold) the declarations render as
        written; with one, every declared root must exist.

        Returns:
            Declaration-ordered roots paired with the checker's rule levels;
            entries that change no rule of the checker are omitted.

        Raises:
            ValueError: If two exceptions declare the same root.
            FileNotFoundError: If a declared root is absent from the project.

        """
        entries = document.tools.pyright.path_rules.diagnostic_path_exceptions
        roots = [entry.root for entry in entries]
        duplicated = sorted({root for root in roots if roots.count(root) > 1})
        if duplicated:
            msg = f"diagnostic exception roots declared twice: {duplicated}"
            raise ValueError(msg)
        resolved: list[tuple[str, Mapping[str, str]]] = []
        for entry in entries:
            if project_root is not None and not (project_root / entry.root).exists():
                msg = (
                    f"diagnostic exception root {entry.root!r} does not exist "
                    f"in {project_root}"
                )
                raise FileNotFoundError(msg)
            levels = {
                change.rule: change.new
                for change in entry.changes
                if change.checker == checker
            }
            if levels:
                resolved.append((entry.root, levels))
        return tuple(resolved)

    @staticmethod
    def native_tool_settings(
        document: p.Infra.ToolConfigDocument, table: str
    ) -> t.JsonDict:
        """Read a declared native table without inventing an absent configuration.

        Returns:
            The elected JSON-compatible options for the declared table.

        """
        return FlextInfraUtilitiesNativeTooling.configuration_pairs(
            document.settings[table]
        )

    @staticmethod
    def native_tool_configuration(
        document: p.Infra.ToolConfigDocument, root: str
    ) -> t.JsonDict:
        """Compose a declared native root and its nested option tables.

        Returns:
            The elected tool configuration with native nested table structure.

        Raises:
            KeyError: If the requested root has no declared option tables.

        """
        result: t.JsonDict = {}
        selected = False
        for table, entries in sorted(document.settings.items()):
            owner, separator, nested = table.partition(".")
            if owner != root:
                continue
            selected = True
            target = u.Cli.toml_mapping_ensure_path(
                result, nested.split(".") if separator else ()
            )
            target.update(FlextInfraUtilitiesNativeTooling.configuration_pairs(entries))
        if not selected:
            raise KeyError(root)
        return result

    @staticmethod
    def native_tool_setting[TValue](
        document: p.Infra.ToolConfigDocument,
        table: str,
        key: str,
        target: TypeForm[TValue],
    ) -> TValue:
        """Validate one native option, preserving lookup and validation failures.

        Returns:
            The configured value validated against the consumer's type.

        """
        return u.type_adapter(target).validate_python(
            dict(document.settings[table])[key], strict=True
        )

    @staticmethod
    def native_tool_strings(
        document: p.Infra.ToolConfigDocument, table: str, key: str
    ) -> Sequence[str]:
        """Validate one native string-array option.

        Returns:
            The configured strings, preserving lookup and validation failures.

        """
        return FlextInfraUtilitiesNativeTooling.native_tool_setting(
            document, table, key, TypeForm(Sequence[str])
        )

    @staticmethod
    def native_exclude_regex(globs: Sequence[str]) -> str:
        """Translate exclusion globs into one regex for regex-only tools.

        Mypy's ``exclude`` takes a single regular expression; the stdlib
        translation of the same globs every analyzer excludes keeps one owner.

        Returns:
            The alternation of every translated glob.

        """
        return "|".join(
            glob.translate(pattern, recursive=True, include_hidden=True)
            for pattern in globs
        )


__all__ = ["FlextInfraUtilitiesNativeTooling"]
