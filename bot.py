import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables (DISCORD_TOKEN from .env)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Enable message content intent
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# File paths
BOSSES_FILE = "bosses.json"
SPAWN_TIMERS_FILE = "spawn_timers.json"

# Load bosses.json
def load_bosses():
    with open(BOSSES_FILE, "r") as f:
        data = json.load(f)
    bosses_dict = {}
    for boss in data:
        bosses_dict[boss["name"].lower()] = boss
    return bosses_dict

bosses = load_bosses()

# Load / save spawn timers
def load_spawn_timers():
    if os.path.exists(SPAWN_TIMERS_FILE):
        with open(SPAWN_TIMERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_spawn_timers(data):
    with open(SPAWN_TIMERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

spawn_timers = load_spawn_timers()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Convert string time like "5:00 PM" to datetime object today
def parse_time_str(time_str):
    return datetime.strptime(time_str, "%I:%M %p")

# /kill command
@bot.command()
async def kill(ctx, name: str, killed_at: str):
    """
    Usage: /kill [bossname] [HH:MM AM/PM] e.g. /kill Undomiel 5:00 PM
    """
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found in list.")
        return

    try:
        killed_time = parse_time_str(killed_at)
        now = datetime.now()
        # Replace today's date
        killed_time = killed_time.replace(year=now.year, month=now.month, day=now.day)
    except ValueError:
        await ctx.send("⚠️ Invalid time format. Use `HH:MM AM/PM`.")
        return

    boss = bosses[name_lower]

    if boss.get("special"):
        # Special boss: use next scheduled spawn
        schedule = boss.get("schedule", [])
        next_spawn_time = None
        for s in schedule:
            dt = datetime.now().replace(hour=s["hour"], minute=s["minute"], second=0, microsecond=0)
            if dt > datetime.now():
                next_spawn_time = dt
                break
        if next_spawn_time is None:
            next_spawn_time = datetime.now()
    else:
        respawn_sec = boss.get("respawn", 0)
        next_spawn_time = killed_time + timedelta(seconds=respawn_sec)

    spawn_timers[name_lower] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %I:%M %p"),
        "next_spawn": next_spawn_time.strftime("%Y-%m-%d %I:%M %p")
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(
        f"☠️ {name.capitalize()} was killed at {killed_time.strftime('%I:%M %p')}.\n"
        f"🕒 Next spawn: **{next_spawn_time.strftime('%I:%M %p')}**"
    )

# /info command
@bot.command()
async def info(ctx, name: str):
    """
    Usage: /info [bossname]
    """
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    if name_lower not in spawn_timers:
        await ctx.send(f"ℹ️ No spawn data recorded for {name.capitalize()} yet.")
        return

    last = spawn_timers[name_lower]["last_killed"]
    next_spawn = spawn_timers[name_lower]["next_spawn"]

    await ctx.send(
        f"📜 Info for {name.capitalize()}:\n"
        f"☠️ Last killed: {last}\n"
        f"🕒 Next spawn: {next_spawn}"
    )

# /next command
@bot.command()
async def next(ctx):
    """
    Show the next boss to spawn based on current time
    """
    upcoming = []
    now = datetime.now()
    for name, data in spawn_timers.items():
        next_spawn_str = data.get("next_spawn")
        if next_spawn_str:
            next_spawn_dt = datetime.strptime(next_spawn_str, "%Y-%m-%d %I:%M %p")
            if next_spawn_dt > now:
                upcoming.append((name, next_spawn_dt))
    if not upcoming:
        await ctx.send("ℹ️ No upcoming spawns recorded yet.")
        return

    upcoming.sort(key=lambda x: x[1])
    next_boss, next_time = upcoming[0]

    await ctx.send(
        f"⏳ Next boss to spawn: **{next_boss.capitalize()}** at {next_time.strftime('%I:%M %p')}"
    )

bot.run(TOKEN)
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
        data = json.load(f)
    # Convert list to dict with lowercase keys for easier lookup
    return {boss["name"].lower(): boss for boss in data}

def load_spawn_timers():
    if os.path.exists(SPAWN_TIMERS_FILE):
        with open(SPAWN_TIMERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_spawn_timers(data):
    with open(SPAWN_TIMERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_next_special_spawn(boss):
    """Calculate next spawn for special bosses with schedules."""
    now = datetime.now()
    next_spawn = None

    for sched in boss["schedule"]:
        day = sched["day"]
        hour = sched["hour"]
        minute = sched["minute"]

        spawn = datetime.combine(
            now.date() + timedelta(days=(day - now.weekday() + 7) % 7),
            datetime.min.time()
        ) + timedelta(hours=hour, minutes=minute)

        if spawn < now:
            spawn += timedelta(days=7)

        if next_spawn is None or spawn < next_spawn:
            next_spawn = spawn

    return next_spawn

bosses = load_bosses()
spawn_timers = load_spawn_timers()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, name: str, killed_at: str = None):
    """
    Usage: /kill [bossname] [HHMMH] 
    For special bosses, killed_at is optional.
    """
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found in list.")
        return

    boss_data = bosses[name_lower]

    # Determine killed_time
    if killed_at:
        try:
            t = datetime.strptime(killed_at, "%H%MH").time()
            killed_time = datetime.combine(datetime.today(), t)
        except ValueError:
            await ctx.send("⚠️ Invalid time format. Use military time like `1700H`.")
            return
    else:
        killed_time = datetime.now()

    # Determine next spawn
    if boss_data.get("special"):
        next_spawn = get_next_special_spawn(boss_data)
    else:
        respawn_seconds = boss_data.get("respawn")
        if not respawn_seconds:
            await ctx.send(f"⚠️ Boss '{name}' does not have a fixed respawn timer.")
            return
        next_spawn = killed_time + timedelta(seconds=respawn_seconds)

    # Save to spawn_timers
    spawn_timers[name_lower] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %H:%M"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %H:%M")
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(
        f"☠️ {name.capitalize()} was killed at {killed_time.strftime('%H:%M')}.\n"
        f"🕒 Next spawn: **{next_spawn.strftime('%Y-%m-%d %H:%M')}**"
    )

# /info command
@bot.command()
async def info(ctx, name: str):
    """
    Usage: /info [bossname]
    """
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    boss_data = bosses[name_lower]

    # If no previous kill recorded, calculate next spawn
    if name_lower not in spawn_timers:
        if boss_data.get("special"):
            next_spawn = get_next_special_spawn(boss_data)
        elif boss_data.get("respawn"):
            next_spawn = datetime.now() + timedelta(seconds=boss_data["respawn"])
        else:
            await ctx.send(f"ℹ️ No spawn data recorded for {name.capitalize()} yet.")
            return

        last_killed = "N/A"
        next_spawn_str = next_spawn.strftime("%Y-%m-%d %H:%M")
    else:
        last_killed = spawn_timers[name_lower]["last_killed"]
        next_spawn_str = spawn_timers[name_lower]["next_spawn"]

    await ctx.send(
        f"📜 Info for {name.capitalize()}:\n"
        f"☠️ Last killed: {last_killed}\n"
        f"🕒 Next spawn: {next_spawn_str}"
    )

# /next command
@bot.command()
async def next(ctx):
    """
    Show which boss(es) will spawn next.
    """
    now = datetime.now()
    next_bosses = []

    for name_lower, boss_data in bosses.items():
        if boss_data.get("special"):
            next_spawn = get_next_special_spawn(boss_data)
        elif boss_data.get("respawn"):
            if name_lower in spawn_timers:
                last_killed = datetime.strptime(spawn_timers[name_lower]["last_killed"], "%Y-%m-%d %H:%M")
                next_spawn = last_killed + timedelta(seconds=boss_data["respawn"])
            else:
                next_spawn = now + timedelta(seconds=boss_data["respawn"])
        else:
            continue

        next_bosses.append((name_lower, next_spawn))

    if not next_bosses:
        await ctx.send("ℹ️ No bosses with spawn timers found.")
        return

    # Find soonest spawn
    next_spawn_time = min(b[1] for b in next_bosses)
    soonest = [b for b in next_bosses if b[1] == next_spawn_time]

    message = "🕒 Next spawn(s):\n"
    for name_lower, spawn_time in soonest:
        message += f"**{name_lower.capitalize()}** at {spawn_time.strftime('%Y-%m-%d %H:%M')}\n"

    await ctx.send(message)

bot.run(TOKEN)
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
        data = json.load(f)
    # Convert list to dict with lowercase keys for easier lookup
    return {boss["name"].lower(): boss for boss in data}

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
async def kill(ctx, name: str, killed_at: str = None):
    """
    Usage: /kill [bossname] [HHMMH] e.g. /kill Undomiel 1700H
    If killed_at is not provided, current time is used.
    """
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found in list.")
        return

    # Parse time if provided
    if killed_at:
        try:
            t = datetime.strptime(killed_at, "%H%MH").time()
            killed_time = datetime.combine(datetime.today(), t)
        except ValueError:
            await ctx.send("⚠️ Invalid time format. Use military time like `1700H`.")
            return
    else:
        killed_time = datetime.now()

    # Determine respawn seconds
    boss_data = bosses[name_lower]
    if "respawn" not in boss_data:
        await ctx.send(f"⚠️ Boss '{name}' does not have a fixed respawn timer.")
        return

    respawn_seconds = boss_data["respawn"]
    next_spawn = killed_time + timedelta(seconds=respawn_seconds)

    # Save to spawn_timers
    spawn_timers[name_lower] = {
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
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    if name_lower not in spawn_timers:
        await ctx.send(f"ℹ️ No spawn data recorded for {name.capitalize()} yet.")
        return

    last = spawn_timers[name_lower]["last_killed"]
    next_spawn = spawn_timers[name_lower]["next_spawn"]

    await ctx.send(
        f"📜 Info for {name.capitalize()}:\n"
        f"☠️ Last killed: {last}\n"
        f"🕒 Next spawn: {next_spawn}"
    )

bot.run(TOKEN)
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

# Files
BOSSES_FILE = "bosses.json"
SPAWN_TIMERS_FILE = "spawn_timers.json"

# Load boss data
def load_bosses():
    with open(BOSSES_FILE, "r") as f:
        data = json.load(f)
    # Convert to dict keyed by lowercase boss names
    return {boss["name"].lower(): boss for boss in data}

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
    Usage: /kill [bossname] [HHMMH] e.g. /kill Undomiel 1700H
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

    respawn_seconds = bosses[name].get("respawn", 0)
    next_spawn = killed_time + timedelta(seconds=respawn_seconds)

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
