import discord
from discord import app_commands
import asyncio
from discord.ui import View, Button

# Built-in games (use image URLs for hosting)
BUILT_IN_GAMES = {
    "game1": "https://i.ibb.co/bSt28cG/srt9b216uhfa1.png",
    "game2": "https://i.ibb.co/xtWCXH5Z/C3fBXkq.png",
    "game3": "https://i.ibb.co/ZptxhPpq/carbon.png",
    "game4": "https://i.ibb.co/rKC8CY0J/RDT-20250428-2151089210212630016384303.png"
}

def setup_delayedpost(bot, sessions, config_data, save_config_func, log_block):
    active_loops = {}

    # Cancel running loop
    def cancel_loop(guild_id):
        if guild_id in active_loops:
            active_loops[guild_id]["cancel"] = True
            active_loops.pop(guild_id, None)

    async def start_loop(interaction, guild_id, delay, content, loop_mode):
        await interaction.followup.send(
            f"✅ Started delayed post loop (every {delay}s)" if loop_mode else f"✅ Post scheduled in {delay}s",
            ephemeral=True
        )

        async def loop_task():
            while True:
                if guild_id not in active_loops or active_loops[guild_id]["cancel"]:
                    break
                try:
                    await interaction.channel.send(content)
                except Exception as e:
                    await interaction.channel.send(f"❌ Failed to post: {e}")
                if not loop_mode:
                    break
                await asyncio.sleep(delay)

        active_loops[guild_id] = {"cancel": False}
        asyncio.create_task(loop_task())

    @bot.tree.command(name="games", description="Show all available built-in games")
    async def games(interaction: discord.Interaction):
        embed = discord.Embed(title="🎮 Available Games", color=discord.Color.green())
        for name, url in BUILT_IN_GAMES.items():
            embed.add_field(name=name, value=f"[Image Link]({url})", inline=False)
        await interaction.response.send_message(embed=embed)

    # Dynamic dropdown for games
    def build_game_choices():
        return [app_commands.Choice(name=name.capitalize(), value=name) for name in BUILT_IN_GAMES.keys()]

    @bot.tree.command(name="delayedpost", description="Schedule link, image or built-in game posting")
    @app_commands.describe(delay="Delay in seconds (minimum 30)", link="Provide a link", file="Upload an image", loop="Loop post? True/False")
    @app_commands.choices(game=build_game_choices())
    async def delayedpost(interaction: discord.Interaction, delay: int, link: str = None, file: discord.Attachment = None, game: app_commands.Choice[str] = None, loop: bool = False):
        await interaction.response.defer(ephemeral=True)
        caller_id = interaction.user.id
        guild_id = interaction.guild_id

        # Session check
        session = None
        if guild_id:
            for (g_id, o_id), s in sessions.items():
                if g_id == guild_id and (caller_id == o_id or caller_id in s["allowed"]):
                    session = s
                    break
        if not session:
            await interaction.followup.send("❌ You are not in any active session.", ephemeral=True)
            return

        if delay < 30:
            await interaction.followup.send("⚠️ Minimum delay is 30 seconds.", ephemeral=True)
            return

        if not link and not file and not game:
            await interaction.followup.send("⚠️ Provide a link, upload a file, or choose a game.", ephemeral=True)
            return

        # Prepare content
        content = ""
        if game:
            content = BUILT_IN_GAMES[game.value]
        elif link:
            content = link
        elif file:
            # store attachment URL instead of raw discord.File
            content = file.url

        # Resume or start new
        if str(guild_id) in config_data["delayed_posts"]:
            view = View()
            btn_resume = Button(label="Resume Previous", style=discord.ButtonStyle.green)
            btn_new = Button(label="Start New", style=discord.ButtonStyle.blurple)

            async def resume_callback(btn_interaction):
                prev = config_data["delayed_posts"][str(guild_id)]
                await start_loop(interaction, guild_id, prev["delay"], prev["content"], prev["loop"])
                await btn_interaction.response.send_message("✅ Resumed previous delayed post.", ephemeral=True)

            async def new_callback(btn_interaction):
                config_data["delayed_posts"][str(guild_id)] = {"delay": delay, "content": content, "loop": loop}
                save_config_func(config_data)
                await start_loop(interaction, guild_id, delay, content, loop)
                await btn_interaction.response.send_message("✅ Started new delayed post.", ephemeral=True)

            btn_resume.callback = resume_callback
            btn_new.callback = new_callback
            view.add_item(btn_resume)
            view.add_item(btn_new)

            await interaction.followup.send("⚠️ Previous delayed post exists. Choose an action:", view=view)
        else:
            config_data["delayed_posts"][str(guild_id)] = {"delay": delay, "content": content, "loop": loop}
            save_config_func(config_data)
            await start_loop(interaction, guild_id, delay, content, loop)

    # Post control commands
    @bot.tree.command(name="pausepost", description="Pause delayed posting in this session")
    async def pausepost(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id in active_loops:
            active_loops[guild_id]["cancel"] = True
            await interaction.response.send_message("⏸️ Delayed post loop paused.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No active delayed post loop.", ephemeral=True)

    @bot.tree.command(name="resumepost", description="Resume last delayed posting")
    async def resumepost(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if str(guild_id) in config_data["delayed_posts"]:
            prev = config_data["delayed_posts"][str(guild_id)]
            await start_loop(interaction, guild_id, prev["delay"], prev["content"], prev["loop"])
        else:
            await interaction.response.send_message("❌ No previous delayed post found.", ephemeral=True)

    @bot.tree.command(name="gamecst", description="Instantly cast the last scheduled image/link/game")
    async def gamecst(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        caller_id = interaction.user.id

        # Session check
        session = None
        if guild_id:
            for (g_id, o_id), s in sessions.items():
                if g_id == guild_id and (caller_id == o_id or caller_id in s["allowed"]):
                    session = s
                    break

        if not session:
            await interaction.response.send_message("❌ You are not in any active session.", ephemeral=True)
            return

        # Check if something exists in config
        if str(guild_id) not in config_data["delayed_posts"]:
            await interaction.response.send_message("⚠️ No previous content found to cast.", ephemeral=True)
            return

        prev = config_data["delayed_posts"][str(guild_id)]
        content = prev["content"]

        try:
            # since we always store URLs/links/strings now
            await interaction.channel.send(content)
            await interaction.response.send_message("✅ Casted the last scheduled content.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to cast: {e}", ephemeral=True)

    @bot.tree.command(name="stoppost", description="Stop delayed posting completely")
    async def stoppost(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        cancel_loop(guild_id)
        if str(guild_id) in config_data["delayed_posts"]:
            del config_data["delayed_posts"][str(guild_id)]
            save_config_func(config_data)
        await interaction.response.send_message("🛑 Delayed post loop stopped and cleared.", ephemeral=True)
