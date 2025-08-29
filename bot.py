2025-08-29 18:22:31 ERROR    discord.ext.commands.bot Ignoring exception in command next
Traceback (most recent call last):
  File "/Users/ciriacogelera/Documents/lordnine_boss/discord-bot/lordnine/venv/lib/python3.13/site-packages/discord/ext/commands/core.py", line 235, in wrapped
    ret = await coro(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/ciriacogelera/Documents/lordnine_boss/discord-bot/lordnine/lordnine-boss-timer/bot.py", line 146, in next
    status, dt = get_next_spawn(name_norm)
                 ~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/Users/ciriacogelera/Documents/lordnine_boss/discord-bot/lordnine/lordnine-boss-timer/bot.py", line 77, in get_next_spawn
    next_spawn = datetime.strptime(timer["next_spawn"], "%Y-%m-%d %H:%M")
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/_strptime.py", line 789, in _strptime_datetime
    tt, fraction, gmtoff_fraction = _strptime(data_string, format)
                                    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/_strptime.py", line 558, in _strptime
    raise ValueError("unconverted data remains: %s" %
                      data_string[found.end():])
ValueError: unconverted data remains:  PM

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/ciriacogelera/Documents/lordnine_boss/discord-bot/lordnine/venv/lib/python3.13/site-packages/discord/ext/commands/bot.py", line 1366, in invoke
    await ctx.command.invoke(ctx)
  File "/Users/ciriacogelera/Documents/lordnine_boss/discord-bot/lordnine/venv/lib/python3.13/site-packages/discord/ext/commands/core.py", line 1029, in invoke
    await injected(*ctx.args, **ctx.kwargs)  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/ciriacogelera/Documents/lordnine_boss/discord-bot/lordnine/venv/lib/python3.13/site-packages/discord/ext/commands/core.py", line 244, in wrapped
    raise CommandInvokeError(exc) from exc
discord.ext.commands.errors.CommandInvokeError: Command raised an exception: ValueError: unconverted data remains:  PMimport discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Files
BOSSES_FILE = "bosses.json"
SPAWN_TIMERS_FILE = "spawn_timers.json"

# Load data
def load_bosses():
    with open(BOSSES_FILE, "r") as f:
        data = json.load(f)
        # Normalize names for lookup
        return {b["name"].lower().replace(" ", ""): b for b in data}

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

# Helpers
def parse_time(time_str: str):
    try:
        return datetime.strptime(time_str.upper(), "%I:%M%p")
    except ValueError:
        return None

def format_datetime(dt: datetime):
    return dt.strftime("%Y-%m-%d %I:%M %p")

def normalize_name(name: str):
    return name.lower().replace(" ", "")

def get_next_spawn(boss_name: str):
    boss = bosses[boss_name]
    timer = spawn_timers.get(boss_name)
    
    if "special" in boss and boss["special"]:
        now = datetime.now()
        upcoming = []
        for schedule in boss["schedule"]:
            # Next date matching schedule
            spawn_dt = datetime.now().replace(hour=schedule["hour"], minute=schedule["minute"], second=0, microsecond=0)
            # Adjust if schedule day already passed
            days_ahead = (schedule["day"] - spawn_dt.weekday()) % 7
            spawn_dt = spawn_dt + timedelta(days=days_ahead)
            upcoming.append(spawn_dt)
        upcoming.sort()
        # Find first spawn in future or currently alive
        for sp in upcoming:
            if sp <= datetime.now() < sp + timedelta(seconds=0):
                return "alive", sp
        return "upcoming", upcoming[0]
    else:
        if timer:
            next_spawn = datetime.strptime(timer["next_spawn"], "%Y-%m-%d %H:%M")
            if datetime.now() >= next_spawn:
                return "alive", next_spawn
            return "upcoming", next_spawn
        else:
            return "no_info", None

# Events
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, name: str, killed_at: str):
    name_norm = normalize_name(name)
    if name_norm not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    killed_time = parse_time(killed_at)
    if not killed_time:
        await ctx.send("⚠️ Invalid time format. Use `HH:MMAM/PM` like `06:30PM`.")
        return

    boss = bosses[name_norm]
    now = datetime.now()
    killed_time = killed_time.replace(year=now.year, month=now.month, day=now.day)

    if "respawn" in boss:
        next_spawn = killed_time + timedelta(seconds=boss["respawn"])
    else:
        next_spawn = None  # For specials, next spawn is calculated dynamically

    spawn_timers[name_norm] = {
        "last_killed": format_datetime(killed_time),
        "next_spawn": format_datetime(next_spawn) if next_spawn else "special"
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(f"☠️ **{name}** killed at {format_datetime(killed_time)}.\n"
                   f"🕒 Next spawn: {format_datetime(next_spawn) if next_spawn else 'Special'}")

# /info command
@bot.command()
async def info(ctx, name: str):
    name_norm = normalize_name(name)
    if name_norm not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Files
BOSSES_FILE = "bosses.json"
SPAWN_TIMERS_FILE = "spawn_timers.json"

# Load data
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

bosses_list = load_bosses()
spawn_timers = load_spawn_timers()

# Normalize names (remove spaces, lowercase)
def normalize_name(name: str):
    return name.lower().replace(" ", "")

# Map normalized names to boss data
bosses = {normalize_name(b["name"]): b for b in bosses_list}

# Helper to parse time in AM/PM format
def parse_time_str(time_str: str):
    try:
        return datetime.strptime(time_str, "%I:%M%p")
    except ValueError:
        return None

# Helper to format datetime in AM/PM
def fmt(dt: datetime):
    return dt.strftime("%Y-%m-%d %I:%M %p")

# Calculate next spawn for a boss
def get_next_spawn(name_norm: str):
    boss = bosses[name_norm]
    timer = spawn_timers.get(name_norm)
    now = datetime.now()

    if timer:
        last_killed = datetime.strptime(timer["last_killed"], "%Y-%m-%d %I:%M %p")
        next_spawn = datetime.strptime(timer["next_spawn"], "%Y-%m-%d %I:%M %p")
        if now >= next_spawn:
            status = "alive"
        else:
            status = "upcoming"
        return status, last_killed, next_spawn
    else:
        # No info yet
        return "no_info", None, None

# Events
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, *args):
    if len(args) < 2:
        await ctx.send("⚠️ Usage: /kill [boss name] [HH:MMAM/PM]")
        return

    killed_at_str = args[-1]
    name = " ".join(args[:-1])
    name_norm = normalize_name(name)

    if name_norm not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    killed_time = parse_time_str(killed_at_str)
    if not killed_time:
        await ctx.send("⚠️ Invalid time format. Use HH:MMAM/PM, e.g., 06:00PM.")
        return

    # Use today for killed time
    now = datetime.now()
    killed_time = killed_time.replace(year=now.year, month=now.month, day=now.day)

    respawn_sec = bosses[name_norm].get("respawn")
    if respawn_sec:
        next_spawn = killed_time + timedelta(seconds=respawn_sec)
    else:
        next_spawn = None

    spawn_timers[name_norm] = {
        "last_killed": fmt(killed_time),
        "next_spawn": fmt(next_spawn) if next_spawn else "N/A"
    }
    save_spawn_timers(spawn_timers)

    embed = discord.Embed(title=f"☠️ {name} killed!", color=discord.Color.red())
    embed.add_field(name="Killed at", value=fmt(killed_time), inline=True)
    embed.add_field(name="Next spawn", value=fmt(next_spawn) if next_spawn else "N/A", inline=True)
    await ctx.send(embed=embed)

