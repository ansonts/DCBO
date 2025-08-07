from dotenv import load_dotenv
load_dotenv()  # Load .env file
import discord
from discord.ext import commands
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")  # Default to English
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", "0"))  # Replace with your channel ID

# Validate environment variables
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN is not set. Please configure it in environment variables.")
    exit(1)
if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY is not set. Please configure it in environment variables.")
    exit(1)
if SOURCE_CHANNEL_ID == 0:
    logger.error("SOURCE_CHANNEL_ID is not set or invalid. Please configure it in environment variables.")
    exit(1)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# DeepSeek API function to translate text
def translate_text(text, target_language):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": f"You are a translator. Translate the following text to {target_language}. Provide only the translated text."
            },
            {"role": "user", "content": text}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error translating text: {e}")
        return None

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != SOURCE_CHANNEL_ID:
        return
    content = message.content
    if not content:
        return
    translated_text = translate_text(content, TARGET_LANGUAGE)
    if translated_text:
        await message.channel.send(f"**Translated ({TARGET_LANGUAGE}):** {translated_text}")
    else:
        await message.channel.send("Error: Could not translate the message.")
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)