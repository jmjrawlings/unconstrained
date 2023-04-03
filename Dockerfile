# ********************************************************
# * Key Arguments
# ********************************************************
ARG UBUNTU_VERSION=22.04
ARG PYTHON_VERSION=3.10
ARG DAGGER_VERSION=0.2.36
ARG MINIZINC_VERSION=2.7.1
ARG MINIZINC_HOME=/usr/local/share/minizinc
ARG ORTOOLS_VERSION=9.6
ARG ORTOOLS_BUILD=2534
ARG ORTOOLS_HOME=/opt/ortools
ARG QUARTO_HOME=/opt/quarto
ARG PYTHON_VENV=/opt/venv
ARG APP_PATH=/app
ARG USER_NAME=harken
ARG USER_UID=1000
ARG USER_GID=1000
ARG OPT_PATH=/opt
ARG DEBIAN_FRONTEND=noninteractive
ARG QUARTO_VERSION=1.2.475


# ********************************************************
# Builder
#
# Common packages used to build dependencies in the correct
# OS version
# ********************************************************
FROM ubuntu:${UBUNTU_VERSION} as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \        
        curl \
        wget \
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

# Install required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install OR-Tools
ARG UBUNTU_VERSION
ARG MINIZINC_HOME
ARG ORTOOLS_VERSION
ARG ORTOOLS_BUILD
ARG ORTOOLS_HOME
ARG ORTOOLS_VERSION_BUILD=${ORTOOLS_VERSION}.${ORTOOLS_BUILD}
ARG ORTOOLS_TAR_NAME=or-tools_amd64_ubuntu-${UBUNTU_VERSION}_cpp_v${ORTOOLS_VERSION_BUILD}.tar.gz
ARG ORTOOLS_TAR_URL=https://github.com/google/or-tools/releases/download/v${ORTOOLS_VERSION}/${ORTOOLS_TAR_NAME}
ARG ORTOOLS_DIR_NAME=or-tools_x86_64_Ubuntu-${UBUNTU_VERSION}_cpp_v${ORTOOLS_VERSION_BUILD}

# Download and unpack the C++ build for this OS
RUN wget -c ${ORTOOLS_TAR_URL} && \
    tar -xzvf ${ORTOOLS_TAR_NAME}

# Move the files to the correct location
RUN mv ${ORTOOLS_DIR_NAME} ${ORTOOLS_HOME} && \
    cp ${ORTOOLS_HOME}/share/minizinc/solvers/* ${MINIZINC_HOME}/solvers \
    && cp -r ${ORTOOLS_HOME}/share/minizinc/ortools ${MINIZINC_HOME}/ortools \
    && ln -s ${ORTOOLS_HOME}/bin/fzn-ortools /usr/local/bin/fzn-ortools

# Test installation
RUN echo "var 1..9: x; constraint x > 5; solve satisfy;" \
  | minizinc --solver com.google.or-tools --input-from-stdin


# ********************************************************
# Quarto
# ********************************************************
FROM builder as quarto-base
ARG QUARTO_VERSION
ARG QUARTO_HOME
ARG QUARTO_NAME=quarto-${QUARTO_VERSION}
ARG QUARTO_TAR=${QUARTO_NAME}-linux-amd64.tar.gz

RUN wget -q https://github.com/quarto-dev/quarto-cli/releases/download/v$QUARTO_VERSION/$QUARTO_TAR \
    && tar -xzf ${QUARTO_TAR} \
    && mv ${QUARTO_NAME} ${QUARTO_HOME} && \
    rm ${QUARTO_TAR}


# ********************************************************
# python-base
#
# Base python venv to be used by other targets
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
# base
# 
# Base layer with core dependencies to be used by other
# layers
# ********************************************************
FROM python:${PYTHON_VERSION}-slim as base

ARG PYTHON_VENV
ARG USER_NAME=harken
ARG USER_GID=1000
ARG USER_UID=1000
ARG APP_PATH
ARG OPT_PATH
ARG MINIZINC_HOME
ARG ORTOOLS_HOME

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV VIRTUAL_ENV=$PYTHON_VENV
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Create the user
RUN groupadd --gid ${USER_GID} ${USER_NAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USER_NAME} \
    && apt-get update \
    && apt-get install -y sudo \
    && echo ${USER_NAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER_NAME} \
    && chmod 0440 /etc/sudoers.d/${USER_NAME}

# # Create an assign app path
RUN mkdir $APP_PATH && chown -R $USER_NAME $APP_PATH

# # Install MiniZinc + ORTools from the build layer
COPY --from=minizinc-builder $MINIZINC_HOME $MINIZINC_HOME
COPY --from=minizinc-builder /usr/local/bin/ /usr/local/bin/
COPY --from=minizinc-builder $ORTOOLS_HOME $ORTOOLS_HOME

USER $USER_NAME     


# ********************************************************
# python-dev
# 
# A python venv with all of the dev dependencies installed
# ********************************************************
FROM python-base as python-dev

COPY ./requirements/requirements-dev.txt ./requirements.txt
RUN pip-sync ./requirements.txt && rm ./requirements.txt

# ********************************************************
# dev 
#  
# This target contains everything needed for a fully 
# featured development environment.  It is intended to 
# be used as a devcontainer via VSCode remote development
# extension.
#  
# See https://code.visualstudio.com/docs/remote/containers
# ********************************************************
FROM base as dev

ARG PYTHON_VENV
ARG USER_NAME
ARG USER_UID
ARG USER_GID
ARG DEBIAN_FRONTEND
ARG QUARTO_HOME

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
COPY --from=quarto-base --chown=${USER_UID}:${USER_GID} ${QUARTO_HOME} ${QUARTO_HOME}

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

CMD zsh


# ********************************************************
# python-test
#
# A python venv with all of the test dependencies installed
# ********************************************************
FROM python-base as python-test

COPY ./requirements/requirements-test.txt ./requirements.txt
RUN pip-sync ./requirements.txt && rm ./requirements.txt

# ********************************************************
# test 
# 
# Contains python source code, testing code, and all 
# dependencies required to run the test suite.
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
# python-prod
#
# A python venv with all of the prod dependencies installed
# ********************************************************
FROM python-base as python-prod

COPY ./requirements/requirements-prod.txt ./requirements.txt
RUN pip-sync ./requirements.txt && rm ./requirements.txt

# ********************************************************
# prod
#
# Contains source code and production dependencies ony
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