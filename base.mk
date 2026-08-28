# =============================================================================
# FLEXT BASE MAKEFILE - Shared patterns for all FLEXT projects
# =============================================================================
# Usage: Set PROJECT_NAME before including the repository-local base.mk.
# Silent by default. Use VERBOSE=1 for detailed output.
# =============================================================================

# === CONFIGURATION (override before include) ===
PROJECT_NAME ?= flext-infra
PYTHON_VERSION ?= 3.13
SRC_DIR ?= src
TESTS_DIR ?= tests
DOCSTRING_MIN ?= 80
COMPLEXITY_MAX ?= 10
PYTEST_ARGS ?=
DEPENDENCY ?=
DIAG ?= 0
CHECK_GATES ?=
VALIDATE_GATES ?=
SCOPE ?= project
NAMESPACE ?=
GATES ?=
PROPAGATE ?=
FIX ?=
PR_ACTION ?= status
PR_BASE ?=
PR_HEAD ?=
PR_TITLE ?=
PR_BODY ?=
PR_DRAFT ?= 0
FILE ?=
FILES ?=
CHANGED_ONLY ?=
MATCH ?=
COV ?=
RUFF_ARGS ?=
PYRIGHT_ARGS ?=
CHECK_ONLY ?=
FAIL_FAST ?=
VERBOSE ?=


PYTEST_REPORT_ARGS := -ra --durations=25 --durations-min=0.001 --tb=short
PYTEST_DIAG_ARGS := -rA --durations=0 --tb=long --showlocals
PYTEST_PROCESS_TIMEOUT_SECONDS ?= 660
# flext-99ae: the pytest process inherits a hard wall-clock boundary, mirroring
# MYPY_BOUNDED, so a hung run is terminated even if the typed runner stalls.
PYTEST_BOUNDED = timeout --signal=TERM --kill-after=5s "$(PYTEST_PROCESS_TIMEOUT_SECONDS)s"
PYTEST_REPORTS_DIR ?= .reports/tests
override PYTEST_CASE_TIMEOUT_SECONDS := 10
override PYTEST_RUN_TIMEOUT_SECONDS := 600
override PYTEST_TERMINATION_GRACE_SECONDS := 2
override PYTEST_TIMEOUT_EXIT_CODE := 124
override PYTEST_ENFORCEMENT_PLUGIN := flext_tests_enforcement
override PYTEST_PROGRESS_ARGS := --verbose
override PYTEST_REPORT_ARGS := -ra --durations=25 --durations-min=0.001 --tb=short
override PYTEST_DIAG_ARGS := -rA --durations=0 --tb=long --showlocals
override PYTEST_PARALLEL_WORKERS := 4
override PYTEST_PARALLEL_DISTRIBUTION := worksteal
override PYTEST_PROFILE_SORT := cumulative
override PYTEST_PROFILE_LIMIT := 50
override PROCESS_TIMEOUT_COMMAND := timeout
override export FLEXT_PYTEST_ARGS_RAW := $(value PYTEST_ARGS)
override export FLEXT_PYTEST_FILE_RAW := $(value FILE)
override export FLEXT_PYTEST_FILES_RAW := $(value FILES)
override export FLEXT_PYTEST_MATCH_RAW := $(value MATCH)
override export FLEXT_PYTEST_DIAG_RAW := $(value DIAG)
override export FLEXT_PYTEST_FAIL_FAST_RAW := $(value FAIL_FAST)
override export FLEXT_PYTEST_REPORTS_RAW := $(value PYTEST_REPORTS_DIR)
override export FLEXT_PYTEST_TARGET_RAW := tests
override export FLEXT_PYTEST_VERBOSE_RAW := $(value VERBOSE)
override export FLEXT_PYTEST_COV_RAW := $(value COV)
override export FLEXT_PYTEST_WHAT_RAW := $(value WHAT)

# === WORKSPACE/STANDALONE DETECTION ===
BASE_MK_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
PROJECT_ROOT := $(CURDIR)
CALLER_PATH := $(PATH)
CALLER_VIRTUAL_ENV := $(patsubst %/,%,$(VIRTUAL_ENV))

# Repository-local topology: only the Makefile owner's own .gitmodules can
# classify it as a workspace. Parent directories and caller environment never
# alter a standalone repository's mode.
ifneq ($(wildcard $(PROJECT_ROOT)/.gitmodules),)
FLEXT_MODE := workspace
else
FLEXT_MODE := standalone
endif

ifeq ($(FLEXT_MODE),workspace)
WORKSPACE_ROOT := $(PROJECT_ROOT)
WORKSPACE_VENV := $(WORKSPACE_ROOT)/.venv
ACTIVE_VENV := $(WORKSPACE_VENV)
else
WORKSPACE_ROOT := $(PROJECT_ROOT)
ACTIVE_VENV := $(PROJECT_ROOT)/.venv
endif

