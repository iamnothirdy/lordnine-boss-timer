import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables (DISCORD_TOKEN from .env)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Enable message content intent (required for commands)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Load boss data
BOSSES_FILE = "bosses.json"
SPAWN_TIMERS_FILE = "spawn_timers.json"

def load_bosses():
    with open(BOSSES_FILE, "r") as f:
        return json.load(f)

def load_spawn_timers():
    if os.path.exists(SPAWN_TIMERS_FILE):
        with open(SPAWN_TIMERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_spawn_timers(data):
    with open(SPAWN_TIMERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

bosses = load_bosses()
spawn_timers = load_spawn_timers()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, name: str, killed_at: str):
    """
    Usage: /kill [bossname] [HHMMH] e.g. /kill orfen 1700H
    """
    name = name.lower()
    if name not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found in list.")
        return

    try:
        killed_time = datetime.strptime(killed_at, "%H%MH")
    except ValueError:
        await ctx.send("⚠️ Invalid time format. Use military time like `1700H`.")
        return

    respawn_minutes = bosses[name]["respawn"]
    next_spawn = killed_time + timedelta(minutes=respawn_minutes)

    spawn_timers[name] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %H:%M"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %H:%M")
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(
        f"☠️ {name.capitalize()} was killed at {killed_time.strftime('%H:%M')}.\n"
        f"🕒 Next spawn: **{next_spawn.strftime('%H:%M')}**"
    )

# /info command
@bot.command()
async def info(ctx, name: str):
    """
    Usage: /info [bossname]
    """
    name = name.lower()
    if name not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    if name not in spawn_timers:
        await ctx.send(f"ℹ️ No spawn data recorded for {name.capitalize()} yet.")
        return

    last = spawn_timers[name]["last_killed"]
    next_spawn = spawn_timers[name]["next_spawn"]

    await ctx.send(
        f"📜 Info for {name.capitalize()}:\n"
        f"☠️ Last killed: {last}\n"
        f"🕒 Next spawn: {next_spawn}"
    )

bot.run(TOKEN)
