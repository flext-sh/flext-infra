"""Generic filesystem helpers shared through ``u.Cli``."""

from __future__ import annotations

import csv
import os
import shutil
import tempfile
from pathlib import Path

from flext_cli import c, p, r, t


class FlextCliUtilitiesFiles:
    """Implementation part for FlextCliUtilitiesFiles."""

    @staticmethod
    def files_read_csv_with_headers(
        file_path: t.Cli.TextPath,
    ) -> p.Result[t.SequenceOf[t.StrMapping]]:
        """Read one CSV file into mapping rows using header row."""

        def _load() -> t.SequenceOf[t.StrMapping]:
            with Path(file_path).open(
                encoding=c.Cli.ENCODING_DEFAULT, newline=""
            ) as handle:
                return [dict(row) for row in csv.DictReader(handle)]

        return FlextCliUtilitiesFiles.files_execute(_load, c.Cli.ERR_CSV_READ_FAILED)

    @staticmethod
    def files_read_binary(file_path: t.Cli.TextPath) -> p.Result[bytes]:
        """Read one binary file."""
        return FlextCliUtilitiesFiles.files_execute(
            lambda: Path(file_path).read_bytes(), c.Cli.ERR_BINARY_READ_FAILED
        )

    @staticmethod
    def files_write_binary(file_path: t.Cli.TextPath, data: bytes) -> p.Result[bool]:
        """Write one binary file atomically in its destination directory."""
        path = Path(file_path)
        ensure_result = FlextCliUtilitiesFiles.ensure_dir(path.parent)
        if ensure_result.failure:
            return r[bool].fail(
                ensure_result.error or c.Cli.ERR_ENSURE_DIR_GENERIC_FAILED
            )
        try:
            FlextCliUtilitiesFiles._write_temp_and_replace(path, data)
        except OSError as exc:
            return r[bool].fail(c.Cli.ERR_BINARY_WRITE_FAILED.format(error=exc))
        return r[bool].ok(True)

    @staticmethod
    def atomic_write_text_file(
        file_path: t.Cli.TextPath, content: str
    ) -> p.Result[bool]:
        """Write a text file atomically via the shared byte primitive."""
        path = Path(file_path)
        ensure_result = FlextCliUtilitiesFiles.ensure_dir(path.parent)
        if ensure_result.failure:
            return r[bool].fail(
                ensure_result.error or c.Cli.ERR_ENSURE_DIR_GENERIC_FAILED
            )
        try:
            FlextCliUtilitiesFiles._write_temp_and_replace(
                path, content.encode(c.Cli.ENCODING_DEFAULT)
            )
        except OSError as exc:
            return r[bool].fail(
                c.Cli.ERR_ATOMIC_WRITE_TEXT_FILE_FAILED.format(error=exc)
            )
        return r[bool].ok(True)

    @staticmethod
    def _write_temp_and_replace(path: Path, content: bytes) -> None:
        """Persist bytes to a sibling temporary file, then atomically replace."""
        # NOTE (multi-agent): Text and binary share this one atomic-write owner.
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
            Path(tmp_path).replace(path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    @staticmethod
    def files_copy(
        source_path: t.Cli.TextPath, destination_path: t.Cli.TextPath
    ) -> p.Result[bool]:
        """Copy one file preserving metadata."""

        def _copy() -> bool:
            shutil.copy2(source_path, destination_path)
            return True

        return FlextCliUtilitiesFiles.files_execute(_copy, c.Cli.ERR_FILE_COPY_FAILED)

    @staticmethod
    def files_execute[T](
        operation_func: t.Cli.NullaryOperation[T],
        error_template: str,
        **format_kwargs: t.Scalar,
    ) -> p.Result[T]:
        """Execute one operation and map common runtime errors to ``r``."""
        try:
            return r[T].ok(operation_func())
        except c.EXC_BROAD_RUNTIME_OS as exc:
            return r[T].fail(error_template.format(error=exc, **format_kwargs))

    @staticmethod
    def files_execute_bool[T](
        operation_func: t.Cli.NullaryOperation[T],
        error_template: str,
        **format_kwargs: t.Scalar,
    ) -> p.Result[bool]:
        """Execute one operation that should return a success boolean."""

        def _run() -> bool:
            _ = operation_func()
            return True

        return FlextCliUtilitiesFiles.files_execute(
            _run, error_template, **format_kwargs
        )

    @staticmethod
    def ensure_dir(path: t.Cli.TextPath) -> p.Result[Path]:
        """Create a directory tree when missing and return the resolved path."""
        target = Path(path)
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[Path].fail(c.Cli.ERR_ENSURE_DIR_FAILED.format(error=exc))
        return r[Path].ok(target)


__all__: list[str] = ["FlextCliUtilitiesFiles"]
