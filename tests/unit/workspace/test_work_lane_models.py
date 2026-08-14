"""Work-lane models reject impossible persisted states."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import c, m
from pydantic import ValidationError


def _plain_topology() -> m.Infra.PlainLaneTopology:
    return m.Infra.PlainLaneTopology(role=c.Infra.WorkLaneRole.PLAIN)


def _pending() -> dict[str, object]:
    return {
        "branch": "feature/typed-lane",
        "namespace": c.Infra.WorkBranchNamespace.FEATURE,
        "worktree": Path("typed-lane"),
        "kind": c.Infra.WorkKind.FEATURE,
        "slug": "typed-lane",
        "integration_base": "0.12.0-dev",
        "topology": _plain_topology(),
        "provisioning": c.Infra.WorkProvisioningState.PENDING,
    }


def test_pending_reservation_accepts_no_head() -> None:
    reservation = m.Infra.PendingLaneReservation.model_validate(_pending())

    assert reservation.provisioning == c.Infra.WorkProvisioningState.PENDING


def test_ready_metadata_requires_head() -> None:
    payload = _pending() | {"provisioning": c.Infra.WorkProvisioningState.READY}

    with pytest.raises(ValidationError):
        m.Infra.ReadyLaneMetadata.model_validate(payload)


def test_failed_metadata_accepts_optional_head() -> None:
    failed = m.Infra.FailedLaneMetadata.model_validate(
        _pending()
        | {
            "provisioning": c.Infra.WorkProvisioningState.FAILED,
            "recovery": c.Infra.WorkRecoveryCategory.RETRY_SETUP,
            "error_category": c.Infra.WorkProvisioningError.SETUP,
        }
    )

    assert failed.head_oid is None


def test_bead_issue_accepts_failed_lane_metadata() -> None:
    issue = m.Infra.BeadIssue.model_validate({
        "id": "mro-failed-lane",
        "status": c.Infra.BeadIssueStatus.IN_PROGRESS,
        "issue_type": "bug",
        "metadata": _pending()
        | {
            "provisioning": c.Infra.WorkProvisioningState.FAILED,
            "recovery": c.Infra.WorkRecoveryCategory.RETRY_SETUP,
            "error_category": c.Infra.WorkProvisioningError.SETUP,
        },
    })

    assert isinstance(issue.metadata, m.Infra.FailedLaneMetadata)


def test_lane_metadata_refuses_extra_fields() -> None:
    with pytest.raises(ValidationError):
        m.Infra.PendingLaneReservation.model_validate(_pending() | {"unknown": "x"})


@pytest.mark.parametrize(
    "payload",
    [
        {
            "branch": "feature/typed-lane",
            "namespace": c.Infra.WorkBranchNamespace.EPIC,
            "kind": c.Infra.WorkKind.FEATURE,
            "topology": {"role": "plain"},
        },
        {
            "branch": "epic/typed-lane",
            "namespace": c.Infra.WorkBranchNamespace.EPIC,
            "kind": c.Infra.WorkKind.FEATURE,
            "topology": {"role": "epic", "epic_bead": "mro-parent"},
        },
        {
            "branch": "feature/typed-lane",
            "namespace": c.Infra.WorkBranchNamespace.FEATURE,
            "kind": None,
            "topology": {"role": "plain"},
        },
    ],
)
def test_lane_metadata_refuses_inconsistent_namespace_topology(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        m.Infra.PendingLaneReservation.model_validate(_pending() | payload)


@pytest.mark.parametrize(
    "topology",
    [
        {"role": "epic", "epic_bead": "mro-parent", "child_slug": "child"},
        {"role": "child"},
        {"role": "plain", "epic_bead": "mro-parent"},
    ],
)
def test_lane_topology_refuses_illegal_variant_fields(topology: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        m.Infra.PendingLaneReservation.model_validate(
            _pending() | {"topology": topology}
        )


__all__: tuple[str, ...] = ()
"""Work-lane models reject impossible persisted states."""
