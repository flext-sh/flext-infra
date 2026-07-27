# Private project handlers for flext-infra.
# This versioned extension accepts only `_custom_<verb>_<what>` handlers and
# `(pre|post)-<verb>[-<what>]` hooks. Public targets, aliases, toolchain setup,
# generated-target redefinitions, and help entries are invalid; the standardized
# FLEXT verbs in base.mk own those. Add project-specific actions as
# `_custom_<verb>_<what>` (e.g. run WHAT=<what>) or wrap a verb with a hook.
