BUILD_TOOLS_TAG          := ghcr.io/alexandru/jdk-build-tools:latest
BUILD_TOOLS_DEV_TAG      := ghcr.io/alexandru/jdk-build-tools-devcontainer:latest
JRE17_MINIMAL_DEBIAN_TAG := ghcr.io/alexandru/jre17-minimal-debian:latest
JRE17_MINIMAL_ALPINE_TAG := ghcr.io/alexandru/jre17-minimal-alpine:latest
CONTAINER_CLI            ?= $(shell command -v wslc.exe 2>/dev/null || command -v wslc 2>/dev/null || command -v docker 2>/dev/null || command -v podman 2>/dev/null)
OPENCODE_CONFIG_REPO     := git@github.com:alexandru/opencode-config.git
OPENCODE_CONFIG_DIR      := .build/opencode-config

check-container-cli:
	@test -n "${CONTAINER_CLI}" || (echo "No container CLI found. Install wslc.exe, docker, or podman, or set CONTAINER_CLI=/path/to/cli." >&2; exit 1)

prepare-opencode-config:
	@if test -d "${OPENCODE_CONFIG_DIR}/.git"; then \
		if test "$${GITHUB_ACTIONS:-}" != "true"; then \
			git -C "${OPENCODE_CONFIG_DIR}" remote set-url origin "${OPENCODE_CONFIG_REPO}"; \
			git -C "${OPENCODE_CONFIG_DIR}" fetch --depth 1 origin HEAD; \
			git -C "${OPENCODE_CONFIG_DIR}" reset --hard FETCH_HEAD; \
		fi; \
	else \
		rm -rf "${OPENCODE_CONFIG_DIR}"; \
		mkdir -p .build; \
		git clone --depth 1 "${OPENCODE_CONFIG_REPO}" "${OPENCODE_CONFIG_DIR}"; \
	fi

build-jdk-build-tools: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jdk-build-tools -t "${BUILD_TOOLS_TAG}" .

push-jdk-build-tools: check-container-cli
	"${CONTAINER_CLI}" push "${BUILD_TOOLS_TAG}"

build-jdk-build-tools-devcontainer: check-container-cli prepare-opencode-config
	"${CONTAINER_CLI}" build -f ./Dockerfile.jdk-build-tools-devcontainer -t "${BUILD_TOOLS_DEV_TAG}" .

push-jdk-build-tools-devcontainer: check-container-cli
	"${CONTAINER_CLI}" push "${BUILD_TOOLS_DEV_TAG}"

build-jre17-minimal-debian: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jre17-minimal-debian -t "${JRE17_MINIMAL_DEBIAN_TAG}" .

push-jre17-minimal-debian: check-container-cli
	"${CONTAINER_CLI}" push "${JRE17_MINIMAL_DEBIAN_TAG}"

build-jre17-minimal-alpine: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jre17-minimal-alpine -t "${JRE17_MINIMAL_ALPINE_TAG}" .

push-jre17-minimal-alpine: check-container-cli
	"${CONTAINER_CLI}" push "${JRE17_MINIMAL_ALPINE_TAG}"
