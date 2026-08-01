"""Tests that every Make profile consumes one hook-only custom policy.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, config
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestsFlextInfraCustomHandlerPolicyIsProfileAware:
    def test_every_declared_profile_has_a_custom_handler_policy(self) -> None:
        """Each Make profile declares the contract for its own custom surface."""
        declared = frozenset(
            c.Infra.MakeProfile(profile.name)
            for profile in config.Infra.codegen.profiles
        )
        covered = frozenset(
            c.Infra.MakeProfile(profile)
            for profile in config.Infra.codegen.make.custom_handler_policies
        )

        tm.that(declared - covered, eq=frozenset())

    def test_workspace_root_uses_the_same_hook_only_policy(self) -> None:
        """The workspace root cannot create a second public target owner."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_ROOT
        ]

        tm.that(policy.allow_public_targets, eq=False)
        tm.that(policy.allow_toolchain_declarations, eq=False)

    def test_standalone_stays_private_only(self) -> None:
        """A standalone custom surface may define only declared pre/post hooks."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.STANDALONE
        ]

        tm.that(policy.allow_public_targets, eq=False)

    def test_validator_rejects_parallel_targets_for_every_profile(self) -> None:
        """No profile may relax the canonical typed handler matrix."""
        content = "WORKSPACE_BASE ?= 0.12.0-dev\ndone-check:\n\t@echo hi\n"
        strict = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.STANDALONE
        ]
        workspace_root = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_ROOT
        ]
        validate = FlextInfraCodegenConform.validate_custom_make
        allowed_verbs = tuple(verb.name for verb in config.Infra.codegen.make.verbs)

        tm.that(validate(content, strict, allowed_verbs=allowed_verbs).failure, eq=True)
        tm.that(
            validate(content, workspace_root, allowed_verbs=allowed_verbs).failure,
            eq=True,
        )

    def test_policy_keys_are_normalised_to_profile_values(self) -> None:
        """Raw strings and StrEnum members resolve to the same policy object."""
        policies = config.Infra.codegen.make.custom_handler_policies
        profile = c.Infra.MakeProfile.WORKSPACE_ROOT

        tm.that(set(policies), eq={member.value for member in c.Infra.MakeProfile})
        tm.that(policies[profile] is policies[profile.value], eq=True)
