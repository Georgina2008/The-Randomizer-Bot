# Randomizer Discord Bot

A feature-rich Discord bot that provides random number generation, session-based uniqueness, delayed content posting, and built-in games.

---

## Features

- **Session-Based Random Numbers**
  - Users can start a session in a server and set a numeric range.
  - Two methods for number picking:
    - **Method 1**: Global uniqueness within the session.
    - **Method 2**: Per-user unique numbers, preventing immediate duplicates across users.

- **User Management**
  - Session owner can allow other users to join.
  - Owner controls session range, method, and permissions.

- **Random Number Generation**
  - `/number` — Get a number from an active session.
  - `/random` — Get a quick random number without creating a session.

- **Delayed Posting & Built-in Games**
  - Schedule delayed posts with `/delayedpost`.
  - Supports sending links, uploaded images, or built-in game images.
  - Can loop posts repeatedly or send only once.
  - Commands for pause/resume/stop (`/pausepost`, `/resumepost`, `/stoppost`).
  - `/games` lists all built-in games and their images.
  - `/gamecst` instantly re-sends the last scheduled content.

- **Advanced & Admin Controls**
  - `.usernum` (DM-only): Whitelisted admins can assign a predefined number for a user.
  - `/method1` and `/method2`: Switch number picking logic.
  - Console commands available for advanced control.

- **Persistent Configuration**
  - Stores data in `bot_config.json` so sessions and delayed posts survive restarts.

---

## Commands Overview

### Basic User Commands
- `/start` — Start a new session in the server.
- `/randombtw <start> <end>` — Set numeric range for the session.
- `/join <user_id>` — Add another user to the session.
- `/number [owner]` — Get a number from the session (owner optional if multiple sessions).
- `/quit` — End your session.
- `/random <start> <end>` — Get a quick random number.
- `/help` — Show all commands (and advanced commands if whitelisted).

### Delayed Post & Game Commands
- `/delayedpost <delay> [link|file|game] [loop]` — Schedule link/image/game to post later or repeatedly.
  - Minimum delay: 30 seconds.
  - `loop` optional: If `true`, repeats at interval.
- `/pausepost` — Pause the delayed posting loop.
- `/resumepost` — Resume the last delayed posting.
- `/stoppost` — Stop and clear delayed post settings.
- `/games` — Show all available built-in games (with image links).
- `/gamecst` — Instantly post the last scheduled link/image/game.

### Advanced / Admin Commands
- `/method1` — Switch session to Method 1 (global uniqueness).
- `/method2` — Switch session to Method 2 (per-user uniqueness).
- `.usernum <user_id> <number>` — DM-only; assign a predefined next number to a user.
- **Console Commands** (run in terminal where bot runs):
  - `.usernum <guild_id> <owner_id> <target_user_id> <number>` — Predefine next number.
  - `method1 <guild_id> <owner_id>` — Force method 1 for session.
  - `method2 <guild_id> <owner_id>` — Force method 2 for session.

---

## File Structure

- **`randomizer.py`** — Main bot file, handles Discord commands and events.
- **`task1_logic.py`** — Implements Method 2 number logic.
- **`delayedpost_logic.py`** — Handles delayed posting & built-in games.
- **`config_manager.py`** — Load and save bot configuration.
- **`bot_config.json`** — Stores persistent data (sessions & delayed posts).

---

## How to Start (Setup & Run)

1. **Install Python dependencies:**
   ```bash
   pip install discord.py
   ```

2. **Configure Bot Token:**
   - Open `randomizer.py`.
   - Find the line:
     ```python
     TOKEN = "YOUR_DISCORD_BOT_TOKEN"
     METHOD2_WHITELIST = {1234} Put your discord account id there
      ```
   - Replace with your bot's token from the Discord Developer Portal.

   - Open `delayedpost_logic.py`.
   - Find the line:
     BUILT_IN_GAMES = {
    "game1": "https://i.ibb.co/bSt28cG/srt9b216uhfa1.png",
    "game2": "https://i.ibb.co/xtWCXH5Z/C3fBXkq.png",
    "game3": "https://i.ibb.co/ZptxhPpq/carbon.png",
    "game4": "https://i.ibb.co/rKC8CY0J/RDT-20250428-2151089210212630016384303.png"
}
   - Replace with your own custom images, follow the format to addd more.


3. **Run the Bot:**
   ```bash
   python randomizer.py
   ```

4. **Invite the Bot to Your Server:**
   - Create an invite link with proper permissions (slash commands + message send).
   - Use the OAuth2 URL from the Discord Developer Portal.

---

## Notes & Tips

- Minimum delay for `/delayedpost` is **30 seconds**.
- Delayed posts and sessions **persist between restarts** (saved in `bot_config.json`).
- The bot uses **slash commands** (Discord interactions); it must have **application.commands** permissions.
- For `.usernum` and `/method2`, make sure your Discord ID is in `METHOD2_WHITELIST` in `randomizer.py`.
- The bot runs a **console loop** for advanced commands (seen directly in your terminal).

---

## Example Workflow

1. Start a session with `/start`.
2. Set range with `/randombtw 1 100`.
3. Add users via `/join <user_id>`.
4. Users get unique numbers using `/number`.
5. Schedule an image post using:
   ```bash
   /delayedpost 60 link=https://example.com/image.png loop=true
   ```
6. Pause/resume with `/pausepost` and `/resumepost`.

---

Developed for flexible random number draws and scheduled content posting for Discord servers.

**Notes:**  
- Idea & concept by me; coding fully by AI (ChatGPT Free Version).  
- Free to modify and improve.
- Host Locally, rest up to you.

