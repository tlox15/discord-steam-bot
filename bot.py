import os
import discord
from discord.ext import tasks, commands
import requests
from flask import Flask
import threading

# Luodaan Flask-websovellus Renderin vaatimaa porttia varten
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

# Haetaan salaisuudet ympäristömuuttujista
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
STEAM_APP_ID = "1196080"  # Space Simulation Toolkit

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

all_time_peak = 0

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
    check_players.start()

@bot.tree.command(name="players", description="Shows the current player count of Space Simulation Toolkit")
async def players(interaction: discord.Interaction):
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={STEAM_APP_ID}"
    try:
        response = requests.get(url).json()
        player_count = response["response"]["player_count"]
    except Exception as e:
        await interaction.response.send_message(f"Error fetching data from Steam: {e}", ephemeral=True)
        return

    try:
        await interaction.response.send_message(f" **Space Simulation Toolkit** current players: **{player_count}**")
    except discord.errors.HTTPException as e:
        if e.status == 429:
            await interaction.response.send_message(" The server IP is temporarily rate-limited by Discord. Please try again in a moment!", ephemeral=True)
        else:
            raise e

@tasks.loop(hours=1)
async def check_players():
    global all_time_peak
    
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={STEAM_APP_ID}"
    try:
        response = requests.get(url).json()
        player_count = response["response"]["player_count"]
    except Exception as e:
        print(f"Error fetching Steam data: {e}")
        return

    record_broken = False
    if player_count > all_time_peak:
        all_time_peak = player_count
        record_broken = True

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        message = f" **Space Simulation Toolkit** player status:\n• Current players: **{player_count}**\n• All-time peak: **{all_time_peak}**"
        if record_broken:
            message += "  **New record broken!**"
            
        try:
            await channel.send(message)
            print("Player status updated to Discord automatically!")
        except Exception as e:
            print(f"Failed to send automated message due to rate limit or error: {e}")

def run_discord_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_discord_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
