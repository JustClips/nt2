import os
import discord
import re
import json
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]

WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"

client = discord.Client()

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

def parse_brainrot_message(msg):
    # Extracts info from Brainrot/Hub finder messages
    money_match = re.search(r'💰 Money per sec\n\$([\d,\.]+[KM]?)/s', msg)
    jobid_match = re.search(r'🆔 Job ID\n([a-f0-9\-]+)', msg)
    placeid_match = re.search(r'game:GetService\("TeleportService"\):TeleportToPlaceInstance\((\d+),', msg)
    instanceid_match = re.search(r'TeleportToPlaceInstance\(\d+, "([a-f0-9\-]+)"', msg)
    players_match = re.search(r'👥 Players\n([\d/]+)', msg)
    name_match = re.search(r'🏷️ Name\n([^\n]+)', msg)
    return {
        "money_per_sec": money_match.group(1) if money_match else None,
        "job_id": jobid_match.group(1) if jobid_match else None,
        "place_id": placeid_match.group(1) if placeid_match else None,
        "instance_id": instanceid_match.group(1) if instanceid_match else None,
        "players": players_match.group(1) if players_match else None,
        "name": name_match.group(1) if name_match else None,
    }

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id not in CHANNEL_IDS:
        return

    full_content = get_message_full_content(message)
    content = f"[{message.created_at}] {message.author}: {full_content}"

    # Send every message to the webhook
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        print(f"Failed to send to webhook: {e}")

    # --- Optional: Parse and log details from Brainrot messages ---
    brainrot_info = parse_brainrot_message(full_content)
    if brainrot_info["money_per_sec"] and brainrot_info["job_id"]:
        print("Brainrot/Hub Finder Message Parsed:")
        print(json.dumps(brainrot_info, indent=2))
        # You can also save this to a file, database, etc. if desired
        with open("brainrot_found.json", "w") as f:
            json.dump(brainrot_info, f)

client.run(TOKEN)
