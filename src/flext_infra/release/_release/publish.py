"""Release publish phase: upload exactly what the build receipt attests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from flext_infra import c, config, m, p, r, u
from flext_infra.release._release import FlextInfraReleaseReleaseBuild


class FlextInfraReleaseReleasePublish(FlextInfraReleaseReleaseBuild):
    """Publish the receipt's artifacts, re-hashed, as a GitHub release and to the index.

    The package index receives them in dependency order, so a dependent
    never precedes its dependency.
    """

    def phase_publish(
        self,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge | None,
    ) -> p.Result[bool]:
        """Publish receipt artifacts as a GitHub release and, if asked, the index.

        ``forge`` is the release forge port bound at the composition root;
        its absence fails before any effect.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if forge is None:
            return r[bool].fail("release forge port is not bound")
        if ctx.index and not config.Infra.release.publish_index:
            return r[bool].fail(
                "package index publication is disabled by release policy"
            )
        receipt = self._verified_receipt(ctx)
        if receipt.failure:
            return r[bool].from_failure(receipt)
        if not ctx.dry_run:
            released = self._github_release(ctx, receipt.value, forge)
            if released.failure:
                return released
            if ctx.index:
                uploaded = self._index_upload(ctx, receipt.value)
                if uploaded.failure:
                    return uploaded
        self.logger.info(
            "release_phase_publish",
            tag=ctx.tag,
            dry_run=ctx.dry_run,
            index=ctx.index,
        )
        return r[bool].ok(value=True)

    def _verified_receipt(
        self,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
    ) -> p.Result[p.Infra.BuildReport]:
        """Load the receipt and prove every artifact still matches its digest.

        Returns:
            The resulting ``p.Result[p.Infra.BuildReport]``.

        """
        path = (
            self._release_dir(ctx.repository_root, ctx.tag)
            / c.Infra.RELEASE_REPORT_FILENAME
        )
        content = u.Cli.files_read_text(path)
        if content.failure:
            return r[p.Infra.BuildReport].from_failure(content)
        report: p.Result[p.Infra.BuildReport] = u.validate_value(
            m.Infra.BuildReport,
            content.value,
            from_json=True,
        )
        if report.failure:
            return r[p.Infra.BuildReport].fail_op(
                "validate release receipt",
                report.error,
            )
        if (
            report.value.dry_run
            or report.value.failures
            or report.value.version != ctx.version
        ):
            return r[p.Infra.BuildReport].fail(
                f"release receipt is not publishable for {ctx.version}: {path}",
            )
        for artifact in (
            a for record in report.value.records for a in record.artifacts
        ):
            try:
                digest = u.Cli.sha256_file(Path(artifact.path))
            except OSError as exc:
                return r[p.Infra.BuildReport].fail_op(
                    f"read artifact {artifact.path}",
                    exc,
                )
            if digest != artifact.sha256:
                return r[p.Infra.BuildReport].fail(
                    f"artifact digest differs from receipt: {artifact.path}",
                )
        return self._verified_sources(ctx, report.value).map(lambda _: report.value)

    @staticmethod
    def _verified_sources(
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        report: p.Infra.BuildReport,
    ) -> p.Result[bool]:
        """Bind source receipts to the tagged candidate, never mutable HEAD.

        Returns:
            Success only when every source belongs to the tagged candidate.

        """
        root = ctx.repository_root.resolve()
        tagged = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", f"refs/tags/{ctx.tag}^{{commit}}"],
            cwd=root,
        )
        if tagged.failure:
            return r[bool].from_failure(tagged)
        for record in report.records:
            project = Path(record.path).resolve()
            if not project.is_relative_to(root):
                return r[bool].fail(f"release source is outside repository: {project}")
            expected = tagged.value.strip()
            if project != root:
                relative = project.relative_to(root).as_posix()
                entry = u.Cli.capture(
                    [c.Infra.GIT, "ls-tree", tagged.value.strip(), "--", relative],
                    cwd=root,
                )
                if entry.failure:
                    return r[bool].from_failure(entry)
                metadata, _, name = entry.value.strip().partition("\t")
                mode, _, rest = metadata.partition(" ")
                kind, _, oid = rest.partition(" ")
                if mode != "160000" or kind != "commit" or name != relative:
                    return r[bool].fail(
                        f"release tag does not attest member gitlink: {relative}",
                    )
                expected = oid
            if record.commit_oid != expected:
                return r[bool].fail(
                    f"release source commit differs from tag {ctx.tag}: "
                    f"{record.project}",
                )
        return r[bool].ok(value=True)

    @classmethod
    def _github_release(
        cls,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        report: p.Infra.BuildReport,
        forge: p.Infra.ReleaseForge,
    ) -> p.Result[bool]:
        """Stage the release as a draft and publish it as the single commit point.

        A missing release is created as a draft; only missing artifacts are
        uploaded and every asset is verified before the draft becomes public.
        A published release is immutable: identical assets are a no-op and
        any absent or differing asset fails without remote effects.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = ctx.repository_root
        artifacts = [a for record in report.records for a in record.artifacts]
        release = cls._github_release_identity(ctx, forge)
        if release.failure:
            return r[bool].from_failure(release)
        identity = release.value
        if identity is None:
            notes = root / c.Infra.DIR_DOCS / "releases" / f"{ctx.tag}.md"
            admitted = u.Infra.release_body_admitted(notes)
            if admitted.failure:
                return admitted
            created = forge.release_forge_create_draft(
                root,
                ctx.tag,
                f"Release {ctx.tag}",
                notes,
            )
            if created.failure:
                return created
            release = cls._github_release_identity(ctx, forge)
            if release.failure:
                return r[bool].from_failure(release)
            identity = release.value
            if identity is None or not identity.draft:
                return r[bool].fail(f"draft release was not created: {ctx.tag}")
        return cls._github_publish_verified(ctx, forge, identity, artifacts)

    @classmethod
    def _github_publish_verified(
        cls,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge,
        identity: p.Infra.GithubReleaseIdentity,
        artifacts: Sequence[p.Infra.BuildArtifact],
    ) -> p.Result[bool]:
        """Complete and verify a draft, then publish it; never mutate a release.

        Returns:
            Success after publication, or for an identical published release.

        """
        missing = cls._github_missing_assets(ctx, forge, identity.id, artifacts)
        if missing.failure:
            return r[bool].from_failure(missing)
        if not identity.draft:
            if missing.value:
                return r[bool].fail(
                    f"published release {ctx.tag} lacks attested assets: "
                    + ", ".join(Path(path).name for path in missing.value),
                )
            return r[bool].ok(value=True)
        if missing.value:
            completed = cls._github_complete_draft(
                ctx,
                forge,
                identity.id,
                artifacts,
                missing.value,
            )
            if completed.failure:
                return completed
        return forge.release_forge_publish(ctx.repository_root, ctx.tag)

    @classmethod
    def _github_complete_draft(
        cls,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge,
        release_id: int,
        artifacts: Sequence[p.Infra.BuildArtifact],
        missing: Sequence[str],
    ) -> p.Result[bool]:
        """Upload missing artifacts to the draft and re-verify every asset.

        Returns:
            Success only when the draft holds every attested asset, verified.

        """
        uploaded = forge.release_forge_upload(ctx.repository_root, ctx.tag, missing)
        if uploaded.failure:
            return uploaded
        remaining = cls._github_missing_assets(ctx, forge, release_id, artifacts)
        if remaining.failure:
            return r[bool].from_failure(remaining)
        if remaining.value:
            return r[bool].fail(
                f"draft release {ctx.tag} still lacks uploaded assets: "
                + ", ".join(Path(path).name for path in remaining.value),
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _github_release_identity(
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge,
    ) -> p.Result[p.Infra.GithubReleaseIdentity | None]:
        """Select the release for the tag only after proving the remote tag.

        Returns:
            The single release for the tag, explicit absence, or the first failure.

        """
        result_type = r[p.Infra.GithubReleaseIdentity | None]
        root = ctx.repository_root
        tagged = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", f"refs/tags/{ctx.tag}^{{commit}}"],
            cwd=root,
        )
        if tagged.failure:
            return result_type.from_failure(tagged)
        remote_commit = forge.release_forge_tag_commit(root, ctx.tag)
        if remote_commit.failure:
            return result_type.from_failure(remote_commit)
        if remote_commit.value.strip() != tagged.value.strip():
            return result_type.fail(
                f"remote release tag differs from candidate: {ctx.tag}",
            )
        inventory = forge.release_forge_releases(root)
        if inventory.failure:
            return result_type.from_failure(inventory)
        existing = [
            release
            for release in inventory.value.releases
            if release.tag_name == ctx.tag
        ]
        if len(existing) > 1:
            return result_type.fail(f"duplicate remote release tag: {ctx.tag}")
        return result_type.ok(existing[0] if existing else None)

    @classmethod
    def _github_missing_assets(
        cls,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge,
        release_id: int,
        artifacts: Sequence[p.Infra.BuildArtifact],
    ) -> p.Result[Sequence[str]]:
        """Verify every remote asset against the receipt before any mutation.

        Returns:
            Missing local artifact paths only after existing assets are verified.

        """
        result_type = r[Sequence[str]]
        parsed = forge.release_forge_assets(ctx.repository_root, release_id)
        if parsed.failure:
            return result_type.from_failure(parsed)
        remote = {asset.name: asset for asset in parsed.value.assets}
        if len(remote) != len(parsed.value.assets):
            return result_type.fail("remote release contains duplicate asset names")
        attested = {Path(artifact.path).name for artifact in artifacts}
        unexpected = sorted(set(remote) - attested)
        if unexpected:
            return result_type.fail(
                "remote release contains assets the receipt does not attest: "
                + ", ".join(unexpected),
            )
        missing: MutableSequence[str] = []
        for artifact in artifacts:
            asset = remote.get(Path(artifact.path).name)
            if asset is None:
                missing.append(artifact.path)
            else:
                verified = cls._verified_remote_asset(ctx, forge, asset, artifact)
                if verified.failure:
                    return result_type.from_failure(verified)
        return result_type.ok(missing)

    @classmethod
    def _verified_remote_asset(
        cls,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge,
        asset: p.Infra.GithubReleaseAsset,
        artifact: p.Infra.BuildArtifact,
    ) -> p.Result[bool]:
        """Compare native digest or downloaded bytes to the attested digest.

        Returns:
            Success only for a completely uploaded, identical asset.

        """
        if asset.state != "uploaded":
            return r[bool].fail(f"remote release asset is not uploaded: {asset.name}")
        digest = asset.digest
        if digest is None:
            downloaded = cls._downloaded_asset_digest(ctx, forge, asset.name)
            if downloaded.failure:
                return r[bool].from_failure(downloaded)
            digest = f"sha256:{downloaded.value}"
        if digest != f"sha256:{artifact.sha256}":
            return r[bool].fail(
                f"remote release asset digest differs from receipt: {asset.name}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _downloaded_asset_digest(
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        forge: p.Infra.ReleaseForge,
        name: str,
    ) -> p.Result[str]:
        """Hash downloaded bytes when GitHub provides no native digest.

        Returns:
            The downloaded file's SHA-256, never an assumed match.

        """
        try:
            directory = FlextInfraReleaseReleasePublish._release_dir(
                ctx.repository_root,
                ctx.tag,
            )
            with TemporaryDirectory(dir=directory) as temporary:
                destination = Path(temporary) / "asset"
                downloaded = forge.release_forge_download(
                    ctx.repository_root,
                    ctx.tag,
                    name,
                    destination,
                )
                if downloaded.failure:
                    return r[str].from_failure(downloaded)
                return r[str].ok(u.Cli.sha256_file(destination))
        except OSError as exc:
            return r[str].fail_op(f"hash remote release asset {name}", exc)

    def _index_upload(
        self,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        report: p.Infra.BuildReport,
    ) -> p.Result[bool]:
        """Upload verified artifacts wave by wave through trusted publishing.

        ``--check-url`` skips files already on the index, so a rerun after a
        partial failure resumes instead of failing on the first duplicate.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        artifacts = {
            record.project: tuple(a.path for a in record.artifacts)
            for record in report.records
        }
        waves = u.Infra.release_publish_waves(
            tuple((record.project, Path(record.path)) for record in report.records),
        )
        if waves.failure:
            return r[bool].from_failure(waves)
        for wave in waves.value:
            uploaded = u.Cli.run_checked(
                [
                    c.Infra.UV,
                    "publish",
                    "--no-config",
                    "--publish-url",
                    config.Infra.release.publish_url,
                    "--check-url",
                    c.Infra.PYPI_SIMPLE_INDEX_URL,
                    "--trusted-publishing",
                    "always",
                    *(path for project in wave for path in artifacts[project]),
                ],
                cwd=ctx.repository_root,
            )
            if uploaded.failure:
                return uploaded
            self.logger.info("release_index_wave_published", projects=", ".join(wave))
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraReleaseReleasePublish"]
