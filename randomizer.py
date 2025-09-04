import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime
import threading

# Import Task 1 logic (new file)
from task1_logic import pick_number_from_session_v2
# Import delayed post logic (new file)
from delayedpost_logic import setup_delayedpost
# Config
from config_manager import load_config, save_config
intents = discord.Intents.default()
intents.message_content = True  # allow bot to read message content

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------- CONFIG -------------
TOKEN = "Your Bot Token"  # replace with your token
METHOD2_WHITELIST = {1345873633456689255}  # your ID(s)
LOGO_URL = "https://i.postimg.cc/c4KY06Y2/randomizer.png"

# ------------- INTENTS / BOT -------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------- DATA MODELS -------------
sessions: dict[tuple[int, int], dict] = {}
predefined_next: dict[int, int] = {}
config_data = load_config()

# ------------- LOGGING -------------
def ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(line: str):
    print(f"[{ts()}] {line}")

def log_block(lines: list[str]):
    print()
    for ln in lines:
        print(f"[{ts()}] {ln}")
    print()

# ------------- HELPERS -------------
def sess_key(guild_id: int, owner_id: int) -> tuple[int, int]:
    return (guild_id, owner_id)

def get_session(guild_id: int, owner_id: int):
    return sessions.get(sess_key(guild_id, owner_id))

def set_user_override(guild_id: int, owner_id: int, target_id: int, number: int):
    """Set a one-time number override for a specific participant in a session."""
    key = (guild_id, owner_id)
    if key not in predefined_next or not isinstance(predefined_next[key], dict):
        predefined_next[key] = {}
    predefined_next[key][target_id] = number
    log_block([f"🎯 Override set | guild={guild_id} owner={owner_id} target={target_id} number={number}"])

def ensure_owner_session(guild_id: int, owner_id: int):
    key = sess_key(guild_id, owner_id)
    if key not in sessions:
        sessions[key] = {
            "owner": owner_id,
            "guild": guild_id,
            "range": None,
            "used": set(),
            "allowed": {owner_id},
            "created_at": datetime.datetime.now(),
            "method": 1,        # NEW: method flag
            "last_number": None,
            "last_user": None,
        }
        log_block([f"✅ Session created | guild={guild_id} owner={owner_id}"])
    return sessions[key]

def pick_number_from_session(session: dict, guild_id: int, owner_id: int, user_id: int):
    """Original method (global uniqueness) with per-user override support."""
    lo_hi = session["range"]
    if not lo_hi:
        return None, "no_range"
    lo, hi = lo_hi

    # --- Override check ---
    key = (guild_id, owner_id)
    if key in predefined_next and isinstance(predefined_next[key], dict):
        if user_id in predefined_next[key]:
            cand = predefined_next[key].pop(user_id)
            if lo <= cand <= hi and cand not in session["used"]:
                session["used"].add(cand)
                log_block([f"🎯 Predefined served | guild={guild_id} owner={owner_id} "
                           f"user={user_id} number={cand}"])
                return cand, None
            else:
                # Remove invalid override
                log_block([f"⚠️ Invalid override discarded | guild={guild_id} owner={owner_id} "
                           f"user={user_id} number={cand}"])
    # ----------------------

    available = [n for n in range(lo, hi + 1) if n not in session["used"]]
    if not available:
        return None, "depleted"

    num = random.choice(available)
    session["used"].add(num)
    return num, None

def minimal_reply(content: str) -> str:
    return content

# ------------- SLASH COMMANDS -------------

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        log_block([
            f"✅ Bot online as {bot.user}",
            f"✅ Synced {len(bot.tree.get_commands())} commands",
        ])
    except Exception as e:
        log_block([f"❌ Sync error: {e}"])

# ---------------- BASIC COMMANDS ----------------

@bot.tree.command(name="start", description="Start your session in this server")
async def start(interaction: discord.Interaction):
    if not interaction.guild_id:
        await interaction.response.send_message(minimal_reply("❌ Use in a server."), ephemeral=True)
        return
    owner_id = interaction.user.id
    guild_id = interaction.guild_id
    key = sess_key(guild_id, owner_id)
    if key in sessions:
        await interaction.response.send_message(minimal_reply("ℹ️ Session already exists."), ephemeral=True)
        return
    ensure_owner_session(guild_id, owner_id)
    await interaction.response.send_message(minimal_reply("✅ Session started"))
    log_block([f"🟢 /start | guild={guild_id} owner={owner_id} user={interaction.user}"])

