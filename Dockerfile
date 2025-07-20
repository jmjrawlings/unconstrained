# ********************************************************
# Key Arguments
# ********************************************************
ARG UBUNTU_VERSION=24.04
ARG PYTHON_VERSION=3.12
ARG MINIZINC_VERSION=2.9.3
ARG MINIZINC_HOME=/usr/local/share/minizinc
ARG ORTOOLS_VERSION=9.14
ARG ORTOOLS_BUILD=6206
ARG ORTOOLS_HOME=/opt/ortools
ARG APP_PATH=/app
ARG USER_NAME=harken
ARG USER_UID=1000
ARG USER_GID=1000
ARG OPT_PATH=/opt
ARG DEBIAN_FRONTEND=noninteractive

# ********************************************************
# MiniZinc Builder
#
# This layer installs MiniZinc into the $MINIZINC_HOME
# directory which is later copied to other images.
#
# Google OR-Tools solver for MiniZinc is also installed
#
# ********************************************************
FROM minizinc/minizinc:${MINIZINC_VERSION} AS minizinc-builder

# Install required packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
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

# # Download and unpack the C++ build for this OS
RUN wget -c ${ORTOOLS_TAR_URL} \
    && tar -xzvf ${ORTOOLS_TAR_NAME}

# Move the files to the correct location
RUN mv ${ORTOOLS_DIR_NAME} ${ORTOOLS_HOME} \
    && cp ${ORTOOLS_HOME}/share/minizinc/solvers/* ${MINIZINC_HOME}/solvers \
    && cp -r ${ORTOOLS_HOME}/share/minizinc/cp-sat ${MINIZINC_HOME}/cp-sat \
    && ln -sf ${ORTOOLS_HOME}/bin/fzn-cp-sat /usr/local/bin/fzn-cp-sat

# Test installation
RUN echo "var 1..9: x; constraint x > 5; solve satisfy;" \
    | minizinc --solver cp-sat --input-from-stdin

# ********************************************************
# base
# 
# Base layer with core dependencies to be used by other
# layers
# ********************************************************
FROM python:${PYTHON_VERSION}-slim AS base

ARG USER_NAME=harken
ARG USER_GID=1000
ARG USER_UID=1000
ARG APP_PATH
ARG OPT_PATH
ARG MINIZINC_HOME
ARG ORTOOLS_HOME

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_CACHE_DIR=/tmp/uv-cache

ENV PYTHONUNBUFFERED=1

ENV UV_PROJECT_ENVIRONMENT=/home/${USER_NAME}/.venv
ENV PATH="/home/${USER_NAME}/.venv/bin:$PATH"

# Create our non-root user
RUN groupadd --gid ${USER_GID} ${USER_NAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USER_NAME} \
    && apt-get update \
    && apt-get install -y sudo \
    && echo ${USER_NAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER_NAME} \
    && chmod 0440 /etc/sudoers.d/${USER_NAME}

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install MiniZinc + ORTools from the build layer
COPY --from=minizinc-builder $MINIZINC_HOME $MINIZINC_HOME
COPY --from=minizinc-builder /usr/local/bin/ /usr/local/bin/
COPY --from=minizinc-builder $ORTOOLS_HOME $ORTOOLS_HOME

USER $USER_NAME

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
FROM base AS dev

ARG PYTHON_VENV
ARG USER_NAME
ARG USER_UID
ARG USER_GID
ARG DEBIAN_FRONTEND

ENV PYTHONDONTWRITEBYTECODE=1

USER root

# Install core packages
RUN apt-get update \
 && apt-get install -y\
        build-essential \
        curl \
        ca-certificates \
        gnupg2 \
        locales \
        lsb-release \
        wget \
 && rm -rf /var/lib/apt/lists/*

# Install Developer packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \ 
        autojump \
        entr \
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

# Install zsh & oh-my-zsh
USER ${USER_NAME}
WORKDIR /home/$USER_NAME
COPY .devcontainer/.p10k.zsh .p10k.zsh
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.2.1/zsh-in-docker.sh)" -- \
    -p git \
    -p docker \
    -p autojump \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions && \
    echo "[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh" >> ~/.zshrc && \
    .oh-my-zsh/custom/themes/powerlevel10k/gitstatus/install

WORKDIR ${APP_PATH}

# For devcontainer usage, we want the dependencies pre-installed
# but source code will be mounted at runtime
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/tmp/uv-cache,uid=${USER_UID},gid=${USER_GID} \
    uv sync --frozen --group dev --no-install-project

# Set up shell to activate virtual environment
RUN echo 'export PATH="/app/.venv/bin:$PATH"' >> /home/${USER_NAME}/.zshrc

# Default command for devcontainer
CMD ["sleep", "infinity"]

# ********************************************************
# prod
#
# Contains source code and production dependencies only
# ********************************************************
FROM base AS prod

ARG APP_PATH
ARG USER_NAME
ARG USER_GID
ARG USER_UID

ENV PYTHONOPTIMIZE=2
ENV PYTHONDONTWRITEBYTECODE=0

# Create and assign app path
USER root
RUN mkdir $APP_PATH && chown -R $USER_NAME $APP_PATH

USER ${USER_NAME}
WORKDIR ${APP_PATH}

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY ./unconstrained ./unconstrained

# Install the project
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev
    
# Set the Python path to use uv's virtual environment
ENV PATH="/app/.venv/bin:$PATH"