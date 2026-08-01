"""Tests that the custom-handler policy is declared per Make profile.

``custom_handler_policy`` was a single flat rule applied to every profile, but
the profiles have genuinely different contracts:

* a standalone repository may only define private
  ``_custom_<verb>_<what>`` handlers and hooks;
* a workspace *root* orchestrates the members, so its ``custom.mk`` legitimately
  owns public orchestration targets and the variables they read.

Applying the member rule to the root made ``codegen conform`` reject the root's
own surface on every run and block the whole transaction -- which is why no
other generated artifact could be landed.

The policy is therefore keyed by profile, and the engine selects the entry for
the profile it is conforming instead of assuming one shape fits every project.

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

    def test_workspace_root_may_own_public_orchestration_targets(self) -> None:
        """The root profile permits the public targets it actually ships."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_ROOT
        ]

        tm.that(policy.allow_public_targets, eq=True)

    def test_standalone_stays_private_only(self) -> None:
        """A standalone custom surface may only define private handlers."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.STANDALONE
        ]

        tm.that(policy.allow_public_targets, eq=False)

    def test_validator_honours_the_permissions_it_is_given(self) -> None:
        """A permissive policy accepts what a strict one rejects.

        The validator derives target syntax from the canonical verb catalogue;
        a workspace root's own public targets and variables are accepted only
        when its typed profile policy explicitly permits them.
        """
        content = "WORKSPACE_BASE ?= 0.12.0-dev\ndone-check:\n\t@echo hi\n"
        strict = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.STANDALONE
        ]
        permissive = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.WORKSPACE_ROOT
        ]
        validate = FlextInfraCodegenConform.validate_custom_make
        allowed_verbs = tuple(verb.name for verb in config.Infra.codegen.make.verbs)

        tm.that(validate(content, strict, allowed_verbs=allowed_verbs).failure, eq=True)
        tm.that(
            validate(content, permissive, allowed_verbs=allowed_verbs).success, eq=True
        )

    def test_policy_keys_are_normalised_to_profile_values(self) -> None:
        """Lookup succeeds for both a raw string and its StrEnum member.

        ``MakeProfile`` is a ``StrEnum``, so a key declared in YAML and the same
        profile passed as an enum member must resolve to ONE entry. If the two
        forms produced separate keys, a lookup would silently miss and fall back
        to the strict base policy -- exactly the failure that made conform
        reject the workspace root's own custom surface.
        """
        policies = config.Infra.codegen.make.custom_handler_policies
        profile = c.Infra.MakeProfile.WORKSPACE_ROOT

        tm.that(set(policies), eq={member.value for member in c.Infra.MakeProfile})
        tm.that(policies[profile] is policies[profile.value], eq=True)