@bot.tree.command(name="randombtw", description="Set the range for your session (owner only)")
@app_commands.describe(start="Minimum", end="Maximum")
async def randombtw(interaction: discord.Interaction, start: int, end: int):
    if not interaction.guild_id:
        await interaction.response.send_message("❌ Use in a server.", ephemeral=True)
        return
    if start >= end:
        await interaction.response.send_message("❌ Invalid range", ephemeral=True)
        return
    owner_id = interaction.user.id
    guild_id = interaction.guild_id
    session = get_session(guild_id, owner_id)
    if not session:
        await interaction.response.send_message("❌ No active session", ephemeral=True)
        return
    session["range"] = (start, end)
    session["used"].clear()
    await interaction.response.send_message(f"✅ Range set: {start} - {end}")
    log_block([f"🟡 /randombtw | guild={guild_id} owner={owner_id} range={start}-{end}"])

@bot.tree.command(name="join", description="Add a user ID to your session to allow /number (owner only)")
@app_commands.describe(user_id="User ID to allow (numbers only)")
async def join_cmd(interaction: discord.Interaction, user_id: str):
    if not interaction.guild_id:
        await interaction.response.send_message("❌ Use in a server.", ephemeral=True)
        return
    if not user_id.isdigit():
        await interaction.response.send_message("❌ Invalid user ID", ephemeral=True)
        return
    owner_id = interaction.user.id
    guild_id = interaction.guild_id
    session = get_session(guild_id, owner_id)
    if not session:
        await interaction.response.send_message("❌ No active session", ephemeral=True)
        return
    uid = int(user_id)
    session["allowed"].add(uid)
    await interaction.response.send_message(f"✅ Added {uid}")
    log_block([f"🟦 /join | guild={guild_id} owner={owner_id} added_user={uid}"])

@bot.tree.command(name="quit", description="End your session (owner only)")
async def quit_cmd(interaction: discord.Interaction):
    if not interaction.guild_id:
        await interaction.response.send_message("❌ Use in a server.", ephemeral=True)
        return
    owner_id = interaction.user.id
    guild_id = interaction.guild_id
    key = sess_key(guild_id, owner_id)
    if key not in sessions:
        await interaction.response.send_message("ℹ️ No active session", ephemeral=True)
        return
    del sessions[key]
    await interaction.response.send_message("✅ Session ended")
    log_block([f"🔴 /quit | guild={guild_id} owner={owner_id}"])

@bot.tree.command(name="random", description="Standalone random from a given range (no session)")
@app_commands.describe(start="Minimum", end="Maximum")
async def random_cmd(interaction: discord.Interaction, start: int, end: int):
    if start >= end:
        await interaction.response.send_message("❌ Invalid range", ephemeral=True)
        return
    num = random.randint(start, end)
    await interaction.response.send_message(f"🎲 Number - {num}")
    log_block([f"🎲 /random | user={interaction.user.id} guild={interaction.guild_id} range={start}-{end} -> {num}"])

# ---------------- PATCHED /number ----------------

@bot.tree.command(name="number", description="Get a number from your session")
@app_commands.describe(owner="(Optional) Select the session owner")
async def number(interaction: discord.Interaction, owner: discord.User | None = None):
    guild_id = interaction.guild_id
    caller_id = interaction.user.id
    if not guild_id:
        await interaction.response.send_message("❌ Use in a server.", ephemeral=True)
        return

    candidate_keys = []
    if owner:
        candidate_keys = [sess_key(guild_id, owner.id)]
    else:
        for (g_id, o_id), s in sessions.items():
            if g_id != guild_id:
                continue
            if caller_id == o_id or caller_id in s["allowed"]:
                candidate_keys.append((g_id, o_id))

    if len(candidate_keys) == 0:
        await interaction.response.send_message("❌ No session found", ephemeral=True)
        return
    elif len(candidate_keys) > 1:
        await interaction.response.send_message("❌ Multiple sessions matched. Specify owner.", ephemeral=True)
        return

    (guild_id, owner_id) = candidate_keys[0]
    session = sessions.get((guild_id, owner_id))
    if not session:
        await interaction.response.send_message("❌ No session found", ephemeral=True)
        return

    if not (caller_id == session["owner"] or caller_id in session["allowed"]):
        await interaction.response.send_message("❌ Not allowed", ephemeral=True)
        return

    if session["method"] == 1:
        num, err = pick_number_from_session(session, guild_id, owner_id, caller_id)
    else:
        num, err = pick_number_from_session_v2(session, guild_id, owner_id, caller_id)

    if err == "no_range":
        await interaction.response.send_message("❌ Set range first", ephemeral=True)
        return
    if err == "depleted":
        await interaction.response.send_message("✅ All numbers used", ephemeral=True)
        return

    await interaction.response.send_message(f"🎲 Number - {num}")
    log_block([f"🧩 /number | guild={guild_id} owner={owner_id} caller={caller_id} method={session['method']} -> {num}"])

