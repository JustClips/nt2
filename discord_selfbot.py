import os
import discord
import re
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URL = "https://discord.com/api/webhooks/1402027109890658455/cvXdXAR1O0zlUsuEz8COOiSfEzIX3FyepSj5LXNFrKRFAZIYQRxGLk2T1JrhjZ2kEzRe"

client = discord.Client()

def parse_info(msg):
    # Parse all possible relevant fields
    name = re.search(r'🏷️ Name\n([^\n]+)', msg)
    money = re.search(r'💰 Money per sec\n([^\n]+)', msg)
    players = re.search(r'👥 Players\n([^\n]+)', msg)
    jobid_mobile = re.search(r'Job ID \(Mobile\)\n([A-Za-z0-9\-+/=]+)', msg)
    jobid_pc = re.search(r'Job ID \(PC\)\n([A-Za-z0-9\-+/=]+)', msg)
    script = re.search(r'Join Script \(PC\)\n(game:GetService\("TeleportService"\):TeleportToPlaceInstance\([^\n]+\))', msg)
    # Also extract placeId and instanceId for join link
    join_match = re.search(r'TeleportToPlaceInstance\((\d+),[ "\']*([A-Za-z0-9\-+/=]+)[ "\']*,', msg)
    return {
        "name": name.group(1) if name else None,
        "money": money.group(1) if money else None,
        "players": players.group(1) if players else None,
        "jobid_mobile": jobid_mobile.group(1) if jobid_mobile else None,
        "jobid_pc": jobid_pc.group(1) if jobid_pc else None,
        "script": script.group(1) if script else None,
        "placeid": join_match.group(1) if join_match else None,
        "instanceid": join_match.group(2) if join_match else None
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
    # Build an embed payload for Discord webhook
    fields = []
    if info["name"]:
        fields.append({
            "name": "🏷️ Name",
            "value": f"**{info['name']}**",
            "inline": False
        })
    if info["money"]:
        fields.append({
            "name": "💰 Money per sec",
            "value": f"**{info['money']}**",
            "inline": True
        })
    if info["players"]:
        fields.append({
            "name": "👥 Players",
            "value": f"**{info['players']}**",
            "inline": True
        })
    # Join link as a clickable field if placeid and instanceid are available
    join_link = ""
    if info["placeid"] and info["instanceid"]:
        join_url = f"https://chillihub1.github.io/chillihub-joiner/?placeId={info['placeid']}&gameInstanceId={info['instanceid']}"
        fields.append({
            "name": "🌐 Join Link",
            "value": "[Click to Join](%s)" % join_url,
            "inline": False
        })
    if info["jobid_mobile"]:
        fields.append({
            "name": "🆔 Job ID (Mobile)",
            "value": f"`{info['jobid_mobile']}`",
            "inline": False
        })
    if info["jobid_pc"]:
        fields.append({
            "name": "🆔 Job ID (PC)",
            "value": f"```\n{info['jobid_pc']}\n```",
            "inline": False
        })
    if info["script"]:
        fields.append({
            "name": "📜 Join Script (PC)",
            "value": f"```lua\n{info['script']}\n```",
            "inline": False
        })
    embed = {
        "title": "Eps1lon Hub Notifier",
        "color": 0x5865F2,  # Discord blurple
        "fields": fields
    }
    return {"embeds": [embed]}

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id not in CHANNEL_IDS:
        return

    full_content = get_message_full_content(message)

    # Try to parse info and build a rich embed
    info = parse_info(full_content)
    # Only send as embed if we have at least a name, money, and players
    if info["name"] and info["money"] and info["players"]:
        embed_payload = build_embed(info)
        try:
            requests.post(WEBHOOK_URL, json=embed_payload)
        except Exception as e:
            print(f"Failed to send embed to webhook: {e}")
    else:
        # fallback: send plain text
        try:
            requests.post(WEBHOOK_URL, json={"content": full_content})
        except Exception as e:
            print(f"Failed to send plain text to webhook: {e}")

client.run(TOKEN)
