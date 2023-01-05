BUILD_TOOLS_TAG := ghcr.io/alexandru/jdk-build-tools:latest

build:
	docker build -f ./Dockerfile.jdk-build-tools -t "${BUILD_TOOLS_TAG}" .

push:
	docker push "${BUILD_TOOLS_TAG}"