# /info command
@bot.command()
async def info(ctx, *args):
    if len(args) < 1:
        await ctx.send("⚠️ Usage: /info [boss name]")
        return

    name = " ".join(args)
    name_norm = normalize_name(name)

    if name_norm not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    status, last_killed, next_spawn = get_next_spawn(name_norm)

    embed = discord.Embed(title=f"📜 Info for {name}", color=discord.Color.blue())
    embed.add_field(name="Last killed", value=fmt(last_killed) if last_killed else "No info yet", inline=True)
    embed.add_field(name="Next spawn", value=fmt(next_spawn) if next_spawn else "No info yet", inline=True)
    await ctx.send(embed=embed)

# /next command
@bot.command()
async def next(ctx):
    now = datetime.now()
    embed = discord.Embed(title="🕒 Next Boss Spawn", color=discord.Color.green())

    for name_norm, boss in bosses.items():
        status, last_killed, next_spawn = get_next_spawn(name_norm)
        display_name = boss["name"]

        if status == "alive":
            value = "💥 **Alive Now!**"
        elif status == "upcoming":
            value = f"Last killed: {fmt(last_killed)}\nNext spawn: {fmt(next_spawn)}"
        else:
            value = "No info yet"

        embed.add_field(name=display_name, value=value, inline=False)

    await ctx.send(embed=embed)

