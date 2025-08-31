import discord
from discord.ext import commands
import json
import datetime
import os
from dotenv import load_dotenv

# Load bosses.json
with open("bosses.json", "r") as f:
    bosses = {b["name"].lower(): b for b in json.load(f)}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

def format_time(dt):
    return dt.strftime("%I:%M %p")

# Load token from environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# /kill command
@bot.command()
async def kill(ctx, name: str):
    name = name.lower()
    if name not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    boss = bosses[name]
    now = datetime.datetime.now()

    # If already killed before
    if "lastKilled" in boss:
        # Parse the stored lastKilled time as today
        last_killed_time = datetime.datetime.strptime(boss["lastKilled"], "%I:%M %p")
        last_killed_time = last_killed_time.replace(year=now.year, month=now.month, day=now.day)

        if "respawn" in boss:
            next_spawn = last_killed_time + datetime.timedelta(seconds=boss["respawn"])

            # If it's not yet respawned → block and show warning
            if now < next_spawn:
                await ctx.send(
                    f"⚠️ The **{boss['name']}** has already been killed and recorded "
                    f"by {boss.get('lastKilledBy','Unknown')} at {boss['lastKilled']}.\n"
                    f"🕒 Next spawn: **{format_time(next_spawn)}** on {next_spawn.strftime('%Y-%m-%d')}\n"
                    f"If you wish to update, use `/update {boss['name']} [HH:MM AM/PM]`"
                )
                return
        # If boss uses fixed schedule, just block updates (no re-kill)
        elif "schedule" in boss:
            await ctx.send(
                f"⚠️ The **{boss['name']}** has a fixed schedule and cannot be re-logged with `/kill`.\n"
                f"Last recorded kill: {boss.get('lastKilled','Unknown')} by {boss.get('lastKilledBy','Unknown')}\n"
                f"Use `/update {boss['name']} [HH:MM AM/PM]` if needed."
            )
            return

    # Record fresh kill (new or after respawn passed)
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

    # Save updates
    with open("bosses.json", "w") as f:
        json.dump(list(bosses.values()), f, indent=2)



# /update command
@bot.command()
async def update(ctx, name: str, *killed_time):
    name = name.lower()
    if name not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    if not killed_time:
        await ctx.send("❌ Please provide a time, e.g., `01:30 AM`.")
        return

    boss = bosses[name]
    now = datetime.datetime.now()

    killed_time_str = " ".join(killed_time).upper()

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

# /info command
@bot.command()
async def info(ctx, name: str):
    name = name.lower()
    if name not in bosses:
        await ctx.send(f"❌ Boss '{name}' not found.")
        return

    boss = bosses[name]
    msg = f"📜 **{boss['name']} Info**\n"

    if "originalKilled" in boss:
        msg += f"🟢 **Original killed:** {boss['originalKilled']} by {boss.get('originalKilledBy','Unknown')}\n"

    if "lastKilled" in boss:
        msg += f"✏️ **Last killed:** {boss['lastKilled']} by {boss.get('lastKilledBy','Unknown')}\n"

    if "respawn" in boss:
        msg += f"⏳ Respawn every {boss['respawn']//3600}h\n"
        msg += f"🕒 Next spawn: {boss.get('nextSpawn', 'Unknown')}\n"
    elif "schedule" in boss:
        msg += "📅 Fixed spawn schedule:\n"
        for s in boss["schedule"]:
            msg += f"- Day {s['day']} at {s['hour']:02}:{s['minute']:02}\n"

    await ctx.send(msg)

# /next command - shows next scheduled boss(es) including overlaps and handles never killed
@bot.command()
async def next(ctx):
    now = datetime.datetime.now()
    next_spawns = []

    for name, boss in bosses.items():
        next_time = None
        alive = False

        # Respawn bosses
        if "respawn" in boss:
            if "lastKilled" in boss:
                last_killed_time = datetime.datetime.strptime(boss["lastKilled"], "%I:%M %p")
            else:
                # If never killed, consider next spawn is now
                last_killed_time = now
            next_time = last_killed_time + datetime.timedelta(seconds=boss["respawn"])
            alive = last_killed_time <= now <= next_time

        # Fixed schedule bosses
        elif "schedule" in boss:
            earliest_spawn = None
            for s in boss["schedule"]:
                spawn_time = datetime.datetime(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    hour=s["hour"],
                    minute=s["minute"]
                )
                if spawn_time < now:
                    spawn_time += datetime.timedelta(days=1)
                if not earliest_spawn or spawn_time < earliest_spawn:
                    earliest_spawn = spawn_time
            next_time = earliest_spawn
            alive = next_time <= now

        if next_time:
            next_spawns.append((next_time, boss, alive))

    if not next_spawns:
        await ctx.send("No upcoming bosses found.")
        return

    # Find earliest next spawn(s)
    next_spawns.sort(key=lambda x: x[0])
    earliest_time = next_spawns[0][0]
    overlapping_bosses = [(b, alive) for t, b, alive in next_spawns if t == earliest_time]

    msg = f"🕒 Next spawn(s) at {earliest_time.strftime('%I:%M %p')}:\n"
    for boss, alive in overlapping_bosses:
        status = "🔥 **ALIVE NOW**" if alive else "Not alive yet"
        last_by = boss.get('lastKilledBy', 'Never killed')
        msg += f"- {boss['name']} ({status}, last killed by {last_by})\n"

    await ctx.send(msg)



# /boss command - shows all bosses
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

# Run bot
bot.run(TOKEN)
