import os
import discord
from discord.ext import tasks, commands
import requests

# Haetaan salaisuudet turvallisesti ympäristömuuttujista
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
STEAM_APP_ID = "1196080"  # Space Simulation Toolkit

# Käytetään komentoja tukevaa bottia (vaaditaan slash-komentoihin)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

all_time_peak = 0

@bot.event
async def on_ready():
    print(f"Kirjauduttiin sisään nimellä {bot.user}")
    
    # Synkronoidaan slash-komennot Discordiin, jotta ne ilmestyvät näkyviin
    try:
        synced = await bot.tree.sync()
        print(f"Synronoitu {len(synced)} slash-komentoa.")
    except Exception as e:
        print(f"Error initializing commands: {e}")
        
    # Käynnistetään tunnin välein pyörivä automaattipäivitys
    check_players.start()

# Luodaan slash-komento /pelaajat
@bot.tree.command(name="pelaajat", description="Current player amount")
async def pelaajat(interaction: discord.Interaction):
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={STEAM_APP_ID}"
    try:
        response = requests.get(url).json()
        player_count = response["response"]["player_count"]
    except Exception as e:
        await interaction.response.send_message(f"Error initializing: {e}", ephemeral=True)
        return

    await interaction.response.send_message(f"**Space Simulation Toolkit** Current players: **{player_count}**")

# Automaattinen taustasilmukka (päivittää kanavalle tunnin välein)
@tasks.loop(hours=1)
async def check_players():
    global all_time_peak
    
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={STEAM_APP_ID}"
    try:
        response = requests.get(url).json()
        player_count = response["response"]["player_count"]
    except Exception as e:
        print(f"Virhe haettaessa Steam-tietoja: {e}")
        return

    record_broken = False
    if player_count > all_time_peak:
        all_time_peak = player_count
        record_broken = True

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        message = f"**Space Simulation Toolkit** Info:\n• Current players: **{player_count}**\n• Highest recorded: **{all_time_peak}**"
        if record_broken:
            message += " **Record broken**"
            
        await channel.send(message)
        print("Pelaajatilanne päivitetty Discordiin automaattisesti!")

bot.run(TOKEN)
