# Private project handlers for flext-infra.
# This versioned extension accepts only `_custom_<verb>_<what>` handlers and
# `(pre|post)-<verb>[-<what>]` hooks. Public targets, aliases, toolchain setup,
# generated-target redefinitions, and help entries are invalid; the standardized
# FLEXT verbs in base.mk own those. Add project-specific actions as
# `_custom_<verb>_<what>` (e.g. run WHAT=<what>) or wrap a verb with a hook.

_custom_basemk_generate:
	@set -eu; \
	output="$(strip $(OUTPUT))"; \
	if [ -z "$$output" ]; then output="base.mk"; fi; \
	$(PROJECT_FLEXT_INFRA) basemk generate \
		--project-name "$(PROJECT_NAME)" --output "$$output"

_custom_run_cprofile-import:
	@set -eu; \
	target="$(strip $(PROFILE_TARGET))"; \
	report_dir="$(PROJECT_ROOT)/.reports/cprofile-import"; \
	mkdir -p "$$report_dir"; \
	env FLEXT_CPROFILE_ACTION=import FLEXT_CPROFILE_TARGET="$$target" \
		FLEXT_CPROFILE_WORKSPACE="$(PROJECT_ROOT)" \
		FLEXT_CPROFILE_ARGS="$(strip $(PROFILE_ARGS))" \
		timeout --signal=INT --kill-after=5s 53s \
		"$(RUNTIME_PYTHON)" -m cProfile \
		-o "$$report_dir/$$target.pstats" \
		-m flext_infra._cprofile_entry
