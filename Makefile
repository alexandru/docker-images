BUILD_TOOLS_TAG          := ghcr.io/alexandru/jdk-build-tools:latest
BUILD_TOOLS_DEV_IMAGE    := ghcr.io/alexandru/jdk-build-tools-devcontainer
BUILD_TOOLS_DEV_TAG      := ${BUILD_TOOLS_DEV_IMAGE}:latest
JRE17_MINIMAL_DEBIAN_TAG := ghcr.io/alexandru/jre17-minimal-debian:latest
JRE17_MINIMAL_ALPINE_TAG := ghcr.io/alexandru/jre17-minimal-alpine:latest
CONTAINER_CLI            ?= $(shell command -v wslc.exe 2>/dev/null || command -v wslc 2>/dev/null || command -v docker 2>/dev/null || command -v podman 2>/dev/null)
OPENCODE_CONFIG_REPO     := git@github.com:alexandru/opencode-config.git
OPENCODE_CONFIG_DIR      := .build/opencode-config
PLATFORM                 ?= linux/amd64
PLATFORM_TAG             = $(subst /,-,${PLATFORM})
BUILD_TOOLS_DEV_PLATFORM_TAG = ${BUILD_TOOLS_DEV_IMAGE}:${PLATFORM_TAG}

check-container-cli:
	@test -n "${CONTAINER_CLI}" || (echo "No container CLI found. Install wslc.exe, docker, or podman, or set CONTAINER_CLI=/path/to/cli." >&2; exit 1)

init-docker-buildx:
	docker buildx inspect mybuilder >/dev/null 2>&1 || docker buildx create --name mybuilder
	docker buildx use mybuilder

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

build-jdk-build-tools-devcontainer-platform: init-docker-buildx prepare-opencode-config
	docker buildx build --platform "${PLATFORM}" -f ./Dockerfile.jdk-build-tools-devcontainer -t "${BUILD_TOOLS_DEV_PLATFORM_TAG}" ${DOCKER_EXTRA_ARGS} .

push-jdk-build-tools-devcontainer-platform:
	DOCKER_EXTRA_ARGS="--push" $(MAKE) build-jdk-build-tools-devcontainer-platform

push-jdk-build-tools-devcontainer-manifest: init-docker-buildx
	docker buildx imagetools create -t "${BUILD_TOOLS_DEV_TAG}" \
		"${BUILD_TOOLS_DEV_IMAGE}:linux-amd64" \
		"${BUILD_TOOLS_DEV_IMAGE}:linux-arm64"

build-jre17-minimal-debian: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jre17-minimal-debian -t "${JRE17_MINIMAL_DEBIAN_TAG}" .

push-jre17-minimal-debian: check-container-cli
	"${CONTAINER_CLI}" push "${JRE17_MINIMAL_DEBIAN_TAG}"

build-jre17-minimal-alpine: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jre17-minimal-alpine -t "${JRE17_MINIMAL_ALPINE_TAG}" .

push-jre17-minimal-alpine: check-container-cli
	"${CONTAINER_CLI}" push "${JRE17_MINIMAL_ALPINE_TAG}"