bot.run(TOKEN)
    timer = spawn_timers.get(name_norm)
    last = timer.get("last_killed") if timer else "No info yet"
    next_spawn = timer.get("next_spawn") if timer else "No info yet"

    embed = discord.Embed(title=f"📜 Info for {name}", color=discord.Color.blue())
    embed.add_field(name="☠️ Last killed", value=last, inline=False)
    embed.add_field(name="🕒 Next spawn", value=next_spawn, inline=False)
    await ctx.send(embed=embed)

# /next command
@bot.command()
async def next(ctx):
    embed = discord.Embed(title="🕒 Next Boss Spawns", color=discord.Color.gold())

    alive_bosses = []
    upcoming_bosses = []

    for name_norm, boss in bosses.items():
        status, dt = get_next_spawn(name_norm)
        display_name = boss.get("name", name_norm)
        if status == "alive":
            alive_bosses.append(f"✅ **{display_name}** is now alive!")
        elif status == "upcoming":
            timer = spawn_timers.get(name_norm)
            last = timer.get("last_killed") if timer else "No info yet"
            upcoming_bosses.append(f"**{display_name}** → Next spawn: {format_datetime(dt)} | Last killed: {last}")
        else:
            upcoming_bosses.append(f"**{display_name}** → No info yet")

    # Limit fields to <=25
    if alive_bosses:
        embed.add_field(name="Alive Now", value="\n".join(alive_bosses), inline=False)
    if upcoming_bosses:
        # Combine all upcoming into a single field to avoid too many fields
        embed.add_field(name="Upcoming Spawns", value="\n".join(upcoming_bosses), inline=False)

    await ctx.send(embed=embed)

bot.run(TOKEN)
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Enable message content intent
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
        return {b["name"].lower(): b for b in data}

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
async def kill(ctx, *, args: str):
    """
    Usage: /kill [bossname] [HH:MMAM/PM]
    e.g. /kill Undomiel 06:00PM
    """
    try:
        name_part, time_part = args.rsplit(" ", 1)
    except ValueError:
        await ctx.send("⚠️ Please provide boss name and time. Example: `/kill Undomiel 06:00PM`")
        return

    name_key = name_part.lower()
    if name_key not in bosses:
        await ctx.send(f"❌ Boss '{name_part}' not found.")
        return

    try:
        killed_time = datetime.strptime(time_part.upper(), "%I:%M%p")
        killed_time = killed_time.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    except ValueError:
        await ctx.send("⚠️ Invalid time format. Use like `06:00PM`.")
        return

    boss = bosses[name_key]
    respawn_seconds = boss.get("respawn", 0)
    next_spawn = killed_time + timedelta(seconds=respawn_seconds)

    spawn_timers[name_key] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %I:%M %p"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %I:%M %p")
    }
    save_spawn_timers(spawn_timers)

    embed = discord.Embed(title=f"{boss['name']} killed!", color=0xff5555)  # red
    embed.add_field(name="Last killed", value=killed_time.strftime("%b %d, %Y %I:%M %p"), inline=True)
    embed.add_field(name="Next spawn", value=next_spawn.strftime("%b %d, %Y %I:%M %p"), inline=True)

    await ctx.send(embed=embed)

