import os
import discord
import re
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"
DEFAULT_PLACE_ID = "109983668079237"  # Set this to your game's default placeId

client = discord.Client()

def extract_place_and_instance(msg):
    # Extract from join script
    script = re.search(r'TeleportToPlaceInstance\((\d+),\s*"?([A-Za-z0-9\-+/=]+)"?', msg)
    if script:
        return script.group(1), script.group(2)
    # Extract from join links (fern, chillihub, etc)
    link = re.search(r'joiner\?placeId=(\d+)&gameInstanceId=([A-Za-z0-9\-+/=]+)', msg)
    if link:
        return link.group(1), link.group(2)
    return None, None

def parse_pet_message(msg):
    # For pet found messages
    pets = re.search(r'Pets:\s*([^\n]+)', msg)
    players = re.search(r'Players:\s*([^\n]+)', msg)
    script_mobile = re.search(r'Script For mobile.*?:\s*([^\n]+)', msg)
    script_pc = re.search(r'Script For PC.*?:\s*([^\n]+)', msg)
    placeid, instanceid = extract_place_and_instance(msg)
    return {
        "pets": pets.group(1) if pets else None,
        "players": players.group(1) if players else None,
        "script_mobile": script_mobile.group(1) if script_mobile else None,
        "script_pc": script_pc.group(1) if script_pc else None,
        "placeid": placeid or DEFAULT_PLACE_ID,
        "instanceid": instanceid
    }

def parse_hub_message(msg):
    name = re.search(r'🏷️ Name\n([^\n]+)', msg)
    money = re.search(r'💰 Money per sec\n([^\n]+)', msg)
    players = re.search(r'👥 Players\n([^\n]+)', msg)
    jobid_mobile = re.search(r'Job ID \(Mobile\)\n([A-Za-z0-9\-+/=]+)', msg)
    jobid_pc = re.search(r'Job ID \(PC\)\n([A-Za-z0-9\-+/=]+)', msg)
    script = re.search(r'Join Script \(PC\)\n(game:GetService\("TeleportService"\):TeleportToPlaceInstance\([^\n]+\))', msg)
    placeid, instanceid = extract_place_and_instance(msg)
    return {
        "name": name.group(1) if name else None,
        "money": money.group(1) if money else None,
        "players": players.group(1) if players else None,
        "jobid_mobile": jobid_mobile.group(1) if jobid_mobile else None,
        "jobid_pc": jobid_pc.group(1) if jobid_pc else None,
        "script": script.group(1) if script else None,
        "placeid": placeid or DEFAULT_PLACE_ID,
        "instanceid": instanceid or jobid_pc.group(1) if jobid_pc else None
    }

def build_pet_embed(info):
    fields = []
    if info["pets"]:
        fields.append({"name": "🐾 Pets", "value": f"**{info['pets']}**", "inline": False})
    if info["players"]:
        fields.append({"name": "👥 Players", "value": f"**{info['players']}**", "inline": True})
    if info["script_mobile"]:
        fields.append({"name": "📱 Script For Mobile", "value": f"```lua\n{info['script_mobile']}\n```", "inline": False})
    if info["script_pc"]:
        fields.append({"name": "💻 Script For PC", "value": f"```lua\n{info['script_pc']}\n```", "inline": False})
    if info["placeid"] and info["instanceid"]:
        join_url = f"https://chillihub1.github.io/chillihub-joiner/?placeId={info['placeid']}&gameInstanceId={info['instanceid']}"
        fields.append({"name": "🌐 Join Link", "value": "[Click to Join](%s)" % join_url, "inline": False})
    embed = {
        "title": "New Pet Found",
        "color": 0x57F287,  # Green
        "fields": fields
    }
    return {"embeds": [embed]}

def build_hub_embed(info):
    fields = []
    if info["name"]:
        fields.append({"name": "🏷️ Name", "value": f"**{info['name']}**", "inline": False})
    if info["money"]:
        fields.append({"name": "💰 Money per sec", "value": f"**{info['money']}**", "inline": True})
    if info["players"]:
        fields.append({"name": "👥 Players", "value": f"**{info['players']}**", "inline": True})
    if info["placeid"] and info["instanceid"]:
        join_url = f"https://chillihub1.github.io/chillihub-joiner/?placeId={info['placeid']}&gameInstanceId={info['instanceid']}"
        fields.append({"name": "🌐 Join Link", "value": "[Click to Join](%s)" % join_url, "inline": False})
    if info["jobid_mobile"]:
        fields.append({"name": "🆔 Job ID (Mobile)", "value": f"`{info['jobid_mobile']}`", "inline": False})
    if info["jobid_pc"]:
        fields.append({"name": "🆔 Job ID (PC)", "value": f"```\n{info['jobid_pc']}\n```", "inline": False})
    if info["script"]:
        fields.append({"name": "📜 Join Script (PC)", "value": f"```lua\n{info['script']}\n```", "inline": False})
    embed = {
        "title": "Eps1lon Hub Notifier",
        "color": 0x5865F2,
        "fields": fields
    }
    return {"embeds": [embed]}

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

    full_content = get_message_full_content(message)
    # Check if it's a pet found message
    if "New Pet Found" in full_content:
        info = parse_pet_message(full_content)
        if info["pets"] and info["players"] and info["instanceid"]:
            embed_payload = build_pet_embed(info)
            try:
                requests.post(WEBHOOK_URL, json=embed_payload)
            except Exception as e:
                print(f"Failed to send pet embed to webhook: {e}")
    # Otherwise, handle as hub notifier
    elif "Name" in full_content and "Money per sec" in full_content:
        info = parse_hub_message(full_content)
        if info["name"] and info["money"] and info["players"] and info["instanceid"]:
            embed_payload = build_hub_embed(info)
            try:
                requests.post(WEBHOOK_URL, json=embed_payload)
            except Exception as e:
                print(f"Failed to send hub embed to webhook: {e}")
    else:
        # fallback: send plain text
        try:
            requests.post(WEBHOOK_URL, json={"content": full_content})
        except Exception as e:
            print(f"Failed to send plain text to webhook: {e}")

client.run(TOKEN)
