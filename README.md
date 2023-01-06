# Docker Images

[![.github/workflows/push.yml](https://github.com/alexandru/docker-images/actions/workflows/push.yml/badge.svg)](https://github.com/alexandru/docker-images/actions/workflows/push.yml)

Personal Docker images that I need as a baseline for other things.

| Image | Build | Description |
|------------|------|-------------|
| [ghcr.io/alexandru/jdk-build-tools:latest](https://github.com/alexandru/docker-images/pkgs/container/jdk-build-tools) | [Dockerfile](./Dockerfile.jdk-build-tools) | Meant for building JVM projects, has OpenJDK installed with all the build tools (sbt, gradle, maven, scalacli, jbang) |
| [ghcr.io/alexandru/jre17-minimal-debian:latest](https://github.com/alexandru/docker-images/pkgs/container/jre17-minimal-debian) | [Dockerfile](./Dockerfile.jre17-minimal-debian) | Slim image with JRE17 installed, based on Debian. |
| [ghcr.io/alexandru/jre17-minimal-alpine:latest](https://github.com/alexandru/docker-images/pkgs/container/jre17-minimal-alpine) | [Dockerfile](./Dockerfile.jre17-minimal-alpine) | Very slim image with JRE17 installed, based on Alpine. |

NOTE: images are being rebuilt every week with the latest versions of the software, so they are kept up to date.
