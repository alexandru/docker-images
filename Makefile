BUILD_TOOLS_IMAGE          := ghcr.io/alexandru/jdk-build-tools
BUILD_TOOLS_TAG            := ${BUILD_TOOLS_IMAGE}:latest
BUILD_TOOLS_DEV_IMAGE      := ghcr.io/alexandru/jdk-build-tools-devcontainer
BUILD_TOOLS_DEV_TAG        := ${BUILD_TOOLS_DEV_IMAGE}:latest
JRE17_MINIMAL_DEBIAN_IMAGE := ghcr.io/alexandru/jre17-minimal-debian
JRE17_MINIMAL_DEBIAN_TAG   := ${JRE17_MINIMAL_DEBIAN_IMAGE}:latest
JRE17_MINIMAL_ALPINE_IMAGE := ghcr.io/alexandru/jre17-minimal-alpine
JRE17_MINIMAL_ALPINE_TAG   := ${JRE17_MINIMAL_ALPINE_IMAGE}:latest
CONTAINER_CLI              ?= $(shell command -v wslc.exe 2>/dev/null || command -v wslc 2>/dev/null || command -v docker 2>/dev/null || command -v podman 2>/dev/null)
PLATFORM                   ?= linux/amd64
PLATFORM_TAG               = $(subst /,-,${PLATFORM})
BUILD_TOOLS_PLATFORM_TAG   = ${BUILD_TOOLS_IMAGE}:${PLATFORM_TAG}
BUILD_TOOLS_DEV_PLATFORM_TAG = ${BUILD_TOOLS_DEV_IMAGE}:${PLATFORM_TAG}
JRE17_MINIMAL_DEBIAN_PLATFORM_TAG = ${JRE17_MINIMAL_DEBIAN_IMAGE}:${PLATFORM_TAG}
JRE17_MINIMAL_ALPINE_PLATFORM_TAG = ${JRE17_MINIMAL_ALPINE_IMAGE}:${PLATFORM_TAG}

check-container-cli:
	@test -n "${CONTAINER_CLI}" || (echo "No container CLI found. Install wslc.exe, docker, or podman, or set CONTAINER_CLI=/path/to/cli." >&2; exit 1)

init-docker-buildx:
	docker buildx inspect mybuilder >/dev/null 2>&1 || docker buildx create --name mybuilder
	docker buildx use mybuilder

build-jdk-build-tools: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jdk-build-tools -t "${BUILD_TOOLS_TAG}" .

push-jdk-build-tools: check-container-cli
	"${CONTAINER_CLI}" push "${BUILD_TOOLS_TAG}"

build-jdk-build-tools-platform: init-docker-buildx
	docker buildx build --platform "${PLATFORM}" -f ./Dockerfile.jdk-build-tools -t "${BUILD_TOOLS_PLATFORM_TAG}" ${DOCKER_EXTRA_ARGS} .

push-jdk-build-tools-platform:
	DOCKER_EXTRA_ARGS="--push" $(MAKE) build-jdk-build-tools-platform

push-jdk-build-tools-manifest: init-docker-buildx
	docker buildx imagetools create -t "${BUILD_TOOLS_TAG}" \
		"${BUILD_TOOLS_IMAGE}:linux-amd64" \
		"${BUILD_TOOLS_IMAGE}:linux-arm64"

build-jdk-build-tools-devcontainer: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jdk-build-tools-devcontainer -t "${BUILD_TOOLS_DEV_TAG}" .

push-jdk-build-tools-devcontainer: check-container-cli
	"${CONTAINER_CLI}" push "${BUILD_TOOLS_DEV_TAG}"

build-jdk-build-tools-devcontainer-platform: init-docker-buildx
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

build-jre17-minimal-debian-platform: init-docker-buildx
	docker buildx build --platform "${PLATFORM}" -f ./Dockerfile.jre17-minimal-debian -t "${JRE17_MINIMAL_DEBIAN_PLATFORM_TAG}" ${DOCKER_EXTRA_ARGS} .

push-jre17-minimal-debian-platform:
	DOCKER_EXTRA_ARGS="--push" $(MAKE) build-jre17-minimal-debian-platform

push-jre17-minimal-debian-manifest: init-docker-buildx
	docker buildx imagetools create -t "${JRE17_MINIMAL_DEBIAN_TAG}" \
		"${JRE17_MINIMAL_DEBIAN_IMAGE}:linux-amd64" \
		"${JRE17_MINIMAL_DEBIAN_IMAGE}:linux-arm64"

build-jre17-minimal-alpine: check-container-cli
	"${CONTAINER_CLI}" build -f ./Dockerfile.jre17-minimal-alpine -t "${JRE17_MINIMAL_ALPINE_TAG}" .

push-jre17-minimal-alpine: check-container-cli
	"${CONTAINER_CLI}" push "${JRE17_MINIMAL_ALPINE_TAG}"

build-jre17-minimal-alpine-platform: init-docker-buildx
	docker buildx build --platform "${PLATFORM}" -f ./Dockerfile.jre17-minimal-alpine -t "${JRE17_MINIMAL_ALPINE_PLATFORM_TAG}" ${DOCKER_EXTRA_ARGS} .

push-jre17-minimal-alpine-platform:
	DOCKER_EXTRA_ARGS="--push" $(MAKE) build-jre17-minimal-alpine-platform

push-jre17-minimal-alpine-manifest: init-docker-buildx
	docker buildx imagetools create -t "${JRE17_MINIMAL_ALPINE_TAG}" \
		"${JRE17_MINIMAL_ALPINE_IMAGE}:linux-amd64" \
		"${JRE17_MINIMAL_ALPINE_IMAGE}:linux-arm64"
