FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    curl \
    wget \
    git \
    nano \
    vim \
    python3 \
    python3-pip \
    ffmpeg \
    build-essential \
    ca-certificates \
    gnupg \
    procps \
    && rm -rf /var/lib/apt/lists/*

CMD ["tail", "-f", "/dev/null"]