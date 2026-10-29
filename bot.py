import os
import discord
from discord.ext import tasks, commands
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- RENDER WEB SERVER FIX ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")
    def log_message(self, format, *args):
        return  # Hiljennetään turhat logimerkinnät

def run_web_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), SimpleHandler)
        print(f"Web server successfully started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Web server error: {e}")

# Käynnistetään web-serveri heti taustalle
threading.Thread(target=run_web_server, daemon=True).start()
# -----------------------------

# Haetaan salaisuudet turvallisesti ympäristömuuttujista
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
STEAM_APP_ID = "1196080"  # Space Simulation Toolkit

intents = discord.Intents.default()
intents.message_content = True  # Korjaa aiemman varoituksen
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

    await interaction.response.send_message(f" **Space Simulation Toolkit** current players: **{player_count}**")

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
            
        await channel.send(message)
        print("Player status updated to Discord automatically!")

bot.run(TOKEN)
