BUILD_TOOLS_TAG          := ghcr.io/alexandru/jdk-build-tools:latest
JRE17_MINIMAL_DEBIAN_TAG := ghcr.io/alexandru/jre17-minimal-debian:latest
JRE17_MINIMAL_ALPINE_TAG := ghcr.io/alexandru/jre17-minimal-alpine:latest

build-jdk-build-tools:
	docker build -f ./Dockerfile.jdk-build-tools -t "${BUILD_TOOLS_TAG}" .

push-jdk-build-tools:
	docker push "${BUILD_TOOLS_TAG}"

build-jre17-minimal-debian:
	docker build -f ./Dockerfile.jre17-minimal-debian -t "${JRE17_MINIMAL_DEBIAN_TAG}" .

push-jre17-minimal-debian:
	docker push "${JRE17_MINIMAL_DEBIAN_TAG}"

build-jre17-minimal-alpine:
	docker build -f ./Dockerfile.jre17-minimal-alpine -t "${JRE17_MINIMAL_ALPINE_TAG}" .

push-jre17-minimal-alpine:
	docker push "${JRE17_MINIMAL_ALPINE_TAG}"