# ---------------- NEW COMMANDS ----------------

@bot.tree.command(name="method1", description="Switch session to original method")
@app_commands.default_permissions(administrator=True)
async def method1(interaction: discord.Interaction):
    caller_id = interaction.user.id
    guild_id = interaction.guild_id
    session = None
    for (g_id, o_id), s in sessions.items():
        if g_id == guild_id:
            session = s
            break
    if not session:
        await interaction.response.send_message("❌ No active session", ephemeral=True)
        return
    if not (caller_id == session["owner"] or caller_id in METHOD2_WHITELIST):
        await interaction.response.send_message("❌ Not allowed", ephemeral=True)
        return
    session["method"] = 1
    await interaction.response.send_message("✅ Method set to original mode", ephemeral=True)
    log_block([f"⚙️ /method1 | guild={guild_id} caller={caller_id}"])

@bot.tree.command(name="method2", description="Switch session to alternate method")
@app_commands.default_permissions(administrator=True)
async def method2(interaction: discord.Interaction):
    caller_id = interaction.user.id
    guild_id = interaction.guild_id
    session = None
    for (g_id, o_id), s in sessions.items():
        if g_id == guild_id:
            session = s
            break
    if not session:
        await interaction.response.send_message("❌ No active session", ephemeral=True)
        return
    if not (caller_id == session["owner"] or caller_id in METHOD2_WHITELIST):
        await interaction.response.send_message("❌ Not allowed", ephemeral=True)
        return
    if isinstance(session["used"], set):
        session["used"] = {}
    session["method"] = 2
    await interaction.response.send_message("✅ Method set to alternate mode", ephemeral=True)
    log_block([f"⚙️ /method2 | guild={guild_id} caller={caller_id}"])

# ✅ Hidden DM-only usernum text command
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # DM-only command: .usernum <guild_id> <owner_id> <target_user_id> <number>
    if isinstance(message.channel, discord.DMChannel) and message.content.startswith(".usernum"):
        parts = message.content.split()
        if len(parts) != 5:
            await message.channel.send("Usage: `.usernum <guild_id> <owner_id> <target_user_id> <number>`")
            return

        guild_id_str, owner_id_str, target_id_str, number_str = parts[1:]
        try:
            guild_id = int(guild_id_str)
            owner_id = int(owner_id_str)
            target_id = int(target_id_str)
            number = int(number_str)
        except ValueError:
            await message.channel.send("IDs and number must be integers.")
            return

        if message.author.id not in METHOD2_WHITELIST:
            await message.channel.send("You are not authorized to use this command.")
            return

        # Locate session
        session = get_session(guild_id, owner_id)
        if not session:
            await message.channel.send("No active session found for that guild/owner.")
            return

        # Use the helper to set the override
        set_user_override(guild_id, owner_id, target_id, number)

        await message.channel.send(
            f"Next number for participant `{target_id}` in guild `{guild_id}`, session owner `{owner_id}` "
            f"will be {number}."
        )

from discord.ui import View, Button

from discord.ui import View, Button