# /info command
@bot.command()
async def info(ctx, *, name: str):
    """
    Usage: /info [bossname]
    """
    name_key = name.lower()
    if name_key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    boss = bosses[name_key]
    timer = spawn_timers.get(name_key)

    embed = discord.Embed(title=f"{boss['name']} Info", color=0x00ffff)  # cyan

    last = timer["last_killed"] if timer else "No info yet"
    next_spawn = timer["next_spawn"] if timer else "No info yet"

    embed.add_field(name="Last killed", value=last, inline=True)
    embed.add_field(name="Next spawn", value=next_spawn, inline=True)

    await ctx.send(embed=embed)

# /next command
@bot.command()
async def next(ctx):
    now = datetime.now()
    currently_alive = []
    upcoming = []

    for key, boss in bosses.items():
        timer = spawn_timers.get(key)
        if timer:
            last_killed_time = datetime.strptime(timer["last_killed"], "%Y-%m-%d %I:%M %p")
            next_spawn_time = datetime.strptime(timer["next_spawn"], "%Y-%m-%d %I:%M %p")
            respawn_seconds = boss.get("respawn", 0)
            alive_time = last_killed_time + timedelta(seconds=respawn_seconds)

            if alive_time <= now <= next_spawn_time:
                currently_alive.append(boss["name"])
            elif next_spawn_time >= now:
                upcoming.append((boss["name"], last_killed_time, next_spawn_time))
        else:
            upcoming.append((boss["name"], None, None))

    embed = discord.Embed(title="Boss Spawn Info", color=0x0000ff)  # blue

    # Currently alive
    if currently_alive:
        embed.add_field(name="⚔️ Currently Alive", value="\n".join(currently_alive), inline=False)

    # Upcoming or no info
    for name, last, next_spawn_time in sorted(upcoming, key=lambda x: x[2] if x[2] else datetime.max):
        last_display = last.strftime("%b %d, %Y %I:%M %p") if last else "No info yet"
        next_display = next_spawn_time.strftime("%b %d, %Y %I:%M %p") if next_spawn_time else "No info yet"
        embed.add_field(
            name=name,
            value=f"🟥 Last killed: {last_display}\n🟩 Next spawn: {next_display}",
            inline=False
        )

    await ctx.send(embed=embed)

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

# Enable message content intent
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
        return {b["name"].lower(): b for b in data}

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
async def kill(ctx, *, name: str, killed_at: str = None):
    key = name.lower()
    if key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    # Parse killed time
    if killed_at:
        try:
            killed_time = datetime.strptime(killed_at.upper(), "%I:%M%p")
            killed_time = killed_time.replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )
        except ValueError:
            await ctx.send("⚠️ Invalid time format. Use AM/PM like `05:32PM`.")
            return
    else:
        killed_time = datetime.now()

    respawn_seconds = bosses[key].get("respawn", 0)
    next_spawn = killed_time + timedelta(seconds=respawn_seconds)

    spawn_timers[key] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %I:%M %p"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %I:%M %p")
    }
    save_spawn_timers(spawn_timers)

    embed = discord.Embed(title=f"{name.title()} Kill Recorded", color=0xff0000)
    embed.add_field(name="Last killed", value=killed_time.strftime("%b %d, %Y %I:%M %p"), inline=True)
    embed.add_field(name="Next spawn", value=next_spawn.strftime("%b %d, %Y %I:%M %p"), inline=True)
    await ctx.send(embed=embed)

