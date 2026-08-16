"""Semantic persisted repository artifact reference validation."""

from __future__ import annotations

from flext_infra import c, m, t
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository
from flext_infra.validate.reference_extraction import FlextInfraReferenceExtraction


class FlextInfraPersistedReferencesValidator:
    """Validate explicit persisted artifact-reference contexts only."""

    @classmethod
    def validate(
        cls,
        payloads: t.SequenceOf[m.Infra.GitCandidatePayload],
        authorities: t.SequenceOf[m.Infra.RepositoryArtifactAuthority],
        template_entries: t.SequenceOf[m.Infra.TemplateEntrySpec],
    ) -> tuple[m.Infra.Issue, ...]:
        """Return deterministic diagnostics for explicit candidate references."""
        issues: list[m.Infra.Issue] = []
        for payload in payloads:
            if not FlextInfraReferenceExtraction.is_semantic_payload(payload):
                continue
            for line_number, target in FlextInfraReferenceExtraction.targets(payload):
                if FlextInfraReferenceExtraction.escapes_repository(
                    payload.path, target, template_entries
                ):
                    issues.append(
                        m.Infra.Issue(
                            file=payload.path,
                            line=line_number,
                            column=1,
                            code=c.Infra.PERSISTED_REFERENCE_ESCAPE_CODE,
                            message="artifact reference escapes repository authority",
                        )
                    )
                    continue
                if not target.startswith(c.Infra.REPOSITORY_ARTIFACT_GITHUB_PREFIX):
                    continue
                parsed = FlextInfraUtilitiesRepository.repository_artifact_parse(
                    target, authorities
                )
                if parsed.failure:
                    issues.append(
                        m.Infra.Issue(
                            file=payload.path,
                            line=line_number,
                            column=1,
                            code=c.Infra.PERSISTED_REFERENCE_AUTHORITY_CODE,
                            message=parsed.error
                            or "invalid repository artifact reference",
                        )
                    )
        return tuple(
            sorted(
                issues,
                key=lambda issue: (issue.file, issue.line, issue.column, issue.code),
            )
        )


__all__: tuple[str, ...] = ("FlextInfraPersistedReferencesValidator",)
