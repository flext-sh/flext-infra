"""Root workspace ``[tool.uv]`` overlay rendering and validation."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_cli import r, u

from flext_infra.constants import c
from flext_infra.typings import t

from ..dependencies import FlextInfraUtilitiesDependencies
from .requirements import FlextInfraUtilitiesPyprojectRequirements

if TYPE_CHECKING:
    from flext_infra.models import m
    from flext_infra.protocols import p


class FlextInfraUtilitiesPyprojectUvSources(FlextInfraUtilitiesPyprojectRequirements):
    """Keep managed uv sources only as the root local-workspace overlay."""

    @classmethod
    def _declared_uv_constraint_dependencies(
        cls, document: t.Cli.TomlDocument
    ) -> t.SequenceOf[str]:
        """Return the document-declared ``[tool.uv] constraint-dependencies``."""
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return ()
        uv = u.Cli.toml_table_child(tool, "uv")
        if uv is None:
            return ()
        declared = u.Cli.toml_value(uv, "constraint-dependencies")
        return tuple(u.Cli.toml_as_string_list(declared))

    @classmethod
    def _sync_uv_sources(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        link_mode: str | None = None,
        constraint_dependencies: t.SequenceOf[str] | None = None,
        exclude_dependencies: t.SequenceOf[p.Model] | None = None,
        uv_environments: t.StrSequence | None = None,
    ) -> p.Result[bool]:
        """Keep managed uv sources only as the root local-workspace overlay."""
        repository_root = cls._is_workspace_context_root(
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        # Documents without any uv concern stay untouched; everything else
        # converges on one explicit [tool.uv] table.
        needs_uv = bool(
            repository_root
            or link_mode is not None
            or exclude_dependencies
            or constraint_dependencies
        )
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None and not needs_uv:
            return r[bool].ok(True)
        if tool is None:
            tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        uv = u.Cli.toml_table_child(tool, "uv")
        if uv is None and not needs_uv:
            return r[bool].ok(True)
        if uv is None:
            uv = u.Cli.toml_ensure_table(tool, "uv")
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        # Constraints are SSOT-rendered: the declared config value is the only
        # source, so a removed declaration exterminates the key everywhere and
        # no orphan cap can survive without an owner (flext-gzfd2 class).
        selected_constraints = tuple(constraint_dependencies or ())
        retained_constraints = tuple(
            requirement
            for requirement in selected_constraints
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != "uv"
        )
        if retained_constraints:
            u.Cli.toml_sync_string_list(
                uv, "constraint-dependencies", retained_constraints
            )
        else:
            u.Cli.toml_remove_key_if_present(uv, "constraint-dependencies")
        if link_mode is not None:
            u.Cli.toml_sync_value(uv, "link-mode", link_mode)
        # The supply-chain cooldown was exterminated fleet-wide (flext-fphyv):
        # uv resolves every version published up to now. Removed declarations
        # exterminate the keys everywhere so no orphan cap survives without an
        # owner (flext-gzfd2 class).
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer")
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer-package")
        # Environments come from the fleet toolchain SSOT: an empty declaration
        # removes the key so uv resolves every environment, and a declared
        # sequence skips the splits the fleet does not support (win32 resolves
        # meltano's structlog cap against flext-core's floor and is
        # unsatisfiable).
        if uv_environments:
            # Declared as list[JsonValue], not list[str]: `list` is invariant,
            # so the narrower element type is not assignable to the writer's
            # parameter even though every element is a valid JsonValue.
            environments: list[t.JsonValue] = list(uv_environments)
            u.Cli.toml_sync_value(uv, "environments", environments)
        elif uv_environments is not None:
            u.Cli.toml_remove_key_if_present(uv, "environments")
        # Project is a flext-infra routing key only; uv scoped form is
        # {package={name, version?}, dependencies=[...]} (uv settings docs).
        # Emit on every owning pyproject so standalone CI clones resolve;
        # do not gate on owns_uv_root_policy (that stripped member excludes).
        if exclude_dependencies is not None:
            exclude_payload = list(
                t.Cli.JSON_LIST_ADAPTER.validate_python([
                    {
                        key: value
                        for key, value in item.model_dump(
                            mode="json", exclude_none=True
                        ).items()
                        if key != "project"
                    }
                    for item in exclude_dependencies
                ])
            )
            if exclude_payload:
                u.Cli.toml_sync_value(uv, "exclude-dependencies", exclude_payload)
            else:
                u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")
        member_paths = tuple(member.path.as_posix() for member in workspace.subprojects)
        # Only an actual multi-project owner declares a uv workspace. A leaf
        # can also be a composed member; inserting an empty workspace there
        # breaks execution from the parent with uv's nested-workspace error.
        if repository_root and member_paths:
            workspace_table = u.Cli.toml_table_child(uv, "workspace")
            if workspace_table is None:
                workspace_table = u.Cli.toml_ensure_table(uv, "workspace")
            u.Cli.toml_sync_string_list(workspace_table, "members", member_paths)
        else:
            u.Cli.toml_remove_key_if_present(uv, "workspace")
        sources = u.Cli.toml_table_child(uv, "sources")
        if sources is None and repository_root:
            sources = u.Cli.toml_ensure_table(uv, "sources")
        if sources is None:
            if not repository_root and not tuple(uv):
                u.Cli.toml_remove_key_if_present(tool, "uv")
            return r[bool].ok(True)
        workspace_names = {member.distribution for member in workspace.subprojects}
        for source_name in tuple(sources):
            # Member documents resolve internal siblings through the direct
            # Git requirement; a git [tool.uv.sources] entry on a workspace
            # member is rejected by uv itself, and only the root carries the
            # workspace overlay.
            if source_name.startswith("flext-") and (
                not repository_root or source_name not in workspace_names
            ):
                u.Cli.toml_remove_key_if_present(sources, source_name)
        if repository_root:
            for member in workspace.subprojects:
                u.Cli.toml_sync_mapping_table(
                    sources, member.distribution, {"workspace": True}
                )
        elif not tuple(sources):
            u.Cli.toml_remove_key_if_present(uv, "sources")
        if not repository_root and not tuple(uv):
            u.Cli.toml_remove_key_if_present(tool, "uv")
        return r[bool].ok(True)

    @classmethod
    def _resolved_root_sources(
        cls,
        *,
        workspace: p.Infra.WorkspaceSpec,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[MutableMapping[str, MutableMapping[str, t.JsonValue]]]:
        """Resolve the workspace source overlay from typed metadata."""
        candidates = (workspace.repository, *workspace.subprojects)
        for distribution in dict.fromkeys(item.distribution for item in candidates):
            reference_result = cls._repository_reference(
                distribution, repositories=candidates, providers=providers
            )
            if reference_result.failure:
                return r[
                    MutableMapping[str, MutableMapping[str, t.JsonValue]]
                ].from_failure(reference_result)
        return r[MutableMapping[str, MutableMapping[str, t.JsonValue]]].ok({
            member.distribution: {"workspace": True} for member in workspace.subprojects
        })

    @classmethod
    def _validate_root_uv_sources(
        cls,
        document: t.Cli.TomlDocument,
        *,
        workspace: p.Infra.WorkspaceSpec,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[bool]:
        """Validate the root overlay without rewriting out-of-order TOML tables."""
        tool = u.Cli.toml_mapping_child(
            u.Cli.toml_as_mapping(document) or {}, c.Infra.TOOL
        )
        uv = None if tool is None else u.Cli.toml_mapping_child(tool, "uv")
        tables = {
            "workspace": None
            if uv is None
            else u.Cli.toml_mapping_child(uv, "workspace"),
            "sources": None if uv is None else u.Cli.toml_mapping_child(uv, "sources"),
        }
        missing = next(
            (
                name
                for name, table in (
                    ("tool", tool),
                    ("tool.uv", uv),
                    ("tool.uv.workspace", tables["workspace"]),
                    ("tool.uv.sources", tables["sources"]),
                )
                if table is None
            ),
            None,
        )
        if missing is not None:
            return r[bool].fail(f"root pyproject must define [{missing}]")
        if uv is not None and "override-dependencies" in uv:
            return r[bool].fail(
                "root pyproject must not define tool.uv.override-dependencies"
            )
        validated_members: p.Result[t.StrSequence] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            (tables["workspace"] or {}).get("members"),
            strict=True,
        )
        if validated_members.failure:
            return r[bool].fail_op(
                "validate root uv workspace package entries", validated_members.error
            )
        if tuple(validated_members.value) != tuple(
            member.path.as_posix() for member in workspace.subprojects
        ):
            return r[bool].fail(
                "root uv workspace package entries differ from workspace SSOT"
            )
        resolved_result = cls._resolved_root_sources(
            workspace=workspace, providers=providers
        )
        if resolved_result.failure:
            return r[bool].from_failure(resolved_result)
        sources = tables["sources"] or {}
        if tuple(sources) != tuple(resolved_result.value):
            return r[bool].fail("root uv workspace sources differ from workspace SSOT")
        for source_name, expected_source in resolved_result.value.items():
            source = u.Cli.toml_mapping_child(sources, source_name)
            if source is None or list(source.items()) != list(expected_source.items()):
                return r[bool].fail(
                    f"root uv workspace sources differ from workspace SSOT: {source_name}"
                )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectUvSources"]
