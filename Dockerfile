FROM n8nio/n8n:latest
USER root

# Restore apk from Alpine (n8n uses Alpine 3.22)
COPY --from=alpine:3.22 /sbin/apk /sbin/apk
COPY --from=alpine:3.22 /lib/apk /lib/apk
COPY --from=alpine:3.22 /etc/apk /etc/apk

# Instalar Python
RUN apk add --no-cache python3 py3-pip 
RUN apk add --no-cache nodejs npm
RUN apk -U add yt-dlp ffmpeg

# PM2
RUN npm install -g pm2
COPY . /home/node

# Crear carpeta de scripts
RUN chown -R node:node /home/node
USER node
CMD ["sh", "-c", "pm2 start /home/node/app.js --name discord-bot && n8n"]