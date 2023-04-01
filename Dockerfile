# ********************************************************
# * Key Arguments
# ********************************************************
ARG PYTHON_VERSION=3.10
ARG DAGGER_VERSION=0.2.36
ARG MINIZINC_VERSION=2.7.1
ARG ORTOOLS_VERSION=9.5
ARG ORTOOLS_BUILD=2237
ARG UBUNTU_VERSION=20.04
ARG MINIZINC_HOME=/usr/local/share/minizinc
ARG PYTHON_VENV=/opt/venv
ARG APP_PATH=/app
ARG USER_NAME=harken
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG OPT_PATH=/opt
ARG DEBIAN_FRONTEND=noninteractive
ARG QUARTO_VERSION=1.2.475

# ********************************************************
# Builder
#
# Base image for building other dependencies
# ********************************************************
FROM ubuntu:$UBUNTU_VERSION as builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        wget \
        curl \    
    && rm -rf /var/lib/apt/lists/*

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
    
# # Install OR-Tools into MiniZinc directory
# RUN mkdir $ORTOOLS_HOME && \
#     wget -c $ORTOOLS_TAR_URL -O - | \
#     tar -xz -C $ORTOOLS_HOME --strip-components=1

# # Register OR-Tools as a MiniZinc solver
# RUN echo '{ \n\
#     "id": "org.ortools.ortools",\n\
#     "name": "OR Tools",\n\
#     "description": "Or Tools FlatZinc executable",\n\
#     "version": "'$ORTOOLS_VERSION/stable'",\n\
#     "mznlib": "../ortools/share/minizinc",\n\
#     "executable": "../ortools/bin/fzn-or-tools",\n\
#     "tags": ["cp","int", "lcg", "or-tools"], \n\
#     "stdFlags": ["-a", "-n", "-p", "-f", "-r", "-v", "-l", "-s"], \n\
#     "supportsMzn": false,\n\
#     "supportsFzn": true,\n\
#     "needsSolns2Out": true,\n\
#     "needsMznExecutable": false,\n\
#     "needsStdlibDir": false,\n\
#     "isGUIApplication": false\n\
# }' >> $MINIZINC_HOME/solvers/ortools.msc

# ********************************************************
# Quarto
# ********************************************************
FROM builder as quarto-base
ARG QUARTO_VERSION
ARG QUARTO_NAME=quarto-${QUARTO_VERSION}
ARG QUARTO_TAR=${QUARTO_NAME}-linux-amd64.tar.gz

RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v$QUARTO_VERSION/$QUARTO_TAR \
    && tar -C /opt -xvzf $QUARTO_TAR \
    && mv /opt/$QUARTO_NAME /opt/quarto

# ********************************************************
# * Python Base
# ********************************************************
FROM python:${PYTHON_VERSION}-slim as python-base

ARG PYTHON_VENV
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV VIRTUAL_ENV=$PYTHON_VENV
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Create the python virtual environment
RUN python -m venv ${PYTHON_VENV}

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pip-tools

WORKDIR ${PYTHON_VENV}


# ********************************************************
# * Base Layer
# *
# * Dependencies and environment variables used
# * by other targets.
# ********************************************************
FROM python:${PYTHON_VERSION}-slim as base

ARG PYTHON_VENV
ARG USER_NAME
ARG USER_GID
ARG USER_UID
ARG APP_PATH
ARG OPT_PATH
ARG MINIZINC_HOME

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV VIRTUAL_ENV=$PYTHON_VENV
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Add a non-root user
RUN groupadd --gid ${USER_GID} ${USER_NAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USER_NAME} \
    && apt-get update \
    && apt-get install -y sudo \
    && echo ${USER_NAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER_NAME} \
    && chmod 0440 /etc/sudoers.d/${USER_NAME}

# Create an assign app path
RUN mkdir $APP_PATH && chown -R $USER_NAME $APP_PATH

# Install MiniZinc + ORTools from the build layer
COPY --from=minizinc-builder $MINIZINC_HOME $MINIZINC_HOME
COPY --from=minizinc-builder /usr/local/bin/ /usr/local/bin/


# ********************************************************
# * Python Dev 
# ********************************************************
FROM python-base as python-dev

COPY ./requirements/requirements-dev.txt ./requirements.txt
RUN pip-sync ./requirements.txt && rm ./requirements.txt

# ********************************************************
# * Dev 
# * 
# * This target contains everything needed for a fully 
# * featured development environment.  It is intended to 
# * be used as a devcontainer via VSCode remote development
# * extension.
# * 
# * See https://code.visualstudio.com/docs/remote/containers
# ********************************************************
FROM base as dev

ARG PYTHON_VENV
ARG USER_NAME
ARG USER_UID
ARG USER_GID
ARG DEBIAN_FRONTEND
ARG QUARTO_VERSION

USER root

# Install core packages
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

# Give Docker access to the non-root user
RUN groupadd docker \
    && usermod -aG docker ${USER_NAME}

# Install Quarto
COPY --from=quarto-base --chown=${USER_UID}:${USER_GID} /opt/quarto ~/quarto

# Install Dagger - TODO: pin version, should be refreshed to due to ARG
ARG DAGGER_VERSION
RUN curl -sfL https://releases.dagger.io/dagger/install.sh | sh \
    && mv ./bin/dagger /usr/local/bin \
    && echo ${DAGGER_VERSION}

# Install Github CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt update \
    && sudo apt install gh -y \
    && rm -rf /var/lib/apt/lists/*

# Install Developer packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        autojump \
        fonts-powerline \
        openssh-client \
        micro \
        less \
        inotify-tools \
        htop \                                                  
        git \    
        tree \
        zsh \
    && rm -rf /var/lib/apt/lists/*

# Install gum.sh
RUN echo 'deb [trusted=yes] https://repo.charm.sh/apt/ /' | tee /etc/apt/sources.list.d/charm.list \
    && apt-get update \
    && apt-get install -y gum \
    && rm -rf /var/lib/apt/lists/*

# Install zsh & oh-my-zsh
USER ${USER_NAME}
WORKDIR /home/$USER_NAME
COPY .devcontainer/.p10k.zsh .p10k.zsh
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.3/zsh-in-docker.sh)" -- \
    -p git \
    -p docker \
    -p autojump \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions && \
    echo "[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh" >> ~/.zshrc && \
    .oh-my-zsh/custom/themes/powerlevel10k/gitstatus/install

# Install Python dependencies
COPY --from=python-dev --chown=${USER_UID}:${USER_GID} ${PYTHON_VENV} ${PYTHON_VENV}
RUN pip install pip-tools

CMD zsh
# Install python packages
COPY ./requirements/dev.txt requirements.txt
RUN pip-sync requirements.txt --pip-args '--no-cache-dir'

CMD zsh


# ********************************************************
# * Python Test Venv
# ********************************************************
FROM python-base as python-test

COPY ./requirements/requirements-test.txt ./requirements.txt
RUN pip-sync ./requirements.txt && rm ./requirements.txt

# ********************************************************
# * Test 
# *
# * This target contains python source code, testing code 
# * and all dependencies required to run the test suite.
# ********************************************************
FROM base as test

ARG APP_PATH
ARG USER_NAME
ARG USER_GID
ARG USER_UID

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

USER ${USER_NAME}
WORKDIR ${APP_PATH}
COPY ./src ./src
COPY ./tests ./tests
COPY ./pytest.ini .

COPY --from=python-test --chown=${USER_UID}:${USER_GID} ${PYTHON_VENV} ${PYTHON_VENV}

CMD pytest

# ********************************************************
# * Python Prod 
# ********************************************************
FROM python-base as python-prod

COPY ./requirements/requirements-prod.txt ./requirements.txt
RUN pip-sync ./requirements.txt && rm ./requirements.txt

# ********************************************************
FROM base as prod

ARG APP_PATH
ARG USER_NAME
ARG USER_GID
ARG USER_UID

ENV PYTHONOPTIMIZE=2
ENV PYTHONDONTWRITEBYTECODE=0

USER ${USER_NAME}
WORKDIR ${APP_PATH}
COPY ./src ./src

COPY --from=python-prod --chown=${USER_UID}:${USER_GID} ${PYTHON_VENV} ${PYTHON_VENV}