# /info command
@bot.command()
async def info(ctx, *, name: str):
    key = name.lower()
    if key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    last_str = spawn_timers.get(key, {}).get("last_killed")
    next_str = spawn_timers.get(key, {}).get("next_spawn")

    now = datetime.now()
    color = 0x808080  # Default gray for no info

    # Determine color based on boss state
    if last_str and next_str:
        last_dt = datetime.strptime(last_str, "%Y-%m-%d %I:%M %p")
        next_dt = datetime.strptime(next_str, "%Y-%m-%d %I:%M %p")
        if last_dt <= now < next_dt:
            color = 0x00ff00  # Green if currently spawned
        elif now < last_dt:
            color = 0xffff00  # Yellow if next spawn
        else:
            color = 0xff0000  # Red if killed

    embed = discord.Embed(title=f"{name.title()} Info", color=color)
    embed.add_field(name="Last killed", value=last_dt.strftime("%b %d, %Y %I:%M %p") if last_str else "No info yet", inline=True)
    embed.add_field(name="Next spawn", value=next_dt.strftime("%b %d, %Y %I:%M %p") if next_str else "No info yet", inline=True)
    await ctx.send(embed=embed)

# /next command
@bot.command(name="next")
async def next_boss(ctx):
    now = datetime.now()
    upcoming = []

    for name, data in bosses.items():
        timer = spawn_timers.get(name, {})
        next_str = timer.get("next_spawn")
        if next_str:
            try:
                next_dt = datetime.strptime(next_str, "%Y-%m-%d %I:%M %p")
                if next_dt >= now:
                    upcoming.append((next_dt, name))
            except ValueError:
                continue

    if not upcoming:
        await ctx.send("ℹ️ No upcoming spawns recorded.")
        return

    upcoming.sort(key=lambda x: x[0])
    next_time, boss_name = upcoming[0]

    embed = discord.Embed(title="Next Boss Spawn", color=0xffff00)  # Yellow
    embed.add_field(name="Boss", value=boss_name.title(), inline=True)
    embed.add_field(name="Spawn Date & Time", value=next_time.strftime("%b %d, %Y %I:%M %p"), inline=True)
    await ctx.send(embed=embed)

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

# Enable message content intent
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
        return {b["name"].lower(): b for b in data}

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
async def kill(ctx, *, name: str, killed_at: str = None):
    key = name.lower()
    if key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    # Parse killed time
    if killed_at:
        try:
            killed_time = datetime.strptime(killed_at.upper(), "%I:%M%p")
            killed_time = killed_time.replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )
        except ValueError:
            await ctx.send("⚠️ Invalid time format. Use AM/PM like `05:32PM`.")
            return
    else:
        killed_time = datetime.now()

    respawn_seconds = bosses[key].get("respawn", 0)
    next_spawn = killed_time + timedelta(seconds=respawn_seconds)

    spawn_timers[key] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %I:%M %p"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %I:%M %p")
    }
    save_spawn_timers(spawn_timers)

    embed = discord.Embed(title=f"{name.title()} Kill Recorded", color=0xff0000)
    embed.add_field(name="Last killed", value=killed_time.strftime("%I:%M %p"), inline=True)
    embed.add_field(name="Next spawn", value=next_spawn.strftime("%I:%M %p"), inline=True)
    await ctx.send(embed=embed)

