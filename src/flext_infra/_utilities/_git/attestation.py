"""SSH-signed Git gate attestation owner."""

from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime
import hashlib
import re
from typing import TYPE_CHECKING

from git import GitCommandError

from flext_cli import u
from flext_core import r
from flext_infra._utilities._git.semantic_identity import (
    FlextInfraUtilitiesGitSemanticIdentityMixin,
)
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra import p, t

_TAG_PREFIX = "attest/gates/v1"
_SSH_SIGNATURE_MARKER = "\n-----BEGIN SSH SIGNATURE-----"
_PROMOTION_MANIFEST = ".github/attestations/promotion-sources.json"


class FlextInfraUtilitiesGitAttestationMixin(
    FlextInfraUtilitiesGitSemanticIdentityMixin
):
    """Create and verify immutable SSH-signed gate tags."""

    @staticmethod
    def _attestation_tag(commit_sha: str) -> str:
        return f"{_TAG_PREFIX}/{commit_sha}"

    @classmethod
    def _attestation_predicate(
        cls, request: m.Infra.GateAttestationCreateRequest
    ) -> p.Result[m.Infra.GateAttestationPredicate]:
        repo_root = Path(request.workspace).expanduser().resolve()
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=repo_root))
        if identity.failure:
            return r[m.Infra.GateAttestationPredicate].fail(
                identity.error or "failed to resolve Git identity"
            )
        repo = cls._repo(repo_root)
        if repo.is_dirty(untracked_files=False):
            return r[m.Infra.GateAttestationPredicate].fail(
                "gate attestation requires a clean committed worktree"
            )
        evidence_result = cls._run_gate_evidence(repo_root, request.gates)
        if evidence_result.failure:
            return r[m.Infra.GateAttestationPredicate].fail(
                evidence_result.error or "local gate execution failed"
            )
        sources_result = cls._promotion_sources(repo_root)
        if sources_result.failure:
            return r[m.Infra.GateAttestationPredicate].fail(
                sources_result.error or "invalid promotion source manifest"
            )
        toolchain = cls._toolchain_digest(repo_root)
        predicate = m.Infra.GateAttestationPredicate(
            schema_version="https://flext.sh/attestations/gates/v1",
            repository=identity.value.origin_remote or "",
            commit_sha=identity.value.head_oid,
            tree_sha=repo.head.commit.tree.hexsha,
            bead=request.bead,
            pull_request=request.pull_request,
            integration_branch=request.integration_branch,
            sources=sources_result.value,
            signer=request.signer,
            toolchain_digest=toolchain,
            covered_gates=request.gates,
            commands=evidence_result.value,
        )
        return r[m.Infra.GateAttestationPredicate].ok(predicate)

    @classmethod
    def _run_gate_evidence(
        cls, repo_root: Path, gates: t.StrSequence
    ) -> p.Result[tuple[m.Infra.GateCommandEvidence, ...]]:
        evidence: list[m.Infra.GateCommandEvidence] = []
        for gate in gates:
            command = f"make {gate}" if gate != "gen" else "make gen WHAT=check"
            started = datetime.now(UTC)
            outcome = u.Cli.run_raw(command.split(), cwd=repo_root)
            completed = datetime.now(UTC)
            if outcome.failure:
                return r[tuple[m.Infra.GateCommandEvidence, ...]].fail(
                    outcome.error or f"local gate failed: {command}"
                )
            output = outcome.value
            digest_input = (
                f"command={command}\nexit_code=0\n"
                f"stdout={output.stdout}\nstderr={output.stderr}"
            )
            digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
            evidence.append(m.Infra.GateCommandEvidence(
                gate=gate,
                command=command,
                cwd=str(repo_root),
                exit_code=0,
                result_digest=f"sha256:{digest}",
                started_at=started.isoformat().replace("+00:00", "Z"),
                completed_at=completed.isoformat().replace("+00:00", "Z"),
            ))
        return r[tuple[m.Infra.GateCommandEvidence, ...]].ok(tuple(evidence))

    @classmethod
    def _promotion_sources(
        cls, repo_root: Path
    ) -> p.Result[tuple[m.Infra.GatePromotionSource, ...]]:
        """Load the ordered source manifest from the exact committed tree."""
        repo = cls._repo(repo_root)
        try:
            blob = repo.head.commit.tree / _PROMOTION_MANIFEST
            content = blob.data_stream.read().decode("utf-8")
        except (KeyError, OSError, UnicodeError, ValueError) as exc:
            return r[tuple[m.Infra.GatePromotionSource, ...]].fail(str(exc))
        parsed = u.Cli.json_loads(content)
        if parsed.failure:
            return r[tuple[m.Infra.GatePromotionSource, ...]].fail(
                parsed.error or "promotion source manifest is not valid JSON"
            )
        if not isinstance(parsed.value, list) or not parsed.value:
            return r[tuple[m.Infra.GatePromotionSource, ...]].fail(
                "promotion source manifest must be a non-empty JSON array"
            )
        try:
            sources = tuple(
                m.Infra.GatePromotionSource.model_validate(item)
                for item in parsed.value
            )
        except ValueError as exc:
            return r[tuple[m.Infra.GatePromotionSource, ...]].fail(str(exc))
        merge_parents = {
            parent.hexsha
            for commit in repo.iter_commits(repo.head.commit)
            if len(commit.parents) > 1
            for parent in commit.parents[1:]
        }
        missing = tuple(source.head_sha for source in sources if source.head_sha not in merge_parents)
        if missing:
            return r[tuple[m.Infra.GatePromotionSource, ...]].fail(
                "promotion source is not a no-ff merge parent of HEAD: "
                + ", ".join(missing)
            )
        return r[tuple[m.Infra.GatePromotionSource, ...]].ok(sources)

    @classmethod
    def _toolchain_digest(cls, repo_root: Path) -> str:
        repo = cls._repo(repo_root)
        names = (".mise.toml", ".python-version", "pyproject.toml", "uv.lock")
        tracked: list[str] = []
        for name in names:
            try:
                blob = repo.head.commit.tree / name
            except KeyError:
                continue
            tracked.append(f"{name}:{blob.hexsha}")
        content = "\n".join(tracked)
        return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"

    @classmethod
    def git_create_gate_attestation(
        cls, request: m.Infra.GateAttestationCreateRequest
    ) -> p.Result[m.Infra.GateAttestationReport]:
        """Create the exact signed tag for a validated HEAD predicate."""
        repo_root = Path(request.workspace).expanduser().resolve()
        predicate_result = cls._attestation_predicate(request)
        if predicate_result.failure:
            return r[m.Infra.GateAttestationReport].fail(
                predicate_result.error or "invalid attestation predicate"
            )
        predicate = predicate_result.value
        tag = cls._attestation_tag(predicate.commit_sha)
        serialized = u.Cli.json_dumps(
            predicate.model_dump(mode="json"), sort_keys=True
        )
        if serialized.failure:
            return r[m.Infra.GateAttestationReport].fail(
                serialized.error or "failed to serialize attestation predicate"
            )
        repo = cls._repo(repo_root)
        tag_created = False
        try:
            if tag in {item.name for item in repo.tags}:
                return r[m.Infra.GateAttestationReport].fail(
                    f"attestation tag already exists: {tag}"
                )
            repo.git.tag("--sign", "--annotate", "--message", serialized.value, tag)
            tag_created = True
            cls._push_gate_attestation(repo_root, tag)
        except (GitCommandError, OSError, ValueError) as exc:
            if tag_created:
                try:
                    tag_ref = next(item for item in repo.tags if item.name == tag)
                    repo.delete_tag(tag_ref)
                except (GitCommandError, OSError, ValueError) as cleanup_exc:
                    return r[m.Infra.GateAttestationReport].fail(
                        f"{exc}; transaction cleanup failed: {cleanup_exc}"
                    )
            return r[m.Infra.GateAttestationReport].fail(str(exc))
        return r[m.Infra.GateAttestationReport].ok(
            cls._attestation_report(tag, predicate)
        )

    @classmethod
    def _push_gate_attestation(cls, repo_root: Path, tag: str) -> None:
        repo = cls._repo(repo_root)
        branch = repo.active_branch.name
        repo.git.push(
            "--atomic",
            "origin",
            f"HEAD:refs/heads/{branch}",
            f"refs/tags/{tag}:refs/tags/{tag}",
        )

    @classmethod
    def git_verify_gate_attestation(
        cls, request: m.Infra.GateAttestationVerifyRequest
    ) -> p.Result[m.Infra.GateAttestationReport]:
        """Verify signature, signer, HEAD identity, and exact gate coverage."""
        repo_root = Path(request.workspace).expanduser().resolve()
        allowed = Path(request.allowed_signers).expanduser().resolve()
        if not allowed.is_file():
            return r[m.Infra.GateAttestationReport].fail(
                f"allowed_signers file not found: {allowed}"
            )
        repo = cls._repo(repo_root)
        tag = cls._attestation_tag(repo.head.commit.hexsha)
        verification = u.Cli.run_raw(
            [
                "git", "-c", "gpg.format=ssh",
                "-c", f"gpg.ssh.allowedSignersFile={allowed}",
                "verify-tag", "--raw", tag,
            ],
            cwd=repo_root,
        )
        if verification.failure:
            return r[m.Infra.GateAttestationReport].fail(
                verification.error or f"signature verification failed: {tag}"
            )
        predicate_result = cls._predicate_from_tag(repo_root, tag)
        if predicate_result.failure:
            return r[m.Infra.GateAttestationReport].fail(
                predicate_result.error or "invalid attestation tag"
            )
        predicate = predicate_result.value
        checked = cls._attestation_predicate_from_value(repo_root, predicate)
        if checked.failure:
            return r[m.Infra.GateAttestationReport].fail(
                checked.error or "attestation identity mismatch"
            )
        output = verification.value
        match = re.search(
            r'^Good "git" signature for (\S+) with ',
            f"{output.stdout}\n{output.stderr}",
            flags=re.MULTILINE,
        )
        if match is None or match.group(1) != predicate.signer:
            return r[m.Infra.GateAttestationReport].fail(
                f"verified signature does not identify signer: {predicate.signer}"
            )
        if tuple(request.expected_gates) != tuple(predicate.covered_gates):
            return r[m.Infra.GateAttestationReport].fail(
                "attestation gate coverage does not exactly match required gates"
            )
        if request.output is not None:
            serialized = u.Cli.json_dumps(
                predicate.model_dump(mode="json"), sort_keys=True
            )
            if serialized.failure:
                return r[m.Infra.GateAttestationReport].fail(
                    serialized.error or "failed to serialize verified predicate"
                )
            Path(request.output).expanduser().resolve().write_text(
                serialized.value, encoding="utf-8"
            )
        return r[m.Infra.GateAttestationReport].ok(
            cls._attestation_report(tag, predicate)
        )

    @classmethod
    def _predicate_from_tag(
        cls, repo_root: Path, tag: str
    ) -> p.Result[m.Infra.GateAttestationPredicate]:
        try:
            tag_ref = next(item for item in cls._repo(repo_root).tags if item.name == tag)
        except (OSError, StopIteration) as exc:
            return r[m.Infra.GateAttestationPredicate].fail(str(exc))
        if tag_ref.tag is None:
            return r[m.Infra.GateAttestationPredicate].fail(
                f"attestation is not an annotated tag: {tag}"
            )
        target = tag_ref.commit.hexsha
        head = cls._repo(repo_root).head.commit.hexsha
        if target != head:
            return r[m.Infra.GateAttestationPredicate].fail(
                f"attestation tag target does not equal HEAD: {target} != {head}"
            )
        message = tag_ref.tag.message.split(_SSH_SIGNATURE_MARKER, maxsplit=1)[0]
        parsed = u.Cli.json_loads(message)
        if parsed.failure:
            return r[m.Infra.GateAttestationPredicate].fail(
                parsed.error or "invalid attestation tag JSON"
            )
        try:
            predicate = m.Infra.GateAttestationPredicate.model_validate(parsed.value)
        except ValueError as exc:
            return r[m.Infra.GateAttestationPredicate].fail(str(exc))
        return r[m.Infra.GateAttestationPredicate].ok(predicate)

    @classmethod
    def _attestation_predicate_from_value(
        cls, repo_root: Path, predicate: m.Infra.GateAttestationPredicate
    ) -> p.Result[bool]:
        identity = cls.git_identity(m.Infra.GitRepoRequest(repo_root=repo_root))
        if identity.failure:
            return r[bool].fail(identity.error or "failed to resolve Git identity")
        tree_sha = cls._repo(repo_root).head.commit.tree.hexsha
        sources = cls._promotion_sources(repo_root)
        if sources.failure:
            return r[bool].fail(sources.error or "invalid promotion source manifest")
        if (
            predicate.repository != identity.value.origin_remote
            or predicate.commit_sha != identity.value.head_oid
            or predicate.tree_sha != tree_sha
            or predicate.toolchain_digest != cls._toolchain_digest(repo_root)
            or predicate.sources != sources.value
        ):
            return r[bool].fail(
                "attestation repository/commit/tree/toolchain/sources does not match HEAD"
            )
        return r[bool].ok(True)

    @staticmethod
    def _attestation_report(
        tag: str, predicate: m.Infra.GateAttestationPredicate
    ) -> m.Infra.GateAttestationReport:
        return m.Infra.GateAttestationReport(
            tag=tag,
            commit_sha=predicate.commit_sha,
            tree_sha=predicate.tree_sha,
            signer=predicate.signer,
            covered_gates=predicate.covered_gates,
            sources=predicate.sources,
        )


__all__: list[str] = ["FlextInfraUtilitiesGitAttestationMixin"]
