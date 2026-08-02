# Private project handlers for flext-infra.
# This versioned extension accepts only `_custom_<verb>_<what>` handlers and
# `(pre|post)-<verb>[-<what>]` hooks. Public targets, aliases, toolchain setup,
# generated-target redefinitions, and help entries are invalid; the standardized
# FLEXT verbs in base.mk own those. Add project-specific actions as
# `_custom_<verb>_<what>` (e.g. run WHAT=<what>) or wrap a verb with a hook.

.PHONY: \
	_custom_basemk_generate \
	_custom_run_cprofile-import \
	_custom_run_cprofile-report \
	_custom_run_cprofile-test
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
	timeout_seconds=$$(( \
		$(PYTEST_RUN_TIMEOUT_SECONDS) - $(PYTEST_TERMINATION_GRACE_SECONDS) \
	)); \
	env FLEXT_CPROFILE_ACTION=import FLEXT_CPROFILE_TARGET="$$target" \
		FLEXT_CPROFILE_WORKSPACE="$(PROJECT_ROOT)" \
		"$(PROCESS_TIMEOUT_COMMAND)" --signal=INT \
		--kill-after="$(PYTEST_TERMINATION_GRACE_SECONDS)s" \
		"$${timeout_seconds}s" "$(RUNTIME_PYTHON)" -m cProfile \
		-o "$$report_dir/$$target.pstats" \
		-m flext_infra._cprofile_entry

_custom_run_cprofile-report:
	@set -eu; \
	target="$(strip $(PROFILE_TARGET))"; \
	if [ -n "$$target" ]; then \
		env FLEXT_CPROFILE_ACTION=report FLEXT_CPROFILE_TARGET="$$target" \
			FLEXT_CPROFILE_WORKSPACE="$(PROJECT_ROOT)" \
			FLEXT_CPROFILE_SORT="$(PYTEST_PROFILE_SORT)" \
			FLEXT_CPROFILE_LIMIT="$(PYTEST_PROFILE_LIMIT)" \
			"$(RUNTIME_PYTHON)" -m flext_infra._cprofile_entry; \
	else \
		"$(RUNTIME_PYTHON)" -m flext_infra._cprofile_entry; \
	fi

_custom_run_cprofile-test:
	@set -eu; \
	file="$(strip $(FILE))"; \
	if [ -z "$$file" ]; then \
		printf 'ERROR: FILE is required for run WHAT=cprofile-test\n' >&2; \
		exit 2; \
	fi; \
	case "$$file" in /*|..|../*|*/../*|*/..) \
		printf 'ERROR: FILE must be a repository-relative path\n' >&2; exit 2 ;; \
	esac; \
	path="$${file%%::*}"; \
	if [ ! -f "$$path" ]; then \
		printf 'ERROR: cProfile test target does not exist: %s\n' "$$path" >&2; \
		exit 2; \
	fi; \
	report_dir="$(PROJECT_ROOT)/.reports/cprofile"; \
	mkdir -p "$$report_dir"; \
	"$(RUNTIME_PYTHON)" -m cProfile -o "$$report_dir/pytest.pstats" \
		-m pytest "$$file" --no-cov -p no:metadata \
		-n=0 \
		$(if $(strip $(MATCH)),-k "$(strip $(MATCH))",)
