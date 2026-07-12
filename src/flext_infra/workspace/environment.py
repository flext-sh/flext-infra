"""Canonical workspace environment file generation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from flext_core import r

from flext_infra import c, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraWorkspaceEnvironment:
    """Generate and sync canonical direnv/mise workspace files."""

    @classmethod
    def sync_environment_files(
        cls,
        workspace_root: Path,
        *,
        apply: bool = True,
        force: bool = False,
    ) -> p.Result[int]:
        """Sync generated workspace environment files."""
        if not cls.has_pyproject(workspace_root):
            return cls.remove_generated_environment_files(workspace_root, apply=apply)
        envrc_result = cls.sync_envrc(workspace_root, apply=apply, force=force)
        if envrc_result.failure:
            return r[int].fail(envrc_result.error or ".envrc sync failed")
        mise_result = cls.sync_mise_toml(workspace_root, apply=apply)
        if mise_result.failure:
            return r[int].fail(mise_result.error or ".mise.toml sync failed")
        changed = int(envrc_result.value) + int(mise_result.value)
        return r[int].ok(changed)

    @classmethod
    def sync_envrc(
        cls,
        workspace_root: Path,
        *,
        apply: bool = True,
        force: bool = False,
    ) -> p.Result[bool]:
        """Write canonical ``.envrc`` when absent, generated, or forced."""
        target_path = workspace_root / c.Infra.ENVRC_FILENAME
        return cls.write_generated_text(
            target_path,
            c.Infra.WORKSPACE_ENVRC_CONTENT,
            apply=apply,
            force=force,
        )

    @classmethod
    def sync_mise_toml(
        cls,
        workspace_root: Path,
        *,
        apply: bool = True,
    ) -> p.Result[bool]:
        """Render or merge canonical Python tool pins into ``.mise.toml``."""
        target_path = workspace_root / c.Infra.MISE_TOML_FILENAME
        rendered = cls.render_mise_toml(workspace_root)
        if rendered.failure:
            return r[bool].fail(rendered.error or ".mise.toml render failed")
        if not target_path.is_file():
            return cls.write_text_if_different(
                target_path,
                rendered.value,
                apply=apply,
            )
        read = u.Cli.files_read_text(target_path)
        if read.failure:
            return r[bool].fail(read.error or ".mise.toml read failed")
        current = read.value
        if cls.is_generated_environment_text(current):
            return cls.write_text_if_different(
                target_path,
                rendered.value,
                apply=apply,
            )
        return cls.merge_custom_mise_toml(
            target_path,
            current,
            workspace_root,
            apply=apply,
        )

    @classmethod
    def render_mise_toml(cls, workspace_root: Path) -> p.Result[str]:
        """Render canonical ``.mise.toml`` content for one workspace."""
        doc = u.Cli.toml_parse_text(c.Infra.WORKSPACE_MISE_TOML_CONTENT)
        if doc is None:
            return r[str].fail("canonical .mise.toml template is invalid")
        python_version = cls.workspace_python_version(workspace_root)
        if python_version is not None:
            tools = u.Cli.toml_ensure_table(doc, "tools")
            tools["python"] = python_version
        return r[str].ok(u.Cli.toml_dumps(doc))

    @classmethod
    def merge_custom_mise_toml(
        cls,
        target_path: Path,
        current: str,
        workspace_root: Path,
        *,
        apply: bool = True,
    ) -> p.Result[bool]:
        """Merge canonical tool pins into a custom ``.mise.toml``."""
        doc = u.Cli.toml_read(target_path)
        if doc is None:
            return r[bool].fail(f"{target_path}: invalid TOML")
        tool_pins_result = cls.mise_tool_pins(workspace_root)
        if tool_pins_result.failure:
            return r[bool].fail(tool_pins_result.error or ".mise.toml pins failed")
        tools = u.Cli.toml_ensure_table(doc, "tools")
        changed = False
        for name, value in tool_pins_result.value.items():
            if u.Cli.toml_value(tools, name) == value:
                continue
            tools[name] = value
            changed = True
        for name in c.Infra.WORKSPACE_MISE_REMOVED_TOOLS:
            if name not in tools:
                continue
            del tools[name]
            changed = True
        if not changed:
            return r[bool].ok(False)
        rendered = u.Cli.toml_dumps(doc)
        if rendered == current:
            return r[bool].ok(False)
        if not apply:
            return r[bool].ok(True)
        write_result = u.Cli.files_write_text(target_path, rendered)
        if write_result.failure:
            return r[bool].fail(write_result.error or f"{target_path}: write failed")
        return r[bool].ok(True)

    @classmethod
    def mise_tool_pins(cls, workspace_root: Path) -> p.Result[dict[str, str]]:
        """Return canonical mise tool pins for one workspace."""
        mapping = u.Cli.toml_mapping_from_text(c.Infra.WORKSPACE_MISE_TOML_CONTENT)
        if mapping is None:
            return r[dict[str, str]].fail("canonical .mise.toml template is invalid")
        tools = u.Cli.toml_mapping_child(mapping, "tools")
        if tools is None:
            return r[dict[str, str]].fail("canonical .mise.toml template lacks [tools]")
        pins: dict[str, str] = {}
        for name, value in tools.items():
            if not isinstance(value, str):
                return r[dict[str, str]].fail(
                    f"canonical .mise.toml [tools].{name} must be a string",
                )
            pins[name] = value
        python_version = cls.workspace_python_version(workspace_root)
        if python_version is not None:
            pins["python"] = python_version
        return r[dict[str, str]].ok(pins)

    @staticmethod
    def has_pyproject(workspace_root: Path) -> bool:
        """Return whether the workspace declares Python project metadata."""
        pyproject_filename: str = c.Infra.PYPROJECT_FILENAME
        return (workspace_root / pyproject_filename).is_file()

    @staticmethod
    def workspace_python_version(workspace_root: Path) -> str | None:
        """Return the Python minor version declared by ``pyproject.toml``."""
        pyproject_filename: str = c.Infra.PYPROJECT_FILENAME
        pyproject = workspace_root / pyproject_filename
        if not pyproject.is_file():
            return None
        mapping_result = u.Cli.toml_read_json(pyproject)
        if mapping_result.failure:
            return None
        project = u.Cli.toml_mapping_child(mapping_result.value, c.Infra.PROJECT)
        if project is None:
            return None
        requires_python = project.get("requires-python")
        if not isinstance(requires_python, str):
            return None
        match = re.search(r">=\s*(3\.\d+)", requires_python)
        return match.group(1) if match else None

    @classmethod
    def remove_generated_environment_files(
        cls,
        workspace_root: Path,
        *,
        apply: bool = True,
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
        cls,
        target_path: Path,
        *,
        apply: bool = True,
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
                delete_result.error or f"{target_path.name} delete failed",
            )
        return r[bool].ok(True)

    @classmethod
    def write_generated_text(
        cls,
        target_path: Path,
        content: str,
        *,
        apply: bool = True,
        force: bool = False,
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
        target_path: Path,
        content: str,
        *,
        apply: bool = True,
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
        """Return True when content carries a known generated marker."""
        markers: t.StrSequence = (
            c.Infra.WORKSPACE_ENV_GENERATED_MARKER,
            *c.Infra.WORKSPACE_ENV_LEGACY_MARKERS,
        )
        return any(marker in content for marker in markers)


__all__: list[str] = ["FlextInfraWorkspaceEnvironment"]