# /info command
@bot.command()
async def info(ctx, *, name: str):
    key = name.lower()
    if key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    last_str = spawn_timers.get(key, {}).get("last_killed")
    next_str = spawn_timers.get(key, {}).get("next_spawn")

    now = datetime.now()
    color = 0x808080  # Default gray for no info

    # Determine color based on boss state
    if last_str and next_str:
        last_dt = datetime.strptime(last_str, "%Y-%m-%d %I:%M %p")
        next_dt = datetime.strptime(next_str, "%Y-%m-%d %I:%M %p")
        if last_dt <= now < next_dt:
            color = 0x00ff00  # Green if currently spawned
        elif now < last_dt:
            color = 0xffff00  # Yellow if next spawn
        else:
            color = 0xff0000  # Red if killed

    embed = discord.Embed(title=f"{name.title()} Info", color=color)
    embed.add_field(name="Last killed", value=last_str or "No info yet", inline=True)
    embed.add_field(name="Next spawn", value=next_str or "No info yet", inline=True)
    await ctx.send(embed=embed)

# /next command
@bot.command(name="next")
async def next_boss(ctx):
    now = datetime.now()
    upcoming = []

    for name, data in bosses.items():
        timer = spawn_timers.get(name, {})
        next_str = timer.get("next_spawn")
        if next_str:
            try:
                next_dt = datetime.strptime(next_str, "%Y-%m-%d %I:%M %p")
                if next_dt >= now:
                    upcoming.append((next_dt, name))
            except ValueError:
                continue

    if not upcoming:
        await ctx.send("ℹ️ No upcoming spawns recorded.")
        return

    upcoming.sort(key=lambda x: x[0])
    next_time, boss_name = upcoming[0]

    embed = discord.Embed(title="Next Boss Spawn", color=0xffff00)  # Yellow
    embed.add_field(name="Boss", value=boss_name.title(), inline=True)
    embed.add_field(name="Spawn Time", value=next_time.strftime("%I:%M %p"), inline=True)
    await ctx.send(embed=embed)

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
        # normalize keys for case-insensitive search
        return {b["name"].lower(): b for b in data}

def load_spawn_timers():
    if os.path.exists(SPAWN_TIMERS_FILE):
        with open(SPAWN_TIMERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_spawn_timers(data):
    with open(SPAWN_TIMERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Helper: parse time string to datetime
def parse_time(timestr):
    try:
        return datetime.strptime(timestr, "%Y-%m-%d %I:%M %p")
    except:
        return None

bosses = load_bosses()
spawn_timers = load_spawn_timers()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, name: str, killed_at: str):
    """
    Usage: /kill [bossname] [HHMMPM] e.g. /kill Undomiel 05:32PM
    """
    key = name.lower()
    if key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found in list.")
        return

    try:
        killed_time = datetime.strptime(killed_at, "%I:%M%p")
        # add current date
        killed_time = killed_time.replace(year=datetime.now().year,
                                          month=datetime.now().month,
                                          day=datetime.now().day)
    except ValueError:
        await ctx.send("⚠️ Invalid time format. Use AM/PM like `05:32PM`.")
        return

    respawn_seconds = bosses[key].get("respawn", 0)
    next_spawn = killed_time + timedelta(seconds=respawn_seconds)

    spawn_timers[key] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %I:%M %p"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %I:%M %p")
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(
        f"☠️ **{name.title()}** was killed at {killed_time.strftime('%I:%M %p')}.\n"
        f"🕒 Next spawn: **{next_spawn.strftime('%I:%M %p')}**"
    )

# /info command
@bot.command()
async def info(ctx, *, name: str):
    key = name.lower()
    if key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    last = spawn_timers.get(key, {}).get("last_killed", "No info yet")
    next_spawn = spawn_timers.get(key, {}).get("next_spawn", "No info yet")

    embed = discord.Embed(title=f"📜 Info for {name.title()}", color=0x00FFFF)
    embed.add_field(name="☠️ Last killed", value=last, inline=True)
    embed.add_field(name="🕒 Next spawn", value=next_spawn, inline=True)

    await ctx.send(embed=embed)

