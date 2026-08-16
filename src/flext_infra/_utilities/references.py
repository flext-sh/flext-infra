"""Public repository-reference facade implementation."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import m, p, t
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra.validate.persisted_references import (
    FlextInfraPersistedReferencesValidator,
)


class FlextInfraUtilitiesReferences:
    """Expose typed persisted-reference validation through ``u.Infra``."""

    @staticmethod
    def repository_persisted_references_validate(
        repository_root: Path,
        authorities: t.SequenceOf[m.Infra.RepositoryArtifactAuthority],
        template_entries: t.SequenceOf[m.Infra.TemplateEntrySpec] = (),
    ) -> p.Result[m.Infra.PersistedReferenceValidationReport]:
        """Validate current candidate references against explicit policy."""
        payloads = FlextInfraUtilitiesGit.git_candidate_payloads(
            m.Infra.GitRepoRequest(repo_root=repository_root)
        )
        if payloads.failure:
            return r[m.Infra.PersistedReferenceValidationReport].fail(
                payloads.error or "candidate payload scan failed"
            )
        issues = FlextInfraPersistedReferencesValidator.validate(
            payloads.value.payloads, authorities, template_entries
        )
        return r[m.Infra.PersistedReferenceValidationReport].ok(
            m.Infra.PersistedReferenceValidationReport(issues=issues)
        )

    @staticmethod
    def repository_persisted_references_validate_content(
        content: str,
        path: str,
        authorities: t.SequenceOf[m.Infra.RepositoryArtifactAuthority],
        repository_root: Path | None = None,
    ) -> p.Result[m.Infra.PersistedReferenceValidationReport]:
        """Validate one in-memory persisted artifact before it is written."""
        normalized_path = Path(path)
        if repository_root is not None:
            resolved_root = repository_root.resolve()
            resolved_path = (
                normalized_path.resolve()
                if normalized_path.is_absolute()
                else (resolved_root / normalized_path).resolve()
            )
            if not resolved_path.is_relative_to(resolved_root):
                return r[m.Infra.PersistedReferenceValidationReport].fail(
                    "content path must be inside repository_root"
                )
            normalized_path = resolved_path.relative_to(resolved_root)
        payload = m.Infra.GitCandidatePayload(
            path=normalized_path.as_posix(), mode="100644", content=content.encode()
        )
        issues = FlextInfraPersistedReferencesValidator.validate(
            (payload,), authorities, ()
        )
        return r[m.Infra.PersistedReferenceValidationReport].ok(
            m.Infra.PersistedReferenceValidationReport(issues=issues)
        )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesReferences",)
