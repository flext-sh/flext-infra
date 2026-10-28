"""Release publish phase: upload exactly what the build receipt attests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from glob import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from flext_infra import c, config, m, p, r, t, u
from flext_infra.release import FlextInfraReleaseReleaseBuild


class FlextInfraReleaseReleasePublish(FlextInfraReleaseReleaseBuild):
    """Publish the receipt's artifacts, re-hashed, as a GitHub release and to the index.

    The package index receives them in dependency order, so a dependent
    never precedes its dependency.
    """

    def phase_publish(self, ctx: m.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
        """Publish receipt artifacts as a GitHub release and, if asked, the index.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if ctx.index and not config.Infra.release.publish_index:
            return r[bool].fail(
                "package index publication is disabled by release policy"
            )
        receipt = self._verified_receipt(ctx)
        if receipt.failure:
            return r[bool].from_failure(receipt)
        if not ctx.dry_run:
            released = self._github_release(ctx, receipt.value)
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
        ctx: m.Infra.ReleasePhaseDispatchConfig,
    ) -> p.Result[m.Infra.BuildReport]:
        """Load the receipt and prove every artifact still matches its digest.

        Returns:
            The resulting ``p.Result[m.Infra.BuildReport]``.

        """
        path = (
            self._release_dir(ctx.repository_root, ctx.tag)
            / c.Infra.RELEASE_REPORT_FILENAME
        )
        content = u.Cli.files_read_text(path)
        if content.failure:
            return r[m.Infra.BuildReport].from_failure(content)
        report: p.Result[m.Infra.BuildReport] = u.validate_value(
            m.Infra.BuildReport,
            content.value,
            from_json=True,
        )
        if report.failure:
            return r[m.Infra.BuildReport].fail_op(
                "validate release receipt",
                report.error,
            )
        if (
            report.value.dry_run
            or report.value.failures
            or report.value.version != ctx.version
        ):
            return r[m.Infra.BuildReport].fail(
                f"release receipt is not publishable for {ctx.version}: {path}",
            )
        for artifact in (
            a for record in report.value.records for a in record.artifacts
        ):
            try:
                digest = u.Cli.sha256_file(Path(artifact.path))
            except OSError as exc:
                return r[m.Infra.BuildReport].fail_op(
                    f"read artifact {artifact.path}",
                    exc,
                )
            if digest != artifact.sha256:
                return r[m.Infra.BuildReport].fail(
                    f"artifact digest differs from receipt: {artifact.path}",
                )
        return self._verified_sources(ctx, report.value).map(lambda _: report.value)

    @staticmethod
    def _verified_sources(
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        report: m.Infra.BuildReport,
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
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        report: m.Infra.BuildReport,
    ) -> p.Result[bool]:
        """Verify all existing assets before uploading only missing artifacts.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = ctx.repository_root
        artifacts = [a for record in report.records for a in record.artifacts]
        releases = cls._github_inventory(ctx)
        if releases.failure:
            return r[bool].from_failure(releases)
        existing = [
            release
            for release in releases.value.releases
            if release.tag_name == ctx.tag
        ]
        if len(existing) > 1:
            return r[bool].fail(f"duplicate remote release tag: {ctx.tag}")
        if existing:
            missing = cls._github_missing_assets(ctx, existing[0].id, artifacts)
            if missing.failure:
                return r[bool].from_failure(missing)
            if not missing.value:
                return r[bool].ok(value=True)
            return u.Cli.run_checked(
                [c.Infra.GH, "release", "upload", ctx.tag, *missing.value],
                cwd=root,
            )
        notes = root / c.Infra.DIR_DOCS / "releases" / f"{ctx.tag}.md"
        return u.Cli.run_checked(
            [
                c.Infra.GH,
                "release",
                "create",
                ctx.tag,
                *(artifact.path for artifact in artifacts),
                "--verify-tag",
                "--title",
                f"Release {ctx.tag}",
                "--notes-file",
                str(notes),
            ],
            cwd=root,
        )

    @staticmethod
    def _github_inventory(
        ctx: m.Infra.ReleasePhaseDispatchConfig,
    ) -> p.Result[m.Infra.GithubReleaseInventory]:
        """Read releases only after proving the remote candidate tag.

        Returns:
            The complete typed release inventory, or the first read failure.

        """
        result_type = r[m.Infra.GithubReleaseInventory]
        root = ctx.repository_root
        tagged = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", f"refs/tags/{ctx.tag}^{{commit}}"],
            cwd=root,
        )
        if tagged.failure:
            return result_type.from_failure(tagged)
        remote_commit = u.Cli.capture(
            [
                c.Infra.GH,
                "api",
                f"repos/{{owner}}/{{repo}}/commits/{ctx.tag}",
                "--jq",
                ".sha",
            ],
            cwd=root,
        )
        if remote_commit.failure:
            return result_type.from_failure(remote_commit)
        if remote_commit.value.strip() != tagged.value.strip():
            return result_type.fail(
                f"remote release tag differs from candidate: {ctx.tag}",
            )
        inventory = u.Cli.capture(
            [
                c.Infra.GH,
                "api",
                "repos/{owner}/{repo}/releases",
                "--paginate",
                "--slurp",
                "--jq",
                "{releases: [.[][] | {id, tag_name}]}",
            ],
            cwd=root,
        )
        if inventory.failure:
            return result_type.from_failure(inventory)
        return u.validate_value(
            m.Infra.GithubReleaseInventory,
            inventory.value,
            from_json=True,
        )

    @classmethod
    def _github_missing_assets(
        cls,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        release_id: int,
        artifacts: t.SequenceOf[m.Infra.BuildArtifact],
    ) -> p.Result[t.StrSequence]:
        """Preflight the full upload set before the first remote mutation.

        Returns:
            Missing local artifact paths only after existing assets are verified.

        """
        result_type = r[t.StrSequence]
        inventory = u.Cli.capture(
            [
                c.Infra.GH,
                "api",
                f"repos/{{owner}}/{{repo}}/releases/{release_id}/assets",
                "--paginate",
                "--slurp",
                "--jq",
                "{assets: [.[][] | {name, digest, state}]}",
            ],
            cwd=ctx.repository_root,
        )
        if inventory.failure:
            return result_type.from_failure(inventory)
        parsed: p.Result[m.Infra.GithubReleaseAssets] = u.validate_value(
            m.Infra.GithubReleaseAssets,
            inventory.value,
            from_json=True,
        )
        if parsed.failure:
            return result_type.from_failure(parsed)
        remote = {asset.name: asset for asset in parsed.value.assets}
        if len(remote) != len(parsed.value.assets):
            return result_type.fail("remote release contains duplicate asset names")
        missing: t.MutableSequenceOf[str] = []
        for artifact in artifacts:
            asset = remote.get(Path(artifact.path).name)
            if asset is None:
                missing.append(artifact.path)
            else:
                verified = cls._verified_remote_asset(ctx, asset, artifact)
                if verified.failure:
                    return result_type.from_failure(verified)
        return result_type.ok(missing)

    @classmethod
    def _verified_remote_asset(
        cls,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        asset: m.Infra.GithubReleaseAsset,
        artifact: m.Infra.BuildArtifact,
    ) -> p.Result[bool]:
        """Compare native digest or downloaded bytes to the attested digest.

        Returns:
            Success only for a completely uploaded, identical asset.

        """
        if asset.state != "uploaded":
            return r[bool].fail(f"remote release asset is not uploaded: {asset.name}")
        digest = asset.digest
        if digest is None:
            downloaded = cls._downloaded_asset_digest(ctx, asset.name)
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
        ctx: m.Infra.ReleasePhaseDispatchConfig,
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
                downloaded = u.Cli.run_checked(
                    [
                        c.Infra.GH,
                        "release",
                        "download",
                        ctx.tag,
                        "--pattern",
                        escape(name),
                        "--output",
                        str(destination),
                    ],
                    cwd=ctx.repository_root,
                )
                if downloaded.failure:
                    return r[str].from_failure(downloaded)
                return r[str].ok(u.Cli.sha256_file(destination))
        except OSError as exc:
            return r[str].fail_op(f"hash remote release asset {name}", exc)

    def _index_upload(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        report: m.Infra.BuildReport,
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
