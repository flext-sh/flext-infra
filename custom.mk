# Private project hooks for flext-infra.
# The typed Make verb/WHAT matrix owns every handler. This file may contain
# only pre/post hooks for declared handlers; it cannot create or shadow one.

.PHONY: _custom_run_cprofile-report _custom_run_cprofile-test _custom_build_layout _custom_check_layout

# _custom_basemk_generate was removed: `basemk` is not a declared public verb,
# so the handler was unreachable through _dispatch AND rejected by the custom
# handler policy, which blocked `codegen conform` outright. base.mk generation
# is reached through the flext-infra CLI directly. Asserted by
# test_custom_surface_never_shadows_public_verbs.

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

_custom_run_cprofile-report:
	@set -eu; \
	"$(RUNTIME_PYTHON)" -m flext_infra._cprofile_entry

# flext-0wuz: project-layout engine (SSOT in flext-infra/config/codegen.yaml).
# Dry-run report by default; APPLY=Y executes the idempotent reorganization.
# PROJECT=<name> scopes to one workspace project; otherwise the whole
# workspace rooted at WORKSPACE_ROOT is planned/applied.
_custom_build_layout:
	@set -eu; \
	apply=""; \
	if [ "$(APPLY)" = "Y" ]; then apply="--apply"; fi; \
	project=""; \
	if [ -n "$(strip $(PROJECT))" ]; then project="--project $(strip $(PROJECT))"; fi; \
	$(PROJECT_FLEXT_INFRA) codegen layout --workspace "$(WORKSPACE_ROOT)" $$project $$apply

# flext-0wuz: layout warning gate (severity from codegen.yaml layout.severity).
_custom_check_layout:
	@set -eu; \
	projects="."; \
	if [ -n "$(strip $(PROJECT))" ]; then projects="$(strip $(PROJECT))"; fi; \
	$(PROJECT_FLEXT_INFRA) check run --workspace "$(WORKSPACE_ROOT)" --gates layout --projects "$$projects"
