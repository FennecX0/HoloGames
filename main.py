import discord
from discord.ext import commands
import json
import random
import asyncio
import os

# Load cards
with open("cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# Rarity weights
rarity_weights = {
    "C": 79,
    "R": 50,
    "RRR": 10,
    "SR": 4,
    "SSR": 2,
    "TOH": 0.01
}

# Cutscene animations
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
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Gacha Helpers ===

def draw_card():
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    pool = [c for c in cards if c["rarity"] == rarity]
    return random.choice(pool)

def rarity_color(rarity):
    if rarity in ["SSR", "TOH"]:
        return discord.Color.gold()
    elif rarity in ["SR", "SP"]:
        return discord.Color.purple()
    else:
        return discord.Color.blue()

# === Inventory System ===

def load_inventory():
    if not os.path.exists("inventory.json"):
        with open("inventory.json", "w") as f:
            json.dump({}, f)
    with open("inventory.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_inventory(data):
    with open("inventory.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_to_inventory(user_id, card):
    data = load_inventory()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append(card)
    save_inventory(data)

# === Bot Events & Commands ===

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def gacha(ctx):
    card = draw_card()
    add_to_inventory(ctx.author.id, card)

    anim = rarity_animations.get(card["rarity"], "")
    await ctx.send(f"🎆 {ctx.author.display_name} is summoning...")
    if anim:
        await ctx.send(anim)
    await asyncio.sleep(6)

    embed = discord.Embed(
        title=f"{ctx.author.display_name} pulled a {card['rarity']} card!",
        description=f"**{card['name']}**\n💥 ATK: `{card['attack']}` | 🛡 DEF: `{card['defense']}`\n💰 Value: ¥{card['value']}",
        color=rarity_color(card['rarity'])
    )
    if card.get("title"):
        embed.set_footer(text=card["title"])
    await ctx.send(embed=embed)

@bot.command()
async def gacha10(ctx):
    pulled = [draw_card() for _ in range(10)]
    for card in pulled:
        add_to_inventory(ctx.author.id, card)

    rarity_rank = ["C", "R", "RRR", "SR", "SP", "SSR", "TOH"]
    best_rarity = max(pulled, key=lambda c: rarity_rank.index(c["rarity"]))["rarity"]
    anim = rarity_animations.get(best_rarity, "")

    await ctx.send(f"🎆 {ctx.author.display_name} is performing a 10x Summon...")
    if anim:
        await ctx.send(anim)
    await asyncio.sleep(6)

    embed = discord.Embed(
        title=f"🎉 {ctx.author.display_name}'s 10x Pull (Best: {best_rarity})",
        color=rarity_color(best_rarity)
    )
    for i, card in enumerate(pulled, start=1):
        embed.add_field(
            name=f"{i}. {card['rarity']} — {card['name']}",
            value=f"💥 ATK: `{card['attack']}` | 🛡 DEF: `{card['defense']}` | 💰 ¥{card['value']}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    data = load_inventory()
    uid = str(ctx.author.id)

    if uid not in data or len(data[uid]) == 0:
        await ctx.send(f"{ctx.author.display_name}, your inventory is empty!")
        return

    user_cards = data[uid]
    total = len(user_cards)

    # Count rarities
    rarity_count = {}
    character_names = set()
    for card in user_cards:
        rarity = card["rarity"]
        name = card["name"]
        rarity_count[rarity] = rarity_count.get(rarity, 0) + 1
        character_names.add(name)

    rarity_lines = "\n".join(f"- {rarity}: {count}" for rarity, count in sorted(rarity_count.items(), key=lambda x: -x[1]))
    name_list = ", ".join(sorted(character_names))

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Inventory",
        description=f"📦 Total cards: **{total}**\n\n🔹 **Rarity Summary:**\n{rarity_lines}\n\n🔸 **Characters Collected:**\n{name_list}",
        color=discord.Color.teal()
    )

    await ctx.send(embed=embed)

# Run bot
bot.run(os.getenv("DISCORD_TOKEN"))
