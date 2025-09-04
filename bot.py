import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load bosses.json
with open("bosses.json", "r") as f:
    bosses = {b["name"].lower(): b for b in json.load(f)}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Channel where announcements will be sent
ANNOUNCEMENT_CHANNEL_ID = 1410625107738755214  # 🔹 Replace with your channel ID

def find_boss(name: str, bosses: dict):
    name = name.lower()
    if name in bosses:
        return name, bosses[name]
    matches = [(key, boss) for key, boss in bosses.items() if key.startswith(name)]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        return "multiple", None
    return None, None

def format_time(dt):
    return dt.strftime("%I:%M %p")

def format_respawn_time(seconds: int) -> str:
    minutes = seconds // 60
    days, rem = divmod(minutes, 1440)
    hours, mins = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if mins > 0:
        parts.append(f"{mins}m")
    return " ".join(parts) if parts else "0m"

# Load token from environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_spawns.start()

# ================= /kill =================
@bot.command()
async def kill(ctx, *, name: str):
    key, boss = find_boss(name, bosses)
    if key == "multiple":
        await ctx.send(f"⚠️ Multiple bosses start with '{name}'. Please be more specific.")
        return
    if not boss:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return
    now = datetime.now()
    boss["originalKilled"] = boss.get("originalKilled", format_time(now))
    boss["originalKilledBy"] = boss.get("originalKilledBy", str(ctx.author))
    boss["lastKilled"] = format_time(now)
    boss["lastKilledBy"] = str(ctx.author)
    if "respawn" in boss:
        next_spawn = now + timedelta(seconds=boss["respawn"])
        boss["nextSpawn"] = format_time(next_spawn)
        await ctx.send(
            f"☠️ {boss['name']} killed at {format_time(now)} by {ctx.author}\n"
            f"🕒 Next spawn: **{format_time(next_spawn)}** on {next_spawn.strftime('%Y-%m-%d')}"
        )
    else:
        await ctx.send(f"⚠️ {boss['name']} has a fixed schedule, not a respawn timer.")
    with open("bosses.json", "w") as f:
        json.dump(list(bosses.values()), f, indent=2)

# ================= /update =================
@bot.command()
async def update(ctx, *, args: str):
    try:
        name, *killed_time = args.split()
        name = name.strip()
    except ValueError:
        await ctx.send("❌ Please provide a boss name and time, e.g., `/update Lady Daliah 01:30 AM`.")
        return
    key, boss = find_boss(name, bosses)
    if key == "multiple":
        await ctx.send(f"⚠️ Multiple bosses start with '{name}'. Please be more specific.")
        return
    if not boss:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return
    if not killed_time:
        await ctx.send("❌ Please provide a time, e.g., `01:30 AM`.")
        return
    killed_time_str = " ".join(killed_time).upper()
    now = datetime.now()
    try:
        new_kill_time = datetime.strptime(killed_time_str, "%I:%M %p")
    except ValueError:
        await ctx.send("❌ Invalid time format. Use `1:30 AM` or `01:30 PM` format.")
        return
    new_kill_time = new_kill_time.replace(year=now.year, month=now.month, day=now.day)
    original_time = boss.get("lastKilled", "Unknown")
    original_by = boss.get("lastKilledBy", "Unknown")
    boss["lastKilled"] = format_time(new_kill_time)
    boss["lastKilledBy"] = str(ctx.author)
    if "respawn" in boss:
        next_spawn = new_kill_time + timedelta(seconds=boss["respawn"])
        boss["nextSpawn"] = format_time(next_spawn)
        await ctx.send(
            f"✏️ **{boss['name']} Updated Kill Info**\n"
            f"🟢 **Original:** {original_time} by {original_by}\n"
            f"✏️ **Updated:** {format_time(new_kill_time)} by {ctx.author}\n"
            f"🕒 Next spawn: **{format_time(next_spawn)}** on {next_spawn.strftime('%Y-%m-%d')}"
        )
    else:
        await ctx.send(
            f"✏️ **{boss['name']} Updated Kill Info**\n"
            f"🟢 **Original:** {original_time} by {original_by}\n"
            f"✏️ **Updated:** {format_time(new_kill_time)} by {ctx.author}\n"
            f"⚠️ This boss has a fixed schedule, not a respawn timer."
        )
    with open("bosses.json", "w") as f:
        json.dump(list(bosses.values()), f, indent=2)

# ================= /info =================
@bot.command()
async def info(ctx, *, name: str):
    key, boss = find_boss(name, bosses)
    if key == "multiple":
        await ctx.send(f"⚠️ Multiple bosses start with '{name}'. Please be more specific.")
        return
    if not boss:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return
    embed = discord.Embed(title=f"📜 {boss['name']} Info", color=discord.Color.blue())
    if "originalKilled" in boss:
        embed.add_field(
            name="🟢 Original killed",
            value=f"{boss['originalKilled']} by {boss.get('originalKilledBy','Unknown')}",
            inline=False
        )
    if "lastKilled" in boss:
        embed.add_field(
            name="✏️ Last killed",
            value=f"{boss['lastKilled']} by {boss.get('lastKilledBy','Unknown')}",
            inline=False
        )
    if "respawn" in boss:
        respawn_time = format_respawn_time(boss['respawn'])
        embed.add_field(name="⏳ Respawn", value=respawn_time, inline=False)
        embed.add_field(name="🕒 Next spawn", value=boss.get("nextSpawn", "Unknown"), inline=False)
    elif "schedule" in boss:
        schedule_text = "\n".join(
            f"- Day {s['day']} at {s['hour']:02}:{s['minute']:02}"
            for s in boss["schedule"]
        )
        embed.add_field(name="📅 Fixed schedule", value=schedule_text, inline=False)
    await ctx.send(embed=embed)

