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

def parse_pet_found(msg):
    # Returns (pet_list, player_count, place_id, instance_id) if matched
    pet_match = re.search(r'🐾 New Pet Found - ([\d\-: ]+)\nPets: (.+)\nPlayers: (\d+/\d+)', msg)
    script_pc_match = re.search(r'Script For PC:\s*game:GetService\("TeleportService"\):TeleportToPlaceInstance\((\d+), "([0-9a-f\-]+)"\)', msg)
    if pet_match and script_pc_match:
        pet_list = pet_match.group(2)
        player_count = pet_match.group(3)
        place_id = script_pc_match.group(1)
        instance_id = script_pc_match.group(2)
        return pet_list, player_count, place_id, instance_id
    return None

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return

    # Log every message with timestamp, author, and content
    print(f"[{message.created_at}] {message.author}: {message.content}")

    # Parse pet found messages
    pet_info = parse_pet_found(message.content)
    if pet_info:
        pet_list, player_count, place_id, instance_id = pet_info
        print(f"🐾 New Pet(s): {pet_list} | Players: {player_count} | PlaceID: {place_id} | InstanceID: {instance_id}")
        # Optionally, save to JSON for Roblox or other uses
        with open("pet_found.json", "w") as f:
            json.dump({
                "pets": pet_list,
                "players": player_count,
                "place_id": place_id,
                "instance_id": instance_id
            }, f)

    # Still include your old money/jobid logic if needed
    money, jobid = parse_money_job(message.content)
    if money and money > 10:
        with open("join_request.json", "w") as f:
            json.dump({"jobid": jobid}, f)
        print(f"Found server with ${money}M/s, Job ID: {jobid}")

client.run(TOKEN)
