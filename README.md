# discord-deepl-translator
Translator application for Discord using [DeepL API](https://github.com/DeepLcom/deepl-python).

# Installation
* Python 3.8 or higher is required
* Clone the repo:
```python
$ git clone https://github.com/peunsu/discord-deepl-translator
```
* Create the virtual environment (optional):
```python
$ python -m venv venv
$ source venv/bin/activate
```
* Install requirements:
```python
$ pip install -r requirements.txt
```
* Create a discord bot application.
  * Under Privileged Gateway Intents enable [Message Content Intent](https://discord.com/developers/applications).
  * Enable the required bot [permissions](https://discord.com/developers/docs/topics/permissions) (administrator).
  * Invite your bot to the server with the scopes [bot & applications.commands](https://discord.com/developers/applications/).
* Generate and copy your [DeepL API key](https://www.deepl.com/pro-api).
* Create the `.env` file and insert your discord bot token and DeepL API key:
```python
BOT_TOKEN = "your_bot_token"
DEEPL_KEY = "your_deepl_api_key"
```
* Set up your `config.json` as shown in the example below:
```python
{
    "translator": {
        # The language into which the text should be translated. Refer to the DeepL API Docs(https://www.deepl.com/docs-api/translate-text).
        "target_lang": "KO"
    },
    "relay": {
        # Relay the message from "input" to "output".
        # You can set "custom_key" whatever you want.
        # The app translates messages sent from "input" channels and sends them to "output" channel.
        # When send the translated messages, mention the "role" you set below.
        "custom_key": {
            "input": [1234567890123456789, 1234567890123456789, 1234567890123456789],
            "output": 1234567890123456789,
            "role": 1234567890123456789
        },
        ...
    },
    "messages": {
        # Customize your bot messages and the footer icon.
        "translate_button": "Translate",
        "translate_complete": "Translated the text!",
        "original_footer": "Original Message",
        "translated_footer": "Translated by DeepL Translator",
        "footer_icon_url": "https://i.imgur.com/sg8WDCE.png"
    }
```
* Run the application:
```python
$ python app.py
```
