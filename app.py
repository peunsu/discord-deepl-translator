import os
from functools import partial
from dotenv import load_dotenv
import discord
import deepl

load_dotenv()

class TranslatorApp(discord.Client):
    async def on_ready(self):
        auth_key = os.environ["auth_key"]
        translator = deepl.Translator(auth_key)
        self.translate = partial(translator.translate_text, target_lang=os.environ["target_lang"])
        
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if embeds := message.embeds:
            reply_embeds = []
            
            for embed in embeds:
                embed_dict = embed.to_dict()
                
                for key in embed_dict.keys():
                    if key in ["title", "description"]:
                        embed_dict[key] = self.translate(embed_dict[key]).text
                    elif key == "fields":
                        for field in embed_dict["fields"]:
                            for attr in ["value", "name"]:
                                field[attr] = self.translate(field[attr]).text
                reply_embeds.append(discord.Embed.from_dict(embed_dict))
                
            return await message.reply(embeds=reply_embeds)
        
        await message.reply(self.translate(message.content).text)

intents = discord.Intents.default()
intents.message_content = True

client = TranslatorApp(intents=intents)
client.run(os.environ["token"])