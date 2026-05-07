FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Instalar paquetes como root
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
    sudo \
    ca-certificates \
    gnupg \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN useradd -m -s /bin/bash n8n

# (Opcional) darle sudo sin contraseña
RUN echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Crear directorio de trabajo
WORKDIR /home/n8n/app

# Dar permisos
RUN chown -R n8n:n8n /home/n8n

# Cambiar al usuario no root
USER n8n

CMD ["tail", "-f", "/dev/null"]