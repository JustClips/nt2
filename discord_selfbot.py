import os
import discord
import re
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"

client = discord.Client()

def parse_and_format_message(msg):
    # Parse the required fields
    name_match = re.search(r'🏷️ Name\n([^\n]+)', msg)
    money_match = re.search(r'💰 Money per sec\n([^\n]+)', msg)
    players_match = re.search(r'👥 Players\n([^\n]+)', msg)
    jobid_mobile = re.search(r'Job ID \(Mobile\)\n([A-Za-z0-9\-+/=]+)', msg)
    jobid_pc = re.search(r'Job ID \(PC\)\n([A-Za-z0-9\-+/=]+)', msg)
    join_pc = re.search(
        r'Join Script \(PC\)\n(game:GetService\("TeleportService"\):TeleportToPlaceInstance\([^\n]+\))', msg)

    if all([name_match, money_match, players_match, jobid_mobile, jobid_pc, join_pc]):
        # Build the normalized message
        normalized = (
            f"eps1llon hub notifier\n"
            f"🏷️ Name\n{name_match.group(1)}\n"
            f"💰 Money per sec\n{money_match.group(1)}\n"
            f"👥 Players\n{players_match.group(1)}\n"
            f"Job ID (Mobile)\n{jobid_mobile.group(1)}\n"
            f"🆔 Job ID (PC)\n{jobid_pc.group(1)}\n"
            f"📜 Join Script (PC)\n{join_pc.group(1)}"
        )
        return normalized
    return None

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id not in CHANNEL_IDS:
        return

    # Combine text, embed, and attachment content for parsing
    content_parts = []
    if message.content and message.content.strip():
        content_parts.append(message.content)
    for embed in message.embeds:
        if embed.title:
            content_parts.append(embed.title)
        if embed.description:
            content_parts.append(embed.description)
        for field in getattr(embed, "fields", []):
            content_parts.append(f"{field.name}\n{field.value}")
    for att in message.attachments:
        content_parts.append(att.url)
    full_content = "\n".join(content_parts)

    formatted = parse_and_format_message(full_content)
    if formatted:
        try:
            requests.post(WEBHOOK_URL, json={"content": formatted})
        except Exception as e:
            print(f"Failed to send to webhook: {e}")

client.run(TOKEN)
