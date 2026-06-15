console.log("Inicialización de Logs")
import { 
  Client, 
  GatewayIntentBits, 
  EmbedBuilder, 
  ButtonBuilder, 
  ButtonStyle, 
  ActionRowBuilder,
  AttachmentBuilder
} from "discord.js";
import fetch from "node-fetch";
import express from 'express';
import dotenv from 'dotenv'
dotenv.config()

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

const channels_ids = {
  "Table Tennis": "1507391557568041074",
  "Music": "1321920857744085096",
  "Music Production": "1339233772570415227",
  "Personal Development": "1308038654194880522",
  "Creative Resorces": "1295551563863162950",
  "Project": "1295952715389603870",
  "Coding": "1346682717583966301",
  "Clothes": "1311648623519338577",
  "DIY": "1371190701794263091",
  "3DPrint": "1373308998476103840",
  "Linux": "1507106482372612157",
  "Homelab":"1512103129599053966",
  "No Related to Any Before": "1309997775756329051",
  "Art": "1512094651052720178",
  "Philosophy": "1515113979159121921",
  "Chess": "1308954666217902120"
}

const app = express();
app.use(express.json({ limit: '50mb' }));

app.post('/send-embed', async (req, res) => {
  try {
    const data  = req.body;

   //! const channel = await client.channels.fetch('CHANNEL_ID');
   //TODO: Seleccionar channels a enviar.
    
    for (const element of data.tags) {
      const channel_id = channels_ids[element];

      if (!channel_id) continue;

      const channel = await client.channels.fetch(channel_id);
      const embed =  await crearEmbed(data)
      const attachments = await getAttachments(data)

      await channel.send({
        embeds: [embed],
        files: attachments
      });
    }
    

    res.json({
      success: true
    });

  } catch (err) {
    console.error(err);

    res.status(500).json({
      error: err.message
    });
  }
});

app.listen(3000, () => {
  console.log('API escuchando en puerto 3000');
});


const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const CHANNEL_ID = process.env.CHANNEL_ID;
const N8N_WEBHOOK = process.env.N8N_WEBHOOK;

client.login(DISCORD_TOKEN);

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

async function getAttachments(data) {
      const MAX_SIZE_MB = 10;
      

    const response = await fetch(data.thumbnail);
    const thumbnailBuffer = Buffer.from(await response.arrayBuffer());
    const attachment_thumbnail = new AttachmentBuilder(thumbnailBuffer, {
          name: 'thumbnail.jpg'
    });

    
    const videoResponse = await fetch(data.video_url);
    const videoBuffer = Buffer.from(await videoResponse.arrayBuffer());
    const videoAttachment = new AttachmentBuilder(videoBuffer, {
    name: 'reel.mp4'
    });

    const profileResponse = await fetch(data.profile_pic_url);
    const profileBuffer = Buffer.from(await profileResponse.arrayBuffer());
    const profileAttachment = new AttachmentBuilder(profileBuffer,{
      name: 'profile.jpg' 
    });

    const sizeMBprofile = profileBuffer.length / 1024 / 1024;
    const sizeMBvideo = videoBuffer.length / 1024 / 1024;
    const sizeMBthumbnail = thumbnailBuffer.length / 1024 / 1024;

      if ( sizeMBprofile > MAX_SIZE_MB || 
        sizeMBvideo > MAX_SIZE_MB ||
        sizeMBthumbnail > MAX_SIZE_MB) {
          
        console.log(`LIMITE SUPERADO: Los archivos pesan:\n 
          video-${sizeMBvideo.toFixed(2)} MB \n 
          profile-${sizeMBprofile.toFixed(2)} MB \n 
          thumbnail-${sizeMBthumbnail.toFixed(2)}`);
          return []
        }

    return [
      attachment_thumbnail,
      videoAttachment,
      profileAttachment,
    ]
}

// 🔹 Función para crear embeds según la vista
async function crearEmbed(data) {
  const embed = new EmbedBuilder().setColor(0x0099ff);
      
      const tools = Array.isArray(data.tools)
    ? data.tools
    : [data.tools];
  
      return embed
        .setTitle(data.title)
        .setAuthor(
          {
            name: data.author,
            iconURL: "attachment://profile.jpg",
            url: `https://instagram.com/${data.video_author}`
          }
        )
        .setURL(data.video_link)
        .setDescription(data.video_analysis)
        .setThumbnail('attachment://thumbnail.jpg')
        .addFields({
            name: '🛠 Tools',
            value: tools.map(tool => `\`${tool}\``).join(' ')
        },
        // Tags
        {
            name: '🏷 Tags',
            value: data.tags.map(tag => `\`${tag}\``).join(' ')
        });

}

// 🔹 Interacciones
client.on('interactionCreate', async interaction => {
  if (!interaction.isButton()) return;

  const vista = interaction.customId;

  await interaction.update({
    embeds: [crearEmbed(vista)],
    components: [crearBotones(vista)]
  });
});

// 🔹 Comando para iniciar panel
client.on('messageCreate', async message => {
  if (message.content === '!panel') {

    await message.channel.send({
      embeds: [crearEmbed('resumen')],
      components: [crearBotones('resumen')]
    });
  }
});

