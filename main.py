import discord
from discord.ext import commands
import json
import random
import asyncio
import os
import time

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load data
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

cards = load_json("cards.json")
inventory = load_json("inventory.json")
pull_timers = load_json("pull_timer.json")
banner_prefs = load_json("banner_prefs.json")

rarity_weights = {
    "C": 79, "R": 50, "RR": 20, "RRR": 10, "SP": 1, "SR": 4,
    "SSR": 2, "SSR+": 1, "ALT": 0.10, "ALT+": 0.1, "TOH": 0.01
}

rarity_animations = {
    "C": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "R": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "RRR": "https://media.tenor.com/KGwWGVz9-XQAAAAM/genshin-impact-wish.gif",
    "SP": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SR": "https://media.tenor.com/JcMSVVkgfgMAAAAM/genshin-wish.gif",
    "SSR": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "SSR+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "ALT": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "ALT+": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif",
    "TOH": "https://media.tenor.com/edP0ZdPcU8IAAAAM/genshin-impact-wish.gif"
}

banner_images = {
    "EN": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320198222479506/Untitled133_20250622200308.png",
    "JP": "https://cdn.discordapp.com/attachments/1383855862673571891/1386320188110143589/Untitled135_20250622201347.png"
}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def draw_card(group):
    pool = [card for card in cards if card["group"] == group]
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    while True:
        rarity = random.choices(rarities, weights=weights, k=1)[0]
        candidates = [card for card in pool if card["rarity"] == rarity]
        if candidates:
            return random.choice(candidates)

@bot.command()
async def banner(ctx):
    embed = discord.Embed(title="ðŸŽ´ Choose Your Banner", description="Type `!enbanner` or `!jpbanner` to pull from a banner.")
    embed.set_image(url=banner_images["EN"])
    await ctx.send(embed=embed)
    await ctx.send(embed=discord.Embed().set_image(url=banner_images["JP"]))

@bot.command()
async def enbanner(ctx):
    banner_prefs[str(ctx.author.id)] = "EN"
    save_json("banner_prefs.json", banner_prefs)
    await ctx.send("âœ… You are now pulling from the **EN** banner.")

@bot.command()
async def jpbanner(ctx):
    banner_prefs[str(ctx.author.id)] = "JP"
    save_json("banner_prefs.json", banner_prefs)
    await ctx.send("âœ… You are now pulling from the **JP** banner.")

def check_limit(user_id):
    now = time.time()
    info = pull_timers.get(user_id, {"count": 0, "last": now})
    if now - info["last"] > 1800:
        info = {"count": 0, "last": now}
    if info["count"] >= 50:
        return False, int(1800 - (now - info["last"]))
    return True, info

def update_timer(user_id, pulls):
    info = pull_timers.get(user_id, {"count": 0, "last": time.time()})
    now = time.time()
    if now - info["last"] > 1800:
        info = {"count": 0, "last": now}
    info["count"] += pulls
    pull_timers[user_id] = info
    save_json("pull_timer.json", pull_timers)

@bot.command()
async def gacha10(ctx):
    user_id = str(ctx.author.id)
    ok, info = check_limit(user_id)
    if not ok:
        await ctx.send(f"ðŸ•’ You've reached your 50 pull limit! Try again in {info} seconds.")
        return

    group = banner_prefs.get(user_id, "EN")
    pulled = [draw_card(group) for _ in range(10)]
    highest = sorted(pulled, key=lambda x: list(rarity_weights).index(x["rarity"]))[-1]
    anim = rarity_animations.get(highest["rarity"])
    await ctx.send(anim)
    await asyncio.sleep(6)

    for card in pulled:
        uid = card["uid"]
        inventory.setdefault(user_id, []).append(uid)
        embed = discord.Embed(
            title=f"{card['name']} - {card['rarity']}",
            description=f"ðŸŽ´ {card['title']} | ðŸ’¥ {card['attack']} | ðŸ›¡ {card['defense']} | ðŸ’° Â¥{card['value']}",
            color=discord.Color.gold() if card["rarity"] in ["SSR", "SSR+", "ALT", "ALT+", "TOH"] else discord.Color.blue()
        )
        embed.set_footer(text=f"Pulled by {ctx.author.display_name} | UID: {uid}")
        await ctx.send(embed=embed)

    update_timer(user_id, 10)
    save_json("inventory.json", inventory)

@bot.command()
async def inventory(ctx, sort_by="rarity"):
    user_id = str(ctx.author.id)
    inv = inventory.get(user_id, [])
    if not inv:
        await ctx.send("ðŸ“¦ Your inventory is empty!")
        return

    items = [card for card in cards if card["uid"] in inv]
    items.sort(key=lambda x: x.get(sort_by, ""))
    for card in items[:20]:
        embed = discord.Embed(
            title=f"{card['name']} - {card['rarity']}",
            description=f"ðŸŽ´ {card['title']} | ðŸ’¥ {card['attack']} | ðŸ›¡ {card['defense']} | ðŸ’° Â¥{card['value']}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"UID: {card['uid']}")
        await ctx.send(embed=embed)

@bot.command()
async def view(ctx, uid):
    for card in cards:
        if card["uid"].lower() == uid.lower():
            embed = discord.Embed(
                title=f"{card['name']} - {card['rarity']}",
                description=f"ðŸŽ´ {card['title']} | ðŸ’¥ {card['attack']} | ðŸ›¡ {card['defense']} | ðŸ’° Â¥{card['value']}",
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"UID: {card['uid']}")
            await ctx.send(embed=embed)
            return
    await ctx.send("âŒ Card not found.")

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
