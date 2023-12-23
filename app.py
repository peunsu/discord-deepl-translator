import os
from dotenv import load_dotenv
import logging
from functools import partial
import discord
import deepl

load_dotenv()

logger = logging.getLogger(discord.client.__name__)

class TranslatorApp(discord.Client):
    async def on_ready(self):
        auth_key = os.environ["DEEPL_KEY"]
        translator = deepl.Translator(auth_key)
        self.translate = partial(translator.translate_text, target_lang=os.environ["TARGET_LANG"])
        
        logger.info(f'Logged on as {self.user}.')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        text_len = 0
        
        if embeds := message.embeds:
            reply_embeds = []
            
            for embed in embeds:
                embed_dict = embed.to_dict()
                
                for key in embed_dict.keys():
                    if key in ["title", "description"]:
                        msg_len += len(embed_dict[key])
                        embed_dict[key] = self.translate(embed_dict[key]).text
                        
                    elif key == "fields":
                        for field in embed_dict["fields"]:
                            for attr in ["value", "name"]:
                                msg_len += len(field[attr])
                                field[attr] = self.translate(field[attr]).text
                                
                reply_embeds.append(discord.Embed.from_dict(embed_dict))
            
            logger.info(f"Translate embed message sent by {message.author} (Text length: {text_len})")
            return await message.reply(embeds=reply_embeds)
        
        text_len += len(message.content)
        logger.info(f"Translate normal message sent by {message.author} (Text length: {text_len})")
        await message.reply(self.translate(message.content).text)

intents = discord.Intents.default()
intents.message_content = True

client = TranslatorApp(intents=intents)
client.run(os.environ["BOT_TOKEN"])