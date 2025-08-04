import os
import discord
import re
import json
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1234567890"))  # Set this as env var on Railway

WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"

client = discord.Client()

def parse_money_job(msg):
    money_match = re.search(r'Money per sec\n\$(\d+\.?\d*)M/s', msg)
    jobid_match = re.search(r'Job ID \(PC\)\n=([A-Za-z0-9+/=]+)', msg)
    if money_match and jobid_match:
        money = float(money_match.group(1))
        jobid = jobid_match.group(1)
        return money, jobid
    return None, None

def get_message_full_content(message):
    parts = []
    # Text content
    if message.content and message.content.strip():
        parts.append(message.content)
    # Embeds
    for embed in message.embeds:
        embed_fields = []
        if embed.title:
            embed_fields.append(f"**{embed.title}**")
        if embed.description:
            embed_fields.append(embed.description)
        for field in getattr(embed, "fields", []):
            embed_fields.append(f"{field.name}: {field.value}")
        parts.append("\n".join(embed_fields))
    # Attachments
    for att in message.attachments:
        parts.append(att.url)
    return "\n".join(parts) if parts else "(no content)"

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return

    full_content = get_message_full_content(message)
    content = f"[{message.created_at}] {message.author}: {full_content}"

    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        print(f"Failed to send to webhook: {e}")

    money, jobid = parse_money_job(message.content)
    if money and money > 10:
        with open("join_request.json", "w") as f:
            json.dump({"jobid": jobid}, f)
        print(f"Found server with ${money}M/s, Job ID: {jobid}")

client.run(TOKEN)