override UV_PROJECT := $(WORKSPACE_ROOT)
override UV_PROJECT_ENVIRONMENT := $(ACTIVE_VENV)
override VIRTUAL_ENV := $(ACTIVE_VENV)
MISE := $(shell command -v mise 2>/dev/null)
SANITIZED_CALLER_PATH := $(CALLER_PATH)
ifneq ($(strip $(CALLER_VIRTUAL_ENV)),)
SANITIZED_CALLER_PATH := $(subst $(CALLER_VIRTUAL_ENV)/bin:,,$(SANITIZED_CALLER_PATH))
SANITIZED_CALLER_PATH := $(subst :$(CALLER_VIRTUAL_ENV)/bin,,$(SANITIZED_CALLER_PATH))
ifeq ($(SANITIZED_CALLER_PATH),$(CALLER_VIRTUAL_ENV)/bin)
SANITIZED_CALLER_PATH :=
endif
endif
override PATH := $(ACTIVE_VENV)/bin:$(SANITIZED_CALLER_PATH)
export UV_PROJECT UV_PROJECT_ENVIRONMENT VIRTUAL_ENV PATH

export PYTHON_KEYRING_BACKEND := keyring.backends.null.Keyring

VENV_PYTHON := $(ACTIVE_VENV)/bin/python
UV ?= uv
FLEXT_INFRA_PYTHON ?= $(VENV_PYTHON)
export FLEXT_INFRA_PYTHON


# Export for subprocesses
export PROJECT_NAME PYTHON_VERSION
export FLEXT_ROOT := $(WORKSPACE_ROOT)

# === FLEXT-INFRA COMMAND ROOTS ===
PROJECT_INFRA_HOME := $(WORKSPACE_ROOT)/flext-infra
ifeq ($(wildcard $(PROJECT_INFRA_HOME)/src/flext_infra),)
PROJECT_INFRA_HOME := $(PROJECT_ROOT)
endif
PROJECT_INFRA_SRC := $(PROJECT_INFRA_HOME)/src
PROJECT_INFRA_PYTHONPATH ?= $(PROJECT_INFRA_SRC)
PROJECT_INFRA_ROOT := test -x "$(FLEXT_INFRA_PYTHON)" || { echo "ERROR: FLEXT_INFRA_PYTHON must name an executable managed Python" >&2; exit 2; }; env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(PATH)" PYTHONPATH="$(PROJECT_INFRA_PYTHONPATH)" $(FLEXT_INFRA_PYTHON) -m flext_infra
PROJECT_INFRA_CHECK := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) check
PROJECT_INFRA_CODEGEN := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) codegen
PROJECT_INFRA_DEPS := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) deps
PROJECT_INFRA_DOCS := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) docs
PROJECT_INFRA_GITHUB := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) github
PROJECT_INFRA_REFACTOR := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) refactor
PROJECT_INFRA_VALIDATE := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) validate

help: ## Show commands
	$(Q)echo "================================================"
	$(Q)echo "  $(PROJECT_NAME)"
	$(Q)echo "================================================"
	$(Q)echo ""
	$(Q)echo "FLEXT base.mk (standalone bootstrap)"
	$(Q)echo "  clean help"
	$(Q)echo ""
	$(Q)echo "After codegen: see 'make help' for the full verb surface."

# === SILENT MODE ===
Q := @
ifdef VERBOSE
Q :=
endif

# === CACHE ===
LINT_CACHE_DIR := .lint-cache
CACHE_TIMEOUT := 300
BASE_INFRA_VALIDATE = $(PROJECT_INFRA_ROOT) validate

$(LINT_CACHE_DIR):
	$(Q)mkdir -p $(LINT_CACHE_DIR)

# === SIMPLE VERB SURFACE ===
# base.mk declares ONLY the verbs it ships a recipe for. R12 moved every other
# public verb into the generated project Makefile, and a verb declared here
# without a recipe is not harmless: Make treats it as a satisfied target, so the
# verb becomes a silent no-op and a gate like `check` exits 0 having validated
# nothing. flext-x0rau.3 removed the `pr` and daemon-* recipes with their
# templates, so `help` (base_venv) and `clean` (base_clean) are the only
# recipes this file composes.
.PHONY: help clean _preflight
STANDARD_VERBS := clean
$(STANDARD_VERBS): _preflight

define ENFORCE_WORKSPACE_VENV
if [ "$(FLEXT_MODE)" = "workspace" ]; then \
	if [ -d "$(WORKSPACE_ROOT)/.venv" ]; then \
		if [ -d ".venv" ] && [ "$(CURDIR)" != "$(WORKSPACE_ROOT)" ]; then \
			echo "ERROR: [preflight] Project-local .venv violates the workspace environment contract: $(CURDIR)/.venv"; \
			exit 1; \
		fi; \
	elif [ "$(CURDIR)" = "$(WORKSPACE_ROOT)" ]; then \
		echo "ERROR: [preflight] Workspace venv not found. Run 'make setup' at workspace root."; \
		exit 1; \
	elif [ "$(filter setup,$(MAKECMDGOALS))" != "setup" ] && [ ! -d "$(ACTIVE_VENV)" ]; then \
		echo "ERROR: [preflight] No venv found (workspace or local). Run 'make setup' in $(PROJECT_NAME)."; \
		exit 1; \
	else \
		echo "INFO: [preflight] Using project-local venv for $(PROJECT_NAME) (workspace venv not found)."; \
	fi; \
