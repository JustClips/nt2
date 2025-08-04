import os
import discord
import re
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"

client = discord.Client()

def hub_name_replace(text):
    # Replace any known hub label with 'eps1llon hub notifier'
    # Add new patterns here as needed!
    patterns = [
        r'Brainrot Notify\s*\|[^\n]+',   # Brainrot Notify | Chilli Hub (or any hub)
        r'Arbix hub finder',
        r'Chilli Hub',
        r'Lyez Hub',
        r'Notify\s*\|[^\n]+',            # Generic "Notify | <Hub>"
        r'New Pet Found.*',              # Pet notifier
        r'Hub Finder.*'
    ]
    for pat in patterns:
        text = re.sub(pat, 'eps1llon hub notifier', text, flags=re.IGNORECASE)
    return text

def get_message_full_content(message):
    parts = []
    if message.content and message.content.strip():
        parts.append(message.content)
    for embed in message.embeds:
        if embed.title:
            parts.append(embed.title)
        if embed.description:
            parts.append(embed.description)
        for field in getattr(embed, "fields", []):
            parts.append(f"{field.name}\n{field.value}")
    for att in message.attachments:
        parts.append(att.url)
    return "\n".join(parts) if parts else "(no content)"

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id not in CHANNEL_IDS:
        return

    # Combine all message parts for content
    full_content = get_message_full_content(message)

    # Remove leading timestamps (if any)
    full_content = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}\] ?[^\n]*\n?', '', full_content)

    # Rename any hub name to eps1llon hub notifier
    final_content = hub_name_replace(full_content)

    # Only send if there's actual content left
    if final_content.strip():
        try:
            requests.post(WEBHOOK_URL, json={"content": final_content})
        except Exception as e:
            print(f"Failed to send to webhook: {e}")

client.run(TOKEN)
