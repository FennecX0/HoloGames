import discord
from discord.ext import commands
import random
import json
import os

# ✅ Setup Discord Intents
intents = discord.Intents.default()
intents.message_content = True  # Required for commands to work

# ✅ Bot setup with prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Load allowed channel ID from environment
ALLOWED_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ✅ Load card data from cards.json
with open("cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# ✅ Define rarity color codes for embed visuals
RARITY_COLORS = {
    "C": 0x95a5a6,
    "R": 0x3498db,
    "RR": 0x9b59b6,
    "RRR": 0xe67e22,
    "SP": 0xf1c40f,
    "SR": 0x1abc9c,
    "SSR": 0xe74c3c,
    "SSR+": 0xc0392b,
    "ALT": 0x8e44ad,
    "ALT+": 0x2c3e50,
    "TOH": 0x000000
}

@bot.event
async def on_ready():
    print(f"🎴 Gacha bot is online as {bot.user}!")

@bot.command()
async def pull(ctx):
    # ✅ Check if the command was used in the correct channel
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        return  # Do nothing if used in the wrong channel

    # ✅ Pick a random card
    card = random.choice(cards)

    # ✅ Build the embed message
    embed = discord.Embed(
        title=f"{card['name']} — {card['title']}",
        description=(
            f"**Rarity:** {card['rarity']}\n"
            f"**Origin:** `{card['origin']}`\n"
            f"**UID:** `{card['uid']}`\n"
            f"**Value:** ¥{card['value']}"
        ),
        color=RARITY_COLORS.get(card['rarity'], 0xFFFFFF)
    )
    embed.set_image(url=card["image"])
    embed.set_footer(text=f"ATK: {card['atk']} | DEF: {card['def']} | MP: {card['mp']}")

    await ctx.send(embed=embed)

# ✅ Run the bot using the Discord token from Railway variables
bot.run(os.getenv("DISCORD_TOKEN"))
