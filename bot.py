import discord
from discord.ext import commands
import json
import datetime
import asyncio

# Load boss data
with open("bosses.json", "r") as f:
    bosses = json.load(f)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --------------------------
# Helper functions
# --------------------------

def get_boss(name):
    """Find boss by name (case insensitive)."""
    for boss in bosses:
        if boss["name"].lower() == name.lower():
            return boss
    return None

def format_time(seconds):
    """Convert seconds into H:M:S."""
    return str(datetime.timedelta(seconds=seconds))

# --------------------------
# Slash commands
# --------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.tree.command(name="kill", description="Mark a boss as killed and reset its timer")
async def kill(interaction: discord.Interaction, boss_name: str):
    boss = get_boss(boss_name)
    if not boss:
        await interaction.response.send_message(f"❌ Boss '{boss_name}' not found.", ephemeral=True)
        return

    if boss.get("special"):
        await interaction.response.send_message(f"⚠️ {boss['name']} is a scheduled boss, not a respawn boss.", ephemeral=True)
        return

    now = datetime.datetime.utcnow()
    respawn = boss["respawn"]
    next_spawn = now + datetime.timedelta(seconds=respawn)

    boss["nextSpawn"] = next_spawn.strftime("%I:%M %p UTC")

    # Save update
    with open("bosses.json", "w") as f:
        json.dump(bosses, f, indent=2)

    await interaction.response.send_message(
        f"☠️ {boss['name']} marked as killed!\nNext spawn at **{boss['nextSpawn']}**."
    )

@bot.tree.command(name="info", description="Get info about a boss")
async def info(interaction: discord.Interaction, boss_name: str):
    boss = get_boss(boss_name)
    if not boss:
        await interaction.response.send_message(f"❌ Boss '{boss_name}' not found.", ephemeral=True)
        return

    if boss.get("special"):
        schedule = "\n".join(
            [f"Day {s['day']} at {s['hour']:02d}:{s['minute']:02d}" for s in boss["schedule"]]
        )
        await interaction.response.send_message(
            f"📅 **{boss['name']}** is a scheduled boss.\nSchedule:\n{schedule}"
        )
    else:
        next_spawn = boss.get("nextSpawn", "Unknown")
        respawn = format_time(boss["respawn"])
        await interaction.response.send_message(
            f"🐉 **{boss['name']}**\nRespawn every: {respawn}\nNext spawn: {next_spawn}"
        )

# --------------------------
# Run the bot
# --------------------------
if __name__ == "__main__":
    import os
    TOKEN = os.getenv("DISCORD_TOKEN")  # safer to use environment variable
    if not TOKEN:
        print("❌ No token found. Please set DISCORD_TOKEN in your environment.")
    else:
        bot.run(TOKEN)
