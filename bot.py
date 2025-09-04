import discord
from discord.ext import commands
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

def find_boss(name: str, bosses: dict):
    """Find a boss by exact or partial (prefix) name match."""
    name = name.lower()

    # Exact match first
    if name in bosses:
        return name, bosses[name]

    # Prefix match (e.g., "lady" -> "lady daliah")
    matches = [(key, boss) for key, boss in bosses.items() if key.startswith(name)]

    if len(matches) == 1:
        return matches[0]  # returns (key, boss)
    elif len(matches) > 1:
        return "multiple", None
    return None, None


def format_time(dt):
    return dt.strftime("%I:%M %p")

def format_respawn_time(seconds: int) -> str:
    """Convert respawn seconds into d/h/m format (corrected)."""
    minutes = seconds // 60
    days, rem = divmod(minutes, 1440)   # 1440 minutes = 1 day
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

    now = datetime.datetime.now()

    # Record fresh kill
    boss["originalKilled"] = boss.get("originalKilled", format_time(now))
    boss["originalKilledBy"] = boss.get("originalKilledBy", str(ctx.author))
    boss["lastKilled"] = format_time(now)
    boss["lastKilledBy"] = str(ctx.author)

    if "respawn" in boss:
        next_spawn = now + datetime.timedelta(seconds=boss["respawn"])
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
    now = datetime.datetime.now()

    try:
        new_kill_time = datetime.datetime.strptime(killed_time_str, "%I:%M %p")
    except ValueError:
        await ctx.send("❌ Invalid time format. Use `1:30 AM` or `01:30 PM` format.")
        return

    new_kill_time = new_kill_time.replace(year=now.year, month=now.month, day=now.day)

    original_time = boss.get("lastKilled", "Unknown")
    original_by = boss.get("lastKilledBy", "Unknown")

    boss["lastKilled"] = format_time(new_kill_time)
    boss["lastKilledBy"] = str(ctx.author)

    if "respawn" in boss:
        next_spawn = new_kill_time + datetime.timedelta(seconds=boss["respawn"])
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

    embed = discord.Embed(
        title=f"📜 {boss['name']} Info",
        color=discord.Color.blue()
    )

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
        respawn_time = format_respawn_time(boss['respawn'])  # ✅ fixed seconds → d/h/m
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
        if "nextSpawn" in boss and boss["nextSpawn"] != "Unknown":
            try:
                next_spawn_time = datetime.strptime(boss["nextSpawn"], "%I:%M %p")
                next_spawn_time = next_spawn_time.replace(year=now.year, month=now.month, day=now.day)

                if next_spawn_time > now:
                    upcoming.append((next_spawn_time, boss["name"], boss.get("lastKilledBy", "Unknown")))
            except Exception:
                continue

    if not upcoming:
        await ctx.send("📭 No upcoming spawns found.")
        return

    upcoming.sort(key=lambda x: x[0])
    next_time, next_boss, killer = upcoming[0]

    embed = discord.Embed(
        title="🕒 Next Boss Spawn",
        description=f"**{next_boss}** is spawning soon!",
        color=discord.Color.blue()
    )
    embed.add_field(name="⏰ Time", value=f"{next_time.strftime('%I:%M %p')}", inline=False)
    embed.add_field(name="✏️ Last killed by", value=killer, inline=False)

    await ctx.send(embed=embed)




# ================= /boss =================
@bot.command()
async def boss(ctx):
    embed = discord.Embed(title="📜 Bosses Info")
    count = 0
    now = datetime.datetime.now()

    for name, boss in bosses.items():
        if count >= 25:
            break

        alive = False
        if "lastKilled" in boss and "respawn" in boss:
            last_killed_time = datetime.datetime.strptime(boss["lastKilled"], "%I:%M %p")
            last_killed_time = last_killed_time.replace(year=now.year, month=now.month, day=now.day)
            next_spawn_time = last_killed_time + datetime.timedelta(seconds=boss["respawn"])
            if last_killed_time <= now <= next_spawn_time:
                alive = True

        info_str = ""
        if alive:
            info_str += "🔥 **ALIVE NOW**\n"

        if "originalKilled" in boss:
            info_str += f"🟢 Original: {boss['originalKilled']} by {boss.get('originalKilledBy','Unknown')}\n"
        if "lastKilled" in boss:
            info_str += f"✏️ Last: {boss['lastKilled']} by {boss.get('lastKilledBy','Unknown')}\n"
        if "respawn" in boss:
            info_str += f"Respawn: {boss['respawn']//3600}h\n"
            info_str += f"Next spawn: {boss.get('nextSpawn','Unknown')}"
        elif "schedule" in boss:
            info_str += "Fixed schedule:\n"
            for s in boss["schedule"]:
                info_str += f"- Day {s['day']} at {s['hour']:02}:{s['minute']:02}\n"

        embed.add_field(name=boss['name'], value=info_str, inline=False)
        count += 1

    await ctx.send(embed=embed)


# ================= /reset_timer =================
@bot.command()
async def reset_timer(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    await ctx.send("⚠️ WARNING: This will reset **ALL boss timers** to their original state (unknown data).\nType **yes** to proceed or **no** to cancel.")

    try:
        reply = await bot.wait_for("message", check=check, timeout=30.0)  # 30s to respond
    except:
        await ctx.send("❌ No response. Reset cancelled.")
        return

    if reply.content.lower() == "no":
        await ctx.send("❌ Reset cancelled.")
        return

    for boss in bosses.values():
        boss.pop("lastKilled", None)
        boss.pop("lastKilledBy", None)
        boss.pop("nextSpawn", None)
        boss.pop("originalKilled", None)
        boss.pop("originalKilledBy", None)

    with open("bosses.json", "w") as f:
        json.dump(list(bosses.values()), f, indent=2)

    await ctx.send("✅ All boss timers have been reset to their original state.")


# Run bot
bot.run(TOKEN)
