"""Workspace environment sync owner for the public ``infra`` facade.

This is the single canonical in-process surface for keeping one workspace's
direnv/mise files (``.envrc``, ``.mise.toml``) aligned with the codegen SSOT.
It renders the same ``templates/project/base`` Jinja templates that
``codegen conform`` owns, from the same ``config.Infra.codegen.toolchain``
spec, so both paths produce identical governed content. Custom (non-generated)
files are preserved unless forced; custom ``.mise.toml`` documents are merged
tool-by-tool with the canonical pins and pruned of forbidden tools.

Consumers must reach this through ``from flext_infra import infra`` — the
module itself stays private service composition.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, m, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceEnvironmentMixin:
    """Generate and sync canonical direnv/mise workspace files."""

    @classmethod
    def sync_environment_files(
        cls, request: m.Infra.WorkspaceEnvironmentSyncRequest
    ) -> p.Result[m.Infra.WorkspaceEnvironmentSyncResult]:
        """Sync one workspace's generated environment files."""
        result_type = m.Infra.WorkspaceEnvironmentSyncResult
        workspace_root = request.workspace_root
        if not (workspace_root / c.Infra.PYPROJECT_FILENAME).is_file():
            return cls._remove_generated_environment_files(request)
        envrc_result = cls._sync_envrc(request)
        if envrc_result.failure:
            return r[result_type].fail(envrc_result.error or ".envrc sync failed")
        mise_result = cls._sync_mise_toml(request)
        if mise_result.failure:
            return r[result_type].fail(mise_result.error or ".mise.toml sync failed")
        changed = (
            *((workspace_root / c.Infra.ENVRC_FILENAME,) if envrc_result.value else ()),
            *(
                (workspace_root / c.Infra.MISE_TOML_FILENAME,)
                if mise_result.value
                else ()
            ),
        )
        return r[result_type].ok(result_type(changed_files=changed))

    @classmethod
    def _sync_envrc(
        cls, request: m.Infra.WorkspaceEnvironmentSyncRequest
    ) -> p.Result[bool]:
        """Write canonical ``.envrc`` when absent, generated, or forced."""
        rendered = cls._render_environment_template(c.Infra.ENVRC_FILENAME)
        if rendered.failure:
            return r[bool].fail(rendered.error or ".envrc template render failed")
        return cls._write_generated_text(
            request.workspace_root / c.Infra.ENVRC_FILENAME,
            rendered.value,
            apply=request.apply,
            force=request.force,
        )

    @classmethod
    def _sync_mise_toml(
        cls, request: m.Infra.WorkspaceEnvironmentSyncRequest
    ) -> p.Result[bool]:
        """Render or merge canonical tool pins into ``.mise.toml``."""
        workspace_root = request.workspace_root
        apply = request.apply
        force = request.force
        target_path = workspace_root / c.Infra.MISE_TOML_FILENAME
        rendered = cls._render_mise_toml(workspace_root)
        if rendered.failure:
            return r[bool].fail(rendered.error or ".mise.toml render failed")
        if not target_path.is_file() or force:
            return cls._write_generated_text(
                target_path, rendered.value, apply=apply, force=force
            )
        read = u.Cli.files_read_text(target_path)
        if read.failure:
            return r[bool].fail(read.error or ".mise.toml read failed")
        current = read.value
        if cls._is_generated_environment_text(current):
            return cls._write_text_if_different(
                target_path, rendered.value, apply=apply
            )
        return cls._merge_custom_mise_toml(
            target_path, current, workspace_root, apply=apply
        )

    @classmethod
    def _render_mise_toml(cls, workspace_root: Path) -> p.Result[str]:
        """Render canonical ``.mise.toml`` content for one workspace."""
        rendered = cls._render_environment_template(c.Infra.MISE_TOML_FILENAME)
        if rendered.failure:
            return r[str].fail(rendered.error or ".mise.toml template render failed")
        doc = u.Cli.toml_parse_text(rendered.value)
        if doc is None:
            return r[str].fail("canonical .mise.toml template is invalid")
        python_version = cls._workspace_python_version(workspace_root)
        if python_version is not None:
            tools = u.Cli.toml_ensure_table(doc, "tools")
            tools["python"] = python_version
        return r[str].ok(u.Cli.toml_dumps(doc))

    @staticmethod
    def _render_environment_template(destination: str) -> p.Result[str]:
        """Render one SSOT environment template from the toolchain spec."""
        template_path = (
            Path(__file__).resolve().parents[2]
            / "templates"
            / config.Infra.codegen.templates.root
            / "base"
            / f"{destination}.j2"
        )
        return u.Cli.template_render(template_path, config.Infra.codegen.toolchain)

    @classmethod
    def _merge_custom_mise_toml(
        cls, target_path: Path, current: str, workspace_root: Path, *, apply: bool
    ) -> p.Result[bool]:
        """Merge canonical tool pins into a custom ``.mise.toml``."""
        doc = u.Cli.toml_read(target_path)
        if doc is None:
            return r[bool].fail(f"{target_path}: invalid TOML")
        tool_pins_result = cls._mise_tool_pins(workspace_root)
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
    def _mise_tool_pins(cls, workspace_root: Path) -> p.Result[dict[str, t.JsonValue]]:
        """Return canonical mise tool pins for one workspace."""
        rendered = cls._render_mise_toml(workspace_root)
        if rendered.failure:
            return r[dict[str, t.JsonValue]].fail(
                rendered.error or "canonical .mise.toml render failed"
            )
        mapping = u.Cli.toml_mapping_from_text(rendered.value)
        if mapping is None:
            return r[dict[str, t.JsonValue]].fail("canonical .mise.toml template is invalid")
        tools = u.Cli.toml_mapping_child(mapping, "tools")
        if tools is None:
            return r[dict[str, t.JsonValue]].fail("canonical .mise.toml template lacks [tools]")
        pins: dict[str, t.JsonValue] = {}
        for name, value in tools.items():
            if not isinstance(value, (str, dict)):
                return r[dict[str, t.JsonValue]].fail(
                    f"canonical .mise.toml [tools].{name} must be a string or table"
                )
            pins[name] = value
        return r[dict[str, t.JsonValue]].ok(pins)

    @staticmethod
    def _workspace_python_version(workspace_root: Path) -> str | None:
        """Return the Python minor version declared by ``pyproject.toml``."""
        pyproject = workspace_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return None
        read = u.Cli.files_read_text(pyproject)
        if read.failure:
            return None
        match = c.Infra.REQUIRES_PYTHON_RE.search(read.value)
        return f"{match.group(1)}.{match.group(2)}" if match else None

    @classmethod
    def _remove_generated_environment_files(
        cls, request: m.Infra.WorkspaceEnvironmentSyncRequest
    ) -> p.Result[m.Infra.WorkspaceEnvironmentSyncResult]:
        """Remove generated environment files from non-Python workspaces."""
        result_type = m.Infra.WorkspaceEnvironmentSyncResult
        removed: list[Path] = []
        for filename in c.Infra.WORKSPACE_ENV_FILES:
            target_path = request.workspace_root / filename
            result = cls._remove_generated_environment_file(
                target_path, apply=request.apply
            )
            if result.failure:
                return r[result_type].fail(result.error or f"{filename} removal failed")
            if result.value:
                removed.append(target_path)
        return r[result_type].ok(result_type(changed_files=tuple(removed)))

    @classmethod
    def _remove_generated_environment_file(
        cls, target_path: Path, *, apply: bool
    ) -> p.Result[bool]:
        """Remove one generated environment file without touching custom files."""
        if not target_path.exists():
            return r[bool].ok(False)
        read = u.Cli.files_read_text(target_path)
        if read.failure:
            return r[bool].fail(read.error or f"{target_path.name} read failed")
        if not cls._is_generated_environment_text(read.value):
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
    def _write_generated_text(
        cls, target_path: Path, content: str, *, apply: bool, force: bool
    ) -> p.Result[bool]:
        """Write generated content without clobbering custom files."""
        if target_path.exists():
            read = u.Cli.files_read_text(target_path)
            if read.failure:
                return r[bool].fail(read.error or f"{target_path.name} read failed")
            existing = read.value
            if u.Cli.sha256_content(existing) == u.Cli.sha256_content(content):
                return r[bool].ok(False)
            if not force and not cls._is_generated_environment_text(existing):
                return r[bool].ok(False)
        return cls._write_text_if_different(target_path, content, apply=apply)

    @staticmethod
    def _write_text_if_different(
        target_path: Path, content: str, *, apply: bool
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
    def _is_generated_environment_text(content: str) -> bool:
        """Return True when content carries a canonical generated marker."""
        return any(
            marker in content for marker in c.Infra.WORKSPACE_ENV_GENERATED_MARKERS
        )


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentMixin"]
