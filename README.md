# Docker Images

[![.github/workflows/push.yml](https://github.com/alexandru/docker-images/actions/workflows/push.yml/badge.svg)](https://github.com/alexandru/docker-images/actions/workflows/push.yml)

Personal Docker images that I need as a baseline for other things.

| Image | Build | Description |
|------------|------|-------------|
| [ghcr.io/alexandru/jdk-build-tools:latest](https://github.com/alexandru/docker-images/pkgs/container/jdk-build-tools) | [Dockerfile](./Dockerfile.jdk-build-tools) | Meant for building JVM projects, has OpenJDK installed with all the build tools (sbt, gradle, maven, scalacli, jbang) |
| [ghcr.io/alexandru/jdk-build-tools-devcontainer:latest](https://github.com/alexandru/docker-images/pkgs/container/jdk-build-tools-devcontainer) | [Dockerfile](./Dockerfile.jdk-build-tools-devcontainer) | Ubuntu dev container for linux/amd64 and linux/arm64 with JVM build tools, Git, OpenSSH client, and sudo. |
| [ghcr.io/alexandru/jre17-minimal-debian:latest](https://github.com/alexandru/docker-images/pkgs/container/jre17-minimal-debian) | [Dockerfile](./Dockerfile.jre17-minimal-debian) | Slim image with JRE17 installed, based on Debian. WARN: runtime is only installling the [java.se](https://docs.oracle.com/javase/9/docs/api/java.se-summary.html) module. |
| [ghcr.io/alexandru/jre17-minimal-alpine:latest](https://github.com/alexandru/docker-images/pkgs/container/jre17-minimal-alpine) | [Dockerfile](./Dockerfile.jre17-minimal-alpine) | Very slim image with JRE17 installed, based on Alpine. WARN: runtime is only installling the [java.se](https://docs.oracle.com/javase/9/docs/api/java.se-summary.html) module. |

NOTE: images are being rebuilt every week with the latest versions of the software, so they are kept up to date.

## Dev Container Usage

Start a container with a project mounted at `/workspace`:

```sh
./bin/devcontainer start /path/to/project
```

Open a shell in the container, starting it first if needed:

```sh
./bin/devcontainer shell /path/to/project
```

The script uses the first available CLI from `wslc.exe`, `wslc`, `docker`, or `podman`. It mounts the project at `/workspace` and persists `/home/dev` in a shared named volume, so settings applied after startup (for example opencode authentication) are available to every devcontainer.

Stop or restart the container for the same project:

```sh
./bin/devcontainer stop /path/to/project
./bin/devcontainer restart /path/to/project
```

Delete only the container for a project, keeping the shared `/home/dev` volume:

```sh
./bin/devcontainer purge /path/to/project
```

Delete all devcontainer containers, the shared `/home/dev` volume, and the devcontainer image:

```sh
./bin/devcontainer purge-all
```

For VS Code Dev Containers:

```json
{
  "image": "ghcr.io/alexandru/jdk-build-tools-devcontainer:latest",
  "remoteUser": "dev",
  "workspaceFolder": "/workspace",
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind",
  "mounts": [
    "source=jdk-build-tools-devcontainer-home,target=/home/dev,type=volume"
  ]
}
```

If you use WSL containers in VS Code, set the Dev Containers extension Docker Path setting to `wslc`.
