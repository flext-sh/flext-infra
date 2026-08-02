# @flext-managed: continuous
# @flext-regenerate: make gen APPLY=Y
# @flext-ssot: config/codegen.yaml + templates/project/base/base.mk.j2
# @flext-maintenance: edit the SSOT, never a generated projection
# flext-infra — generated project interface.

.DEFAULT_GOAL := help

# Identity and topology are rendered from the typed repository target.
PROJECT_NAME := flext-infra
MAKE_PROFILE := standalone
SELF_MAKEFILE := $(abspath $(firstword $(MAKEFILE_LIST)))
MAKEFILE_ROOT := $(patsubst %/,%,$(dir $(SELF_MAKEFILE)))
PROJECT_ROOT := $(MAKEFILE_ROOT)
WORKSPACE_ROOT := $(abspath $(PROJECT_ROOT)/.)
UV ?= uv
WHAT ?=
APPLY ?= N
override export CI := $(value CI)

# Reject every undeclared command-line assignment before handler selection.
# The allowlist is projected only from the typed Make contract.
ALLOWED_COMMAND_VARIABLES := WHAT APPLY CI PROJECT PROJECTS CHECK_GATES FAIL_FAST DEPENDENCY BRANCH BASE ARGS FILE MATCH WORKSPACE DIAG VERBOSE
COMMAND_VARIABLES := $(foreach variable,$(.VARIABLES),$(if $(filter command line,$(origin $(variable))),$(variable)))
UNKNOWN_COMMAND_VARIABLES := $(filter-out $(ALLOWED_COMMAND_VARIABLES),$(COMMAND_VARIABLES))
ifneq ($(strip $(UNKNOWN_COMMAND_VARIABLES)),)
$(error undeclared Make variable(s): $(UNKNOWN_COMMAND_VARIABLES))
endif

# Every optional public input is declared once in config and transported once.
# Parsing and conflict detection happen at the typed Python boundary.
override export FLEXT_MAKE_INPUT_PROJECT := $(value PROJECT)
override export FLEXT_MAKE_INPUT_PROJECTS := $(value PROJECTS)
override export FLEXT_MAKE_INPUT_CHECK_GATES := $(value CHECK_GATES)
override export FLEXT_MAKE_INPUT_FAIL_FAST := $(value FAIL_FAST)
override export FLEXT_MAKE_INPUT_DEPENDENCY := $(value DEPENDENCY)
override export FLEXT_MAKE_INPUT_BRANCH := $(value BRANCH)
override export FLEXT_MAKE_INPUT_BASE := $(value BASE)
override export FLEXT_MAKE_INPUT_ARGS := $(value ARGS)
override export FLEXT_MAKE_INPUT_FILE := $(value FILE)
override export FLEXT_MAKE_INPUT_MATCH := $(value MATCH)
override export FLEXT_MAKE_INPUT_WORKSPACE := $(value WORKSPACE)
override export FLEXT_MAKE_INPUT_DIAG := $(value DIAG)
override export FLEXT_MAKE_INPUT_VERBOSE := $(value VERBOSE)


# The configured profile decides who owns the environment. No verb carries a
# workspace/root/standalone recipe variant.
RUNTIME_ROOT := $(PROJECT_ROOT)

RUNTIME_VENV := $(RUNTIME_ROOT)/.venv
ifeq ($(OS),Windows_NT)
RUNTIME_PYTHON := $(RUNTIME_VENV)/Scripts/python.exe
else
RUNTIME_PYTHON := $(RUNTIME_VENV)/bin/python
endif

# Bootstrap operations work before setup. Runtime operations use the one
# environment selected by the profile; the executor validates its capability.
FLEXT_INFRA_BOOTSTRAP_REQUIREMENT := flext-infra @ git+https://github.com/flext-sh/flext-infra.git@0.12.0-dev
UV_BOOTSTRAP_FLAGS := --isolated --all-groups --all-extras
FLEXT_INFRA_BOOTSTRAP := env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT $(UV) run --project "$(PROJECT_ROOT)" $(UV_BOOTSTRAP_FLAGS) --with-editable "$(abspath $(PROJECT_ROOT)/.)" python -m flext_infra
PROJECT_FLEXT_INFRA := test -x "$(RUNTIME_PYTHON)" || { printf 'ERROR: missing managed environment %s; run make setup\n' "$(RUNTIME_PYTHON)" >&2; exit 2; }; env -u PYTHONPATH -u MYPYPATH "$(RUNTIME_PYTHON)" -m flext_infra

PUBLIC_VERBS := help setup deps build check test fmt fix run status docs clean release conform gen worktree
BOOTSTRAP_VERBS := help setup clean
MAKE_OPERATION_EXECUTOR = $(if $(filter $@,$(BOOTSTRAP_VERBS)),$(FLEXT_INFRA_BOOTSTRAP),$(PROJECT_FLEXT_INFRA))

.PHONY: $(PUBLIC_VERBS)

# One generated recipe executes every builtin and repository extension. The
# runtime graph resolves operation, scope, capabilities, inputs, APPLY,
# locking, and the existing implementation owner.
$(PUBLIC_VERBS):
	@$(MAKE_OPERATION_EXECUTOR) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "$@" --selector-value "$(value WHAT)" --apply-token "$(value APPLY)" --make-level "$(MAKELEVEL)"
