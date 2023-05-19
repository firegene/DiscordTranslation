import asyncio
import json

import discord
from babel import languages
from google.cloud import translate

with open("environment.json") as f:
    environ = json.load(f)

PROJECT_ID = environ.get("project_id", "")
assert PROJECT_ID
PARENT = f"projects/{PROJECT_ID}"

with open("token.json") as f:
    tokenjson = json.load(f)

token = tokenjson.get("token")

with open("unicode.json") as f:
    unicode = json.load(f)


def translate_text(text: str, target_language_code: str):
    client = translate.TranslationServiceClient()
    response = client.translate_text(
        parent=PARENT, contents=[text], target_language_code=target_language_code
    )
    return response.translations[0]


intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_raw_reaction_add(payload):
    emoji = payload.emoji
    if not emoji.is_unicode_emoji:
        return
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    for unicodestring, bytes in unicode.items():
        if bytes == emoji.name:
            break
    if not unicodestring.startswith("flag"):
        return
    countrycode = unicodestring[-2:]
    language = languages.get_official_languages(countrycode)[0]
    loop = asyncio.get_running_loop()
    translation = await loop.run_in_executor(
        None, translate_text, message.content, language
    )
    source_lang = translation.detected_language_code
    translated_text = translation.translated_text

    result = discord.Embed()
    result.title = f"{source_lang.upper()} → {language.upper()}"
    result.set_author(name=payload.member,icon_url=payload.member.avatar)
    result.description = translated_text
    result.colour = 16752360
    result.set_footer(
        text="created by firegene#5815",
        icon_url="https://cdn.discordapp.com/avatars/236448694172516353/6f13a94970b5dd1b3cb1518a1c75f362.webp",
    )

    await channel.send(
        embed=result, reference=message.to_reference(), mention_author=False
    )


client.run(token)
