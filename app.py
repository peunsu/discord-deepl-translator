import datetime
import json
import logging
import os
from functools import partial

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

    async def on_message(self, message):
        # Ignore messages sent by the bot itself.
        if message.author == self.user:
            return
        
        # Ignore messages sent in channels not specified in config.json.
        for channel_key in self.config["channels_in"].keys():
            # If the message is sent in a channel specified in config.json, translate it.
            if message.channel.id in self.config["channels_in"][channel_key]:
                channel_out = self.get_channel(self.config["channels_out"][channel_key])
                break
        else:
            return
        
        # The length of input message.
        message_len = 0
        
        # The list of output embeds.
        embeds_out = []
        
        # Default embed dictionary.
        default_embed_dict = {
            "author": {
                "name": message.author.name,
                "icon_url": message.author.avatar.url
            },
            "image": {
                "url": message.attachments[0].url if message.attachments else None
            },
            "footer": {
                "icon_url": "https://i.imgur.com/sg8WDCE.png"
            },
            "timestamp": datetime.datetime.now().isoformat(),
            "color": discord.Color.blue().value
        }
        
        if embeds := message.embeds: # Works if the message has embeds.
            for embed in embeds:                
                # Transform the embed to dictionary, copy default embed dictionary and set footer.
                embed_dict = embed.to_dict()
                embed_dict.update(default_embed_dict)
                embed_dict["footer"]["text"] = "원본 메시지"
                embed_out = discord.Embed.from_dict(embed_dict)
                embeds_out.append(embed_out)
                
                # Translate the texts in specified fields.
                embed_dict = embed_dict.copy()
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
        else: # Works if the message has no embeds.         
            # Copy default embed dictionary and set footer and description.
            embed_dict = default_embed_dict
            embed_dict["description"] = message.content
            embed_dict["footer"]["text"] = "원본 메시지"
            embed_out = discord.Embed.from_dict(embed_dict)
            embeds_out.append(embed_out)
            
            # Translate the message.
            embed_dict = embed_dict.copy()
            if message.content:
                message_len += len(message.content)
                
                result = self.translate(message.content)
                translated_text = result.text
                detected_source_lang = result.detected_source_lang

                # If the source language is not the same as the target language, append the translated message to the embed list.
                if detected_source_lang != os.environ["TARGET_LANG"]:
                    embed_dict["description"] = translated_text
                    embed_dict["footer"]["text"] = "DeepL Translator로 번역됨"
                    embed_out = discord.Embed.from_dict(embed_dict)
                    embeds_out.append(embed_out)
                    
        logger.info(f"Translated message. (channel: {message.channel.name}, author: {message.author.name}, length: {message_len})")
        await channel_out.send(embeds=embeds_out)

intents = discord.Intents.default()
intents.message_content = True

client = DeepLTranslator(intents=intents)
client.run(os.environ["BOT_TOKEN"])