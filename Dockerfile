# ********************************************************
# Key Arguments
# ********************************************************
ARG UBUNTU_VERSION=20.04
ARG PYTHON_VERSION=3.9
ARG PYTHON_VENV=/opt/venv
ARG MINIZINC_VERSION=2.6.0
ARG MINIZINC_HOME=/usr/local/share/minizinc
ARG ORTOOLS_VERSION=9.3
ARG ORTOOLS_BUILD=10502
ARG DAGGER_VERSION=0.2.30
ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=jmjr
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG APP_PATH="/unconstrained"

# ********************************************************
# MiniZinc Builder
#
# This layer installs MiniZinc into the $MINIZINC_HOME
# directory which is later copied to other images.
#
# Google OR-Tools solver for MiniZinc is also installed
#
# ********************************************************
FROM minizinc/minizinc:${MINIZINC_VERSION} as minizinc-builder

ARG UBUNTU_VERSION
ARG MINIZINC_HOME
ARG ORTOOLS_VERSION
ARG ORTOOLS_BUILD
ARG ORTOOLS_HOME=$MINIZINC_HOME/ortools
ARG ORTOOLS_TAR_NAME=or-tools_amd64_flatzinc_ubuntu-${UBUNTU_VERSION}_v$ORTOOLS_VERSION.$ORTOOLS_BUILD
ARG ORTOOLS_TAR_URL=https://github.com/google/or-tools/releases/download/v$ORTOOLS_VERSION/$ORTOOLS_TAR_NAME.tar.gz
ARG DEBIAN_FRONTEND

# Install required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
    && rm -rf /var/lib/apt/lists/*
    
# Install OR-Tools into MiniZinc directory
RUN mkdir $ORTOOLS_HOME && \
    wget -c $ORTOOLS_TAR_URL -O - | \
    tar -xz -C $ORTOOLS_HOME --strip-components=1

# Register OR-Tools as a MiniZinc solver
RUN echo '{ \n\
    "id": "org.ortools.ortools",\n\
    "name": "OR Tools",\n\
    "description": "Or Tools FlatZinc executable",\n\
    "version": "'$ORTOOLS_VERSION/stable'",\n\
    "mznlib": "../ortools/share/minizinc",\n\
    "executable": "../ortools/bin/fzn-or-tools",\n\
    "tags": ["cp","int", "lcg", "or-tools"], \n\
    "stdFlags": ["-a", "-n", "-p", "-f", "-r", "-v", "-l", "-s"], \n\
    "supportsMzn": false,\n\
    "supportsFzn": true,\n\
    "needsSolns2Out": true,\n\
    "needsMznExecutable": false,\n\
    "needsStdlibDir": false,\n\
    "isGUIApplication": false\n\
}' >> $MINIZINC_HOME/solvers/ortools.msc


# ********************************************************
# * Python Layer
# ********************************************************
FROM python:3.9-slim as builder

ARG PYTHON_VENV
ARG USERNAME
ARG USER_UID
ARG USER_GID

# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#         gcc

ENV PATH="$VIRTUAL_ENV/bin:$PATH"    


# ********************************************************
# * Base Layer
# *
# * This is the base Ubuntu layer that is built upon by other 
# * layers. It contains Python, MiniZinc, and other key 
# * dependencies
# ********************************************************

FROM python:3.9-slim as base

ARG PYTHON_VENV
ARG PYTHON_VERSION
ARG MINIZINC_HOME
ARG DEBIAN_FRONTEND
ARG USERNAME
ARG USER_GID
ARG USER_UID

ENV PYTHON_NAME=python$PYTHON_VERSION
ENV VIRTUAL_ENV=$PYTHON_VENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# ********************************************************
# * Add a non-root user
# ********************************************************

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN mkdir -p $PYTHON_VENV && chown -R $USERNAME $PYTHON_VENV

USER $USERNAME

# Copy Python virtual env
RUN python -m venv $PYTHON_VENV
RUN pip install pip-tools

# Copy MiniZinc + ORTools from the build layer
COPY --chown=$USERNAME --from=minizinc-builder $MINIZINC_HOME $MINIZINC_HOME
COPY --chown=$USERNAME --from=minizinc-builder /usr/local/bin/ /usr/local/bin/

# ********************************************************
# * Dev 
# * 
# * This targget contains everything needed for a fully 
# * featured development environment.  It is intended to 
# * be used as a devcontainer via VSCode remote development
# * extension.
# * 
# * See https://code.visualstudio.com/docs/remote/containers
# ********************************************************
FROM base as dev

ARG DEBIAN_FRONTEND
ARG USERNAME
ARG USER_UID
ARG USER_GID

USER root

# Install packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg2 \
        locales \
        lsb-release \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CE CLI
RUN curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null \
    && echo "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Docker Compose
RUN LATEST_COMPOSE_VERSION=$(curl -sSL "https://api.github.com/repos/docker/compose/releases/latest" | grep -o -P '(?<="tag_name": ").+(?=")') \
    && curl -sSL "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Install Dagger - TODO: pin version, should be refreshed to due to ARG
ARG DAGGER_VERSION
RUN curl -sfL https://releases.dagger.io/dagger/install.sh | sh \
    && mv ./bin/dagger /usr/local/bin \
    && echo $DAGGER_VERSION

# Give docker access to the non-root user
RUN groupadd docker && usermod -aG docker $USERNAME

# Install developer packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-powerline \
        openssh-client \
        micro \
        less \
        inotify-tools \
        htop \                                                  
        git \    
        zsh \
    && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER $USERNAME 

# Install zsh & oh-my-zsh
COPY .devcontainer/.p10k.zsh /home/$USERNAME/.p10k.zsh
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.2/zsh-in-docker.sh)" -- \
    -p git \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions \
    && echo "[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh" >> ~/.zshrc \
    && bash -c 'zsh -is <<<exit &>/dev/null' \
    && $HOME/.oh-my-zsh/custom/themes/powerlevel10k/gitstatus/install \
    && sudo usermod --shell $(which zsh) $USERNAME

# Install python packages
COPY ./requirements/dev.txt requirements.txt
RUN pip-sync requirements.txt --pip-args '--no-cache-dir'

CMD zsh

# ********************************************************
# * Test 
# *
# * This target contains only the code and dependencies 
# * needed to run tests.
# ********************************************************
FROM base as test

ARG APP_PATH
ARG USERNAME
ARG USER_GID
ARG USER_UID
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy source code
USER root
RUN mkdir $APP_PATH
WORKDIR $APP_PATH
COPY ./unconstrained ./unconstrained
COPY ./examples ./examples
COPY ./pytest.ini .
COPY ./tests ./tests
RUN chown -R $USER_UID:$USER_GID $APP_PATH


USER $USERNAME

# Install python packages
COPY ./requirements/test.txt ./requirements.txt
RUN pip-sync requirements.txt --pip-args '--no-cache-dir'

# Run pytest on container run
CMD pytest


# ********************************************************
# * Prod 
# *
# * This target contains only the source code and required
# * packages.
# ********************************************************
FROM base as prod

ARG APP_PATH
ARG USERNAME
ARG USER_GID
ARG USER_UID
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy source code
USER root
RUN mkdir $APP_PATH
WORKDIR $APP_PATH
COPY ./unconstrained ./unconstrained
COPY ./examples ./examples
RUN chown -R $USER_UID:$USER_GID $APP_PATH

USER $USERNAME

# Install python packages
COPY ./requirements/test.txt ./requirements.txt
RUN pip-sync requirements.txt --pip-args '--no-cache-dir'