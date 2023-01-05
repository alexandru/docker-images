FROM --platform=linux/amd64 ubuntu:latest
SHELL ["/bin/bash", "-c"]

RUN apt update && apt upgrade -y && apt install -y curl zip unzip
# # Installs SDKMan!
RUN curl -s "https://get.sdkman.io" | bash

# Installs Java (should be latest Temurin LTS)
RUN source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install java
# Installs build tools
RUN source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install maven
RUN source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install gradle
RUN source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install sbt
RUN source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install scalacli
RUN source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install jbang
