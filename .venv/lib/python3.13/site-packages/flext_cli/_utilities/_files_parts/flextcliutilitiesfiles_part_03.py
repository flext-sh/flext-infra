"""Generic filesystem helpers shared through ``u.Cli``."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from flext_cli import c, p, r, t
from flext_cli._utilities._files_parts.flextcliutilitiesfiles_part_02 import (
    FlextCliUtilitiesFiles as FlextCliUtilitiesFilesPart02,
)


class FlextCliUtilitiesFiles:
    """Implementation part for FlextCliUtilitiesFiles."""

    @staticmethod
    def files_list_directory_names(
        file_path: t.Cli.TextPath,
    ) -> p.Result[t.SequenceOf[str]]:
        """Return sorted child directory names for one path."""
        path = Path(file_path)
        if not path.exists():
            return r[t.SequenceOf[str]].ok(())

        def _list() -> t.SequenceOf[str]:
            names = sorted(entry.name for entry in path.iterdir() if entry.is_dir())
            return tuple(names)

        return FlextCliUtilitiesFilesPart02.files_execute(
            _list, c.Cli.ERR_TEXT_READ_FAILED
        )

    @staticmethod
    def ensure_symlink(
        target: t.Cli.TextPath, source: t.Cli.TextPath
    ) -> p.Result[bool]:
        """Ensure target points to source via directory symlink."""
        target_path = Path(target)
        source_path = Path(source).resolve()
        ensure_result = FlextCliUtilitiesFilesPart02.ensure_dir(target_path.parent)
        if ensure_result.failure:
            return r[bool].fail(
                ensure_result.error
                or c.Cli.ERR_CREATE_PARENT_DIR_FAILED.format(target_path=target_path)
            )
        if target_path.is_symlink() and target_path.resolve() == source_path:
            return r[bool].ok(True)
        FlextCliUtilitiesFiles._remove_symlink_target(target_path)
        try:
            target_path.symlink_to(source_path, target_is_directory=True)
        except OSError as exc:
            return r[bool].fail(
                c.Cli.ERR_ENSURE_SYMLINK_FAILED.format(
                    target_path=target_path, error=exc
                )
            )
        return r[bool].ok(True)

    @staticmethod
    def _remove_symlink_target(target_path: Path) -> None:
        """Remove an existing file, directory, or symlink at ``target_path``."""
        if not target_path.exists() and not target_path.is_symlink():
            return
        if target_path.is_dir() and not target_path.is_symlink():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()

    @staticmethod
    def sha256_content(content: str) -> str:
        """Return the SHA-256 hex digest for text content."""
        return hashlib.sha256(content.encode(c.Cli.ENCODING_DEFAULT)).hexdigest()

    @staticmethod
    def sha256_file(file_path: t.Cli.TextPath) -> str:
        """Return the SHA-256 hex digest for a file on disk."""
        path = Path(file_path)
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


__all__: list[str] = ["FlextCliUtilitiesFiles"]
