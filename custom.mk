# Private project handlers for flext-infra.
# This versioned extension accepts only `_custom_<verb>_<what>` handlers and
# `(pre|post)-<verb>[-<what>]` hooks. Public targets, aliases, toolchain setup,
# generated-target redefinitions, and help entries are invalid; the standardized
# FLEXT verbs in the generated Makefile own those. Add project-specific actions as
# `_custom_<verb>_<what>` (e.g. run WHAT=<what>) or wrap a verb with a hook.

.PHONY: _custom_basemk_generate
_custom_basemk_generate:
	@set -eu; \
	output="$(strip $(OUTPUT))"; \
	if [ -z "$$output" ]; then output="base.mk"; fi; \
	$(PROJECT_FLEXT_INFRA) basemk generate \
		--project-name "$(PROJECT_NAME)" --output "$$output"
