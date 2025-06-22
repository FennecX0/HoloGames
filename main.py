import discord
from discord.ext import commands
import json
import random
import asyncio
import os
import string
import secrets

# === Load cards ===
with open("cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# === Config ===
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

rarity_titles = {
    "C": "Common Idol",
    "R": "Rising Star",
    "RRR": "Rare Radiance",
    "SR": "Super Rare",
    "SSR": "Superstar Idol",
    "TOH": "🌟 Talent of Hololive 🌟"
}

PULL_LIMIT = 50

# === Setup bot ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Utilities ===

def rarity_color(rarity):
    if rarity in ["SSR", "TOH"]:
        return discord.Color.gold()
    elif rarity in ["SR", "SP"]:
        return discord.Color.purple()
    else:
        return discord.Color.blue()

def generate_uid(length=6):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def draw_card():
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    pool = [c for c in cards if c["rarity"] == rarity]
    card = random.choice(pool)
    card_copy = card.copy()
    card_copy["uid"] = generate_uid()
    card_copy["title"] = rarity_titles.get(card["rarity"], "") + f" • {card['name']}"
    return card_copy

# === Inventory ===

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

def get_user_pulls(user_id):
    data = load_inventory()
    return len(data.get(str(user_id), []))

# === Commands ===

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def gacha(ctx):
    if get_user_pulls(ctx.author.id) >= PULL_LIMIT:
        await ctx.send("🚫 You've reached the limit of 50 pulls!")
        return

    card = draw_card()
    add_to_inventory(ctx.author.id, card)

    anim = rarity_animations.get(card["rarity"], "")
    await ctx.send(f"🎆 {ctx.author.display_name} is summoning...")
    if anim:
        await ctx.send(anim)
    await asyncio.sleep(6)

    embed = discord.Embed(
        title=f"{ctx.author.display_name} pulled a {card['rarity']} card!",
        description=f"**{card['name']}**\n💥 ATK: `{card['attack']}` | 🛡 DEF: `{card['defense']}`\n💰 Value: ¥{card['value']}\n🆔 UID: `{card['uid']}`",
        color=rarity_color(card['rarity'])
    )
    embed.set_footer(text=card["title"])
    await ctx.send(embed=embed)

@bot.command()
async def gacha10(ctx):
    if get_user_pulls(ctx.author.id) + 10 > PULL_LIMIT:
        await ctx.send("🚫 You've reached the limit of 50 pulls!")
        return

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
        title=f"{ctx.author.display_name}'s 10x Pull (Best: {best_rarity})",
        color=rarity_color(best_rarity)
    )
    for i, card in enumerate(pulled, start=1):
        embed.add_field(
            name=f"{i}. {card['rarity']} — {card['name']}",
            value=f"ATK: `{card['attack']}` | DEF: `{card['defense']}` | ¥{card['value']} | UID: `{card['uid']}`",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx, *, args=""):
    data = load_inventory()
    uid = str(ctx.author.id)
    if uid not in data or len(data[uid]) == 0:
        await ctx.send(f"{ctx.author.display_name}, your inventory is empty!")
        return

    user_cards = data[uid]
    sort_key = "rarity"
    if "sort=name" in args:
        sort_key = "name"
    elif "sort=value" in args:
        sort_key = "value"

    if sort_key == "value":
        sorted_cards = sorted(user_cards, key=lambda c: c["value"], reverse=True)
    elif sort_key == "name":
        sorted_cards = sorted(user_cards, key=lambda c: c["name"])
    else:
        rarity_order = ["TOH", "SSR", "SR", "RRR", "R", "C"]
        sorted_cards = sorted(user_cards, key=lambda c: rarity_order.index(c["rarity"]))

    lines = []
    for card in sorted_cards[:20]:  # only show top 20 to avoid spam
        lines.append(f"[{card['rarity']}] {card['name']} | UID: `{card['uid']}`")

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Inventory (Sorted by {sort_key})",
        description="\n".join(lines) + f"\n\nTotal cards: **{len(user_cards)}**",
        color=discord.Color.teal()
    )
    await ctx.send(embed=embed)

@bot.command()
async def view(ctx, uid: str):
    data = load_inventory()
    user_cards = data.get(str(ctx.author.id), [])
    card = next((c for c in user_cards if c.get("uid") == uid.upper()), None)

    if not card:
        await ctx.send("❌ Card with that UID not found in your inventory.")
        return

    embed = discord.Embed(
        title=f"{card['title']} ({card['rarity']})",
        description=f"💥 ATK: `{card['attack']}`\n🛡 DEF: `{card['defense']}`\n💰 Value: ¥{card['value']}\n🆔 UID: `{card['uid']}`",
        color=rarity_color(card['rarity'])
    )
    await ctx.send(embed=embed)

# === Run the bot ===
bot.run(os.getenv("DISCORD_TOKEN"))