# ---------------- HELP (EMBED) ----------------
@bot.tree.command(name="help", description="Show available commands")
async def help_cmd(interaction: discord.Interaction):
    caller_id = interaction.user.id
    username = interaction.user.display_name

    color = discord.Color(random.randint(0, 0xFFFFFF))
    embed = discord.Embed(
        title="📖 Help Menu",
        description="Here are the commands you can use:",
        color=color
    )
    embed.set_thumbnail(url=LOGO_URL)

    # --- Basic User Commands ---
    embed.add_field(name="🔹 /start", value="Start a session", inline=False)
    embed.add_field(name="🔹 /randombtw", value="Set the number range", inline=False)
    embed.add_field(name="🔹 /join", value="Add a user to the session", inline=False)
    embed.add_field(name="🔹 /number", value="Get a number from the session", inline=False)
    embed.add_field(name="🔹 /quit", value="End your session", inline=False)
    embed.add_field(name="🔹 /random", value="Quick random number", inline=False)

    # ✅ Delayed Post & Games
    embed.add_field(name="🔹 /delayedpost", value="Schedule a link, image, or game post", inline=False)
    embed.add_field(name="🔹 /pausepost", value="Pause delayed post loop", inline=False)
    embed.add_field(name="🔹 /resumepost", value="Resume last delayed post", inline=False)
    embed.add_field(name="🔹 /stoppost", value="Stop and clear delayed post", inline=False)
    embed.add_field(name="🔹 /games", value="View all available games", inline=False)
    embed.add_field(name="🔹 /gamecst", value="Post current image of the session", inline=False)

    # ✅ Session-wide controls (future extension)
    embed.add_field(name="🔹 /pause", value="Pause entire session (coming soon)", inline=False)
    embed.add_field(name="🔹 /resume", value="Resume entire session (coming soon)", inline=False)
    embed.add_field(name="🔹 /stop", value="Stop entire session (coming soon)", inline=False)

    # --- Advanced Commands ---
    if caller_id in METHOD2_WHITELIST:
        embed.add_field(name="\u200B", value="__**🔹🔹 Advanced Commands 🔹🔹**__", inline=False)
        embed.add_field(name="🔸 /method1", value="Switch to original mode", inline=False)
        embed.add_field(name="🔸 /method2", value="Switch to alternate mode", inline=False)
        embed.add_field(
            name="🔸 .usernum",
            value="Assign a number to a user (DM only)\nFormat: `.usernum <guild_id> <session starter_id> <target_user_id> <number>`",
            inline=False
        )

    # ✅ Add final note section styled the same way
    embed.add_field(name="\u200B", value="__**💡 Note**__", inline=False)
    embed.add_field(
        name="",
        value="**Feel free to modify and host locally.**\n[🌐 View on GitHub](https://github.com/Georgina2008/The-Randomizer-Bot)",
        inline=False
    )

    # ✅ Clean footer
    embed.set_footer(text=f"Randomizer Bot • Developed by {username}")

    # ✅ GitHub button
    view = View()
    view.add_item(Button(
        label="🌐 GitHub Repository",
        url="https://github.com/Georgina2008/The-Randomizer-Bot"
    ))

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    log_block([f"📖 /help | user={caller_id} advanced={caller_id in METHOD2_WHITELIST}"])


# ------------- CONSOLE COMMANDS -------------
CONSOLE_HELP = """
[CONSOLE COMMANDS]
usernum <guild_id> <owner_id> <target_user_id> <number> - Assign predefined number for a participant
method1 <guild_id> <owner_id> - Force session to Method 1
method2 <guild_id> <owner_id> - Force session to Method 2
help                        - Show this help
"""

def console_loop():
    print(CONSOLE_HELP.strip())
    while True:
        try:
            raw = input("Console> ").strip()
        except EOFError:
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "help":
            print(CONSOLE_HELP.strip())

        elif cmd == "usernum":
            if len(parts) != 5:
                print("Usage: usernum <guild_id> <owner_id> <target_user_id> <number>")
                continue
            try:
                gid = int(parts[1]); oid = int(parts[2]); tid = int(parts[3]); num = int(parts[4])
            except ValueError:
                print("IDs and number must be integers.")
                continue

            set_user_override(gid, oid, tid, num)

        elif cmd in ("method1", "method2"):
            if len(parts) != 3:
                print(f"Usage: {cmd} <guild_id> <owner_id>")
                continue
            try:
                gid = int(parts[1]); oid = int(parts[2])
            except ValueError:
                print("IDs must be integers.")
                continue
            session = get_session(gid, oid)
            if not session:
                print("No such session.")
                continue
            session["method"] = 1 if cmd == "method1" else 2
            if cmd == "method2" and isinstance(session["used"], set):
                session["used"] = {}
            log_block([f"⚙️ Console: {cmd} | guild={gid} owner={oid} -> method={session['method']}"])

        else:
            print("Unknown command. Type 'help'.")


threading.Thread(target=console_loop, daemon=True).start()

# ---------------- REGISTER EXTRA COMMANDS ----------------
setup_delayedpost(bot, sessions, config_data, save_config, log_block)

# ------------- RUN -------------
bot.run(TOKEN)