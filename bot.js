import { Client, GatewayIntentBits } from "discord.js";
import fetch from "node-fetch";

require('dotenv').config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const CHANNEL_ID = process.env.CHANNEL_ID;
const N8N_WEBHOOK = process.env.N8N_WEBHOOK;

client.once("clientReady", () => {
  console.log(`Bot conectado como ${client.user.tag}`);
});

client.on("messageCreate", async (message) => {
  // evitar loops
  if (message.author.bot) return;

  // filtrar canal
  if (message.channel.id !== CHANNEL_ID) return;

  console.log("Se ha puesto un mensaje en el canal")

  await fetch(N8N_WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content: message.content,
      author: message.author.username,
      author_id: message.author.id,
      channel_id: message.channel.id,
      timestamp: message.createdAt,
    }),
  });
});

client.login(DISCORD_TOKEN);
