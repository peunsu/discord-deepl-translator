import datetime
import json
import logging
import os
from functools import partial
from copy import deepcopy

import deepl
import discord
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(discord.client.__name__)

class DeepLTranslator(discord.Client):
    async def on_ready(self):
        # Load config.json.
        self.config = json.load(open("config.json", "r"))
        logger.info(f"Successfully loaded config.json.")
        
        # Set DeepL translator.
        auth_key = os.environ["DEEPL_KEY"]
        translator = deepl.Translator(auth_key)
        self.translate = partial(translator.translate_text, target_lang=os.environ["TARGET_LANG"])
        logger.info(f"Successfully set DeepL translator.")
        
        logger.info(f'Logged on as {self.user}.')

    async def on_message(self, message: discord.Message):
        # Ignore messages sent by the bot itself.
        if message.author == self.user:
            return
        
        # Ignore messages sent in channels not specified in config.json.
        for channel_key in self.config.keys():
            # If the message is sent in a channel specified in config.json, translate it.
            if message.channel.id in self.config[channel_key]["channels_in"]:
                channel_out: discord.TextChannel = self.get_channel(self.config[channel_key]["channel_out"])
                role_id: int = self.config[channel_key]["role"]
                break
        else:
            return
        
        # The list of output embeds.
        embeds_out = []
        
        default_embed_dict = {
            "author": {
                "name": message.author.name,
                "icon_url": message.author.avatar.url
            },
            "image": {
                "url": message.attachments[0].url if message.attachments else None
            },
            "footer": {
                "text": "원본 메시지",
                "icon_url": "https://i.imgur.com/sg8WDCE.png"
            },
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "color": discord.Color.blue().value
        }
        
        embed_dict = default_embed_dict
        embed_dict["description"] = message.content
        embed_out = discord.Embed.from_dict(embed_dict)
        embeds_out.append(embed_out)
        
        if embeds := message.embeds: # Works if the message has embeds.
            for embed in embeds:
                # Transform the embed to dictionary, copy default embed dictionary and set footer.
                embed_dict = embed.to_dict()
                embed_dict.update(default_embed_dict)
                embed_out = discord.Embed.from_dict(embed_dict)
                embeds_out.append(embed_out)
        
        button = discord.ui.Button(label="번역하기", style=discord.ButtonStyle.primary(), custom_id="translate", emoji="🔀")
        
        logger.info(f"Relayed message. (from: {message.channel.id}, to: {channel_out.id}, author: {message.author.name})")
        await channel_out.send(f"<@&{role_id}>", embeds=embeds_out, components=[button])
    
    @discord.ui.button(label="번역하기", style=discord.ButtonStyle.primary(), custom_id="translate", emoji="🔀")
    async def translate(self, button: discord.ui.Button, interaction: discord.Interaction):
        message: discord.Message = interaction.message
        
        # The list of output embeds.
        embeds_out = []
        
        for embed in message.embeds:
            # Transform the embed to dictionary, copy default embed dictionary and set footer.
            embed_dict = embed.to_dict()
            
            # Translate the texts in specified fields.
            for embed_key in embed_dict.keys():
                if embed_key in ["title", "description"]:
                    message_len += len(embed_dict[embed_key])
                    embed_dict[embed_key] = self.translate(embed_dict[embed_key]).text
                    
                elif embed_key == "fields":
                    for field in embed_dict["fields"]:
                        for attr in ["value", "name"]:
                            message_len += len(field[attr])
                            field[attr] = self.translate(field[attr]).text
                            
            embed_dict["footer"]["text"] = "DeepL Translator로 번역됨"
            embed_out = discord.Embed.from_dict(embed_dict)
            embeds_out.append(embed_out)
        
        await interaction.response.send_message()

intents = discord.Intents.default()
intents.message_content = True

client = DeepLTranslator(intents=intents)
client.run(os.environ["BOT_TOKEN"])