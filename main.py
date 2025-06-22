import discord
from discord.ext import commands
import json
import random
import asyncio
import os

# Load the cards
with open("cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# Rarity settings
rarity_weights = {
    "C": 79,
    "R": 50,
    "RRR": 10,
    "SR": 4,
    "SSR": 2,
    "TOH": 0.01
}

rarity_animations = {
    "C": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "R": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RRR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "SR": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SP": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SSR": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif"
}

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Gacha draw helper
def draw_card():
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    possible_cards = [card for card in cards if card["rarity"] == rarity]
    return random.choice(possible_cards)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def gacha(ctx):
    card = draw_card()

    # Show animation first
    anim = rarity_animations.get(card["rarity"], "")
    await ctx.send(f"🎆 Summoning... get ready!", file=discord.File(fp=os.devnull) if not anim else None, embed=discord.Embed(title="✨", image=anim) if anim else None)
    await ctx.send(anim)

    # Wait 6 seconds for dramatic effect
    await asyncio.sleep(6)

    # Show card reveal
    embed = discord.Embed(
        title=f"You pulled a {card['rarity']} card!",
        description=f"**{card['name']}**\n💥 ATK: `{card['attack']}` | 🛡 DEF: `{card['defense']}`\n🎯 Value: ¥{card['value']}",
        color=discord.Color.gold() if card['rarity'] in ["SSR", "TOH"] else discord.Color.blue()
    )
    if card.get("title"):
        embed.set_footer(text=card["title"])

    await ctx.send(embed=embed)

# Start bot
bot.run(os.getenv("DISCORD_TOKEN"))
