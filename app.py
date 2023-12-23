import os
from dotenv import load_dotenv
import json
import logging
from functools import partial
import datetime
import discord
import deepl

load_dotenv()

logger = logging.getLogger(discord.client.__name__)

class TranslatorApp(discord.Client):
    async def on_ready(self):
        self.config = json.load(open("config.json", "r"))
        logger.info(f"Translate messages sent in the following channels: {self.config['channels']}")
        
        auth_key = os.environ["DEEPL_KEY"]
        translator = deepl.Translator(auth_key)
        self.translate = partial(translator.translate_text, target_lang=os.environ["TARGET_LANG"])
        
        logger.info(f'Logged on as {self.user}.')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.channel.id not in self.config["channels"]:
            return
        
        text_len = 0
        
        if embeds := message.embeds:
            reply_embeds = []
            
            for embed in embeds:
                embed_dict = embed.to_dict()
                
                for key in embed_dict.keys():
                    if key in ["title", "description"]:
                        text_len += len(embed_dict[key])
                        embed_dict[key] = self.translate(embed_dict[key]).text
                        
                    elif key == "fields":
                        for field in embed_dict["fields"]:
                            for attr in ["value", "name"]:
                                text_len += len(field[attr])
                                field[attr] = self.translate(field[attr]).text
                                
                embed_dict["author"] = {
                    "name": message.author.name,
                    "icon_url": message.author.avatar.url
                }
                embed_dict["footer"] = {
                    "text": "Translated by DeepL"
                }
                embed_dict["timestamp"] = datetime.datetime.now().isoformat()
                embed_dict["color"] = discord.Color.blue().value
                                
                reply_embeds.append(discord.Embed.from_dict(embed_dict))
                
                logger.info(f"Translate embed message sent by {message.author} (Text length: {text_len})")
                return await message.reply(embeds=reply_embeds)
        
        text_len += len(message.content)
        
        logger.info(f"Translate normal message sent by {message.author} (Text length: {text_len})")
        await message.reply(embed=discord.Embed.from_dict({
            "author": {
                "name": message.author.name,
                "icon_url": message.author.avatar.url
            },
            "description": self.translate(message.content).text,
            "footer": {
                "text": "Translated by DeepL"
            },
            "timestamp": datetime.datetime.now().isoformat(),
            "color": discord.Color.blue().value
        }))

intents = discord.Intents.default()
intents.message_content = True

client = TranslatorApp(intents=intents)
client.run(os.environ["BOT_TOKEN"])