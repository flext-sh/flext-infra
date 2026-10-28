"""Versioning utilities for semantic version management.

All methods are static — exposed via u.Infra.parse_semver() etc. through FLEXT.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_cli import u
from packaging.version import InvalidVersion, Version

from flext_infra import c, m, p, r, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesVersioning:
    """Static versioning utilities for semantic version management.

    All methods are ``@staticmethod`` — no instantiation required.
    Exposed via ``u.Infra.parse_semver()`` etc. through FLEXT.
    """

    @staticmethod
    def _project_document(
        content: str,
    ) -> p.Result[tuple[t.Cli.TomlDocument, t.Cli.TomlTable]]:
        """Parse one pyproject document with its live ``[project]`` table.

        Returns:
            The parsed document and its ``[project]`` table.

        """
        result = r[tuple[t.Cli.TomlDocument, t.Cli.TomlTable]]
        document = u.Cli.toml_parse_text(content)
        if document is None:
            return result.fail("invalid pyproject.toml")
        project = u.Cli.toml_table_child(document, c.Infra.PROJECT)
        if project is None:
            return result.fail("missing [project] table")
        return result.ok((document, project))

    @staticmethod
    def bump_version(
        version: str,
        bump_type: str | c.Infra.VersionBump,
    ) -> p.Result[str]:
        """Return the next release version for one bump kind.

        A pre-release (``0.12.0``) is finalized to its base release by any
        real bump: the base was already reserved when the pre-release was cut,
        so the first releasable change ships it. ``none`` returns the version
        unchanged for both shapes.

        Returns:
            The next release version for one bump kind.

        """
        try:
            normalized_bump = c.Infra.VersionBump(bump_type)
        except ValueError:
            return r[str].fail(f"invalid bump type: {bump_type}")
        result = FlextInfraUtilitiesVersioning.parse_semver(version)
        if result.failure:
            return r[str].from_failure(result)
        if normalized_bump == c.Infra.VersionBump.NONE:
            return r[str].ok(version)
        major, minor, patch = result.value
        if Version(version).is_prerelease:
            return r[str].ok(f"{major}.{minor}.{patch}")
        if normalized_bump == c.Infra.VersionBump.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif normalized_bump == c.Infra.VersionBump.MINOR:
            minor += 1
            patch = 0
        else:
            patch += 1
        return r[str].ok(f"{major}.{minor}.{patch}")

    @staticmethod
    def finalize_version(version: str) -> p.Result[str]:
        """Return the base release of ``version`` (a final version is itself).

        Returns:
            The base release of ``version`` (a final version is itself).

        """
        return FlextInfraUtilitiesVersioning.parse_semver(version).map(
            lambda parts: ".".join(str(segment) for segment in parts),
        )

    @staticmethod
    def current_workspace_version(repository_root: Path) -> p.Result[str]:
        """Read the current version from the main pyproject.toml.

        Args:
            repository_root: The root directory of the workspace.

        Returns:
            r[str] with the version string.

        """
        pyproject = repository_root / c.PYPROJECT_FILENAME
        try:
            content = pyproject.read_text(encoding=c.DEFAULT_ENCODING)
        except OSError as exc:
            return r[str].fail_op("read", exc)
        return FlextInfraUtilitiesVersioning.project_version_from_text(content)

    @staticmethod
    def project_version_from_text(content: str) -> p.Result[str]:
        """Read ``[project].version`` from one pyproject document's text.

        Returns:
            The declared project version.

        """
        parsed = FlextInfraUtilitiesVersioning._project_document(content)
        if parsed.failure:
            return r[str].from_failure(parsed)
        version = u.Cli.toml_value(parsed.value[1], c.Infra.VERSION)
        if not isinstance(version, str) or not version.strip():
            return r[str].fail("version not found in pyproject.toml")
        return r[str].ok(version)

    @staticmethod
    def parse_semver(version: str) -> p.Result[tuple[int, int, int]]:
        """Parse one canonical FLEXT PEP 440 version into its release tuple.

        Args:
            version: The version string to parse.

        Returns:
            r with version tuple.

        """
        try:
            parsed = Version(version)
        except InvalidVersion:
            return r[tuple[int, int, int]].fail(f"invalid semver: {version}")
        unsupported = (
            str(parsed) != version
            or len(parsed.release) != c.Infra.VERSION_RELEASE_SEGMENTS
            or parsed.epoch != 0
            or parsed.post is not None
            or parsed.local is not None
            or (parsed.pre is not None and parsed.pre[0] != "rc")
            or (parsed.pre is not None and parsed.dev is not None)
            or (parsed.dev is not None and parsed.dev != 0)
        )
        if unsupported:
            return r[tuple[int, int, int]].fail(f"invalid semver: {version}")
        major, minor, patch = parsed.release
        return r[tuple[int, int, int]].ok((major, minor, patch))

    @staticmethod
    def version_is_newer(candidate: str, reference: str) -> p.Result[bool]:
        """Whether ``candidate`` orders after ``reference`` under PEP 440.

        Pre-release segments take part in the ordering: ``0.12.0`` is newer
        than ``0.12.0rc2`` although both share the release triple.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        try:
            return r[bool].ok(Version(candidate) > Version(reference))
        except InvalidVersion as exc:
            return r[bool].fail(f"invalid version: {exc}", exception=exc)

    @staticmethod
    def latest_release_tag(tags: Sequence[str]) -> p.Result[str]:
        """Return the highest release tag under PEP 440, or ``""`` when none exist.

        Git's ``--sort=version:refname`` is a refname collation, not a PEP 440
        ordering: it places ``v0.12.0rc2`` above ``v0.12.0`` because the longer
        refname collates later. The release protocol then read the newest
        release as a release candidate, decided the released version still
        "awaits its tag", and never bumped again in any repository that had
        ever cut an rc. Order by the same PEP 440 owner
        ``version_is_newer`` already uses, and fail loud on a ``v*`` tag that
        is not a version rather than silently ranking it.

        Returns:
            The highest release tag under PEP 440, or ``""`` when none exist.

        """
        prefix = c.Infra.TAG_FORMAT.format(version="")
        highest_version: Version | None = None
        highest_tag = ""
        for raw_tag in tags:
            tag = raw_tag.strip()
            if not tag:
                continue
            remainder = tag.removeprefix(prefix)
            if not remainder[:1].isdigit():
                # Foreign tag namespace — cycle-control markers (val*), fork
                # tags, anything that only collides with the prefix. Those are
                # not release candidates, so skipping keeps them out of the
                # ranking; a tag that LOOKS like a version (digit-leading) but
                # does not parse still fails loud below.
                continue
            try:
                parsed = Version(remainder)
            except InvalidVersion as exc:
                return r[str].fail(f"invalid release tag {tag}: {exc}")
            if highest_version is None or parsed > highest_version:
                highest_version = parsed
                highest_tag = tag
        return r[str].ok(highest_tag)

    @staticmethod
    def render_project_version(content: str, version: str) -> p.Result[str]:
        """Render one canonical project-version update without writing it.

        Returns:
            The resulting ``p.Result[str]``.

        """
        version_result = FlextInfraUtilitiesVersioning.parse_semver(version)
        if version_result.failure:
            return r[str].from_failure(version_result)
        parsed = FlextInfraUtilitiesVersioning._project_document(content)
        if parsed.failure:
            return r[str].from_failure(parsed)
        document, project = parsed.value
        if u.Cli.toml_item_child(project, c.Infra.VERSION) is None:
            return r[str].fail("missing [project] version")
        u.Cli.toml_sync_value(project, c.Infra.VERSION, version)
        return r[str].ok(u.Cli.toml_dumps(document))

    @staticmethod
    def project_version_plan(
        project_path: Path, version: str
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Plan the canonical version-field edit against its actual physical input.

        Returns:
            The original file witness and exact rendered bytes, without effects.

        """
        result = r[m.Infra.CodegenFilePlan]
        root = project_path.resolve()
        captured = u.Cli.atomic_read_binary_file_state(
            root / c.PYPROJECT_FILENAME, required=True
        )
        if captured.failure:
            return result.from_failure(captured)
        if captured.value.content is None:
            return result.fail("project version requires its actual file preimage")
        try:
            content = captured.value.content.decode(c.DEFAULT_ENCODING)
        except UnicodeError as exc:
            return result.fail_op("read project version", exc)
        rendered = FlextInfraUtilitiesVersioning.render_project_version(
            content, version
        )
        if rendered.failure:
            return result.from_failure(rendered)
        return result.ok(
            m.Infra.CodegenFilePlan(
                project=root,
                path=captured.value.path,
                before=captured.value,
                desired_content=rendered.value.encode(c.DEFAULT_ENCODING),
                desired_mode=captured.value.mode,
            )
        )

    @staticmethod
    def replace_project_version(project_path: Path, version: str) -> p.Result[bool]:
        """Publish the same version plan through the existing boolean file API.

        Returns:
            The guarded atomic writer result; this is not Git publication authority.

        """
        planned = FlextInfraUtilitiesVersioning.project_version_plan(
            project_path, version
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        if planned.value.desired_content is None:
            return r[bool].fail("project version plan cannot delete its version anchor")
        before = planned.value.before
        written = u.Cli.atomic_write_binary_file_guarded(
            before,
            planned.value.desired_content,
            permission_mode=before.mode,
        )
        if written.failure:
            return written
        # Why: flext-core caches the parsed pyproject per process. This is the
        # protocol's only writer of the version, and the docs projections
        # rendered right after the stamp must see the stamped version, not
        # the document read before it (flext-cli#129 drifted that way).
        u.read_project_document_cached.cache_clear()
        return written


__all__: list[str] = ["FlextInfraUtilitiesVersioning"]
