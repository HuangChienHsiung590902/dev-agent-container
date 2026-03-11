# =============================================================================
# Dev Agent Container - Complete Development Environment
# Base: Ubuntu 22.04 with Node.js, Python, Go, Rust, Docker (DinD)
# =============================================================================

FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Taipei

# =============================================================================
# Install System Dependencies
# =============================================================================
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    cmake \
    pkg-config \
    # Version control
    git \
    git-lfs \
    # Networking & Utils
    curl \
    wget \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    zip \
    tar \
    rsync \
    openssh-client \
    # Docker (for DinD)
    docker.io \
    # Additional utilities
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Install Node.js 22.x
# =============================================================================
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Install Python 3 & pip
# =============================================================================
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Install common Python tools
RUN pip3 install --no-cache-dir \
    pipenv \
    poetry \
    virtualenv \
    black \
    flake8 \
    pylint \
    mypy \
    pytest \
    ipython

# =============================================================================
# Install LangChain & AI Development Tools
# =============================================================================
RUN pip3 install --no-cache-dir \
    langchain \
    langchain-core \
    langchain-community \
    langchain-openai \
    langchain-anthropic \
    langgraph \
    # Anthropic SDK (for Minimax compatibility)
    anthropic \
    # Vector stores
    chromadb \
    faiss-cpu \
    # Utilities
    python-dotenv \
    httpx \
    tiktoken \
    pytz \
    # Web Framework
    fastapi \
    uvicorn \
    sse-starlette \
    # Jupyter support
    jupyter \
    ipykernel

# =============================================================================
# Environment Variables for Minimax
# =============================================================================
ENV ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic

# =============================================================================
# Install Docker Compose (Standalone)
# =============================================================================
RUN curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# =============================================================================
# Configure Docker daemon for DinD
# =============================================================================
RUN mkdir -p /etc/docker \
    && echo '{"storage-driver": "overlay2", "log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' > /etc/docker/daemon.json

# =============================================================================
# Create working directory
# =============================================================================
WORKDIR /workspace

# =============================================================================
# Create non-root user (agent)
# =============================================================================
RUN useradd -m -s /bin/bash agent \
    && usermod -aG docker agent \
    && echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to non-root user
USER agent
WORKDIR /home/agent

# =============================================================================
# Shell configuration
# =============================================================================
RUN echo 'export PS1="(dev-agent) $PS1"' >> ~/.bashrc

# =============================================================================
# Verify installations
# =============================================================================
RUN echo "=== Verifying installations ===" \
    && node --version \
    && npm --version \
    && python3 --version \
    && pip --version \
    && docker --version \
    && docker-compose --version \
    && echo "=== All tools verified ==="

# =============================================================================
# Copy startup script
# =============================================================================
COPY --chmod=755 start.sh /usr/local/bin/start.sh

# Default command - auto-start services
CMD ["/usr/local/bin/start.sh"]
