import discord
from discord.ext import commands
import requests
import os
import logging
import time
from dotenv import load_dotenv
from aiohttp import web
import asyncio

# Load .env file for local testing
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
JAPANESE_CHANNEL_ID = int(os.getenv("JAPANESE_CHANNEL_ID", "0"))
ENGLISH_CHANNEL_ID = int(os.getenv("ENGLISH_CHANNEL_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))  # Default to 10000 if PORT not set

# Validate environment variables
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN is not set. Please configure it in environment variables.")
    exit(1)
if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY is not set. Please configure it in environment variables.")
    exit(1)
if JAPANESE_CHANNEL_ID == 0:
    logger.error("JAPANESE_CHANNEL_ID is not set or invalid. Please configure it in environment variables.")
    exit(1)
if ENGLISH_CHANNEL_ID == 0:
    logger.error("ENGLISH_CHANNEL_ID is not set or invalid. Please configure it in environment variables.")
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
                "content": f"You are a translation expert. Translate the following text to {target_language} with high accuracy. Provide only the translated text. For short or ambiguous text, prioritize natural translations. If untranslatable, return 'Untranslatable content'."
            },
            {"role": "user", "content": text}
        ],
        "temperature": 0.7
    }
    for attempt in range(5):
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            translated_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            if not translated_text:
                logger.warning(f"Empty translation for text '{text}' to {target_language}.")
                return "Untranslatable content"
            return translated_text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}). Retrying after 5 seconds...")
                time.sleep(5)
            else:
                logger.error(f"HTTP error translating text (attempt {attempt + 1}): {e}")
                if attempt == 4:
                    return None
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error translating text (attempt {attempt + 1}): {e}")
            if attempt == 4:
                return None
            time.sleep(2)
    logger.error(f"Translation failed for '{text}' to {target_language} after 5 attempts.")
    return None

# HTTP server to keep Render service alive
async def handle_health_check(request):
    return web.Response(text="OK")

async def start_http_server():
    app = web.Application()
    app.add_routes([web.get('/', handle_health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"HTTP server started on port {PORT}")

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    content = message.content
    if not content or content.isspace() or all(c in '😀😊👍' for c in content):  # Skip empty or emoji-only messages
        logger.info(f"Skipping empty or emoji-only message from {message.author.display_name}.")
        return

    # Check if message is in Japanese or English channel
    if message.channel.id == JAPANESE_CHANNEL_ID:
        # Translate Japanese to English and post in English channel
        target_language = "en"
        translated_text = translate_text(content, target_language)
        if translated_text:
            english_channel = bot.get_channel(ENGLISH_CHANNEL_ID)
            if english_channel:
                output = f"{message.author.display_name}: {translated_text}"
                logger.info(f"Sending to English channel: {output}")
                await english_channel.send(output)
            else:
                logger.error(f"English channel ID {ENGLISH_CHANNEL_ID} not found.")
                await message.channel.send(f"Error: Could not translate message by {message.author.display_name}.")
        else:
            await message.channel.send(f"Error: Could not translate message by {message.author.display_name}.")
    elif message.channel.id == ENGLISH_CHANNEL_ID:
        # Translate English to Japanese and post in Japanese channel
        target_language = "ja"
        translated_text = translate_text(content, target_language)
        if translated_text:
            japanese_channel = bot.get_channel(JAPANESE_CHANNEL_ID)
            if japanese_channel:
                output = f"{message.author.display_name}: {translated_text}"
                logger.info(f"Sending to Japanese channel: {output}")
                await japanese_channel.send(output)
            else:
                logger.error(f"Japanese channel ID {JAPANESE_CHANNEL_ID} not found.")
                await message.channel.send(f"Error: Could not translate message by {message.author.display_name}.")
        else:
            await message.channel.send(f"Error: Could not translate message by {message.author.display_name}.")
    
    await bot.process_commands(message)

# Run bot and HTTP server concurrently
async def main():
    await asyncio.gather(
        bot.start(DISCORD_TOKEN),
        start_http_server()
    )

if __name__ == "__main__":
    asyncio.run(main())