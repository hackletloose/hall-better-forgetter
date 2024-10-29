import discord
from discord.ext import tasks, commands
import datetime
import asyncio
import os
from dotenv import load_dotenv
import pytz  # Zeitzonenunterstützung

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
TIMEZONE = os.getenv('LOCAL_TIMEZONE', 'Europe/Berlin')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} ist nun bereit und verbunden!')
    await delete_old_messages()  # Nachrichten beim Starten löschen
    schedule_deletion.start()  # Starte den täglichen Lösch-Task

async def delete_old_messages():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f'Kanal mit ID {CHANNEL_ID} nicht gefunden.')
        return

    seven_days_ago = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=7)

    async for message in channel.history(limit=None):
        if message.created_at < seven_days_ago:
            try:
                await message.delete()
                await asyncio.sleep(1)
            except discord.Forbidden:
                print('Fehler: Keine Berechtigung zum Löschen der Nachricht.')
            except discord.HTTPException as e:
                print(f'Fehler beim Löschen der Nachricht: {e}')

@tasks.loop(hours=24)
async def schedule_deletion():
    print('Starte tägliche Lösch-Routine...')
    await delete_old_messages()

@schedule_deletion.before_loop
async def before_schedule_deletion():
    # Warten, bis der Bot bereit ist
    await bot.wait_until_ready()
    # Lokale Zeitzone festlegen
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    next_midnight = tz.localize(datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time.min))
    await asyncio.sleep((next_midnight - now).total_seconds())

bot.run(TOKEN)
