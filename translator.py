import discord
from discord.ext import commands
import requests
import os
import logging
from dotenv import load_dotenv

# Load .env file for local testing
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID1", "0"))

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

# DeepSeek API function to detect language
def detect_language(text):
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
                "content": "You are a language detection expert. Analyze the following text and return only the ISO 639-1 language code (e.g., 'en' for English, 'ja' for Japanese) with high confidence. Prioritize English ('en') and Japanese ('ja') for short or ambiguous text. If uncertain, return 'en' as a fallback."
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
        logger.error(f"Error detecting language: {e}")
        return None

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

    # Detect the language of the message
    detected_language = detect_language(content)
    if not detected_language:
        await message.channel.send(f"Error: Could not detect language for message by {message.author.name}.")
        return

    # Determine target language based on detected language
    if detected_language == "en":
        target_language = "ja"
    
    else:
        target_language = "en"

    # Translate the message
    translated_text = translate_text(content, target_language)
    if translated_text:
        await message.channel.send(f"** {message.author.display_name}:** {translated_text}")
    else:
        await message.channel.send(f"Error: Could not translate message from {detected_language} by {message.author.display_name} to {target_language}.")
    
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)