import discord
import requests
import urllib.parse
from datetime import datetime, timedelta

DISCORD_BOT_TOKEN = 'your_discord_bot_token'
INCLUDE_LOCATION_IN_MESSAGE = False

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

cities = {line.strip().lower().split(',')[0]: line.strip().split(',')[1] for line in open('cities.txt', 'r')}

weather_messages = {
    "massive_thunderstorm": "very big thunderstorm tomorrow :thunder_cloud_rain: :thunder_cloud_rain: :thunder_cloud_rain:",
    "severe_thunderstorm": "big thunderstorm tomorrow :thunder_cloud_rain: :thunder_cloud_rain:",
    "thunderstorm": "thunderstorm tomorrow :thunder_cloud_rain:",
    "blizzard": "blizzard tomorrow",
    "snow": "its gonna snow tomorrow bro :cloud_snow:",
    "hurricane": "hurricane tomorrow :cloud_tornado:",
    "rain": "its gonna rain tomorrow bro",
    "windy": "very big winds tomorrow :leaves:",
    "extreme_heat": "youre extremely cooked tomorrow bro stay hydrated :fried_shrimp:",
    "warm": "its gonna be warm tomorrow bro :hotsprings:",
    "icy": "you are gonna freeze tomorrow bro :ice_cube:",
    "cold": "its gonna be cold tomorrow bro :snowflake:"
}

@client.event
async def on_ready():
    print(f'{client.user} connected')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.lower() == 'test':
        await message.channel.send('at your disposal vro :heart:')
        return

    content = message.content.lower()
    for city in cities:
        if city in content:
            location = f"{city.title()},{cities[city]}"
            await check_weather(message.channel, location)
            return
    
    await message.channel.send("that place doesnt exist or im too dumb to find it my bad")

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
            message = weather_messages["massive_thunderstorm"] if wind_speed > 120 else \
                    weather_messages["severe_thunderstorm"] if wind_speed > 90 else \
                    weather_messages["thunderstorm"]
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
        
        if INCLUDE_LOCATION_IN_MESSAGE:
            await channel.send(f"{message}\n-# {location}")
        else:
            await channel.send(message)
    
    except Exception as e:
        print(f"error: {str(e)}")

client.run(DISCORD_BOT_TOKEN)