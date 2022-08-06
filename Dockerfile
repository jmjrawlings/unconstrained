# ********************************************************
# * Key Arguments
# ********************************************************
ARG UBUNTU_VERSION=20.04
ARG PYTHON_VERSION=3.9
ARG MINIZINC_VERSION=2.6.4
ARG ORTOOLS_VERSION=9.3
ARG ORTOOLS_BUILD=10502
ARG DAGGER_VERSION=0.2.28

ARG PYTHON_VENV=/opt/venv
ARG MINIZINC_HOME=/usr/local/share/minizinc


# ********************************************************
# * MiniZinc Builder
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
ARG ORTOOLS_MSC=$MINIZINC_HOME/solvers/ortools.msc
ARG DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
    
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
}' >> $ORTOOLS_MSC


# ********************************************************
# * Builder
#
# This is the base Ubuntu layer that is built upon by other 
# layers. It contains Python, MiniZinc, and other key 
# dependencies
# ********************************************************

FROM ubuntu:$UBUNTU_VERSION as base

ARG PYTHON_VENV
ARG PYTHON_VERSION
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHON_NAME=python$PYTHON_VERSION
ENV VIRTUAL_ENV=$PYTHON_VENV

# Install Python3 + helpful packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        $PYTHON_NAME \
        $PYTHON_NAME-dev \
        $PYTHON_NAME-venv \
        apt-transport-https \
        build-essential \
        ca-certificates \
        curl \
        gnupg2 \ 
        python3-pip \
        python3-wheel \
        sqlite3 \
        sudo \
        wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy MiniZinc + ORTools from the build layer
ARG MINIZINC_HOME
COPY --from=minizinc-builder $MINIZINC_HOME $MINIZINC_HOME
COPY --from=minizinc-builder /usr/local/bin/ /usr/local/bin/

# Create a python virtual environment
RUN $PYTHON_NAME -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install pip-tools


# ********************************************************
# * Dev 
# 
# This layer contains everything needed for a fully 
# featured development environment.  It is intended to 
# be used as a devcontainer via VSCode remote development
# extension.
# 
# See https://code.visualstudio.com/docs/remote/containers
# ********************************************************

FROM base as dev

ARG DEBIAN_FRONTEND=noninteractive

# Install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-powerline \
        git \    
        htop \
        inotify-tools \
        less \
        locales \
        lsb-release \
        micro \
        openssh-client \
        zsh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Docker CE CLI
RUN curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null \
    && echo "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        docker-ce-cli

# Install Docker Compose
RUN LATEST_COMPOSE_VERSION=$(curl -sSL "https://api.github.com/repos/docker/compose/releases/latest" | grep -o -P '(?<="tag_name": ").+(?=")') \
    && curl -sSL "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Install Dagger - TODO: pin version
ARG DAGGER_VERSION
RUN curl -sfL https://releases.dagger.io/dagger/install.sh | sh \
    && mv ./bin/dagger /usr/local/bin

# Install zsh & oh-my-zsh
COPY .devcontainer/.p10k.zsh /root/.p10k.zsh
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.2/zsh-in-docker.sh)" -- \
    -p git \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions \
    && echo "[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh" >> ~/.zshrc \
    && bash -c 'zsh -is <<<exit &>/dev/null' \
    && $HOME/.oh-my-zsh/custom/themes/powerlevel10k/gitstatus/install \
    && sudo usermod --shell $(which zsh) root

# Install Dev Python packages
COPY ./requirements/dev.txt requirements.txt
RUN pip-sync requirements.txt \
    && rm requirements.txt

# ********************************************************
# * Test
#
# This layer contains only the code and dependencies 
# needed to run tests.
# ********************************************************

FROM base as test

ARG APP_PATH="/unconstrained"

WORKDIR $APP_PATH

# Install Python testing packages
COPY ./requirements/test.txt requirements.txt
RUN pip-sync requirements.txt --pip-args '--no-cache-dir' \
    && rm requirements.txt

# Copy source code
COPY ./tests ./tests
COPY ./unconstrained ./unconstrained 
COPY ./examples ./examples
COPY ./pytest.ini .


# ********************************************************
# * Prod
#
# This target contains only the source code and required
# packages.
# ********************************************************

FROM base as prod

ARG APP_PATH="/unconstrained"

WORKDIR $APP_PATH

# Install Python testing packages
COPY ./requirements/test.txt requirements.txt
RUN pip-sync requirements.txt --pip-args '--no-cache-dir' \
    && rm requirements.txt

# Copy source code
COPY ./unconstrained ./unconstrained 
COPY ./examples ./examples