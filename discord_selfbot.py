import os
import discord
import re
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"
BACKEND_URL = "https://discordbot-production-800b.up.railway.app/brainrots"

client = discord.Client()  # No intents!

def parse_info(msg):
    # Flexible regex to match field with or without emoji and with optional colon or whitespace
    name = re.search(r'(?:🏷️\s*)?Name[:\s]*([^\n]+)', msg, re.IGNORECASE)
    money = re.search(r'(?:💰\s*)?Money per sec[:\s]*([^\n]+)', msg, re.IGNORECASE)
    players = re.search(r'(?:👥\s*)?Players[:\s]*([0-9]+\s*/\s*[0-9]+)', msg, re.IGNORECASE)
    jobid_mobile = re.search(r'(?:🆔\s*)?Job ID \(Mobile\)[:\s]*([A-Za-z0-9\-+/=]+)', msg, re.IGNORECASE)
    jobid_pc = re.search(r'(?:🆔\s*)?Job ID \(PC\)[:\s]*([A-Za-z0-9\-+/=]+)', msg, re.IGNORECASE)
    script = re.search(r'(?:📜\s*)?Join Script \(PC\)[:\s]*(game:GetService\("TeleportService"\):TeleportToPlaceInstance\([^\n]+\))', msg, re.IGNORECASE)
    join_match = re.search(r'TeleportToPlaceInstance\((\d+),[ "\']*([A-Za-z0-9\-+/=]+)[ "\']*,', msg)

    players_str = players.group(1) if players else None
    current_players = None
    max_players = None
    if players_str:
        m = re.search(r'(\d+)\s*/\s*(\d+)', players_str)
        if m:
            current_players = int(m.group(1))
            max_players = int(m.group(2))

    # If join_match found, extract place_id and instance_id
    place_id = join_match.group(1) if join_match else None
    instance_id = join_match.group(2) if join_match else None

    return {
        "brainrot_name": name.group(1).strip() if name else None,
        "money_per_sec": money.group(1).strip() if money else None,
        "players": players_str.strip() if players_str else None,
        "current_players": current_players,
        "max_players": max_players,
        "job_id_mobile": jobid_mobile.group(1).strip() if jobid_mobile else None,
        "job_id_pc": jobid_pc.group(1).strip() if jobid_pc else None,
        "join_script": script.group(1).strip() if script else None,
        "place_id": place_id,
        "instance_id": instance_id,
        "server_id": place_id,      # explicit for backend
        "job_id": instance_id       # explicit for backend
    }

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

def build_embed(info):
    fields = []
    if info["brainrot_name"]:
        fields.append({
            "name": "Brainrot Name",
            "value": f"**{info['brainrot_name']}**",
            "inline": False
        })
    if info["money_per_sec"]:
        fields.append({
            "name": "Money Per Second",
            "value": f"**{info['money_per_sec']}**",
            "inline": True
        })
    if info["players"]:
        fields.append({
            "name": "Players",
            "value": f"**{info['players']}**",
            "inline": True
        })
    if info["place_id"] and info["instance_id"]:
        join_url = f"https://chillihub1.github.io/chillihub-joiner/?placeId={info['place_id']}&gameInstanceId={info['instance_id']}"
        fields.append({
            "name": "Join Link",
            "value": f"[Click to Join]({join_url})",
            "inline": False
        })
    if info["job_id_mobile"]:
        fields.append({
            "name": "Job ID (Mobile)",
            "value": f"`{info['job_id_mobile']}`",
            "inline": False
        })
    if info["job_id_pc"]:
        fields.append({
            "name": "Job ID (PC)",
            "value": f"```\n{info['job_id_pc']}\n```",
            "inline": False
        })
    if info["join_script"]:
        fields.append({
            "name": "Join Script (PC)",
            "value": f"```lua\n{info['join_script']}\n```",
            "inline": False
        })
    embed = {
        "title": "Eps1lon Hub Notifier",
        "color": 0x00ff99,
        "fields": fields
    }
    return {"embeds": [embed]}

def send_to_backend(info):
    """
    Instantly send all info to backend, always.
    """
    # Send everything, no filters
    try:
        response = requests.post(BACKEND_URL, json=info, timeout=10)
        if response.status_code == 200:
            print(f"✅ Sent to backend: {info}")
        elif response.status_code == 429:
            print(f"⚠️ Rate limited for backend: {info}")
        else:
            print(f"❌ Backend error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Failed to send to backend: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id not in CHANNEL_IDS:
        return

    full_content = get_message_full_content(message)
    info = parse_info(full_content)
    print("DEBUG: full_content:\n", full_content)
    print("DEBUG: parsed info:", info)
    embed_payload = build_embed(info)
    try:
        requests.post(WEBHOOK_URL, json=embed_payload)
    except Exception as e:
        print(f"Failed to send embed to webhook: {e}")
    # Send everything to backend, always
    send_to_backend(info)

client.run(TOKEN)
