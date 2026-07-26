"""Tests that the custom-handler policy is declared per Make profile.

``custom_handler_policy`` was a single flat rule applied to every profile, but
the profiles have genuinely different contracts:

* a workspace *member* extends the generated verbs, so its ``custom.mk`` may
  only define private ``_custom_<verb>_<what>`` handlers and hooks;
* a workspace *root* orchestrates the members, so its ``custom.mk`` legitimately
  owns public orchestration targets and the variables they read.

Applying the member rule to the root made ``codegen conform`` reject the root's
own surface on every run, emitting a ``custom.mk.rej`` artifact and blocking the
whole transaction -- which is why no other generated artifact could be landed.

The policy is therefore keyed by profile, and the engine selects the entry for
the profile it is conforming instead of assuming one shape fits every project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c, config
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsFlextInfraCustomHandlerPolicyIsProfileAware:
    def test_every_declared_profile_has_a_custom_handler_policy(self) -> None:
        """Each Make profile declares the contract for its own custom surface."""
        declared = frozenset(profile.name for profile in config.Infra.codegen.profiles)
        covered = frozenset(config.Infra.codegen.make.custom_handler_policies)

        tm.that(declared - covered, eq=frozenset())

    def test_workspace_root_may_own_public_orchestration_targets(self) -> None:
        """The root profile permits the public targets it actually ships."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_ROOT
        ]

        tm.that(policy.allow_public_targets, eq=True)

    def test_workspace_member_stays_private_only(self) -> None:
        """A member custom surface may still only define private handlers."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_MEMBER
        ]

        tm.that(policy.allow_public_targets, eq=False)

    def test_validator_honours_the_permissions_it_is_given(self) -> None:
        """A permissive policy accepts what a strict one rejects.

        The ``allow_*`` flags were declarative only: the validator read just
        ``target_pattern``, so a workspace root's own public targets and
        variables were rejected no matter what the config permitted.
        """
        content = "WORKSPACE_BASE ?= 0.12.0-dev\ndone-check:\n\t@echo hi\n"
        strict = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_MEMBER
        ]
        permissive = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_ROOT
        ]
        validate = FlextInfraCodegenConform.validate_custom_make

        tm.that(validate(content, strict).failure, eq=True)
        tm.that(validate(content, permissive).success, eq=True)