# /next command
@bot.command()
async def next(ctx):
    now = datetime.now()
    upcoming_bosses = []

    for key, boss in bosses.items():
        timer = spawn_timers.get(key, {})
        spawn_time_str = timer.get("next_spawn")
        spawn_time = parse_time(spawn_time_str) if spawn_time_str else None
        upcoming_bosses.append((key, spawn_time))

    # Sort: earliest first, None at end
    upcoming_bosses.sort(key=lambda x: x[1] if x[1] else datetime.max)

    embed = discord.Embed(title="🕒 Next Bosses to Spawn", color=0x00FFFF)
    for i, (key, spawn_time) in enumerate(upcoming_bosses[:5]):
        if spawn_time:
            time_str = spawn_time.strftime("%I:%M %p")
            if i == 0:
                embed.add_field(name=f"⏳ **{key.title()}**", value=f"🟩 {time_str}", inline=False)
            else:
                embed.add_field(name=key.title(), value=f"🟩 {time_str}", inline=False)
        else:
            embed.add_field(name=key.title(), value="No info yet", inline=False)

    await ctx.send(embed=embed)

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
    # Convert names to lowercase for easier matching
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
async def kill(ctx, *, name: str):
    """
    Usage: /kill [bossname]
    """
    name_key = name.lower()
    if name_key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found in list.")
        return

    killed_time = datetime.now()
    boss = bosses[name_key]

    if "respawn" in boss:
        respawn_seconds = boss["respawn"]
        next_spawn = killed_time + timedelta(seconds=respawn_seconds)
    else:
        await ctx.send(f"⚠️ Boss '{name.title()}' does not have a respawn timer.")
        return

    spawn_timers[name_key] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %I:%M %p"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %I:%M %p")
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(
        f"☠️ {name.title()} was killed at {killed_time.strftime('%I:%M %p')}.\n"
        f"🕒 Next spawn: **{next_spawn.strftime('%I:%M %p')}**"
    )

# /info command
@bot.command()
async def info(ctx, *, name: str):
    """
    Usage: /info [bossname]
    """
    name_key = name.lower()
    if name_key not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    if name_key not in spawn_timers:
        await ctx.send(f"ℹ️ No spawn data recorded for {name.title()} yet.")
        return

    last = spawn_timers[name_key]["last_killed"]
    next_spawn = spawn_timers[name_key]["next_spawn"]

    await ctx.send(
        f"📜 Info for {name.title()}:\n"
        f"☠️ Last killed: {last}\n"
        f"🕒 Next spawn: {next_spawn}"
    )

# /next command
@bot.command()
async def next(ctx):
    """
    Shows the next boss to spawn based on current time
    """
    now = datetime.now()
    next_boss = None
    next_time = None

    for key, timer in spawn_timers.items():
        spawn_time = datetime.strptime(timer["next_spawn"], "%Y-%m-%d %I:%M %p")
        if spawn_time > now and (next_time is None or spawn_time < next_time):
            next_time = spawn_time
            next_boss = key

    if next_boss:
        await ctx.send(
            f"🕒 Next boss to spawn: **{next_boss.title()}** at {next_time.strftime('%I:%M %p')}"
        )
    else:
        await ctx.send("ℹ️ No upcoming boss spawn recorded.")

bot.run(TOKEN)
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Enable message content intent
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Files
BOSSES_FILE = "bosses.json"
SPAWN_TIMERS_FILE = "spawn_timers.json"

# Load bosses
def load_bosses():
    with open(BOSSES_FILE, "r") as f:
        data = json.load(f)
        return {b["name"].lower(): b for b in data}

# Load spawn timers
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

def parse_time_str(time_str):
    return datetime.strptime(time_str.strip(), "%I:%M %p")