elif [ "$(FLEXT_MODE)" = "standalone" ]; then \
	echo "INFO: [preflight] Running in standalone mode (workspace features unavailable)."; \
elif [ "$(filter setup,$(MAKECMDGOALS))" = "" ] && [ ! -d "$(ACTIVE_VENV)" ]; then \
	echo "ERROR: [preflight] No venv found at $(ACTIVE_VENV). Run 'make setup' in $(PROJECT_NAME)."; \
	exit 1; \
fi
endef

# flext-wkii.17.27 (codex): validation verbs detect drift without mutating files.
define VALIDATE_CANONICAL_BASE_MK
if [ "$(FLEXT_MODE)" = "workspace" ] && [ "$(CURDIR)" != "$(WORKSPACE_ROOT)" ]; then \
	if [ "$(filter setup,$(MAKECMDGOALS))" = "setup" ] && [ ! -x "$(FLEXT_INFRA_PYTHON)" ]; then \
		echo "INFO: [preflight] Deferring canonical base.mk validation until setup creates the workspace environment."; \
	elif ! $(BASE_INFRA_VALIDATE) basemk-validate --workspace "$(WORKSPACE_ROOT)/flext-infra"; then \
		echo "ERROR: [preflight] Canonical base.mk is stale. Run 'make -C $(WORKSPACE_ROOT) build WHAT=sync PROJECT=$(PROJECT_NAME)'."; \
		exit 1; \
	fi; \
elif [ "$(FLEXT_MODE)" = "standalone" ]; then \
	echo "INFO: [preflight] Standalone mode: skipping workspace base.mk validation."; \
fi
endef

# flext-ga9q (custom.mk blacklist): member projects may define ANY custom
# verb/WHAT through _custom_<verb>_<what> handlers and (pre|post)-<verb>[-<what>]
# hooks EXCEPT the reserved verbs/WHATs below, which stay a flext-infra
# monopoly (SSOT: flext_infra.basemk.custom_policy). Parse-time guard: every
# make invocation fails loud when custom.mk redefines a reserved target;
# every other target is permitted.
CUSTOM_MK_RESERVED_TARGETS :=_custom_build_artifacts _custom_check_all _custom_check_lint _custom_check_markdown _custom_check_mypy _custom_check_pyrefly _custom_check_pyright _custom_check_security _custom_check_smells _custom_clean_generated _custom_clean_status _custom_deps_check _custom_deps_lock _custom_deps_upgrade _custom_docs_all _custom_docs_audit _custom_docs_build _custom_docs_fix _custom_docs_generate _custom_docs_validate _custom_fix_all _custom_fix_apply _custom_fix_check _custom_fmt_all _custom_fmt_apply _custom_fmt_check _custom_gen_all _custom_gen_apply _custom_gen_check _custom_gen_init _custom_help_usage _custom_mod_all _custom_mod_apply _custom_mod_check _custom_release_status _custom_run_default _custom_setup_environment _custom_status_diagnostics _custom_test_all _custom_test_cache-checkpoint _custom_test_cache-clear _custom_test_cache-status build check clean deps docs fix fmt gen help mod release run setup status test
ifneq ($(wildcard custom.mk),)
# Target definitions at column 0, excluding assignments (=) and dot-directives.
# $(shell) converts the newline-separated results to space-separated lists.
_CUSTOM_MK_DEFINED := $(shell awk '/^[A-Za-z_][A-Za-z0-9_-]*([ \t]+[A-Za-z_][A-Za-z0-9_-]*)*[ \t]*:/ && index($$0, "=") == 0 { line = $$0; sub(/:.*/, "", line); count = split(line, names, /[ \t]+/); for (i = 1; i <= count; i++) print names[i] }' custom.mk | sort -u)
_CUSTOM_MK_OFFENDERS := $(shell printf '%s\n' $(_CUSTOM_MK_DEFINED) | grep -xF $(foreach target,$(CUSTOM_MK_RESERVED_TARGETS),-e $(target)))
ifneq ($(_CUSTOM_MK_OFFENDERS),)
$(error custom.mk redefines reserved flext-infra target(s): $(_CUSTOM_MK_OFFENDERS) - reserved verbs/WHATs are a flext-infra monopoly; use _custom_<verb>_<what> with a non-reserved WHAT or (pre|post)-<verb>[-<what>] hooks)
endif
endif

_preflight: ## Preflight: validate base.mk and enforce venv contract
	$(Q)$(VALIDATE_CANONICAL_BASE_MK)
	$(Q)$(ENFORCE_WORKSPACE_VENV)

clean: ## Clean artifacts
	$(Q)rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage* \
		.mypy_cache/ .pyrefly_cache/ .ruff_cache/ $(LINT_CACHE_DIR)/ \
		.pyright/ .pytype/ .pyrefly-report.json .pyrefly-output.txt
	$(Q)find . -type d -name __pycache__ -exec rm -rf {} +
	$(Q)find . -type f -name "*.pyc" -delete
	$(Q)echo "Clean complete: $(PROJECT_NAME)"
