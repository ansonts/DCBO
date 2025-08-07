import discord
from discord.ext import commands
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
DISCORD_TOKEN = "MTQwMDM0MzYxNDYyNTY4MTU0MQ.GKRmIB.vkKosqHC0krwT-UuA0JjcZNLMXIOQlSKwJqSjs"  # Replace with your Discord bot token
DEEPSEEK_API_KEY = "sk-7a15e5c7db3a43acbd00088ae370cdf7"  # Replace with your DeepSeek API key
TARGET_LANGUAGE = "en"  # Target language code (e.g., 'en' for English, 'zh' for Chinese, 'es' for Spanish)
SOURCE_CHANNEL_ID = YOUR_CHANNEL_ID  # Replace with your Discord channel ID (integer)

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
        "model": "deepseek-chat",  # Use DeepSeek-R1 or DeepSeek-V3 as needed
        "messages": [
            {
                "role": "system",
                "content": f"You are a translator. Translate the following text to {target_language}. Provide only the translated text in the response."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        translated_text = result['choices'][0]['message']['content'].strip()
        return translated_text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error translating text: {e}")
        return None

# Discord bot event: On ready
@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")

# Discord bot event: On message
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself or from other channels
    if message.author == bot.user or message.channel.id != SOURCE_CHANNEL_ID:
        return
    
    # Get the message content
    content = message.content
    if not content:
        return
    
    # Translate the message
    translated_text = translate_text(content, TARGET_LANGUAGE)
    if translated_text:
        # Send the translated message back to the channel
        await message.channel.send(f"**Translated ({TARGET_LANGUAGE}):** {translated_text}")
    else:
        await message.channel.send("Error: Could not translate the message.")
    
    # Process commands (if any)
    await bot.process_commands(message)

# Run the bot
bot.run(DISCORD_TOKEN)