NAME := ghcr.io/alexandru/jdk-build-tools
TAG  := ${NAME}:latest

build:
	docker build -f ./Dockerfile -t "${TAG}" .

push:
	docker push "${TAG}"
