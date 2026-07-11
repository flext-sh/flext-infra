"""``codegen new`` — create a new FLEXT project from the canonical templates.

Root cause addressed here: ``flext-infra`` had no command to materialize a project,
so the templates could only be validated by hand-rolled harnesses (fake). This
service drives the real, policy-free engine (``u.Cli.template_render_dir``) with
the data manifest (``c.Infra.PROJECT_TEMPLATE_ENTRIES``) and a context derived
through the canonical name helpers (``u.derive_class_stem`` / ``u.pascalize``,
ADR-005 §9 — never a parallel re-derivation).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.14 / agent: codegen): new file per operator live
# order (ULW). ctx via u.derive_class_stem (no parallel detection, ADR-005 §9);
# accessor typing/config+settings symmetry fixed in templates in the same lane.
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra._settings import settings
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraCodegenProjectNew(s[m.Infra.ProjectNewResult]):
    """Create a new FLEXT project (internal member or external standalone)."""

    name: Annotated[
        str,
        m.Field(
            min_length=1,
            description="Distribution name in kebab-case (e.g. flext-demo / acme-demo).",
        ),
    ]
    kind: Annotated[
        c.Infra.ProjectKind,
        m.Field(description="Project kind: internal (monorepo member) or external."),
    ]
    output_root: Annotated[
        Path,
        m.Field(
            description="Directory that becomes the generated project root.",
        ),
    ]
    package_name: Annotated[
        str,
        m.Field(
            description="Python package name (default: name with '-'→'_').",
        ),
    ] = ""
    # NOTE (multi-agent, mro-wkii.14 / agent: codegen): field renamed
    # ``namespace``→``project_namespace`` to avoid colliding with the inherited
    # base field ``target_namespace`` (alias ``namespace``); CLI flag stays ``--ns``.
    project_namespace: Annotated[
        str,
        m.Field(
            alias="ns",
            description="Facade namespace slot (default: class stem minus 'Flext').",
        ),
    ] = ""
    description: Annotated[
        str,
        m.Field(default="", description="Project description (default: derived)."),
    ] = ""
    # NOTE(mro-wkii.14, agent codegen): default version vem de settings.Infra
    # .flext_version (metadados do flext-infra = "0.12.0-dev") — operator directive:
    # version NUNCA constante/hardcoded, sempre settings. --version sobrescreve.
    version: Annotated[
        str,
        m.Field(
            description="Initial project version (default: settings.Infra.flext_version).",
        ),
    ] = settings.Infra.flext_version
    python_version: Annotated[
        str,
        m.Field(
            default="3.13", description="Python version (x.y) for generated files."
        ),
    ] = "3.13"
    author_name: Annotated[
        str,
        m.Field(default="FLEXT Team", description="Author/maintainer display name."),
    ] = "FLEXT Team"
    author_email: Annotated[
        str,
        m.Field(default="team@flext.dev", description="Author/maintainer email."),
    ] = "team@flext.dev"
    repository: Annotated[
        str,
        m.Field(
            default="",
            description="Repository URL (default: https://github.com/flext/<name>).",
        ),
    ] = ""
    upstream: Annotated[
        str,
        m.Field(
            default="flext_cli",
            description="Upstream facade module (flext_core / flext_cli).",
        ),
    ] = "flext_cli"

    @override
    def execute(self) -> p.Result[m.Infra.ProjectNewResult]:
        """Render the manifest into ``output_root`` and return the typed report."""
        # NOTE (multi-agent, mro-wkii.14 / agent: codegen): the inherited
        # ``use_enum_values=True`` stores ``self.kind`` as its str value; rehydrate
        # the enum at the boundary so ``entries_for`` (frozenset[ProjectKind]) and
        # ``ProjectNewResult.kind`` stay type-correct at runtime (pyrefly trusts the
        # annotation and cannot see this — caught only by real execution).
        kind = c.Infra.ProjectKind(self.kind)
        ctx = self._context()
        templates_root = self._templates_root()
        if not templates_root.is_dir():
            return r[m.Infra.ProjectNewResult].fail(
                f"{c.Cli.ERR_TEMPLATE_NOT_FOUND}: {templates_root}",
            )
        manifest = m.Infra.ProjectTemplateManifest.from_raw(
            c.Infra.PROJECT_TEMPLATE_ENTRIES,
        )
        # NOTE (multi-agent, mro-wkii.14 / agent: codegen): ancoragem por kind.
        # external  => output_root E o project root. internal => output_root e a
        # raiz do WORKSPACE; o membro vive em "<ws>/<dist>/" e so as deltas de
        # registro (projects/<dist>.md, REGISTRATION.md, kinds=={INTERNAL}) ficam
        # na raiz do workspace. Sem isso, src/tests/pyproject/Makefile eram
        # espalhados na raiz do workspace (defeito "arquivo no lugar errado").
        workspace_root = self.output_root
        project_root = (
            workspace_root / self.name
            if kind is c.Infra.ProjectKind.INTERNAL
            else workspace_root
        )
        ws_only: frozenset[c.Infra.ProjectKind] = frozenset(
            {c.Infra.ProjectKind.INTERNAL},
        )
        path_ctx: dict[str, str] = {
            key: value for key, value in ctx.items() if isinstance(value, str)
        }
        project_entries: list[m.Cli.TemplateRenderEntry] = []
        workspace_entries: list[m.Cli.TemplateRenderEntry] = []
        for entry in manifest.entries:
            if entry.delegate != "render" or kind not in entry.kinds:
                continue
            cli_entry = entry.to_cli(path_ctx)
            if entry.kinds == ws_only:
                workspace_entries.append(cli_entry)
            else:
                project_entries.append(cli_entry)

        def _planned(
            root: Path,
            group: t.SequenceOf[m.Cli.TemplateRenderEntry],
        ) -> tuple[str, ...]:
            return tuple(str(root / e.output_relpath) for e in group)

        if self.effective_dry_run:
            planned = _planned(project_root, project_entries) + _planned(
                workspace_root,
                workspace_entries,
            )
            result = m.Infra.ProjectNewResult(
                project=self.name,
                kind=kind,
                root=project_root,
                files_created=planned,
                files_skipped=(),
                failed=(),
            )
            return r[m.Infra.ProjectNewResult].ok(result)

        created: list[str] = []
        skipped: list[str] = []
        failed: list[tuple[str, str]] = []
        for root, group in (
            (project_root, project_entries),
            (workspace_root, workspace_entries),
        ):
            if not group:
                continue
            rendered = u.Cli.template_render_dir(
                templates_root,
                root,
                ctx,
                tuple(group),
                overwrite=False,
            )
            if rendered.failure:
                return r[m.Infra.ProjectNewResult].fail(
                    rendered.error or c.Cli.ERR_TEMPLATE_RENDER_FAILED,
                )
            report = rendered.value
            created.extend(str(p) for p in report.created)
            skipped.extend(str(p) for p in report.skipped)
            failed.extend((str(p), err) for p, err in report.failed)
        result = m.Infra.ProjectNewResult(
            project=self.name,
            kind=kind,
            root=project_root,
            files_created=tuple(created),
            files_skipped=tuple(skipped),
            failed=tuple(failed),
        )
        return r[m.Infra.ProjectNewResult].ok(result)

    def _templates_root(self) -> Path:
        """Locate the bundled ``templates/project`` directory of flext-infra.

        Derived from ``__file__`` (this module lives under ``flext_infra/codegen/``),
        so there is no lazy self-import and no ``# noqa`` (flext-law §1.8/§5.2).
        """
        return (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATES_PROJECT_DIR
        )

    def _context(self) -> t.JsonMapping:
        """Build the full render context from canonical name helpers (ADR-005 §9).

        ``class_stem`` is derived ONLY through ``u.derive_class_stem`` (the SSOT);
        ``ns``/``alias``/``env_prefix`` are deterministic transforms of it and of
        the package name — never a parallel name detection.
        """
        dist = self.name
        package_name = self.package_name or dist.replace("-", "_")
        class_stem = u.derive_class_stem(dist)
        ns = self.project_namespace or self._derive_namespace(class_stem)
        alias = self._derive_alias(package_name)
        repository = self.repository or f"https://github.com/flext/{dist}"
        kind = c.Infra.ProjectKind(self.kind)
        make_profile = (
            c.Infra.MakeProfile.WORKSPACE_MEMBER
            if kind is c.Infra.ProjectKind.INTERNAL
            else c.Infra.MakeProfile.STANDALONE
        )
        # NOTE (multi-agent, mro-wkii.17 / agent: codex): profile/topology are
        # mandatory template inputs. New internal projects are dual-mode members
        # rooted one level above; external projects never discover siblings.
        ctx: dict[str, t.JsonValue] = {
            "dist": dist,
            "const_name": dist,
            "package_name": package_name,
            "class_stem": class_stem,
            "ns": ns,
            "ns_attr": ns.lower(),
            "alias": alias,
            "env_prefix": f"{package_name.upper()}_",
            "upstream": self.upstream,
            "description": (
                self.description or f"{class_stem} — FLEXT typed integration package"
            ),
            "version": self.version,
            # NOTE(mro-wkii.14, agent codegen): license parametrized (was hardcoded
            # "MIT" in pyproject.toml.j2); ctx is dict[str,str] so string is fine.
            "license": "MIT",
            "python_version": self.python_version,
            "python_requires": f">={self.python_version}",
            "author_name": self.author_name,
            "author_email": self.author_email,
            "repository": repository,
            # NOTE(mro-wkii.13, agent codegen): git base URL (org flext-sh) +
            # default branch from settings.Infra.flext_git_branch (= package
            # version "0.12.0-dev"); consumed by pyproject.toml.j2/Makefile.j2.
            "flext_git_base_url": "https://github.com/flext-sh",
            "flext_git_branch": settings.Infra.flext_git_branch,
            "make_profile": make_profile.value,
            "workspace_root_rel": (
                ".." if make_profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else "."
            ),
            "workspace_members": [],
            "workspace_repositories": [],
            "homepage": repository,
            "documentation": repository,
            "year": str(datetime.now(UTC).year),
            "project_kind": kind.value,
        }
        return ctx

    @staticmethod
    def _derive_namespace(class_stem: str) -> str:
        """``FlextDemo`` → ``Demo``; a non-``Flext`` stem stays as-is."""
        prefix = "Flext"
        if class_stem.startswith(prefix) and len(class_stem) > len(prefix):
            return class_stem[len(prefix) :]
        return class_stem

    @staticmethod
    def _derive_alias(package_name: str) -> str:
        """``flext_demo`` → ``demo``; otherwise the package name unchanged."""
        prefix = "flext_"
        if package_name.startswith(prefix) and len(package_name) > len(prefix):
            return package_name[len(prefix) :]
        return package_name


__all__: list[str] = ["FlextInfraCodegenProjectNew"]
