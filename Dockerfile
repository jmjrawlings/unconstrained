ARG MINIZINC_VERSION=2.6.2
ARG ORTOOLS_VERSION=9.3
ARG ORTOOLS_BUILD=10502
ARG UBUNTU_VERSION=20.04
ARG PYTHON_VERSION=3.9
ARG MINIZINC_HOME=/usr/local/share/minizinc
ARG DEBIAN_FRONTEND=noninteractive
ARG APP_PATH=/app
ARG USER_NAME=hrkn
ARG USER_UID=1000
ARG USER_GID=$USER_UID

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

ARG MINIZINC_HOME
ARG ORTOOLS_VERSION
ARG ORTOOLS_BUILD
ARG UBUNTU_VERSION
ENV ORTOOLS_TAR_NAME=or-tools_amd64_flatzinc_ubuntu-${UBUNTU_VERSION}_v${ORTOOLS_VERSION}.${ORTOOLS_BUILD}
ENV ORTOOLS_TAR_URL=https://github.com/google/or-tools/releases/download/v${ORTOOLS_VERSION}/${ORTOOLS_TAR_NAME}.tar.gz
ENV ORTOOLS_HOME=${MINIZINC_HOME}/ortools
ENV ORTOOLS_MSC=${MINIZINC_HOME}/solvers/ortools.msc
ARG DEBIAN_FRONTEND

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        wget
    
# Install OR-Tools into MiniZinc directory
RUN mkdir ${ORTOOLS_HOME} && \
    wget -c ${ORTOOLS_TAR_URL} -O - | \
    tar -xz -C ${ORTOOLS_HOME} --strip-components=1

# Register OR-Tools as a MiniZinc solver
RUN echo '{ \n\
    "id": "org.ortools.ortools", \n\
    "name": "OR Tools", \n\
    "description": "Or Tools FlatZinc executable", \n\
    "version": "$ORTOOLS_VERSION/stable", \n\
    "mznlib": "../ortools/share/minizinc", \n\
    "executable": "../ortools/bin/fzn-or-tools",     \n\
    "tags": ["cp","int", "lcg", "or-tools"], \n\
    "stdFlags": ["-a", "-n", "-p", "-f", "-r", "-v", "-l", "-s"], \n\
    "supportsMzn": false, \n\
    "supportsFzn": true, \n\
    "needsSolns2Out": true, \n\
    "needsMznExecutable": false, \n\
    "needsStdlibDir": false, \n\
    "isGUIApplication": false \n\
    }' >> ${ORTOOLS_MSC}


# ********************************************************
# * Builder
#
# This is the base Ubuntu layer that is built upon by other 
# layers. It contains Python, MiniZinc, and other key 
# dependencies
# ********************************************************

ARG UBUNTU_VERSION
FROM ubuntu:${UBUNTU_VERSION} as builder

ARG PYTHON_VERSION
ARG DEBIAN_FRONTEND
ARG APP_PATH
ENV PYTHON_NAME=python$PYTHON_VERSION

RUN mkdir $APP_PATH
WORKDIR $APP_PATH

# Install Python3 + helpful packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-transport-https \
        build-essential \
        ca-certificates \
        curl \
        gnupg2 \ 
        $PYTHON_NAME \
        $PYTHON_NAME-dev \
        $PYTHON_NAME-venv \
        python3-pip \
        python3-wheel \
        sqlite3 \
        sudo \
        wget


# Copy MiniZinc + ORTools from the build layer
ARG MINIZINC_HOME
COPY --from=minizinc-builder ${MINIZINC_HOME} ${MINIZINC_HOME}
COPY --from=minizinc-builder /usr/local/bin/ /usr/local/bin/

# Create a python virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN $PYTHON_NAME -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN echo "$VIRTUAL_ENV/bin:$PATH" >> /etc/environment

# Install Python packages
ADD ./requirements/base.txt requirements.txt
RUN pip install pip-tools && pip-sync requirements.txt

# Create an alternate user with root priveleges
ARG USER_NAME
ARG USER_UID
ARG USER_GID

RUN groupadd --gid $USER_GID $USER_NAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USER_NAME \
    && echo $USER_NAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USER_NAME \
    && chmod 0440 /etc/sudoers.d/$USER_NAME
RUN usermod -aG sudo $USER_NAME


# ********************************************************
# * Dev
# 
# This layer contains everything needed for a fully 
# featured development environment.  It is intended to 
# be used with VSCode devcontainers.
# ********************************************************

FROM builder as dev

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
        zsh

# Install Docker CE CLI
RUN curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null \
    && echo "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        docker-ce-cli

# Install Docker Compose
RUN LATEST_COMPOSE_VERSION=$(curl -sSL "https://api.github.com/repos/docker/compose/releases/latest" | grep -o -P '(?<="tag_name": ").+(?=")') \
    && curl -sSL "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Install Dagger
RUN curl -sfL https://releases.dagger.io/dagger/install.sh | sh
RUN mv ./bin/dagger /usr/local/bin

# Install zsh & oh-my-zsh
ARG USER_NAME
USER $USER_NAME
WORKDIR /home/$USER_NAME
COPY .devcontainer/.p10k.zsh .
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.2/zsh-in-docker.sh)" -- \
    -p git \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions \
    && echo "[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh" >> ~/.zshrc \
    && bash -c 'zsh -is <<<exit &>/dev/null' \
    && $HOME/.oh-my-zsh/custom/themes/powerlevel10k/gitstatus/install


# Install Dev Python packages
WORKDIR $APP_PATH   
USER root
COPY ./requirements/dev.txt requirements.txt
RUN pip-sync requirements.txt && rm requirements.txt

USER $USER_NAME

# ********************************************************
# * Test
#
# This layer copies the source code and installs dependencies
# required to test the code.  Could be used in a CI/CD 
# pipeline or similar.
# ********************************************************

FROM builder as test

WORKDIR $APP_PATH

# Install Test Python packages
COPY ./requirements/test.txt requirements.txt
RUN pip-sync requirements.txt

# Copy source code
COPY ./tests ./tests
COPY ./unconstrained ./unconstrained 
COPY ./examples ./examples
COPY ./pytest.ini . 

ARG USER_NAME
USER $USER_NAME