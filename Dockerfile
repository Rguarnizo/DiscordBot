FROM n8nio/n8n:1.41.0-debian

USER root

# Instalar Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean

# yt-dlp
RUN pip3 install yt-dlp

# PM2
RUN npm install -g pm2

# Crear carpeta de scripts
RUN chown -R node:node /home/node
USER node

CMD ["sh", "-c", "pm2 start /home/node/bot.js && n8n"]