# ================= /next =================
@bot.command()
async def next(ctx):
    now = datetime.now()
    upcoming = []

    for boss in bosses.values():
        next_spawn_time = None

        # Respawn-based
        if "lastKilled" in boss and "respawn" in boss:
            try:
                last_killed_time = datetime.strptime(boss["lastKilled"], "%I:%M %p")
                last_killed_time = last_killed_time.replace(year=now.year, month=now.month, day=now.day)
                next_spawn_time = last_killed_time + timedelta(seconds=boss["respawn"])
                while next_spawn_time <= now:
                    next_spawn_time += timedelta(seconds=boss["respawn"])
                upcoming.append((next_spawn_time, boss["name"], boss.get("lastKilledBy", "Unknown")))
            except:
                continue

        # Fixed schedule
        elif "schedule" in boss:
            schedule_times = []
            for s in boss["schedule"]:
                schedule_time = now.replace(hour=s["hour"], minute=s["minute"], second=0, microsecond=0)
                if schedule_time < now:
                    schedule_time += timedelta(days=7)
                schedule_times.append(schedule_time)
            if schedule_times:
                upcoming.append((min(schedule_times), boss["name"], "Fixed schedule"))

    if not upcoming:
        await ctx.send("📭 No upcoming spawns found.")
        return

    upcoming.sort(key=lambda x: x[0])
    soonest_time = upcoming[0][0]
    spawn_list = [(t, name, killer) for t, name, killer in upcoming if t == soonest_time]

    embed = discord.Embed(title="🕒 Next Boss Spawn(s)", color=discord.Color.blue())
    for t, bname, killer in spawn_list:
        embed.add_field(name=bname, value=f"⏰ {t.strftime('%I:%M %p')} | Last killed by: {killer}", inline=False)

    await ctx.send(embed=embed)

# ================= /boss =================
@bot.command()
async def boss(ctx):
    now = datetime.now()
    embed = discord.Embed(title="📜 Bosses Info", color=discord.Color.blue())
    count = 0

    for name, boss in bosses.items():
        if count >= 25:  # Prevent 25+ fields issue
            break

        alive = False
        next_spawn_time = None

        if "lastKilled" in boss and "respawn" in boss:
            try:
                last_killed_time = datetime.strptime(boss["lastKilled"], "%I:%M %p")
                last_killed_time = last_killed_time.replace(year=now.year, month=now.month, day=now.day)
                next_spawn_time = last_killed_time + timedelta(seconds=boss["respawn"])
                while next_spawn_time <= now:
                    next_spawn_time += timedelta(seconds=boss["respawn"])
                if last_killed_time <= now < next_spawn_time:
                    alive = True
            except:
                pass

        info_str = ""
        if alive:
            info_str += "🔥 **ALIVE NOW**\n"
        if "originalKilled" in boss:
            info_str += f"🟢 Original: {boss['originalKilled']} by {boss.get('originalKilledBy','Unknown')}\n"
        if "lastKilled" in boss:
            info_str += f"✏️ Last: {boss['lastKilled']} by {boss.get('lastKilledBy','Unknown')}\n"
        if "respawn" in boss:
            info_str += f"Respawn: {format_respawn_time(boss['respawn'])}\n"
            info_str += f"Next spawn: {next_spawn_time.strftime('%I:%M %p') if next_spawn_time else 'Unknown'}"
        elif "schedule" in boss:
            info_str += "Fixed schedule:\n"
            for s in boss["schedule"]:
                info_str += f"- Day {s['day']} at {s['hour']:02}:{s['minute']:02}\n"

        embed.add_field(name=boss['name'], value=info_str, inline=False)
        count += 1

    await ctx.send(embed=embed)

# ================= Background Task =================
@tasks.loop(minutes=1)
async def check_spawns():
    now = datetime.now()
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if not channel:
        return

    warnings = []
    spawns = []

    for boss in bosses.values():
        next_spawn_time = None

        # Respawn-based
        if "lastKilled" in boss and "respawn" in boss:
            try:
                last_killed_time = datetime.strptime(boss["lastKilled"], "%I:%M %p")
                last_killed_time = last_killed_time.replace(year=now.year, month=now.month, day=now.day)
                next_spawn_time = last_killed_time + timedelta(seconds=boss["respawn"])
                while next_spawn_time <= now:
                    next_spawn_time += timedelta(seconds=boss["respawn"])
                diff = (next_spawn_time - now).total_seconds()
                if 0 <= diff <= 60:
                    spawns.append(boss["name"])
                elif 540 <= diff <= 600:  # 10-minute warning
                    warnings.append(boss["name"])
            except:
                continue

        # Fixed schedule
        elif "schedule" in boss:
            for s in boss["schedule"]:
                schedule_time = now.replace(hour=s["hour"], minute=s["minute"], second=0, microsecond=0)
                if schedule_time < now:
                    schedule_time += timedelta(days=7)
                diff = (schedule_time - now).total_seconds()
                if 0 <= diff <= 60:
                    spawns.append(boss["name"])
                elif 540 <= diff <= 600:
                    warnings.append(boss["name"])

    if warnings:
        embed = discord.Embed(title="⚠️ Upcoming Boss Spawn", color=discord.Color.orange())
        for b in warnings[:25]:  # Discord limit
            embed.add_field(name=b, value="⏳ Spawning in 10 minutes!", inline=False)
        await channel.send(embed=embed)

    if spawns:
        embed = discord.Embed(title="🔥 Boss Spawned!", color=discord.Color.red())
        for b in spawns[:25]:
            embed.add_field(name=b, value="✅ Alive now!", inline=False)
        await channel.send(embed=embed)

# Run bot
bot.run(TOKEN)
