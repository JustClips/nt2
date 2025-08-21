import os
import discord
import re
import requests
import threading

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("CHANNEL_ID", "1234567890").split(",")]
WEBHOOK_URLS = [url.strip() for url in os.getenv("WEBHOOK_URLS", "").split(",") if url.strip()]
BACKEND_URL = os.getenv("BACKEND_URL")

client = discord.Client()  # Selfbot, NO intents!

def parse_brainrot_message(msg):
    """Parse only Name, Money per sec, Players, Job ID (PC) from the message."""
    def grab(pattern):
        m = re.search(pattern, msg, re.MULTILINE)
        return m.group(1).strip() if m else None

    name = grab(r"🏷️ Name\s*\n([^\n]+)")
    money = grab(r"💰 Money per sec\s*\n([^\n]+)")
    players = grab(r"👥 Players\s*\n([^\n]+)")
    jobid = grab(r"Job ID \(PC\)\s*\n([^\n]+)")

    return {
        "name": name,
        "money": money,
        "players": players,
        "jobid": jobid  # This will be sent as both jobId and instanceId
    }

def build_embed(info):
    """Return a Discord webhook embed with a clean, modern design."""
    fields = []
    if info["name"]:
        fields.append({"name": "🏷️ Name", "value": f"**{info['name']}**", "inline": False})
    if info["money"]:
        fields.append({"name": "💰 Money per sec", "value": f"**{info['money']}**", "inline": True})
    if info["players"]:
        fields.append({"name": "👥 Players", "value": f"**{info['players']}**", "inline": True})
    if info["jobid"]:
        fields.append({"name": "🆔 Job ID", "value": f"```{info['jobid']}```", "inline": False})

    embed = {
        "title": "🧠 Brainrot Server Snapshot",
        "color": 0x00FF94,
        "fields": fields,
        "footer": {"text": "Made by notasnek | Eps1lon Hub"},
    }
    return {"embeds": [embed]}

def send_to_webhooks(payload):
    def send(url, payload):
        try:
            response = requests.post(url, json=payload, timeout=10)
            print("✅ Webhook sent" if response.status_code in [200,204] else f"❌ Webhook error {response.status_code}")
        except Exception as e:
            print(f"❌ Webhook exception: {e}")
    threads = []
    for url in WEBHOOK_URLS:
        t = threading.Thread(target=send, args=(url, payload))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def send_to_backend(info):
    # Only send minimal required: name, money, jobId=instanceId
    if not info["name"] or not info["jobid"]:
        print("Skipping backend send - missing name or jobid")
        return
    payload = {
        "name": info["name"],
        "moneyPerSec": info["money"] or "",
        "jobId": info["jobid"],
        "instanceId": info["jobid"],  # For your backend, both are set
    }
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Sent to backend: {info['name']}")
        elif response.status_code == 429:
            print(f"⚠️ Rate limited for backend: {info['name']}")
        else:
            print(f"❌ Backend error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Failed to send to backend: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    print(f'Configured to send to {len(WEBHOOK_URLS)} webhook(s)')

@client.event
async def on_message(message):
    if message.channel.id not in CHANNEL_IDS:
        return
    msg = message.content
    # Only parse plain text, ignore embeds/attachments for this format
    info = parse_brainrot_message(msg)
    print("Parsed info:", info)
    if info["name"] and info["money"] and info["players"] and info["jobid"]:
        embed_payload = build_embed(info)
        send_to_webhooks(embed_payload)
        send_to_backend(info)
        print(f"✅ Sent embed and backend for: {info['name']}")
    else:
        print("⚠️ Missing required fields. Skipping.")

client.run(TOKEN)
