FROM n8nio/n8n:latest

USER root

# Instalar Python y pip
RUN apk add --no-cache python3 py3-pip

# Instalar yt-dlp
RUN pip3 install yt-dlp
RUN npm install -g pm2

# Crear carpeta de scripts
RUN mkdir -p /home/node/scripts && chown -R node:node /home/node
CMD ["sh", "-c", "pm2 start /home/node/bot.js && n8n"]
USER node