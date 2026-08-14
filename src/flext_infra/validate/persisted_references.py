"""Semantic persisted repository artifact reference validation."""

from __future__ import annotations

from flext_infra import m, t
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
            for line_number, target in FlextInfraReferenceExtraction.targets(payload):
                if FlextInfraReferenceExtraction.escapes_repository(
                    payload.path, target, template_entries
                ):
                    issues.append(
                        m.Infra.Issue(
                            file=payload.path,
                            line=line_number,
                            column=1,
                            code="PREF001",
                            message="artifact reference escapes repository authority",
                        )
                    )
                    continue
                if not target.startswith("https://github.com/"):
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
                            code="PREF002",
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
