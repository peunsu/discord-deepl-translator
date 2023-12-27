import datetime
import json
import logging
import os
import shelve
from functools import partial

import deepl
import discord
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(discord.client.__name__)

config = json.load(open("config.json", "r"))
config_translator = config["translator"]
config_relay = config["relay"]
config_msg = config["messages"]
print("Successfully loaded config.json.")

translator = deepl.Translator(os.environ["DEEPL_KEY"])
print("Successfully set DeepL translator API.")

class ButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label=config_msg["translate_button"],
        style=discord.ButtonStyle.primary,
        custom_id="translate",
        emoji="🔀"
    )
    async def translate(self, interaction: discord.Interaction, button: discord.ui.Button):
        def _translate(text: str) -> str:
            try:
                return translator.translate_text(text, target_lang=config_translator["target_lang"]).text
            except deepl.DeepLException:
                return text

        message: discord.Message = interaction.message
        message_id = str(message.id)
        
        with shelve.open("cache.db") as cache:
            if message_id in cache:
                embeds_out: list = cache[message_id]
                logger.info(f"Load cached message. (channel: {message.channel.name}, user: {interaction.user.name})")
            else:
                embeds_out = []
        
                for embed in message.embeds:
                    embed_dict = embed.to_dict()
                    
                    for embed_key in ["title", "description", "fields"]:
                        if embed_key not in embed_dict:
                            continue
                        
                        if embed_key == "fields":
                            for field in embed_dict["fields"]:
                                for attr in ["value", "name"]:
                                    field[attr] = _translate(field[attr])
                        else:
                            embed_dict[embed_key] = _translate(embed_dict[embed_key])
                                    
                    embed_dict["footer"]["text"] = config_msg["translated_footer"]
                    embed_dict["timestamp"] = datetime.datetime.utcnow().isoformat()
                    embed_out = discord.Embed.from_dict(embed_dict)
                    embeds_out.append(embed_out)
                
                cache[message_id] = embeds_out
                logger.info(f"Translate message. (channel: {message.channel.name}, user: {interaction.user.name})")
        
        await interaction.response.send_message(config_msg["translate_complete"], embeds=embeds_out, ephemeral=True)

class DeepLTranslator(discord.Client):        
    async def on_ready(self):
        logger.info(f'Logged on as {self.user}.')
        self.add_view(ButtonView())
    
    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        
        guild = message.guild
        
        for key in config_relay.keys():
            if message.channel.id in config_relay[key]["input"]:
                channel_out: discord.TextChannel = guild.get_channel(config_relay[key]["output"])
                role: discord.Role = guild.get_role(config_relay[key]["role"])                
                break
        else:
            return
        
        embeds_out = []
        
        default_embed_dict = {
            "author": {
                "name": message.author.name,
                "icon_url": message.author.avatar.url
            },
            "footer": {
                "text": config_msg["original_footer"],
                "icon_url": config_msg["footer_icon_url"]
            },
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "color": discord.Color.blue().value
        }
        
        embed_dict = default_embed_dict.copy()
        embed_dict["description"] = message.content
        embed_dict["image"] = {"url": message.attachments[0].url if message.attachments else None}
        embed_out = discord.Embed.from_dict(embed_dict)
        embeds_out.append(embed_out)
        
        if embeds := message.embeds:
            for embed in embeds:
                embed_dict = embed.to_dict()
                embed_dict.update(default_embed_dict)
                embed_out = discord.Embed.from_dict(embed_dict)
                embeds_out.append(embed_out)
        
        logger.info(f"Relay message. (from: {message.channel.name}, to: {channel_out.name}, author: {message.author.name})")
        await channel_out.send(role.mention, embeds=embeds_out, view=ButtonView())

intents = discord.Intents.default()
intents.message_content = True

client = DeepLTranslator(intents=intents)
client.run(os.environ["BOT_TOKEN"])
