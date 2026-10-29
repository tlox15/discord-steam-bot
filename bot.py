import os
import discord
from discord.ext import tasks
import requests

# Haetaan salaisuudet turvallisesti pilvipalvelun ympäristömuuttujista
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
STEAM_APP_ID = "1196080"  # Space Simulation Toolkit

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Muuttuja ennätyksen tallennukseen muistissa
all_time_peak = 0

@client.event
async def on_ready():
    print(f"Kirjauduttiin sisään nimellä {client.user}")
    # Käynnistetään taustasilmukka, joka tarkistaa tilanteen heti ja sen jälkeen tunnin välein
    check_players.start()

@tasks.loop(hours=1)
async def check_players():
    global all_time_peak
    
    # Haetaan pelaajamäärä Steamista
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={STEAM_APP_ID}"
    try:
        response = requests.get(url).json()
        player_count = response["response"]["player_count"]
    except Exception as e:
        print(f"Virhe haettaessa Steam-tietoja: {e}")
        return

    # Tarkistetaan onko syntynyt uusi ennätys
    record_broken = False
    if player_count > all_time_peak:
        all_time_peak = player_count
        record_broken = True

    # Lähetetään viesti Discord-kanavalle
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        message = f"**Space Simulation Toolkit** pelaajatilanne:\n• Pelaajia nyt: **{player_count}**\n• Kaikkien aikojen huippu: **{all_time_peak}**"
        if record_broken:
            message += " **Uusi ennätys rikottu!**"
            
        await channel.send(message)
        print("Pelaajatilanne päivitetty Discordiin!")

client.run(TOKEN)
