"""Validate configured profile policies and independent permission flags.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, tm


class TestsFlextInfraCustomHandlerPolicyIsProfileAware:
    """Tests for ``FlextInfraCustomHandlerPolicyIsProfileAware``."""

    @staticmethod
    def test_every_declared_profile_has_a_custom_handler_policy() -> None:
        """Each Make profile declares the contract for its own custom surface."""
        codegen_profiles: tuple[m.Infra.ProfileSpec, ...] = (
            config.Infra.codegen.profiles
        )
        declared = frozenset(
            c.Infra.MakeProfile(profile.name) for profile in codegen_profiles
        )
        handler_policies: Mapping[str, m.Infra.CustomHandlerPolicy] = (
            config.Infra.codegen.make.custom_handler_policies
        )
        covered = frozenset(
            c.Infra.MakeProfile(profile) for profile in handler_policies
        )

        tm.that(declared - covered, empty=True)

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_profile_permissions_follow_declared_overrides(
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Effective permissions derive from the base and the declared override."""
        make = config.Infra.codegen.make
        policy = make.custom_handler_policies[profile]
        override = make.custom_handler_profile_overrides.get(profile)
        for actual, declared, inherited in (
            (
                policy.allow_public_targets,
                None if override is None else override.allow_public_targets,
                make.custom_handler_policy.allow_public_targets,
            ),
            (
                policy.allow_toolchain_declarations,
                None if override is None else override.allow_toolchain_declarations,
                make.custom_handler_policy.allow_toolchain_declarations,
            ),
        ):
            tm.that(
                actual,
                eq=inherited if declared is None else declared,
            )

    @staticmethod
    @pytest.mark.parametrize("allow_public_targets", [False, True])
    @pytest.mark.parametrize("allow_toolchain_declarations", [False, True])
    def test_validator_honours_the_permissions_it_is_given(
        *, allow_public_targets: bool, allow_toolchain_declarations: bool
    ) -> None:
        """Each permission controls its own public grammar independently."""
        base = config.Infra.codegen.make.custom_handler_policy
        policy = m.Infra.CustomHandlerPolicy(
            filename=base.filename,
            target_pattern=base.target_pattern,
            allow_public_targets=allow_public_targets,
            allow_toolchain_declarations=allow_toolchain_declarations,
        )
        validate = FlextInfraCodegenConform.Generate.validate_custom_make
        tm.that(
            validate("public-task:\n\t@:\n", policy).success,
            eq=allow_public_targets,
        )
        tm.that(
            validate("SAMPLE_SETTING := supplied\n", policy).success,
            eq=allow_toolchain_declarations,
        )

    @staticmethod
    def test_policy_keys_are_normalised_to_profile_values() -> None:
        """Lookup succeeds for both a raw string and its StrEnum member.

        ``MakeProfile`` is a ``StrEnum``, so a key declared in YAML and the same
        profile passed as an enum member must resolve to ONE entry. If the two
        forms produced separate keys, a lookup would silently miss and fall back
        to the strict base policy -- exactly the failure that made conform
        reject the repository root's own custom surface.
        """
        policies: MutableMapping[str, m.Infra.CustomHandlerPolicy] = dict(
            config.Infra.codegen.make.custom_handler_policies,
        )
        profile: c.Infra.MakeProfile = c.Infra.MakeProfile.WORKSPACE

        tm.that(set(policies), eq={member.value for member in c.Infra.MakeProfile})
        tm.ok(policies[profile] is policies[profile.value])
