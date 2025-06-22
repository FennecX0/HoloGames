import discord
from discord.ext import commands
import json
import asyncio
import random
import os  # Needed for Railway environment variable

# Set up Discord bot intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Load cards from JSON file
def load_cards():
    with open("cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Define rarity weights
RARITY_WEIGHTS = {
    "C": 65.79,
    "R": 20,
    "RRR": 10,
    "SR": 4,
    "SSR": 0.2,
    "TOH": 0.01
}

# Get summon animation based on rarity
def get_rarity_animation(rarity):
    if rarity in ["C", "R", "RR", "RRR"]:
        return "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif"
    elif rarity in ["SP", "SR"]:
        return "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif"
    elif rarity in ["SSR", "SSR+", "ALT", "ALT+", "TOH"]:
        return "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif"
    return None

# Gacha roll logic
def gacha_roll():
    cards = load_cards()
    chosen_rarity = random.choices(
        population=list(RARITY_WEIGHTS.keys()),
        weights=list(RARITY_WEIGHTS.values()),
        k=1
    )[0]
    candidates = [c for c in cards if c["rarity"] == chosen_rarity]
    return random.choice(candidates) if candidates else None

# Gacha command
@bot.command()
async def gacha(ctx):
    card = gacha_roll()
    if not card:
        await ctx.send("No card found for that rarity.")
        return

    glow = get_rarity_animation(card["rarity"])

    # Show summon light first
    embed = discord.Embed(title="🎲 Gacha Roll", description=f"Summoning your card...\n**Rarity:** {card['rarity']}")
    if glow:
        embed.set_image(url=glow)
    await ctx.send(embed=embed)

    # Wait for dramatic effect
    await asyncio.sleep(3)

    # Reveal the card
    result = discord.Embed(
        title=f"✨ You got {card['name']}!",
        description=f"**Rarity:** {card['rarity']}\n**Value:** ¥{card['value']}\n**Special Move:** {card['special_move']}"
    )
    if card.get("title"):
        result.add_field(name="💠 TOH Title", value=card["title"], inline=False)
    await ctx.send(embed=result)

# Start the bot using Railway's environment variable
bot.run(os.getenv("DISCORD_TOKEN"))