def format_time(dt):
    return dt.strftime("%I:%M %p")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, name: str, killed_at: str = None):
    """
    Usage: /kill [bossname] [HH:MM AM/PM] (optional, defaults to now)
    """
    name_lower = name.lower()
    if name_lower not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    # Use provided time or default to now
    if killed_at:
        try:
            killed_time = parse_time_str(killed_at)
            now = datetime.now()
            killed_time = killed_time.replace(year=now.year, month=now.month, day=now.day)
        except ValueError:
            await ctx.send("⚠️ Invalid time format. Use `HH:MM AM/PM`.")
            return
    else:
        killed_time = datetime.now()

    boss_data = bosses[name_lower]

    if "respawn" in boss_data:
        respawn_seconds = boss_data["respawn"]
        next_spawn = killed_time + timedelta(seconds=respawn_seconds)
    elif boss_data.get("special") and "schedule" in boss_data:
        # For special bosses, pick next scheduled time
        now = datetime.now()
        next_spawn = None
        for sched in boss_data["schedule"]:
            spawn_dt = now.replace(hour=sched["hour"], minute=sched["minute"], second=0, microsecond=0)
            weekday = sched["day"]
            days_ahead = (weekday - now.weekday()) % 7
            spawn_dt += timedelta(days=days_ahead)
            if spawn_dt > now:
                next_spawn = spawn_dt
                break
        if not next_spawn:
            # If none left this week, pick the earliest next week
            sched = boss_data["schedule"][0]
            spawn_dt = now.replace(hour=sched["hour"], minute=sched["minute"], second=0, microsecond=0)
            days_ahead = (sched["day"] - now.weekday() + 7) % 7
            next_spawn = spawn_dt + timedelta(days=days_ahead)

    spawn_timers[name_lower] = {
        "last_killed": killed_time.strftime("%Y-%m-%d %H:%M"),
        "next_spawn": next_spawn.strftime("%Y-%m-%d %H:%M")
    }
    save_spawn_timers(spawn_timers)

    await ctx.send(
        f"☠️ {name.capitalize()} was killed at {format_time(killed_time)}.\n"
        f"🕒 Next spawn: **{format_time(next_spawn)}**"
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

    last = datetime.strptime(spawn_timers[name_lower]["last_killed"], "%Y-%m-%d %H:%M")
    next_spawn = datetime.strptime(spawn_timers[name_lower]["next_spawn"], "%Y-%m-%d %H:%M")

    await ctx.send(
        f"📜 Info for {name.capitalize()}:\n"
        f"☠️ Last killed: {format_time(last)}\n"
        f"🕒 Next spawn: {format_time(next_spawn)}"
    )

# /next command
@bot.command()
async def next(ctx):
    """
    Show the next boss spawn based on current time
    """
    now = datetime.now()
    next_boss = None
    next_time = None

    for name, data in bosses.items():
        if name in spawn_timers:
            spawn_dt = datetime.strptime(spawn_timers[name]["next_spawn"], "%Y-%m-%d %H:%M")
        else:
            if "respawn" in data:
                spawn_dt = now  # assume it can spawn anytime
            elif data.get("special") and "schedule" in data:
                # find next scheduled
                spawn_dt = None
                for sched in data["schedule"]:
                    dt = now.replace(hour=sched["hour"], minute=sched["minute"], second=0, microsecond=0)
                    days_ahead = (sched["day"] - now.weekday()) % 7
                    dt += timedelta(days=days_ahead)
                    if dt > now:
                        spawn_dt = dt
                        break
                if not spawn_dt:
                    sched = data["schedule"][0]
                    dt = now.replace(hour=sched["hour"], minute=sched["minute"], second=0, microsecond=0)
                    days_ahead = (sched["day"] - now.weekday() + 7) % 7
                    spawn_dt = dt + timedelta(days=days_ahead)
        if next_time is None or spawn_dt < next_time:
            next_time = spawn_dt
            next_boss = name

    if next_boss and next_time:
        await ctx.send(f"⏳ Next boss spawn: **{next_boss.capitalize()}** at **{format_time(next_time)}**")
    else:
        await ctx.send("ℹ️ No upcoming boss spawn found.")

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
