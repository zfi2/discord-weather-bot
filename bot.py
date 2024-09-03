import os
import discord
import requests
import urllib.parse
import asyncio
from datetime import datetime, timedelta

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
INCLUDE_LOCATION_IN_MESSAGE = False

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

cities = {}
with open('cities.txt', 'r') as file:
    for line in file:
        city, country = line.strip().lower().split(',')
        cities[city] = country

tomorrow_bro = 'tomorrow bro'
weather_messages = {
    "massive_thunderstorm": f"very big thunderstorm {tomorrow_bro} :thunder_cloud_rain: :thunder_cloud_rain: :thunder_cloud_rain:",
    "severe_thunderstorm": f"big thunderstorm {tomorrow_bro} :thunder_cloud_rain: :thunder_cloud_rain:",
    "thunderstorm": f"thunderstorm {tomorrow_bro} :thunder_cloud_rain:",
    "blizzard": f"blizzard {tomorrow_bro}",
    "snow": f"snow {tomorrow_bro} :cloud_snow:",
    "hurricane": f"hurricane {tomorrow_bro} :cloud_tornado:",
    "rain": f"rain {tomorrow_bro}",
    "windy": f"very big winds {tomorrow_bro} :leaves:",
    "extreme_heat": f"extremely cooked {tomorrow_bro} :fried_shrimp:",
    "warm": f"warm {tomorrow_bro} :hotsprings:",
    "icy": f"very icy {tomorrow_bro} :ice_cube:",
    "cold": f"cold {tomorrow_bro} :snowflake:"
}

@client.event
async def on_ready():
    print(f'{client.user} connected')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.lower()

    if content.startswith('weather'):
        await message.channel.send('at your disposal vro :heart:')
        return

    matches = [city for city in cities if city in content]

    if not matches:
        return
    elif len(matches) == 1:
        location = f"{matches[0].title()},{cities[matches[0]]}"
        await check_weather(message.channel, location)
    else:
        view = discord.ui.View()
        for i, match in enumerate(matches[:5]):
            button = discord.ui.Button(label=f"{match.title()}, {cities[match]}".lower().replace(',', ' '), custom_id=str(i))
            view.add_item(button)
        
        sent_message = await message.channel.send("i got a bit confused can you specify please", view=view)
        
        try:
            interaction = await client.wait_for('interaction', timeout=30.0)
            selected = matches[int(interaction.data['custom_id'])]
            location = f"{selected.title()},{cities[selected]}"
            await interaction.response.defer()
            await sent_message.delete()
            await check_weather(message.channel, location)
        except asyncio.TimeoutError:
            await message.channel.send("choice expired bro")
            await sent_message.delete()
        except Exception as e:
            print(f"error in city selection: {str(e)}")
            await message.channel.send("some error occurred try again bro")
            await sent_message.delete()

async def check_weather(channel, location):
    print(f"checking weather for: {location}")
    encoded_location = urllib.parse.quote(location)
    
    try:
        geocode_data = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_location}&count=1&language=en&format=json").json()
        print(f"geocode api response: {geocode_data}")
        
        if not geocode_data.get('results'):
            city = location.split(',')[0]
            geocode_data = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json").json()
            print(f"new geocode api response: {geocode_data}")
        
        lat, lon = geocode_data['results'][0]['latitude'], geocode_data['results'][0]['longitude']
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        weather_data = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,weathercode,windspeed_10m_max&timezone=auto&start_date={tomorrow}&end_date={tomorrow}").json()
        
        temp = weather_data['daily']['temperature_2m_max'][0]
        weather_code = weather_data['daily']['weathercode'][0]
        wind_speed = weather_data['daily']['windspeed_10m_max'][0]
        
        if weather_code in [95, 96, 99]:
            if wind_speed > 120:
                message = weather_messages["massive_thunderstorm"]
            elif wind_speed > 90:
                message = weather_messages["severe_thunderstorm"]
            else:
                message = weather_messages["thunderstorm"]
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            message = weather_messages["blizzard"] if wind_speed > 50 else weather_messages["snow"]
        elif weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            message = weather_messages["hurricane"] if wind_speed > 90 else weather_messages["rain"]
        elif wind_speed > 120:
            message = weather_messages["windy"]
        elif temp > 40:
            message = weather_messages["extreme_heat"]
        elif temp > 20:
            message = weather_messages["warm"]
        elif temp < -10:
            message = weather_messages["icy"]
        else:
            message = weather_messages["cold"]

        message_text = f"{message}\n-# {location}" if INCLUDE_LOCATION_IN_MESSAGE else message

        if 'chicago' in location.lower():
            await channel.send(message_text.replace("tomorrow bro", "tomorrow and a shootout bro"))
        else:
            await channel.send(message_text)
    
    except Exception as e:
        print(f"error: {str(e)}")

client.run(DISCORD_BOT_TOKEN)
