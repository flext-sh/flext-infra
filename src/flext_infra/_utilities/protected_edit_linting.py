"""In-process structural validation for protected source edits."""

from __future__ import annotations

import hashlib
from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar

from flext_infra.constants import c
from flext_infra.typings import t


class FlextInfraUtilitiesProtectedEditLinting:
    """Validate Python syntax around protected edits without quality tools."""

    _snapshot_cache: ClassVar[
        MutableMapping[tuple[str, str], t.Infra.LintSnapshot]
    ] = {}

    @classmethod
    def selected_lint_tool_names(cls) -> t.StrSequence:
        """Return the generator-owned structural validation name."""
        del cls
        return (c.Infra.SOURCE_VALIDATION_NAME,)

    @staticmethod
    def _relative_path(py_file: Path, workspace: Path) -> Path:
        """Return *py_file* relative to *workspace* when possible."""
        try:
            return py_file.relative_to(workspace)
        except ValueError:
            return py_file

    @classmethod
    def _new_file_lint_baseline(
        cls, py_file: Path, workspace: Path
    ) -> t.Infra.LintSnapshot:
        """Return the valid structural baseline used for a new Python file."""
        del cls, workspace
        compile(c.Infra.FUTURE_ANNOTATIONS, str(py_file), "exec")
        return {}

    @classmethod
    def clear_snapshot_cache(cls) -> None:
        """Reset the content-hash keyed structural snapshot cache."""
        cls._snapshot_cache.clear()

    @staticmethod
    def _lint_snapshot_cache_key(py_file: Path) -> tuple[str, str] | None:
        """Return a stable structural snapshot cache key for *py_file*."""
        try:
            raw_bytes = py_file.read_bytes()
        except OSError:
            return None
        return (str(py_file.resolve()), hashlib.sha256(raw_bytes).hexdigest())

    @staticmethod
    def _source_errors(py_file: Path) -> t.StrSequence:
        """Return deterministic read or syntax errors for one Python source."""
        try:
            source = py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            compile(source, str(py_file), "exec")
        except SyntaxError as exc:
            location = f"{exc.lineno or 0}:{exc.offset or 0}"
            return (f"{location}: {exc.msg}",)
        except OSError as exc:
            return (f"read failed: {exc}",)
        return ()

    @classmethod
    def lint_snapshot(cls, py_file: Path, workspace: Path) -> t.Infra.LintSnapshot:
        """Return an in-process Python structural snapshot for *py_file*."""
        del workspace
        cache_key = cls._lint_snapshot_cache_key(py_file)
        if (
            cache_key is not None
            and (cached := cls._snapshot_cache.get(cache_key)) is not None
        ):
            return cached
        errors = cls._source_errors(py_file)
        result: t.Infra.LintSnapshot = (
            {c.Infra.SOURCE_VALIDATION_NAME: errors} if errors else {}
        )
        if cache_key is not None:
            cls._snapshot_cache[cache_key] = dict(result)
        return result

    @classmethod
    def lint_snapshots(
        cls,
        paths: t.SequenceOf[Path],
        workspace: Path,
    ) -> MutableMapping[Path, t.Infra.LintSnapshot]:
        """Return structural snapshots in deterministic path order."""
        return {
            path: cls.lint_snapshot(path, workspace) for path in paths
        }

    @staticmethod
    def lint_new_errors(
        before: t.Infra.LintSnapshot, after: t.Infra.LintSnapshot
    ) -> t.Infra.LintSnapshot:
        """Return only structural errors introduced relative to *before*."""
        return {
            validator: added
            for validator, lines in after.items()
            if (
                added := tuple(
                    line for line in lines if line not in before.get(validator, ())
                )
            )
        }

    @staticmethod
    def preview_source_lint(
        py_file: Path,
        workspace: Path,
        *,
        updated_source: str,
    ) -> tuple[t.Infra.LintSnapshot, t.Infra.LintSnapshot]:
        """Preview structural output for *updated_source* and restore the file."""
        original_source = py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        before = FlextInfraUtilitiesProtectedEditLinting.lint_snapshot(
            py_file, workspace
        )
        if updated_source == original_source:
            return before, before
        py_file.write_text(updated_source, encoding=c.Cli.ENCODING_DEFAULT)
        try:
            after = FlextInfraUtilitiesProtectedEditLinting.lint_snapshot(
                py_file, workspace
            )
        finally:
            py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)
        return before, after


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditLinting"]
