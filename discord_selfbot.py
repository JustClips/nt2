import os
import discord
import re
import json

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1234567890"))  # Set this as env var on Railway

client = discord.Client()

def parse_money_job(msg):
    money_match = re.search(r'Money per sec\n\$(\d+\.?\d*)M/s', msg)
    jobid_match = re.search(r'Job ID \(PC\)\n=([A-Za-z0-9+/=]+)', msg)
    if money_match and jobid_match:
        money = float(money_match.group(1))
        jobid = jobid_match.group(1)
        return money, jobid
    return None, None

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    content = message.content
    money, jobid = parse_money_job(content)
    if money and money > 10:
        with open("join_request.json", "w") as f:
            json.dump({"jobid": jobid}, f)
        print(f"Found server with ${money}M/s, Job ID: {jobid}")

client.run(TOKEN)
