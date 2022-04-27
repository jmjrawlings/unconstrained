ARG MINIZINC_VERSION=2.6.2
ARG ORTOOLS_VERSION=9.3
ARG ORTOOLS_BUILD=10502
ARG UBUNTU_VERSION=20.04
ARG PYTHON_VERSION=3.9
ARG MINIZINC_HOME=/usr/local/share/minizinc
ARG DEBIAN_FRONTEND=noninteractive

# ===============================
# MiniZinc + ORTools Solver Layer
# ===============================
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
    wget \
&& rm -rf /var/lib/apt/lists/*

# Install OR-Tools into MiniZinc directory
RUN mkdir ${ORTOOLS_HOME} && \
    wget -c ${ORTOOLS_TAR_URL} -O - | \
    tar -xz -C ${ORTOOLS_HOME} --strip-components=1

# Register OR-Tools as a MiniZinc solver
RUN echo '{ \n\
    "id": "org.ortools.ortools", \n\
    "name": "OR Tools", \n\
    "description": "Or Tools FlatZinc executable", \n\
    "version": "9.3/stable", \n\
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


# ===============================
# Main Layer
# ===============================
ARG UBUNTU_VERSION
FROM ubuntu:${UBUNTU_VERSION} as builder

# Install Python3 + helpful packages
ARG PYTHON_VERSION
ARG DEBIAN_FRONTEND
ENV PYTHON_NAME=python$PYTHON_VERSION

RUN apt-get update && apt-get install -y --no-install-recommends \
    $PYTHON_NAME \
    $PYTHON_NAME-dev \
    $PYTHON_NAME-venv \
    python3-pip \
    python3-wheel \
    build-essential \
    ca-certificates \
    wget \
    curl \
    gnupg2 \ 
    micro \
    openssh-client \
    less \
    git \    
    locales \
    fonts-powerline \
    inotify-tools \
    htop \
&& rm -rf /var/lib/apt/lists/*

# Install Docker CE CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https ca-certificates curl gnupg2 lsb-release \
    && curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null \
    && echo "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli

# Install Docker Compose
RUN LATEST_COMPOSE_VERSION=$(curl -sSL "https://api.github.com/repos/docker/compose/releases/latest" | grep -o -P '(?<="tag_name": ").+(?=")') \
    && curl -sSL "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Copy MiniZinc + ORTools from the build layer
ARG MINIZINC_HOME
COPY --from=minizinc-builder ${MINIZINC_HOME} ${MINIZINC_HOME}
COPY --from=minizinc-builder /usr/local/bin/ /usr/local/bin/

# Create a python virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN $PYTHON_NAME -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install python packages
ADD requirements.txt .
RUN pip install pip-tools && \
    pip-sync requirements.txt

# ===============================
# Devcontainer
# ===============================
FROM builder as development

# Install zsh & oh-my-zsh
COPY .devcontainer/.p10k.zsh /root
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.2/zsh-in-docker.sh)" -- \
    -p git \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions \
    && echo "[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh" >> ~/.zshrc \
    && bash -c 'zsh -is <<<exit &>/dev/null'

# Install Dagger
RUN curl -sfL https://releases.dagger.io/dagger/install.sh | sh && \
    mv ./bin/dagger /usr/local/bin


# ===============================
# Testing
# ===============================        
FROM builder as testing
ARG APP_PATH=/app
RUN mkdir $APP_PATH
WORKDIR $APP_PATH

COPY ./tests ./tests
COPY ./unconstrained ./unconstrained 
COPY ./examples ./examples
COPY ./pytest.ini .