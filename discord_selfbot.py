import os
import discord
import re
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"

client = discord.Client()

def hub_name_replace(text):
    # Replace any known hub label with 'Eps1llon Hub Notifier'
    patterns = [
        r'Brainrot Notify\s*\|[^\n]+',   # Brainrot Notify | Chilli Hub (or any hub)
        r'Arbix hub finder',
        r'Chilli Hub',
        r'Lyez Hub',
        r'Notify\s*\|[^\n]+',            # Generic "Notify | <Hub>"
        r'Hub Finder.*',
    ]
    for pat in patterns:
        text = re.sub(pat, 'Eps1llon Hub Notifier', text, flags=re.IGNORECASE)
    return text

def extract_place_and_instance(msg):
    # Try to extract placeid and instanceid from Join Script (PC) or from the message
    script_match = re.search(
        r'game:GetService\("TeleportService"\):TeleportToPlaceInstance\((\d+),\s*"?([A-Za-z0-9\-+/=]+)"?', msg)
    if script_match:
        placeid = script_match.group(1)
        instanceid = script_match.group(2)
        return placeid, instanceid
    # Fallback: look for keys in the message itself
    placeid_match = re.search(r'place.?id[^\d]*(\d+)', msg, re.IGNORECASE)
    instanceid_match = re.search(r'(instance.?id|job.?id.?pc)[^\w-]*([A-Za-z0-9\-+/=]+)', msg, re.IGNORECASE)
    if placeid_match and instanceid_match:
        return placeid_match.group(1), instanceid_match.group(2)
    return None, None

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

    # Rename any hub name to Eps1llon Hub Notifier
    final_content = hub_name_replace(full_content)

    # Add the join link if placeId and instanceId are present
    placeid, instanceid = extract_place_and_instance(final_content)
    if placeid and instanceid:
        join_link = f"https://chillihub1.github.io/chillihub-joiner/?placeId={placeid}&gameInstanceId={instanceid}"
        final_content = f"{final_content}\n{join_link}"

    # Only send if there's actual content left
    if final_content.strip():
        try:
            requests.post(WEBHOOK_URL, json={"content": final_content})
        except Exception as e:
            print(f"Failed to send to webhook: {e}")

client.run(TOKEN)
