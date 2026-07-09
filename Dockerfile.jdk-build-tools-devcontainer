FROM ubuntu:26.04

ARG USER_UID="1000"
ARG USER_GID="1000"
ARG NODE_MAJOR="24"

SHELL ["/bin/bash", "-lc"]
ENV DEBIAN_FRONTEND=noninteractive
ENV SDKMAN_DIR=/opt/sdkman

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        direnv \
        git \
        gnupg \
        less \
        openssh-client \
        sudo \
        tar \
        unzip \
        wget \
        zip && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*

RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs openjdk-21-jdk-headless && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*

RUN mkdir -p /etc/ssh/ssh_known_hosts.d && \
    ssh-keyscan github.com > /etc/ssh/ssh_known_hosts

RUN curl -fsSL "https://get.sdkman.io?ci=true&rcupdate=false" | bash && \
    sed -i 's/^sdkman_auto_env=.*/sdkman_auto_env=true/' "$SDKMAN_DIR/etc/config" && \
    rm -rf "$SDKMAN_DIR/tmp"/*

RUN mkdir -p /tmp/opencode-home && \
    curl -fsSL https://opencode.ai/install | HOME=/tmp/opencode-home bash -s -- --no-modify-path && \
    /tmp/opencode-home/.opencode/bin/opencode --version && \
    cp /tmp/opencode-home/.opencode/bin/opencode /usr/local/bin/opencode && \
    chmod 0755 /usr/local/bin/opencode && \
    rm -rf /tmp/opencode-home

RUN if getent group "$USER_GID" >/dev/null; then \
        existing_group="$(getent group "$USER_GID" | cut -d: -f1)"; \
        if [ "$existing_group" != "dev" ]; then \
            groupmod -n dev "$existing_group"; \
        fi; \
    else \
        groupadd -g "$USER_GID" dev; \
    fi && \
    if getent passwd "$USER_UID" >/dev/null; then \
        existing_user="$(getent passwd "$USER_UID" | cut -d: -f1)"; \
        if [ "$existing_user" != "dev" ]; then \
            usermod -l dev "$existing_user"; \
        fi; \
        usermod -d /home/dev -m -s /bin/bash -g dev dev; \
    else \
        useradd -m -s /bin/bash -g dev -u "$USER_UID" dev; \
    fi && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/dev && \
    chmod 0440 /etc/sudoers.d/dev && \
    mkdir -p /workspaces /home/dev/.config && \
    chown -R dev:dev /opt/sdkman /workspaces /home/dev

ENV HOME=/home/dev
ENV PATH="/opt/opencode-config/bin:/usr/local/bin:${PATH}"

COPY bin/devcontainer-entrypoint /usr/local/bin/devcontainer-entrypoint
COPY bin/osc52-clipboard /usr/local/bin/osc52-clipboard
RUN chmod 0755 /usr/local/bin/devcontainer-entrypoint /usr/local/bin/osc52-clipboard && \
    ln -sf /usr/local/bin/osc52-clipboard /usr/local/bin/wl-copy && \
    ln -sf /usr/local/bin/osc52-clipboard /usr/local/bin/xclip && \
    ln -sf /usr/local/bin/osc52-clipboard /usr/local/bin/xsel && \
    printf '\nexport SDKMAN_DIR=/opt/sdkman\n[ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ] && source "$SDKMAN_DIR/bin/sdkman-init.sh"\n' >> /etc/bash.bashrc && \
    mkdir -p /home/dev/.config/opencode && \
    chown -R dev:dev /home/dev/.config

USER dev
WORKDIR /home/dev
VOLUME ["/home/dev"]
EXPOSE 10012
ENTRYPOINT ["/usr/local/bin/devcontainer-entrypoint"]
CMD ["bash"]
