"""Canonical workspace environment file generation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceEnvironment:
    """Generate and sync the canonical direnv workspace file."""

    @classmethod
    def sync_environment_files(
        cls, workspace_root: Path, *, apply: bool = True, force: bool = False
    ) -> p.Result[int]:
        """Sync generated workspace environment files."""
        if not cls.has_pyproject(workspace_root):
            return cls.remove_generated_environment_files(workspace_root, apply=apply)
        envrc_result = cls.sync_envrc(workspace_root, apply=apply, force=force)
        if envrc_result.failure:
            return r[int].fail(envrc_result.error or ".envrc sync failed")
        return r[int].ok(int(envrc_result.value))

    @classmethod
    def sync_envrc(
        cls, workspace_root: Path, *, apply: bool = True, force: bool = False
    ) -> p.Result[bool]:
        """Write canonical ``.envrc`` when absent, generated, or forced."""
        target_path = workspace_root / c.Infra.ENVRC_FILENAME
        rendered = cls._render_environment_template(
            c.Infra.WORKSPACE_ENVRC_TEMPLATE_NAME
        )
        if rendered.failure:
            return r[bool].fail(rendered.error or ".envrc template render failed")
        return cls.write_generated_text(
            target_path, rendered.value, apply=apply, force=force
        )

    @staticmethod
    def _render_environment_template(template_name: str) -> p.Result[str]:
        """Render one workspace environment template from validated toolchain data."""
        # mro-sltx (backport 0.20): config-driven Jinja render replaces inline
        # content constants; template dir resolved package-relative (0.12 pattern).
        template_path = Path(__file__).resolve().parent / "templates" / template_name
        return u.Cli.template_render(template_path, config.Infra.codegen.toolchain)

    @staticmethod
    def has_pyproject(workspace_root: Path) -> bool:
        """Return whether the workspace declares Python project metadata."""
        pyproject_filename: str = c.Infra.PYPROJECT_FILENAME
        return (workspace_root / pyproject_filename).is_file()

    @classmethod
    def remove_generated_environment_files(
        cls, workspace_root: Path, *, apply: bool = True
    ) -> p.Result[int]:
        """Remove generated environment files from non-Python workspaces."""
        changed = 0
        for filename in c.Infra.WORKSPACE_ENV_FILES:
            target_path = workspace_root / filename
            result = cls.remove_generated_environment_file(target_path, apply=apply)
            if result.failure:
                return r[int].fail(result.error or f"{filename} removal failed")
            changed += int(result.value)
        return r[int].ok(changed)

    @classmethod
    def remove_generated_environment_file(
        cls, target_path: Path, *, apply: bool = True
    ) -> p.Result[bool]:
        """Remove one generated environment file without touching custom files."""
        if not target_path.exists():
            return r[bool].ok(False)
        read = u.Cli.files_read_text(target_path)
        if read.failure:
            return r[bool].fail(read.error or f"{target_path.name} read failed")
        if not cls.is_generated_environment_text(read.value):
            return r[bool].ok(False)
        if not apply:
            return r[bool].ok(True)
        delete_result = u.Cli.files_delete(target_path)
        if delete_result.failure:
            return r[bool].fail(
                delete_result.error or f"{target_path.name} delete failed"
            )
        return r[bool].ok(True)

    @classmethod
    def write_generated_text(
        cls, target_path: Path, content: str, *, apply: bool = True, force: bool = False
    ) -> p.Result[bool]:
        """Write generated content without clobbering custom files."""
        if target_path.exists():
            read = u.Cli.files_read_text(target_path)
            if read.failure:
                return r[bool].fail(read.error or f"{target_path.name} read failed")
            existing = read.value
            if u.Cli.sha256_content(existing) == u.Cli.sha256_content(content):
                return r[bool].ok(False)
            if not force and not cls.is_generated_environment_text(existing):
                return r[bool].ok(False)
        return cls.write_text_if_different(target_path, content, apply=apply)

    @staticmethod
    def write_text_if_different(
        target_path: Path, content: str, *, apply: bool = True
    ) -> p.Result[bool]:
        """Write text when content differs."""
        if target_path.is_file():
            read = u.Cli.files_read_text(target_path)
            if read.failure:
                return r[bool].fail(read.error or f"{target_path.name} read failed")
            if read.value == content:
                return r[bool].ok(False)
        if not apply:
            return r[bool].ok(True)
        return u.Cli.atomic_write_text_file(target_path, content)

    @staticmethod
    def is_generated_environment_text(content: str) -> bool:
        """Return True when content carries the canonical generated marker."""
        return c.Infra.WORKSPACE_ENV_GENERATED_MARKER in content


__all__: list[str] = ["FlextInfraWorkspaceEnvironment"]
